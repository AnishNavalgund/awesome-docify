from app.schemas import Intent, DocumentUpdate
from app.ai_engine_service.intent import extract_intent, IntentHandlerFactory
from langchain_openai import ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from app.config import settings
from app.utils import logger_info, logger_error
import warnings
from typing import List, Dict, Any
import re
from pathlib import Path

warnings.filterwarnings("ignore")

class DocuRAG:
    """Awesome Document RAG using local file-based Qdrant"""
    
    def __init__(self, llm_model: ChatOpenAI = None, top_k_docs: int = 50):
        self.llm_model = llm_model or ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.top_k_docs = top_k_docs
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Store path and collection name, but don't create client yet
        self.qdrant_path = Path(settings.QDRANT_PATH)
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._client = None
        
    def _get_client(self):
        """Get or create Qdrant client"""
        if self._client is None:
            self._client = QdrantClient(path=str(self.qdrant_path))
        return self._client
        
    async def search_documents(self, keyword: str, intent_action: str = None) -> List[Dict[str, Any]]:
        """Search for documents using local Qdrant"""
        try:
            print(f"Searching for keyword: {keyword}")
            
            # Get client when needed
            client = self._get_client()
            
            # Connect to existing Qdrant collection
            vector_store = QdrantVectorStore(
                client=client,
                collection_name=self.collection_name,
                embedding=self.embeddings
            )
            
            # Search using Qdrant
            docs_and_scores = vector_store.similarity_search_with_score(
                keyword, k=self.top_k_docs
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
            
            print(f"Found {len(results)} documents")
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def filter_chunks(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter chunks - remove those with less than 100 characters"""
        filtered_docs = [doc for doc in documents if len(doc.get("content", "").strip()) >= 100]
        print(f"Filtered from {len(documents)} to {len(filtered_docs)} chunks")
        return filtered_docs
    
    def extract_content_with_context(self, documents: List[Dict[str, Any]], keyword: str, intent_action: str = None) -> List[Dict[str, Any]]:
        """Extract content with context around the keyword"""
        content_extracts = []
        keyword_lower = keyword.lower()
        
        for doc in documents:
            content = doc.get("content", "")
            doc_id = doc.get("document_id", "")
            title = doc.get("title", "")
            
            # Find keyword in content
            content_lower = content.lower()
            if keyword_lower in content_lower:
                start_pos = content_lower.find(keyword_lower)
                context_size = 300 if intent_action == "add" else 400
                context_start = max(0, start_pos - context_size)
                context_end = min(len(content), start_pos + len(keyword) + context_size)
                context = content[context_start:context_end]
                
                # Find actual keyword with original case
                keyword_pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                match = keyword_pattern.search(context)
                
                if match:
                    actual_keyword = context[match.start():match.end()]
                    content_extracts.append({
                        "document_id": doc_id,
                        "title": title,
                        "content": context,
                        "keyword": actual_keyword,
                        "keyword_position": match.start(),
                        "full_content": content,
                        "url": doc.get("url", ""),
                        "source_url": doc.get("source_url", "")
                    })
            # For addition operations, provide full content when no keyword found
            elif intent_action == "add":
                content_extracts.append({
                    "document_id": doc_id,
                    "title": title,
                    "content": content,
                    "keyword": keyword,
                    "keyword_position": -1,
                    "full_content": content,
                    "url": doc.get("url", ""),
                    "source_url": doc.get("source_url", "")
                })
            # For other operations, include first part as context
            else:
                context_size = 400
                context = content[:context_size] if len(content) > context_size else content
                content_extracts.append({
                    "document_id": doc_id,
                    "title": title,
                    "content": context,
                    "keyword": keyword,
                    "keyword_position": -1,
                    "full_content": content,
                    "url": doc.get("url", ""),
                    "source_url": doc.get("source_url", "")
                })
        
        return content_extracts
    
    async def task_runner(self, query: str) -> dict:
        """Main task runner"""
        try:
            print(f"=== TASK ENTRY POINT ===")
            print(f"Query: {query}")
            
            # Extract keyword
            print("Step 1: Extracting keyword...")
            intent = await extract_intent(query)
            print(f">>>> Intent: {intent}")
            keyword = intent.target
            print(f"Extracted keyword: {keyword}")
            
            # Search documents
            print("Step 2: Searching documents...")
            documents = await self.search_documents(keyword, intent.action)
            
            # Filter chunks
            print("Step 3: Filtering chunks...")
            filtered_docs = self.filter_chunks(documents)
            
            # Extract content with context
            print("Step 4: Extracting content with context...")
            content_extracts = self.extract_content_with_context(filtered_docs, keyword, intent.action)
            
            # Process intent using handler
            print("Step 5: Processing intent with handler...")
            handler = IntentHandlerFactory.create_handler(intent, self.llm_model)
            documents_to_update = await handler.process_intent(intent, query, content_extracts)
            
            print(f"Generated {len(documents_to_update)} document updates")
            
            return {
                "query": query,
                "keyword": keyword,
                "analysis": f"Found {len(documents_to_update)} documents containing the keyword '{keyword}'. Generated suggested changes for {intent.action} operation.",
                "documents_to_update": documents_to_update,
                "total_documents": len(documents_to_update)
            }
            
        except Exception as e:
            print(f"Pipeline error: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "query": query,
                "keyword": "unknown",
                "analysis": f"Error occurred while processing query: {str(e)}",
                "documents_to_update": [],
                "total_documents": 0
            }

# Global instance
task = DocuRAG()

async def orchestrator(query: str) -> dict:
    """Main entry point"""
    print(f"Query: {query}")
    return await task.task_runner(query)
