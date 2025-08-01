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
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.top_k_docs = top_k_docs
        
    async def search_documents(self, keyword: str, intent_action: str = None) -> List[Dict[str, Any]]:
        """
        Search for documents containing the exact keyword or related content for additions.
        """
        try:
            print(f"Searching for keyword: {keyword} with action: {intent_action}")
            
            # Optimize initial search limit based on operation type
            initial_limit = 50 if intent_action == "add" else 30
            results = await vector_store.search(query=keyword, limit=initial_limit)
            print(f"Found {len(results)} initial results")
            
            # Filter to include documents that contain the keyword or related terms
            keyword_matches = []
            keyword_lower = keyword.lower()
            keyword_words = keyword_lower.split()
            
            for doc in results:
                content = doc.get("content", "").lower()
                
                # Check for exact keyword match
                if keyword_lower in content:
                    keyword_matches.append(doc)
                # Check for partial matches (at least 2 words from the keyword)
                elif len(keyword_words) > 1:
                    word_matches = sum(1 for word in keyword_words if word in content)
                    if word_matches >= min(2, len(keyword_words)):
                        keyword_matches.append(doc)
                # For single word keywords, check for partial matches
                elif len(keyword_words) == 1 and len(keyword_lower) > 3:
                    # Check if the word appears as part of other words
                    if any(keyword_lower in word for word in content.split()):
                        keyword_matches.append(doc)
            
            print(f"Found {len(keyword_matches)} documents with keyword match")
            
            # For addition operations, if no matches found, get some general content
            if intent_action == "add" and len(keyword_matches) == 0:
                print("No matches found for addition, getting general content...")
                # Get some general documentation content for the LLM to work with
                general_results = await vector_store.search(query="documentation", limit=3)
                keyword_matches = general_results
                print(f"Found {len(keyword_matches)} general documents for addition")
            
            return keyword_matches
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def filter_chunks(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter chunks - remove those with less than 100 characters.
        """
        # Use list comprehension for better performance
        filtered_docs = [doc for doc in documents if len(doc.get("content", "").strip()) >= 100]
        
        print(f"Filtered from {len(documents)} to {len(filtered_docs)} chunks")
        return filtered_docs
    
    def extract_content_with_context(self, documents: List[Dict[str, Any]], keyword: str, intent_action: str = None) -> List[Dict[str, Any]]:
        """
        Extract content with context around the keyword for each document.
        For addition operations, provide full document content when keyword is not found.
        """
        content_extracts = []
        keyword_lower = keyword.lower()
        keyword_words = keyword_lower.split()
        
        for doc in documents:
            content = doc.get("content", "")
            doc_id = doc.get("document_id", "")
            title = doc.get("title", "")
            
            # Find the keyword in the content
            content_lower = content.lower()
            
            # Check for exact keyword match first
            if keyword_lower in content_lower:
                start_pos = content_lower.find(keyword_lower)
                context_size = 300 if intent_action == "add" else 400
                context_start = max(0, start_pos - context_size)
                context_end = min(len(content), start_pos + len(keyword) + context_size)
                context = content[context_start:context_end]
                
                # Find the actual keyword with original case
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
            # Check for partial keyword matches
            elif len(keyword_words) > 1:
                # Find the best matching word position
                best_match_pos = -1
                best_match_word = ""
                
                for word in keyword_words:
                    if word in content_lower:
                        pos = content_lower.find(word)
                        if best_match_pos == -1 or pos < best_match_pos:
                            best_match_pos = pos
                            best_match_word = word
                
                if best_match_pos != -1:
                    context_size = 300 if intent_action == "add" else 400
                    context_start = max(0, best_match_pos - context_size)
                    context_end = min(len(content), best_match_pos + len(best_match_word) + context_size)
                    context = content[context_start:context_end]
                    
                    content_extracts.append({
                        "document_id": doc_id,
                        "title": title,
                        "content": context,
                        "keyword": keyword,
                        "keyword_position": best_match_pos - context_start,
                        "full_content": content,
                        "url": doc.get("url", ""),
                        "source_url": doc.get("source_url", "")
                    })
            # For addition operations, provide full content when no keyword found
            elif intent_action == "add":
                content_extracts.append({
                    "document_id": doc_id,
                    "title": title,
                    "content": content,  # Use full content for additions
                    "keyword": keyword,
                    "keyword_position": -1,  # Indicates keyword not found
                    "full_content": content,
                    "url": doc.get("url", ""),
                    "source_url": doc.get("source_url", "")
                })
            # For other operations, still include documents with partial relevance
            else:
                # Use the first part of the content as context
                context_size = 400
                context = content[:context_size] if len(content) > context_size else content
                
                content_extracts.append({
                    "document_id": doc_id,
                    "title": title,
                    "content": context,
                    "keyword": keyword,
                    "keyword_position": -1,  # Indicates keyword not found in context
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
            documents = await self.search_documents(keyword, intent.action)
            
            # Filter chunks
            print("Step 3: Filtering chunks...")
            filtered_docs = self.filter_chunks(documents)
            
            # Extract content with context
            print("Step 4: Extracting content with context...")
            content_extracts = self.extract_content_with_context(filtered_docs, keyword, intent.action)
            
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
