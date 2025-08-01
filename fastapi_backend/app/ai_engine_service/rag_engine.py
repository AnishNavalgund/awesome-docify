from app.schemas import Intent, DocumentUpdate
from app.data_ingestion_service import vector_store
from app.ai_engine_service.intent import extract_intent, IntentHandlerFactory
from langchain_openai import ChatOpenAI
from app.config import settings
from app.utils import logger_info
import warnings
from typing import List, Dict, Any
import re

warnings.filterwarnings("ignore")

class DocuRAG:
    """
    Awesome Docuemnt RAG
    """
    
    def __init__(self, 
                 llm_model: ChatOpenAI = None,
                 top_k_docs: int = 50):  # Increased to get more results
        
        self.llm_model = llm_model or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.top_k_docs = top_k_docs
        
    async def search_documents(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for documents containing the exact keyword.
        """
        try:
            print(f"Searching for exact keyword: {keyword}")
            # Get more results initially to filter
            results = await vector_store.search(query=keyword, limit=100)
            print(f"Found {len(results)} initial results")
            
            # Filter to only include documents that actually contain the keyword
            exact_matches = []
            for doc in results:
                content = doc.get("content", "").lower()
                if keyword.lower() in content:
                    exact_matches.append(doc)
            
            print(f"Found {len(exact_matches)} documents with exact keyword match")
            return exact_matches
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def filter_chunks(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter chunks - remove those with less than 100 characters.
        """
        filtered_docs = []
        for doc in documents:
            content = doc.get("content", "")
            if len(content.strip()) >= 100:
                filtered_docs.append(doc)
        
        print(f"Filtered from {len(documents)} to {len(filtered_docs)} chunks")
        return filtered_docs
    
    def extract_content_with_context(self, documents: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
        """
        Extract content with context around the keyword for each document.
        """
        content_extracts = []
        
        for doc in documents:
            content = doc.get("content", "")
            doc_id = doc.get("document_id", "")
            title = doc.get("title", "")
            
            # Find the keyword in the content
            keyword_lower = keyword.lower()
            content_lower = content.lower()
            
            if keyword_lower in content_lower:
                # Find the position of the keyword
                start_pos = content_lower.find(keyword_lower)
                
                # Extract context around the keyword 
                context_start = max(0, start_pos - 500)
                context_end = min(len(content), start_pos + len(keyword) + 500)
                
                # Extract the context
                context = content[context_start:context_end]
                
                # Find the actual keyword in the original case
                keyword_pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                match = keyword_pattern.search(context)
                
                if match:
                    # Get the actual keyword with original case
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
        
        return content_extracts
    
    async def task_runner(self, query: str) -> dict:

        try:
            print(f"=== TASK ENTRY POINT ===")
            print(f"Query: {query}")
            
            #  Extract keyword using Query Extractor Service
            print("Step 1: Extracting keyword...")
            intent = await extract_intent(query)
            print(f">>>> Intent: {intent}")
            keyword = intent.target
            print(f"Extracted keyword: {keyword}")
            
            # Search documents
            print("Step 2: Searching documents...")
            documents = await self.search_documents(keyword)
            
            # Filter chunks
            print("Step 3: Filtering chunks...")
            filtered_docs = self.filter_chunks(documents)
            
            # Extract content with context
            print("Step 4: Extracting content with context...")
            content_extracts = self.extract_content_with_context(filtered_docs, keyword)
            
            # Process intent using appropriate handler
            print("Step 5: Processing intent with handler...")
            handler = IntentHandlerFactory.create_handler(intent, self.llm_model)
            documents_to_update = await handler.process_intent(intent, query, content_extracts)
            
            print(f"Generated {len(documents_to_update)} document updates with content")
            
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
    """
    Main entry point
    """
    print(f"Query: {query}")
    return await task.task_runner(query)
