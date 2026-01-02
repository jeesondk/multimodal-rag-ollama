# Multimodal RAG Solution

Full-stack RAG (Retrieval-Augmented Generation) system with Python ingestion, .NET orchestration, Open WebUI Pipelines, and Ollama local models.

> **Built with:**
> - [Open WebUI](https://github.com/open-webui/open-webui) - User-friendly interface for LLMs
> - [Ollama](https://ollama.com/) - Local LLM runtime for privacy-focused AI
> - [Claude.ai](https://claude.ai/) - Solution architecture and implementation assistance
> - PGVector - PostgreSQL extension for vector similarity search
> - .NET & Python - Backend orchestration and document processing

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### C4 Model - System Context

```mermaid
C4Context
    title System Context Diagram - Multimodal RAG Solution

    Person(user, "User", "End user querying documents")

    System_Boundary(rag_system, "Multimodal RAG System") {
        System(openwebui, "Open WebUI", "Chat interface")
        System(pipeline, "Pipelines Server", "RAG pipeline orchestrator")
        System(dotnet, ".NET API", "RAG orchestration & query processing")
        System(python, "Python Ingestion", "Document processing & embedding")
        SystemDb(pgvector, "PGVector", "Vector database")
    }

    System_Ext(ollama, "Ollama", "Local LLM & embeddings")
    System_Ext(docs, "Documents", "PDFs, images, text files")

    Rel(user, openwebui, "Interacts with", "HTTP/WebSocket")
    Rel(openwebui, pipeline, "Sends queries", "HTTP/OpenAI API")
    Rel(pipeline, dotnet, "Routes to RAG", "HTTP/REST")
    Rel(dotnet, pgvector, "Vector search", "PostgreSQL")
    Rel(dotnet, ollama, "Generate & embed", "HTTP/REST")
    Rel(python, docs, "Reads", "File I/O")
    Rel(python, ollama, "Creates embeddings", "HTTP/REST")
    Rel(python, pgvector, "Stores vectors", "PostgreSQL")

    UpdateRelStyle(user, openwebui, $offsetY="-40", $offsetX="-50")
    UpdateRelStyle(openwebui, pipeline, $offsetY="-30")
    UpdateRelStyle(pipeline, dotnet, $offsetY="-20")
```

### C4 Model - Container Diagram

```mermaid
C4Container
    title Container Diagram - Multimodal RAG System

    Person(user, "User")

    Container_Boundary(webui, "Open WebUI Stack") {
        Container(openwebui, "Open WebUI", "Node.js/React", "Web-based chat interface")
        Container(pipeline, "Pipelines Server", "Python/FastAPI", "Pipeline execution engine")
        Container(rag_pipeline, "RAG Pipeline", "Python", "Manifold pipeline routing queries through RAG")
    }

    Container_Boundary(backend, "Backend Services") {
        Container(dotnet_api, ".NET API", "ASP.NET Core", "RAG orchestration with Semantic Kernel")
        Container(python_ingest, "Python Ingestion", "Python", "Document processing & chunking")

        Container(orchestrator, "RAG Orchestrator", ".NET/C#", "Query processing & context building")
        Container(vector_search, "Vector Search", ".NET/C#", "Similarity search service")
        Container(ollama_svc, "Ollama Service", ".NET/C#", "LLM interaction wrapper")
    }

    ContainerDb(pgvector, "PGVector", "PostgreSQL 16", "Vector database with pgvector extension")

    System_Ext(ollama, "Ollama", "Local LLM runtime")
    System_Ext(files, "Documents", "PDF, Images, Text")

    Rel(user, openwebui, "Uses", "HTTPS")
    Rel(openwebui, pipeline, "Connects to", "HTTP/OpenAI API")
    Rel(pipeline, rag_pipeline, "Loads & executes")
    Rel(rag_pipeline, dotnet_api, "Calls", "HTTP/REST")

    Rel(dotnet_api, orchestrator, "Uses")
    Rel(orchestrator, vector_search, "Retrieves context")
    Rel(orchestrator, ollama_svc, "Generates response")
    Rel(vector_search, pgvector, "Queries", "SQL/pgvector")
    Rel(ollama_svc, ollama, "API calls", "HTTP/REST")

    Rel(python_ingest, files, "Reads", "File I/O")
    Rel(python_ingest, ollama, "Embeds", "HTTP/REST")
    Rel(python_ingest, pgvector, "Stores", "PostgreSQL")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

---

## Data Flow

### Ingestion Flow

```mermaid
sequenceDiagram
    participant User
    participant Python as Python Ingestion
    participant Processor as Document Processor
    participant Ollama
    participant DB as PGVector Database

    User->>Python: python main.py ingest-file document.pdf
    Python->>Processor: Process document

    alt PDF Document
        Processor->>Processor: Extract text via PyMuPDF
        Processor->>Processor: Extract images
        Processor->>Processor: OCR images (if needed)
    else Image Document
        Processor->>Processor: OCR via Tesseract
    else Text Document
        Processor->>Processor: Read text
    end

    Processor->>Processor: Chunk content (512 tokens)

    loop For each chunk
        Processor->>Ollama: POST /api/embeddings<br/>{text: chunk, model: nomic-embed-text}
        Ollama-->>Processor: embedding vector [768 dim]
        Processor->>DB: INSERT INTO documents<br/>(content, embedding, metadata)
    end

    DB-->>Python: Ingestion complete
    Python-->>User: Success: N chunks stored
```

### Query Flow

```mermaid
sequenceDiagram
    participant User
    participant OpenWebUI
    participant Pipeline as Pipelines Server
    participant RAGPipe as RAG Pipeline
    participant DotNet as .NET API
    participant Orchestrator as RAG Orchestrator
    participant VectorDB as PGVector
    participant Ollama

    User->>OpenWebUI: Enter query: "What is machine learning?"
    OpenWebUI->>Pipeline: POST /v1/chat/completions<br/>{model: rag-qwen-7b, messages: [...]}
    Pipeline->>RAGPipe: Execute pipe() method

    RAGPipe->>DotNet: POST /api/rag/query<br/>{query: "What is...", topK: 5}

    DotNet->>Orchestrator: QueryAsync(query, topK)

    Orchestrator->>Ollama: POST /api/embeddings<br/>{text: query}
    Ollama-->>Orchestrator: query_embedding [768]

    Orchestrator->>VectorDB: SELECT ... ORDER BY embedding <=> query_vector LIMIT 5
    VectorDB-->>Orchestrator: Top 5 similar documents

    Orchestrator->>Orchestrator: Build context from documents

    Orchestrator->>Ollama: POST /api/generate<br/>{prompt: context + query, model: qwen2.5:7b}
    Ollama-->>Orchestrator: Generated response

    Orchestrator-->>DotNet: QueryResponse{answer, sources, processingTime}
    DotNet-->>RAGPipe: HTTP 200 + JSON response

    RAGPipe->>RAGPipe: Format response + sources
    RAGPipe-->>Pipeline: Formatted response
    Pipeline-->>OpenWebUI: SSE stream of response
    OpenWebUI-->>User: Display answer with sources
```

### Component Interaction Diagram

```mermaid
graph TB
    subgraph "User Interface Layer"
        A[Web Browser]
        B[Open WebUI Container<br/>Port 3000]
    end

    subgraph "Pipeline Layer"
        C[Pipelines Server<br/>Port 9099]
        D[rag_pipeline.py<br/>Manifold Pipeline]
    end

    subgraph "Orchestration Layer"
        E[.NET API<br/>Port 5236]
        F[RAG Orchestrator]
        G[Vector Search Service]
        H[Ollama Service]
    end

    subgraph "Data Layer"
        I[(PGVector DB<br/>Port 5432)]
    end

    subgraph "Ingestion Layer"
        J[Python Ingestion<br/>main.py]
        K[PDF Processor]
        L[Image Processor]
        M[Text Processor]
    end

    subgraph "Model Layer"
        N[Ollama Runtime<br/>Port 11434]
        O[nomic-embed-text<br/>Embeddings]
        P[qwen2.5:7b<br/>Generation]
        Q[qwen2.5-coder:14b<br/>Generation]
    end

    A -->|HTTPS| B
    B -->|OpenAI API| C
    C -->|Loads & Executes| D
    D -->|HTTP REST| E
    E --> F
    F --> G
    F --> H
    G -->|pgvector queries| I
    H -->|HTTP REST| N
    N --> O
    N --> P
    N --> Q

    J --> K
    J --> L
    J --> M
    K -->|Embed| N
    L -->|Embed| N
    M -->|Embed| N
    K -->|Store| I
    L -->|Store| I
    M -->|Store| I

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#fff4e1
    style D fill:#ffe1f5
    style E fill:#e1ffe1
    style I fill:#f5e1ff
    style N fill:#ffe1e1
```

---

## Prerequisites

- **Mac M4 Pro** (or similar ARM Mac)
- **Docker Desktop** or Podman
- **.NET 10 SDK** (or .NET 8+)
- **Python 3.11+**
- **Ollama** installed and running with models:
  - `nomic-embed-text` (embeddings)
  - `qwen2.5:7b` (generation)
  - `qwen2.5-coder:14b` (optional, for code-related queries)

### Install Ollama Models

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:14b
```

---

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd multimodal-rag

# Make setup script executable
chmod +x start.sh

# Run automated setup
./start.sh
```

### 2. Start All Services

```bash
# Start database, pipelines, and Open WebUI
docker-compose up -d

# Or with Podman
podman compose up -d
```

### 3. Setup Python Ingestion

```bash
cd python-ingestion
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database schema
python main.py setup
```

### 4. Run .NET API

```bash
cd dotnet-orchestration/MultimodalRAG
dotnet restore
dotnet run
```

The API will start at `http://localhost:5236`

### 5. Configure Open WebUI Pipeline Connection

1. Open http://localhost:3000
2. Navigate to **Settings** → **Connections**
3. Click **"+ Add OpenAI API"** (NOT Ollama)
4. Configure:
   - **API Base URL**: `http://pipelines:9099/v1`
   - **API Key**: `0p3n-w3bu!`
   - **Name**: `RAG Pipelines`
5. Click **Verify** and **Save**

### 6. Select RAG Model in Chat

In the chat interface, select one of:
- **RAG + Qwen 2.5 7B**
- **RAG + Qwen 2.5 Coder 14B**

Now all your queries will use the RAG system!

---

## Component Details

### 1. Python Ingestion Service

**Location**: `python-ingestion/`

**Purpose**: Process and ingest documents into the vector database

**Key Features**:
- Multi-format support: PDF, images (PNG, JPG), text files
- Intelligent chunking with overlap
- Metadata extraction
- Parallel processing
- OCR for images using Tesseract

**Commands**:
```bash
# Setup database
python main.py setup

# Ingest single file
python main.py ingest-file /path/to/document.pdf

# Ingest directory
python main.py ingest-dir /path/to/documents

# Check database stats
python main.py stats
```

**Configuration**: `.env` file (see Configuration section)

### 2. .NET RAG Orchestration API

**Location**: `dotnet-orchestration/MultimodalRAG/`

**Purpose**: Handle RAG queries with vector search and response generation

**Key Components**:
- **RAGOrchestrator**: Main query processing logic
- **VectorSearchService**: pgvector similarity search
- **OllamaService**: LLM interaction wrapper

**Endpoints**:
- `POST /api/rag/query` - Full RAG query (retrieval + generation)
- `POST /api/rag/search` - Vector search only
- `GET /api/rag/health` - Health check
- `GET /api/rag/stats` - Database statistics
- `POST /api/rag/embed` - Get embeddings
- `POST /api/rag/generate` - Direct generation

**Swagger UI**: http://localhost:5236/swagger

### 3. Open WebUI Pipelines

**Location**: `open-webui-pipeline/`

**Purpose**: Route queries through the RAG system in Open WebUI

**Pipeline Type**: Manifold (provides multiple model endpoints)

**Key Features**:
- Automatic RAG enhancement for all queries
- Graceful error handling with fallback
- Source citation display
- Configurable via valves (in Open WebUI admin)

**Configuration Valves** (editable in UI):
- `RAG_API_URL`: URL of .NET API (default: `http://host.docker.internal:5236/api/rag`)
- `TOP_K`: Number of documents to retrieve (default: 5)
- `ENABLE_RAG`: Toggle RAG on/off (default: true)
- `SHOW_SOURCES`: Display source documents (default: true)
- `TIMEOUT`: API request timeout in seconds (default: 30)

**Models Provided**:
- `rag-qwen-7b` → RAG + Qwen 2.5 7B
- `rag-qwen-coder-14b` → RAG + Qwen 2.5 Coder 14B

### 4. PGVector Database

**Container**: `multimodal-rag-db`

**Purpose**: Vector similarity search with PostgreSQL

**Schema**:
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB,
    content_type VARCHAR(50),
    source_file VARCHAR(500),
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

**Connection**:
- Host: localhost
- Port: 5432
- Database: multimodal_rag
- User: raguser
- Password: ragpassword

### 5. Pipelines Server

**Container**: `pipelines`

**Purpose**: Execute Open WebUI pipelines

**Image**: `ghcr.io/open-webui/pipelines:main`

**Port**: 9099

**API Compatibility**: OpenAI-compatible endpoints

**Pipeline Discovery**: Auto-loads `.py` files from `/app/pipelines/`

---

## Configuration

### Environment Variables (.env for Python)

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=multimodal_rag
DB_USER=raguser
DB_PASSWORD=ragpassword

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
VISION_MODEL=qwen2.5-vl:7b
TEXT_MODEL=qwen2.5:14b

# Vector Dimension (nomic-embed-text = 768)
VECTOR_DIMENSION=768

# Chunking Settings
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### .NET Configuration (appsettings.json)

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Port=5432;Database=multimodal_rag;Username=raguser;Password=ragpassword"
  },
  "Ollama": {
    "BaseUrl": "http://localhost:11434",
    "EmbeddingModel": "nomic-embed-text",
    "GenerationModel": "qwen2.5:7b",
    "Temperature": 0.7,
    "TopK": 40,
    "TopP": 0.9
  },
  "VectorSearch": {
    "DefaultTopK": 5,
    "VectorDimension": 768
  }
}
```

### Docker Compose Services

```yaml
services:
  pgvector:       # PostgreSQL with pgvector extension
  pipelines:      # Open WebUI pipelines server
  open-webui:     # Chat interface
```

**Network**: All services share `rag-network` bridge network

**Volumes**:
- `pgvector_data`: Persistent database storage
- `open-webui-data`: Open WebUI data
- `./open-webui-pipeline`: Mounted pipeline files

---

## Usage Examples

### Ingest Documents

```bash
cd python-ingestion
source venv/bin/activate

# Single PDF
python main.py ingest-file ~/Documents/machine-learning.pdf

# Directory of documents
python main.py ingest-dir ~/Documents/research-papers

# Check what's been ingested
python main.py stats
```

### Query via API

```bash
# Full RAG query
curl -X POST http://localhost:5236/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is gradient descent?",
    "topK": 5
  }'

