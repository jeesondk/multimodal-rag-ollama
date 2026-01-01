import os
from typing import Optional
from embedders import TextEmbedder
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
        """Ingress plain text"""
        # Clean text
        cleaned = self.text_processor.clean(text)

        # Chunk if text is long
        chunks = self.text_processor.chunk_text(cleaned)

        for i, chunk in enumerate(chunks):
            embedding = self.text_embedder.embed_single(chunk)

            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_number'] = i
            chunk_metadata['total_chunks'] = len(chunks)

            doc_id = self.db.insert_document(
                content = chunk,
                embedding = embedding.toList(),
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
        """Ingest PDF by extracting and chunking text from each page"""
        pages = self.pdf_processor.extract_pages(pdf_path)

        for page in pages:
            text = self.text_processor.clean_text(page['text'])

            if not text.strip():
                continue

            # Chunk page text
            chunks = self.text_processor.chunk_text(text)

            for i, chunk in enumerate(chunks):
                embedding = self.text_embedder.embed_single(chunk)

                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata['pdf_path'] = pdf_path
                chunk_metadata['page_number'] = page['page_number']
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)
                chunk_metadata['total_pages'] = page['metadata']['total_pages']

                doc_id = self.db.insert_document(
                    content=chunk,
                    embedding=embedding.tolist(),
                    content_type='pdf',
                    metadata=chunk_metadata
                )

            logger.info(f"Inserted PDF page {page['page_number']}/{page['metadata']['total_pages']}, doc_id: {doc_id}")

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
