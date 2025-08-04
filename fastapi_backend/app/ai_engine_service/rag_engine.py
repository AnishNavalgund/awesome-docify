from app.schemas import Intent, DocumentUpdate
from app.ai_engine_service.intent import extract_intent, UnifiedIntentHandler, IntentHandlerFactory
from app.ai_engine_service.prompts import UNIFIED_CONTENT_PROMPT
from app.config import settings
from app.utils import logger_info, logger_error
from sqlalchemy import select

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchAny
from langchain_core.documents import Document

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session  
from app.models import DocumentChunk

from pathlib import Path
from typing import List, Dict
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

    async def _get_relevant_chunk_ids(self, intent: Intent, db: AsyncSession) -> List[str]:
        keyword = intent.target

        # content-based filter
        stmt = select(DocumentChunk.chunk_id).where(
            DocumentChunk.content.ilike(f"%{keyword}%")
        )
        result = await db.execute(stmt)
        chunk_ids = [str(row[0]) for row in result.fetchall()]

       # intent is "add" - fallback to top-K recent or semantic search
        if not chunk_ids and intent.action == "add":
            logger_info.info(f"No chunks found for '{keyword}', fallback to recent or related chunks for 'add' intent.")

            # Return latest N chunks - temporary fix
            stmt = select(DocumentChunk.chunk_id).order_by(DocumentChunk.created_at.desc()).limit(10)
            result = await db.execute(stmt)
            chunk_ids = [str(row[0]) for row in result.fetchall()]

        return chunk_ids

    async def task_runner(self, query: str) -> Dict:
        try:
            print("=== TASK ENTRY POINT ===")
            print(f"Query: {query}")

            intent = await extract_intent(query)
            print(f">>>> Intent: {intent}")

            async with get_db_session() as db:
                relevant_chunk_ids = await self._get_relevant_chunk_ids(intent, db)

            print(f" >>> Postgres filter returned {len(relevant_chunk_ids)} chunk_ids")
            print(f" >>> Chunk IDs: {relevant_chunk_ids}")

            query_embedding = self.embeddings.embed_query(query)
            client = self._get_client()

            search_results = []

            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata.chunk_id",
                        match=MatchAny(any=relevant_chunk_ids)
                    )
                ]
            )

            if relevant_chunk_ids:
                search_results = client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=settings.TOP_K_DOCS * 2,
                    with_payload=True,
                    query_filter=query_filter
                )
            else:
                logger_info.info("No relevant chunk_ids found — skipping Qdrant search.")

            logger_info.info(
                f"Filtered chunks: {len(relevant_chunk_ids)}, "
                f"Qdrant results: {len(search_results)}"
            )

            source_documents = []
            for result in search_results:
                chunk_id = result.payload.get('metadata', {}).get('chunk_id', 'N/A')
                print(f"Chunk ID: {chunk_id}, Score: {result.score:.4f}")
                if result.score >= settings.MIN_SIMILARITY_SCORE:
                    doc = Document(
                        page_content=result.payload.get("page_content", ""),
                        metadata=result.payload.get("metadata", {})
                    )
                    source_documents.append(doc)

            print(f"Retrieved {len(source_documents)} high-confidence documents")

            handler = IntentHandlerFactory.create_handler(intent, self.llm_model)
            documents_to_update = await handler.process_intent(intent, query, source_documents)

            return {
                "query": query,
                "keyword": intent.target,
                "analysis": f"Retrieved {len(source_documents)} relevant documents (similarity ≥ {settings.MIN_SIMILARITY_SCORE}) containing '{intent.target}'.",
                "documents_to_update": documents_to_update,
                "total_documents": len(documents_to_update)
            }

        except Exception as e:
            logger_error.error(f"Pipeline error: {e}")
            raise e
        
# Global instance
task = DocuRAG()

async def orchestrator(query: str) -> dict:
    return await task.task_runner(query)