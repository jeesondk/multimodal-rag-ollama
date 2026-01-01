import ollama
import numpy as np
from typing import List
from config import config


class TextEmbedder:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.client = ollama.Client(host=config.OLLAMA_HOST)

    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        embeddings = []
        for text in texts:
            response = self.client.embeddings(
                model=self.model_name,
                prompt=text
            )
            embeddings.append(response['embedding'])
        return np.array(embeddings)

    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        response = self.client.embeddings(
            model=self.model_name,
            prompt=text
        )
        return np.array(response['embedding'])