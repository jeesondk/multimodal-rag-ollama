import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "multimodal_rag")
    DB_USER = os.getenv("DB_USER", "raguser")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "ragpassword")

    # Ollama
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5-vl:7b")
    TEXT_MODEL = os.getenv("TEXT_MODEL", "qwen2.5:14b")

    # Vector
    VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "768"))

    @property
    def db_config(self):
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "database": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD
        }


config = Config()