#!/usr/bin/env python3
"""
JSON document loader for ingesting JSON files into Qdrant using LangChain
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.utils import logger_info, logger_error

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from .vector_store import vector_store
from ..config import settings

class DocumentLoader:
    """JSON document loader with LangChain text splitting capabilities"""
    
    def __init__(self):
        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def load_json_documents(self, docs_dir: str) -> List[Dict[str, Any]]:
        """Load all JSON documents from the specified directory"""
        documents = []
        docs_path = Path(docs_dir)
        
        if not docs_path.exists():
            logger_error.error(f"Error: Directory {docs_dir} does not exist")
            return documents
        
        # Get all JSON files
        json_files = list(docs_path.glob("*.json"))
        print(f"Found {len(json_files)} JSON files")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc = json.load(f)
                    # Add file metadata
                    doc['metadata']['file_path'] = str(json_file)
                    doc['metadata']['file_size'] = json_file.stat().st_size
                    doc['metadata']['last_modified'] = datetime.fromtimestamp(json_file.stat().st_mtime).isoformat()
                    doc['metadata']['document_id'] = f"{json_file.stem}_{int(json_file.stat().st_mtime)}"
                    documents.append(doc)
            except Exception as e:
                logger_error.error(f"Error loading {json_file}: {e}")
        
        return documents
    
    async def chunk_documents(self, documents: List[Dict[str, Any]], chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Chunk documents using LangChain text splitter"""
        chunked_docs = []
        
        for doc in documents:
            content = doc.get("markdown", "")
            metadata = doc.get("metadata", {})
            
            # Use LangChain text splitter for better chunking
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                chunked_doc = {
                    "markdown": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_id": f"{metadata.get('document_id', 'unknown')}_chunk_{i}"
                    }
                }
                chunked_docs.append(chunked_doc)
        
        return chunked_docs
    
    async def ingest_documents(self, docs_dir: str, chunk_size: int = 1000):
        """Main ingestion function for JSON documents using LangChain"""
        print("Starting JSON document ingestion with LangChain...")
        
        # Load documents
        documents = await self.load_json_documents(docs_dir)
        
        if not documents:
            logger_error.error("No JSON documents found to ingest")
            return
        
        logger_info.info(f"Loaded {len(documents)} JSON documents")
        
        # Chunk documents using LangChain
        chunked_docs = await self.chunk_documents(documents, chunk_size)
        logger_info.info(f"Created {len(chunked_docs)} chunks using LangChain text splitter")
        
        try:
            # Create collection
            await vector_store.create_collection()
            
            # Add documents to vector database using LangChain
            await vector_store.add_documents(chunked_docs)
            
            # Get collection info
            info = await vector_store.get_collection_info()
            #print(f"Collection info: {info}")
            
            logger_info.info("JSON document ingestion completed successfully with LangChain!")
            
        except Exception as e:
            logger_error.error(f"Error during ingestion: {e}")
            raise

# Global instance
document_loader = DocumentLoader()