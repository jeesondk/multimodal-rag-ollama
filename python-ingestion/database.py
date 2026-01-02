import psycopg2
from psycopg2.extras import Json, execute_values
from pgvector.psycopg2 import register_vector
from typing import List, Dict, Optional
from config import config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, register_vector_type=True):
        self.conn = None
        self.register_vector_type = register_vector_type
        self.connect()

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**config.db_config)
            if self.register_vector_type:
                register_vector(self.conn)
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def setup(self):
        """Create tables and indexes"""
        with self.conn.cursor() as cur:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Now register the vector type after creating the extension
            register_vector(self.conn)

            # Create documents table
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    metadata JSONB,
                    content_type VARCHAR(50),
                    embedding vector({config.VECTOR_DIMENSION}),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create index for vector similarity search
            cur.execute("""
                CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                ON documents USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            """)

            # Create index on content_type for filtering
            cur.execute("""
                CREATE INDEX IF NOT EXISTS documents_content_type_idx 
                ON documents (content_type);            
            """)

            self.conn.commit()
            logger.info("Database setup complete")

    def insert_document(self, content: str, embedding: List[float],
                        content_type: str, metadata: Optional[Dict] = None):
        """Insert a single document"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (content, metadata, content_type, embedding) 
                VALUES (%s, %s, %s, %s)
                    RETURNING id
            """, (content, Json(metadata or {}), content_type, embedding))

            doc_id = cur.fetchone()[0]
            self.conn.commit()
            return doc_id

    def search_similar(self, query_embedding: List[float],
                       top_k: int = 5,
                       content_type: Optional[str] = None) -> List[Dict]:
        """Search for similar documents"""
        with self.conn.cursor() as cur:
            if content_type:
                cur.execute("""
                    SELECT id, content, metadata, content_type,
                           embedding <=> %s as distance
                    FROM documents
                    WHERE content_type = %s
                    ORDER BY embedding <=> %s
                    LIMIT %s
                """, (query_embedding, content_type, query_embedding, top_k))
            else:
                cur.execute("""
                            SELECT id,
                                   content,
                                   metadata,
                                   content_type,
                                   embedding <=> %s as distance
                            FROM documents
                            ORDER BY embedding <=> %s
                            LIMIT %s
                            """, (query_embedding, query_embedding, top_k))

            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'content': row[1],
                    'metadata': row[2],
                    'content_type': row[3],
                    'distance': float(row[4])
                })

            return results

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