# Search only (no generation)
curl -X POST http://localhost:5236/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "topK": 3,
    "contentType": "pdf"
  }'

# Health check
curl http://localhost:5236/api/rag/health
```

### Query via Open WebUI

1. Open http://localhost:3000
2. Select **RAG + Qwen 2.5 7B** model
3. Ask: "What is machine learning?"
4. Response will include:
   - Generated answer based on your documents
   - Source citations with relevance scores
   - Processing time

---

## Troubleshooting

### Pipeline Not Showing in Open WebUI

**Symptom**: Models don't appear in chat interface

**Solutions**:
1. Verify pipelines server is running:
   ```bash
   docker logs pipelines
   # Should see: "Loaded module: rag_pipeline"
   ```

2. Check connection in Open WebUI:
   - Settings → Connections
   - Must be added as **OpenAI API**, not Ollama
   - URL: `http://pipelines:9099/v1`
   - API Key: `0p3n-w3bu!`

3. Restart pipelines server:
   ```bash
   docker restart pipelines
   ```

### RAG API Returning 500 Errors

**Symptom**: Queries fail with "RAG API error: HTTP 500"

**Solutions**:
1. Check .NET API is running:
   ```bash
   curl http://localhost:5236/api/rag/health
   ```

2. Verify Ollama is running:
   ```bash
   ollama list
   curl http://localhost:11434/api/tags
   ```

