from app.schemas import Intent, DocumentUpdate, ContentChange
from app.ai_engine_service.intent import extract_intent, UnifiedIntentHandler, IntentHandlerFactory
from app.ai_engine_service.prompts import UNIFIED_CONTENT_PROMPT
from app.config import settings

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.prompts import ChatPromptTemplate
from qdrant_client import QdrantClient
from langchain_core.documents import Document

from pathlib import Path
from typing import List, Dict
import warnings
import json
import re

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

            # Step 2: Retrieve relevant documents
            print("Step 2: Retrieving documents...")
            vector_store = self._get_vector_store()
            retriever = vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": settings.TOP_K_DOCS, "fetch_k": 2 * settings.TOP_K_DOCS, "lambda_mult": 0.5}
            )
            source_documents: List[Document] = await retriever.ainvoke(query)
            
            print("Step 3: Processing intent with handler...")
            handler = IntentHandlerFactory.create_handler(intent, self.llm_model)
            documents_to_update = await handler.process_intent(intent, query, source_documents)
            
            print(f"Generated {len(documents_to_update)} document updates with content")
            
            return {
                "query": query,
                "keyword": intent.target,
                "analysis": f"Found {len(documents_to_update)} documents containing the keyword '{intent.target}'. Generated suggested changes for {intent.action} operation.",
                "documents_to_update": documents_to_update,
                "total_documents": len(documents_to_update)
            }

        except Exception as e:
            import traceback
            print(f"Pipeline error: {e}")
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
