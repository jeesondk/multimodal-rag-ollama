import psycopg2
from psycopg2.extras import execute_values
from embedders.text_embedder import TextEmbedder
from processors.image_processor import ImageProcessor

class MultimodalIngestion:
    def __init__(self, db_config: dict):
        self.text_embedder = TextEmbedder()
        self.image_processor = ImageProcessor()
        self.conn = psycopg2.connect(**db_config)
        self._setup_database()

    def _setup_database(self):
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT,
                metadata JSONB,
                content_type VARCHAR(50),
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                ON documents USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            """)
            self.conn.commit()

    def ingest_text(self, text: str, metadata: dict = None):
        embedding = self.text_embedder.embed([text])[0]

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (content, metadata, content_type, embedding) 
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (text, metadata or {}, 'text', embedding.toList()))
            self.conn.commit()

    def ingest_image(self, image_path: str, metadata: dict = None):
        # Describe image using vision model
        description = self.image_processor.describe_image(image_path)

        # Embed the description
        embedding = self.text_embedder.embed([description])[0]

        metadata = metadata or {}
        metadata['image_path'] = image_path
        metadata['description'] = description

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (content, metadata, content_type, embedding) 
                VALUES (%s, %s, %s, %s)
            """, (description, metadata, 'image', embedding.toList()))
            self.conn.commit()