3. Check database connection:
   ```bash
   docker exec -it multimodal-rag-db psql -U raguser -d multimodal_rag -c "SELECT COUNT(*) FROM documents;"
   ```

4. View .NET logs for detailed errors

### Database Connection Issues

**Symptom**: "Cannot connect to database"

**Solutions**:
1. Ensure PGVector is running:
   ```bash
   docker ps | grep pgvector
   ```

2. Check health:
   ```bash
   docker exec multimodal-rag-db pg_isready -U raguser
   ```

3. Verify credentials in `.env` and `appsettings.json` match

### Ollama Model Not Found

**Symptom**: "model 'nomic-embed-text' not found"

**Solutions**:
1. Pull required models:
   ```bash
   ollama pull nomic-embed-text
   ollama pull qwen2.5:7b
   ollama pull qwen2.5-coder:14b
   ```

2. Verify models are loaded:
   ```bash
   ollama list
   ```

### Pipeline File Moved to `failed/` Directory

**Symptom**: Pipeline loads but immediately fails

**Solutions**:
1. Check logs:
   ```bash
   docker logs pipelines
   ```

2. Common issues:
   - Missing `pipelines()` method (not `pipes()`)
   - Missing `Pipeline` class
   - Syntax errors in Python code

3. Fix and restore:
   ```bash
   docker exec pipelines rm -rf /app/pipelines/__pycache__
   docker restart pipelines
   ```

