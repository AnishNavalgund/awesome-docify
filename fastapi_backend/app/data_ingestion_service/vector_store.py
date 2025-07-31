import json
import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from qdrant_client.http import models

# LangChain imports
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.schema import Document

from ..config import settings

class VectorStore:
    """Enhanced vector store using LangChain framework"""
    
    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embedding_model = "text-embedding-3-small"
        self.vector_size = 1536  # OpenAI text-embedding-3-small dimension
        
        # Initialize LangChain embeddings
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize LangChain Qdrant vector store
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )
        
    async def create_collection(self):
        """Create the vector collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection: {self.collection_name}")
            else:
                print(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents using LangChain framework"""
        try:
            # Convert to LangChain Document objects
            langchain_docs = []
            for doc in documents:
                content = doc.get("markdown", "")
                metadata = doc.get("metadata", {})
                
                # Create LangChain Document
                langchain_doc = Document(
                    page_content=content,
                    metadata={
                        "title": metadata.get("title", ""),
                        "url": metadata.get("url", ""),
                        "source_url": metadata.get("sourceURL", ""),
                        "language": metadata.get("language", "en"),
                        "content_type": metadata.get("contentType", ""),
                        "scrape_id": metadata.get("scrapeId", ""),
                        "document_id": metadata.get("document_id", ""),
                        "chunk_index": metadata.get("chunk_index", 0),
                        "file_path": metadata.get("file_path", ""),
                        "file_size": metadata.get("file_size", 0),
                        "last_modified": metadata.get("last_modified", "")
                    }
                )
                langchain_docs.append(langchain_doc)
            
            # Add documents in batches using LangChain
            batch_size = 50
            total_added = 0
            
            for i in range(0, len(langchain_docs), batch_size):
                batch = langchain_docs[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(langchain_docs) + batch_size - 1) // batch_size
                
                print(f"Processing batch {batch_num}/{total_batches}")
                
                # Add batch to vector store
                self.vector_store.add_documents(batch)
                total_added += len(batch)
                
                print(f"Added {len(batch)} documents to vector database (batch {batch_num})")
            
            print(f"Total documents added: {total_added}")
            
        except Exception as e:
            print(f"Error adding documents: {e}")
            raise
    
    async def search(self, query: str, limit: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents using LangChain"""
        try:
            # Build search parameters
            search_kwargs = {"k": limit}
            
            # Add filters if provided
            if filters:
                search_kwargs["filter"] = self._build_langchain_filter(filters)
            
            # Search using LangChain
            docs_and_scores = self.vector_store.similarity_search_with_score(
                query, **search_kwargs
            )
            
            # Format results
            results = []
            for doc, score in docs_and_scores:
                results.append({
                    "score": score,
                    "title": doc.metadata.get("title", ""),
                    "url": doc.metadata.get("url", ""),
                    "content": doc.page_content,
                    "source_url": doc.metadata.get("source_url", ""),
                    "document_id": doc.metadata.get("document_id", ""),
                    "chunk_index": doc.metadata.get("chunk_index", 0)
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching: {e}")
            raise
    
    def _build_langchain_filter(self, filters: Dict) -> Dict:
        """Build LangChain filter from dictionary"""
        return {}
    
    def _build_filter(self, filters: Dict) -> Filter:
        """Build Qdrant filter from dictionary (legacy method)"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            elif isinstance(value, list):
                conditions.append(FieldCondition(key=key, match=MatchValue(any=value)))
        
        return Filter(must=conditions)
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            print(f">>>> Collection info object: {collection_info}")
            print(f">>>> Collection info type: {type(collection_info)}")
            print(f">>>> Collection info dir: {dir(collection_info)}")
            

            name = getattr(collection_info, 'name', None)
            if name is None:
                name = getattr(collection_info, 'collection_name', self.collection_name)
            
            vectors_count = getattr(collection_info, 'vectors_count', None)
            if vectors_count is None:
                vectors_count = getattr(collection_info, 'count', 0)
            
            points_count = getattr(collection_info, 'points_count', None)
            if points_count is None:
                points_count = getattr(collection_info, 'count', 0)
            
            status = getattr(collection_info, 'status', 'unknown')
            
            return {
                "name": name,
                "vectors_count": vectors_count,
                "points_count": points_count,
                "status": status
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            # Return a default structure if there's an error
            return {
                "name": self.collection_name,
                "vectors_count": 0,
                "points_count": 0,
                "status": "unknown"
            }
    
    async def delete_documents(self, document_ids: List[str]):
        """Delete documents by document_id"""
        try:
            # Build filter for document_ids
            filter_condition = Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(any=document_ids))]
            )
            
            # Delete points matching the filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=filter_condition
            )
            
            print(f"Deleted documents with IDs: {document_ids}")
            
        except Exception as e:
            print(f"Error deleting documents: {e}")
            raise

# Global instance
vector_store = VectorStore() 