#!/usr/bin/env python3
import argparse
import sys
from ingestion import MultimodalIngestion
from database import Database
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_database():
    """Initialize database schema"""
    logger.info("Setting up database...")
    db = Database(register_vector_type=False)
    db.setup()
    db.close()
    logger.info("Database setup complete!")


def ingest_file(file_path: str):
    """Ingest a single file"""
    logger.info(f"Ingesting file: {file_path}")
    ingestion = MultimodalIngestion()

    try:
        if file_path.endswith('.pdf'):
            ingestion.ingest_pdf(file_path)
        elif file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            ingestion.ingest_image(file_path)
        elif file_path.endswith('.txt'):
            with open(file_path, 'r') as f:
                ingestion.ingest_text(f.read(), {'source': file_path})
        else:
            logger.error(f"Unsupported file type: {file_path}")
    finally:
        ingestion.close()


def ingest_directory(directory_path: str):
    """Ingest all files from a directory"""
    logger.info(f"Ingesting directory: {directory_path}")
    ingestion = MultimodalIngestion()

    try:
        ingestion.ingest_directory(directory_path)
    finally:
        ingestion.close()


def main():
    parser = argparse.ArgumentParser(description='Multimodal RAG Ingestion Pipeline')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Setup command
    subparsers.add_parser('setup', help='Initialize database schema')

    # Ingest file command
    file_parser = subparsers.add_parser('ingest-file', help='Ingest a single file')
    file_parser.add_argument('file', help='Path to file')

    # Ingest directory command
    dir_parser = subparsers.add_parser('ingest-dir', help='Ingest all files from directory')
    dir_parser.add_argument('directory', help='Path to directory')

    args = parser.parse_args()

    if args.command == 'setup':
        setup_database()
    elif args.command == 'ingest-file':
        ingest_file(args.file)
    elif args.command == 'ingest-dir':
        ingest_directory(args.directory)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()