---

## Development

### Running Tests

**.NET Tests**:
```bash
cd dotnet-orchestration/MultimodalRAG.Tests
dotnet test
```

**Python Tests**:
```bash
cd python-ingestion
pytest tests/
```

### Debugging

**Enable detailed logging in .NET**:
```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Debug",
      "Microsoft.AspNetCore": "Debug"
    }
  }
}
```

**Monitor all container logs**:
```bash
docker-compose logs -f
```

---

## Performance Tuning

### Vector Search Optimization

Adjust index type for dataset size:

```sql
-- For small datasets (<100k vectors)
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- For large datasets (>100k vectors)
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 1000);
```

### Chunking Strategy

Edit in `.env`:
```bash
# Smaller chunks = more precise but more DB records
CHUNK_SIZE=256
CHUNK_OVERLAP=25

# Larger chunks = more context but less precision
CHUNK_SIZE=1024
CHUNK_OVERLAP=100
```

### Pipeline Timeout

Adjust in pipeline valves (Open WebUI admin) or in code:
```python
TIMEOUT: int = Field(
    default=60,  # Increase for slower systems
    description="API request timeout in seconds"
)
```

---

## Security Considerations

1. **Change default credentials** in production:
   - Database password
   - Pipeline API key (`0p3n-w3bu!`)

