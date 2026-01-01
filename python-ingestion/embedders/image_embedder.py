import ollama
from config import config


class ImageEmbedder:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.VISION_MODEL
        self.client = ollama.Client(host=config.OLLAMA_HOST)

    def describe_image(self, image_path: str) -> str:
        """Generate text description of image for embedding"""
        response = self.client.chat(
            model=self.model_name,
            messages=[{
                'role': 'user',
                'content': 'Describe this image in detail for indexing and search purposes. Include objects, colors, scene, text if any, and overall context.',
                'images': [image_path]
            }]
        )
        return response['message']['content']