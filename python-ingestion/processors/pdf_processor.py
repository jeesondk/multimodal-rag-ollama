from pypdf import PdfReader
from typing import List, Dict

class PDFProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text from a PDF file"""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def extract_pages(pdf_path: str) -> List[Dict[str, any]]:
        """Extract text from each page separately"""
        reader = PdfReader(pdf_path)
        pages = []

        for i, page in enumerate(reader.pages):
            pages.append({
                'page_number': i + 1,
                'text': page.extract_text(),
                'metadata': {
                    'total_pages': len(reader.pages)
                }
            })

        return pages