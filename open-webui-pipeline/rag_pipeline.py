"""
title: Multimodal RAG Pipeline
author: Jesper Jensen
author_url: https://github.com/jeesondk
version: 1.0.0
description: Routes queries through the .NET RAG API for document-enhanced responses
required_open_webui_version: 0.3.0
"""

import requests
from typing import List, Dict, Any, Optional, Union, Generator, Iterator
from pydantic import BaseModel, Field
import os
import json


class Pipeline:
    class Valves(BaseModel):
        """Configuration for the RAG Pipeline"""
        RAG_API_URL: str = Field(
            default="http://host.docker.internal:5236/api/rag",
            description="URL of your .NET RAG API"
        )
        TOP_K: int = Field(
            default=5,
            description="Number of documents to retrieve"
        )
        ENABLE_RAG: bool = Field(
            default=True,
            description="Enable/disable RAG enhancement"
        )
        SHOW_SOURCES: bool = Field(
            default=True,
            description="Show source documents in response"
        )
        TIMEOUT: int = Field(
            default=30,
            description="API request timeout in seconds"
        )

    def __init__(self):
        self.type = "manifold"
        self.name = "Multimodal RAG Pipeline"
        self.valves = self.Valves()
        
    async def on_startup(self):
        """Called when the pipeline starts"""
        print(f"🚀 RAG Pipeline started")
        print(f"📍 Connecting to: {self.valves.RAG_API_URL}")
        
        # Test connection to RAG API
        try:
            response = requests.get(
                f"{self.valves.RAG_API_URL}/health",
                timeout=5
            )
            if response.status_code == 200:
                print("✅ RAG API connection successful")
            else:
                print(f"⚠️  RAG API returned status: {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot connect to RAG API: {e}")

    async def on_shutdown(self):
        """Called when the pipeline shuts down"""
        print("🛑 RAG Pipeline shutdown")

    async def on_valves_updated(self):
        """Called when configuration is updated"""
        print("🔄 RAG Pipeline configuration updated")
        print(f"   RAG Enabled: {self.valves.ENABLE_RAG}")
        print(f"   API URL: {self.valves.RAG_API_URL}")
        print(f"   Top K: {self.valves.TOP_K}")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Process each message through the RAG pipeline.
        This is called for every user message.
        """
        
        print(f"💬 Processing message: {user_message[:50]}...")
        
        # If RAG is disabled, pass through to Ollama
        if not self.valves.ENABLE_RAG:
            print("⏭️  RAG disabled, passing through to model")
            return None
        
        try:
            # Call your .NET RAG API
            print(f"🔍 Querying RAG API...")
            response = requests.post(
                f"{self.valves.RAG_API_URL}/query",
                json={
                    "query": user_message,
                    "topK": self.valves.TOP_K
                },
                timeout=self.valves.TIMEOUT
            )
            
            if response.status_code == 200:
                rag_response = response.json()
                
                # Extract answer and sources
                rag_answer = rag_response.get("answer", "")
                sources = rag_response.get("sources", [])
                processing_time = rag_response.get("processingTimeMs", 0)
                
                print(f"✅ RAG response received ({processing_time}ms)")
                print(f"📚 Found {len(sources)} relevant sources")
                
                # Build the final response
                final_response = rag_answer
                
                # Add sources if enabled
                if self.valves.SHOW_SOURCES and sources:
                    final_response += "\n\n---\n\n### 📚 Sources\n\n"
                    
                    for i, source in enumerate(sources, 1):
                        content_preview = source['content'][:150].replace('\n', ' ')
                        distance = source['distance']
                        relevance = (1 - distance) * 100
                        content_type = source['contentType'].upper()
                        
                        final_response += f"**{i}. [{content_type}]** (Relevance: {relevance:.1f}%)\n"
                        final_response += f"   {content_preview}...\n\n"
                    
                    # Add metadata info
                    final_response += f"\n*Query processed in {processing_time}ms*"
                
                return final_response
                
            else:
                error_msg = f"RAG API error: HTTP {response.status_code}"
                print(f"❌ {error_msg}")
                
                # Return error message but don't fail completely
                return f"⚠️ {error_msg}\n\nFalling back to model without RAG context."
                
        except requests.exceptions.Timeout:
            error_msg = "RAG API request timed out"
            print(f"⏱️  {error_msg}")
            return f"⚠️ {error_msg}\n\nFalling back to model without RAG context."
            
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to RAG API"
            print(f"🔌 {error_msg}")
            return f"⚠️ {error_msg}\n\nIs your .NET API running?"
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"💥 {error_msg}")
            return f"⚠️ {error_msg}\n\nFalling back to model without RAG context."

    def pipelines(self) -> List[dict]:
        """
        Define available pipeline models.
        Each model can have different configurations.
        """
        return [
            {
                "id": "rag-qwen-7b",
                "name": "RAG + Qwen 2.5 7B",
            },
            {
                "id": "rag-qwen-coder-14b",
                "name": "RAG + Qwen 2.5 Coder 14B",
            }
        ]