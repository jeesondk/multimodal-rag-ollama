from typing import List, Dict

class TextProcessor:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks

    @staticmethod
    def clean_text(text: str) -> str:
        """Basic text cleaning"""

        # Remove excessive whitespace
        text = ' '.join(text.split())
        return text.strip()
