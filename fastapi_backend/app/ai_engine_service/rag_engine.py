from app.schemas import Intent, DocumentUpdate
from app.ai_engine_service.intent import extract_intent, UnifiedIntentHandler, IntentHandlerFactory
from app.ai_engine_service.prompts import UNIFIED_CONTENT_PROMPT
from app.config import settings
from app.utils import logger_info, logger_error

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.documents import Document

from pathlib import Path
from typing import List, Dict, Tuple
import warnings

warnings.filterwarnings("ignore")

class DocuRAG:
    def __init__(self):
        self.llm_model = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY
        )

        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )

        self.qdrant_path = Path(settings.QDRANT_PATH)
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = QdrantClient(path=str(self.qdrant_path))
        return self._client

    def _get_vector_store(self):
        return QdrantVectorStore(
            client=self._get_client(),
            collection_name=self.collection_name,
            embedding=self.embeddings
        )

    
    async def task_runner(self, query: str) -> Dict:
        try:
            print("=== TASK ENTRY POINT ===")
            print(f"Query: {query}")

            # Step 1: Intent extraction
            print("Step 1: Extracting intent...")
            intent = await extract_intent(query)
            print(f">>>> Intent: {intent}")

            # Step 2: Retrieve relevant documents with similarity filtering
            print("Step 2: Retrieving documents with similarity filtering...")
            
            # Get documents with similarity scores
            client = self._get_client()
            query_embedding = self.embeddings.embed_query(query)
            
            search_results = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=settings.TOP_K_DOCS * 2,
                with_payload=True
            )
            
            # Filter by similarity score
            source_documents = []
            for result in search_results:
                if result.score >= settings.MIN_SIMILARITY_SCORE:
                    doc = Document(
                        page_content=result.payload.get("page_content", ""),
                        metadata=result.payload.get("metadata", {})
                    )
                    source_documents.append(doc)
                    print(f"Document included (score: {result.score:.3f})")
                else:
                    print(f"Document excluded (score: {result.score:.3f} < {settings.MIN_SIMILARITY_SCORE})")
            
            print(f"Retrieved {len(source_documents)} documents after similarity filtering")
            
            print("Step 3: Processing intent with handler...")
            handler = IntentHandlerFactory.create_handler(intent, self.llm_model)
            documents_to_update = await handler.process_intent(intent, query, source_documents)
            
            print(f"Generated {len(documents_to_update)} document updates with content")
            
            return {
                "query": query,
                "keyword": intent.target,
                "analysis": f"Retrieved {len(source_documents)} relevant documents (similarity ≥ {settings.MIN_SIMILARITY_SCORE}) containing '{intent.target}'. Generated suggested changes for {intent.action} operation.",
                "documents_to_update": documents_to_update,
                "total_documents": len(documents_to_update)
            }

        except Exception as e:
            import traceback
            logger_error.error(f"Pipeline error: {e}")
            print(traceback.format_exc())
            return {
                "query": query,
                "keyword": "unknown",
                "analysis": f"Error: {str(e)}",
                "documents_to_update": [],
                "total_documents": 0
            }

# Global instance
task = DocuRAG()

async def orchestrator(query: str) -> dict:
    print(f"Query: {query}")
    return await task.task_runner(query)
