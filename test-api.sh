#!/bin/bash

API_URL="http://localhost:5000/api/rag"

echo "🧪 Testing Multimodal RAG API"
echo "=============================="

# Test 1: Health check
echo ""
echo "1️⃣  Testing health endpoint..."
curl -s "$API_URL/health" | jq .

# Test 2: Get stats
echo ""
echo "2️⃣  Getting database stats..."
curl -s "$API_URL/stats" | jq .

# Test 3: Embed text
echo ""
echo "3️⃣  Testing embedding..."
curl -s -X POST "$API_URL/embed" \
  -H "Content-Type: application/json" \
  -d '{"text": "What is artificial intelligence?"}' | jq '.dimension'

# Test 4: Search (without generation)
echo ""
echo "4️⃣  Testing search..."
curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "topK": 3}' | jq '.count'

# Test 5: Full RAG query
echo ""
echo "5️⃣  Testing full RAG query..."
curl -s -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "topK": 3}' | jq '.answer' | head -c 200

echo ""
echo ""
echo "✅ Tests complete!"