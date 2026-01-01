from setuptools import setup, find_packages

setup(
    name="multimodal-rag-ingestion",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ollama>=0.1.0",
        "psycopg2-binary>=2.9.9",
        "pgvector>=0.2.3",
        "pillow>=10.0.0",
        "pypdf>=3.17.0",
        "python-magic>=0.4.27",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0",
    ],
)