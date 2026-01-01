from PIL import Image
import os


class ImageProcessor:
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

    @staticmethod
    def is_valid_image(file_path: str) -> bool:
        """Check if file is a supported image"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ImageProcessor.SUPPORTED_FORMATS

    @staticmethod
    def get_image_metadata(file_path: str) -> dict:
        """Extract basic image metadata"""
        with Image.open(file_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height
            }