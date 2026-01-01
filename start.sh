#!/bin/bash

echo "🚀 Starting Multimodal RAG Solution"
echo "===================================="

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start Ollama first."
    exit 1
fi

# Pull required models
echo "📥 Pulling Ollama models..."
ollama pull nomic-embed-text
ollama pull qwen2.5:14b
ollama pull qwen2.5-vl:7b

# Start database
echo "🐘 Starting PostgreSQL with PGVector..."
docker-compose up -d pgvector

# Wait for database
echo "⏳ Waiting for database to be ready..."
sleep 10

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd python-ingestion
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
echo "💾 Initializing database schema..."
python main.py setup

# Setup .NET project
echo "🔷 Setting up .NET project..."
cd ../dotnet-orchestration/MultimodalRAG
dotnet restore

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the system:"
echo "1. Ingest data: cd python-ingestion && source venv/bin/activate && python main.py ingest-dir /path/to/docs"
echo "2. Start API: cd dotnet-orchestration/MultimodalRAG && dotnet run"
echo "3. Start Open WebUI: docker-compose up -d open-webui"
echo "4. Access Open WebUI at http://localhost:3000"