import os
from typing import Optional
from embedders import TextEmbedder, ImageEmbedder
from processors import TextProcessor, ImageProcessor, PDFProcessor
from database import Database
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultimodalIngestion:
    def __init__(self):
        self.db = Database()
        self.text_embedder = TextEmbedder()
        self.image_embedder = ImageEmbedder()
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.pdf_processor = PDFProcessor()

    def ingest_text(self, text: str, metadata: Optional[dict] = None):
        """Ingest plain text"""
        # Clean text
        cleaned = self.text_processor.clean_text(text)

        # Chunk if text is long
        chunks = self.text_processor.chunk_text(cleaned)

        for i, chunk in enumerate(chunks):
            embedding = self.text_embedder.embed_single(chunk)

            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_number'] = i
            chunk_metadata['total_chunks'] = len(chunks)

            doc_id = self.db.insert_document(
                content = chunk,
                embedding = embedding.tolist(),
                content_type = 'text',
                metadata = chunk_metadata
            )

            logger.info(f"Ingested text chunk {i+1}/{len(chunks)}, doc_id: {doc_id}")

    def ingest_image(self, image_path: str, metadata: Optional[dict] = None):
        """Ingest image by describing it and embedding the description"""
        if not self.image_processor.is_valid_image(image_path):
            logger.warning(f"Unsupported image format: {image_path}")
            return

        # Get image metadata
        img_metadata = self.image_processor.get_image_metadata(image_path)

        # Describe image using vision model
        description = self.image_embedder.describe_image(image_path)
        logger.info(f"Image description: {description[:100]}...")

        # Embed the description
        embedding = self.text_embedder.embed_single(description)

        # Merge metadata
        final_metadata = metadata.copy() if metadata else {}
        final_metadata['image_path'] = image_path
        final_metadata['image_info'] = img_metadata
        final_metadata['description'] = description

        doc_id = self.db.insert_document(
            content=description,
            embedding=embedding.tolist(),
            content_type='image',
            metadata=final_metadata
        )

        logger.info(f"Inserted image: {image_path}, doc_id: {doc_id}")

    def ingest_pdf(self, pdf_path: str, metadata: Optional[dict] = None):
        """Ingest PDF by extracting multimodal content from each page"""
        pages = self.pdf_processor.extract_pages(pdf_path)

        for page in pages:
            page_num = page['page_number']
            total_pages = page['metadata']['total_pages']

            # 1. Process text content
            text = self.text_processor.clean_text(page['text'])
            if text.strip():
                chunks = self.text_processor.chunk_text(text)

                for i, chunk in enumerate(chunks):
                    embedding = self.text_embedder.embed_single(chunk)

                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata['pdf_path'] = pdf_path
                    chunk_metadata['page_number'] = page_num
                    chunk_metadata['chunk_index'] = i
                    chunk_metadata['total_chunks'] = len(chunks)
                    chunk_metadata['total_pages'] = total_pages
                    chunk_metadata['content_subtype'] = 'text'

                    doc_id = self.db.insert_document(
                        content=chunk,
                        embedding=embedding.tolist(),
                        content_type='pdf',
                        metadata=chunk_metadata
                    )

                logger.info(f"Ingested {len(chunks)} text chunks from page {page_num}/{total_pages}")

            # 2. Process extracted images
            for img_data in page['images']:
                try:
                    # Use vision model to describe the image
                    description = self.image_embedder.describe_image(img_data['image_path'])
                    logger.info(f"Image description (page {page_num}, img {img_data['image_index']}): {description[:100]}...")

                    # Embed the description
                    embedding = self.text_embedder.embed_single(description)

                    img_metadata = metadata.copy() if metadata else {}
                    img_metadata['pdf_path'] = pdf_path
                    img_metadata['page_number'] = page_num
                    img_metadata['total_pages'] = total_pages
                    img_metadata['content_subtype'] = 'image'
                    img_metadata['image_index'] = img_data['image_index']
                    img_metadata['image_size'] = img_data['size']
                    img_metadata['image_format'] = img_data['format']
                    img_metadata['description'] = description

                    doc_id = self.db.insert_document(
                        content=description,
                        embedding=embedding.tolist(),
                        content_type='pdf',
                        metadata=img_metadata
                    )

                    logger.info(f"Ingested image from page {page_num}/{total_pages}, doc_id: {doc_id}")

                except Exception as e:
                    logger.error(f"Failed to process image on page {page_num}: {e}")

            # 3. Process detected tables
            for table_idx, table in enumerate(page['tables']):
                try:
                    # For tables, we store metadata about their location
                    # The text content should already be captured in the text chunks above
                    table_metadata = metadata.copy() if metadata else {}
                    table_metadata['pdf_path'] = pdf_path
                    table_metadata['page_number'] = page_num
                    table_metadata['total_pages'] = total_pages
                    table_metadata['content_subtype'] = 'table'
                    table_metadata['table_index'] = table_idx
                    table_metadata['table_bbox'] = table['bbox']
                    table_metadata['table_confidence'] = table['confidence']

                    # We could extract text from the table region specifically
                    # For now, just log that we detected it
                    logger.info(f"Detected table on page {page_num} at {table['bbox']}")

                except Exception as e:
                    logger.error(f"Failed to process table on page {page_num}: {e}")

    def ingest_directory(self, directory_path: str):
        """Ingest all supported files from a directory"""
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                try:
                    if ext == '.pdf':
                        self.ingest_pdf(file_path, {'source': file_path})
                    elif ext in ImageProcessor.SUPPORTED_FORMATS:
                        self.ingest_image(file_path, {'source': file_path})
                    elif ext == '.txt':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            self.ingest_text(f.read(), {'source': file_path})
                except Exception as e:
                    logger.error(f"Failed to ingest {file_path}: {e}")

    def close(self):
        """Close database connection"""
        self.db.close()