2. **Enable authentication** in Open WebUI:
   ```yaml
   environment:
     - WEBUI_AUTH=true
   ```

3. **Use HTTPS** for production deployments

4. **Restrict network access** to only required services

5. **Regularly update** container images:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

---

## Acknowledgments

This solution was built using the following open-source and commercial technologies:

### Core Technologies
- **[Open WebUI](https://github.com/open-webui/open-webui)** - Extensible, feature-rich web interface for LLMs with support for pipelines and functions. Licensed under MIT.
- **[Ollama](https://ollama.com/)** - Run large language models locally with ease. Enables privacy-focused AI without cloud dependencies.
- **[PGVector](https://github.com/pgvector/pgvector)** - Open-source vector similarity search extension for PostgreSQL.

### Development & Architecture
- **[Claude.ai](https://claude.ai/)** by Anthropic - AI assistant used for solution architecture, implementation guidance, and documentation. This project benefited from Claude's expertise in system design, code structure, and technical documentation.

### Models
- **Qwen 2.5** by Alibaba Cloud - High-performance open-source language models
- **Nomic Embed Text** - Open-source embedding model optimized for semantic search

### Special Thanks
- Open WebUI community for the excellent pipelines framework
- Ollama team for making local LLM deployment accessible
- Anthropic for Claude.ai's architectural and coding assistance

---

## License

This project is provided as-is with no restrictions on use, modification, or distribution. Feel free to use, adapt, and build upon this solution for any purpose, commercial or non-commercial.

### Component Licenses

Please note that this solution integrates various open-source and proprietary components, each with their own licenses:

- **Open WebUI**: MIT License
- **Ollama**: MIT License
- **PGVector**: PostgreSQL License (similar to MIT/BSD)
- **.NET**: MIT License
- **Python Libraries**: Various open-source licenses (see `requirements.txt`)
- **Qwen Models**: Apache 2.0 License
- **Nomic Embed**: Apache 2.0 License

When using this solution, ensure you comply with the licenses of the individual components.

### Attribution

While not required, attribution is appreciated. If you use this solution in your work, consider mentioning:
- This repository and its contributors
- The technologies listed in the Acknowledgments section

## Contributing

Contributions are welcome! This project was built with the goal of being a practical, production-ready RAG solution.

### How to Contribute

1. **Bug Reports**: Open an issue describing the bug and steps to reproduce
2. **Feature Requests**: Share your ideas for improvements or new features
3. **Code Contributions**:
   - Fork the repository
   - Create a feature branch
   - Make your changes with clear commit messages
   - Submit a pull request with a description of your changes

### Areas for Contribution

- Additional document processors (Word, Excel, etc.)
- Performance optimizations
- Additional pipeline configurations
- Enhanced error handling and monitoring
- Documentation improvements
- Test coverage expansion

All contributions will be reviewed and acknowledged.

## Support

For issues and questions:
- GitHub Issues: [your-repo-url/issues]
- Documentation: [link to wiki/docs]
