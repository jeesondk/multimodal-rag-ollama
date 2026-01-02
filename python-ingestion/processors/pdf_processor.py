import fitz  # pymupdf
from PIL import Image
from typing import List, Dict, Optional, Tuple
import io
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Enhanced PDF processor that extracts text, images, and tables"""

    def __init__(self, extract_images: bool = True, min_image_size: int = 10000):
        """
        Initialize PDF processor

        Args:
            extract_images: Whether to extract embedded images
            min_image_size: Minimum image size in bytes to extract (filters out icons/small graphics)
        """
        self.extract_images = extract_images
        self.min_image_size = min_image_size

    def extract_text(self, file_path: str) -> str:
        """Extract text from a PDF file"""
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text

    def extract_pages(self, pdf_path: str) -> List[Dict]:
        """
        Extract multimodal content from each page

        Returns a list of page dictionaries containing:
        - page_number: Page number (1-indexed)
        - text: Extracted text content
        - images: List of extracted images with metadata
        - tables: List of detected table regions (basic detection)
        - metadata: PDF metadata
        """
        doc = fitz.open(pdf_path)
        pages = []

        for page_num, page in enumerate(doc):
            page_data = {
                'page_number': page_num + 1,
                'text': page.get_text(),
                'images': [],
                'tables': [],
                'metadata': {
                    'total_pages': len(doc),
                    'pdf_path': pdf_path
                }
            }

            # Extract images from page
            if self.extract_images:
                page_data['images'] = self._extract_page_images(page, page_num + 1, pdf_path)

            # Detect potential table regions (basic heuristic)
            page_data['tables'] = self._detect_tables(page)

            pages.append(page_data)

        doc.close()
        logger.info(f"Extracted {len(pages)} pages from {pdf_path}")
        return pages

    def _extract_page_images(self, page: fitz.Page, page_num: int, pdf_path: str) -> List[Dict]:
        """Extract images from a PDF page"""
        images = []
        image_list = page.get_images()

        for img_index, img_info in enumerate(image_list):
            try:
                xref = img_info[0]
                base_image = page.parent.extract_image(xref)

                # Filter out small images (likely icons or decorations)
                if len(base_image["image"]) < self.min_image_size:
                    continue

                # Create a temporary file for the image
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Convert to PIL Image for consistency
                pil_image = Image.open(io.BytesIO(image_bytes))

                # Save to temporary file
                temp_dir = tempfile.gettempdir()
                temp_filename = f"pdf_img_p{page_num}_i{img_index}.{image_ext}"
                temp_path = os.path.join(temp_dir, temp_filename)
                pil_image.save(temp_path)

                images.append({
                    'image_path': temp_path,
                    'image_index': img_index,
                    'page_number': page_num,
                    'format': image_ext,
                    'size': pil_image.size,
                    'source_pdf': pdf_path
                })

                logger.debug(f"Extracted image {img_index} from page {page_num}: {pil_image.size}")

            except Exception as e:
                logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
                continue

        return images

    def _detect_tables(self, page: fitz.Page) -> List[Dict]:
        """
        Detect potential table regions using basic heuristics

        This is a simple implementation that looks for:
        - Rectangular regions with lines
        - Areas with structured text alignment

        For production use, consider using dedicated libraries like:
        - camelot-py
        - tabula-py
        - pdfplumber
        """
        tables = []

        # Get all drawings (lines, rectangles) on the page
        drawings = page.get_drawings()

        # Simple heuristic: Look for groups of horizontal and vertical lines
        horizontal_lines = []
        vertical_lines = []

        for drawing in drawings:
            for item in drawing["items"]:
                if item[0] == "l":  # line
                    p1, p2 = item[1], item[2]
                    # Check if horizontal or vertical
                    if abs(p1.y - p2.y) < 2:  # Horizontal line
                        horizontal_lines.append((p1, p2))
                    elif abs(p1.x - p2.x) < 2:  # Vertical line
                        vertical_lines.append((p1, p2))

        # If we find both horizontal and vertical lines, it might be a table
        if len(horizontal_lines) >= 3 and len(vertical_lines) >= 2:
            # Calculate bounding box
            all_points = [p for line in horizontal_lines + vertical_lines for p in line]
            if all_points:
                min_x = min(p.x for p in all_points)
                max_x = max(p.x for p in all_points)
                min_y = min(p.y for p in all_points)
                max_y = max(p.y for p in all_points)

                tables.append({
                    'bbox': [min_x, min_y, max_x, max_y],
                    'confidence': 'low',  # Simple heuristic
                    'type': 'grid_table'
                })

        return tables

    def extract_page_as_image(self, pdf_path: str, page_num: int, dpi: int = 300) -> str:
        """
        Convert a specific PDF page to an image

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            dpi: Resolution for conversion

        Returns:
            Path to temporary image file
        """
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]  # Convert to 0-indexed

        # Render page to pixmap
        mat = fitz.Matrix(dpi/72, dpi/72)  # Scale factor
        pix = page.get_pixmap(matrix=mat)

        # Save to temporary file
        temp_dir = tempfile.gettempdir()
        temp_filename = f"pdf_page_{page_num}.png"
        temp_path = os.path.join(temp_dir, temp_filename)

        pix.save(temp_path)
        doc.close()

        logger.info(f"Converted page {page_num} to image: {temp_path}")
        return temp_path

    def get_page_layout_blocks(self, page: fitz.Page) -> List[Dict]:
        """
        Get layout blocks from a page (text, images, tables)
        This provides more structured information about page layout
        """
        blocks = page.get_text("dict")["blocks"]
        structured_blocks = []

        for block in blocks:
            if block["type"] == 0:  # Text block
                structured_blocks.append({
                    "type": "text",
                    "bbox": block["bbox"],
                    "content": " ".join([
                        span["text"]
                        for line in block.get("lines", [])
                        for span in line.get("spans", [])
                    ])
                })
            elif block["type"] == 1:  # Image block
                structured_blocks.append({
                    "type": "image",
                    "bbox": block["bbox"],
                    "width": block.get("width"),
                    "height": block.get("height")
                })

        return structured_blocks
