# Multimodal RAG Solution

Full-stack RAG system with Python ingestion, .NET orchestration, and Ollama local models.

## Prerequisites

- Mac M4 Pro (or similar ARM Mac)
- Docker Desktop
- .NET 8 SDK
- Python 3.11+
- Ollama installed and running

## Quick Start
```bash
# Make setup script executable
chmod +x start.sh

# Run setup
./start.sh
```

## Manual Setup

### 1. Start Database
```bash
docker-compose up -d pgvector
```

### 2. Setup Python Environment
```bash
cd python-ingestion
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py setup
```

### 3. Ingest Data
```bash
# Ingest a single file
python main.py ingest-file /path/to/document.pdf

# Ingest directory
python main.py ingest-dir /path/to/documents
```

### 4. Run .NET API
```bash
cd ../dotnet-orchestration/MultimodalRAG
dotnet restore
dotnet run
```

### 5. Start Open WebUI
```bash
docker-compose up -d open-webui
```

Access at http://localhost:3000

## Architecture

- **Python**: Document ingestion and embedding
- **.NET**: Query orchestration with Semantic Kernel
- **PGVector**: Vector similarity search
- **Ollama**: Local LLM and embedding models
- **Open WebUI**: Chat interface

## API Endpoints

- `POST /api/rag/query` - Query the RAG system
- `GET /api/rag/health` - Health check

## Configuration

Edit `.env` for Python settings and `appsettings.json` for .NET settings.

## API Endpoints (Minimal API)

### Query & Search
- `POST /api/rag/query` - Full RAG query with context retrieval and generation
- `POST /api/rag/search` - Vector search only (no generation)

### Testing & Utilities
- `GET /api/rag/health` - Health check
- `GET /api/rag/stats` - Database statistics
- `POST /api/rag/embed` - Get embeddings for text
- `POST /api/rag/generate` - Direct text generation

### Interactive API Docs
When running in development mode, access Swagger UI at:
- http://localhost:5000/swagger

### Example Usage
```bash
# Full RAG Query
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "topK": 5
  }'

# Search only
curl -X POST http://localhost:5000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "topK": 3,
    "contentType": "pdf"
  }'

# Get stats
curl http://localhost:5000/api/rag/stats
```