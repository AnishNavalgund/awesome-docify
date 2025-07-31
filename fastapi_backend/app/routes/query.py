from fastapi import APIRouter, HTTPException
from pathlib import Path
from app.schemas import (
    QueryRequest,
    QueryResponse,
    SaveChangeRequest,
    SaveChangeResponse,
    IngestRequest,
    IngestResponse,
    CollectionInfo,
)
from app.query_extractor_service.intent import extract_intent
from app.ai_engine_service import run_query_pipeline
from app.data_ingestion_service import vector_store, document_loader
from app.utils import logger_info, logger_error

router = APIRouter(prefix="/api/v1", tags=["Docify"])


@router.post("/query", response_model=QueryResponse)
async def query_docs(request: QueryRequest):
    """
    Accept user query and return AI-generated diff suggestion
    """
    intent = await extract_intent(request.query)
    logger_info.info(f">>>> Intent extracted: {intent.model_dump()}")

    try:
        rag_result = await run_query_pipeline(intent, original_query=request.query)
        return QueryResponse(**rag_result)
    except Exception as e:
        logger_error.error(f"RAG pipeline error: {e}")
        return QueryResponse(
            suggested_diff=(
                f"Action: {intent.action}, Target: {intent.target} "
                "(Fallback: RAG pipeline unavailable)"
            ),
            confidence=0.0,
            fallback_used=True,
            score_breakdown=None
        )


@router.post("/save-change", response_model=SaveChangeResponse)
async def save_change(request: SaveChangeRequest):
    """
    Save the user-approved change to DB 
    """
    # TODO: Implement persistent save (PostgreSQL)
    logger_info.info(f"Saving change: {request.diff}")
    return SaveChangeResponse(status="success")


# For future use
@router.post("/ingest", response_model=IngestResponse)
async def manual_ingest(request: IngestRequest):
    """
    Manually trigger ingestion from a directory
    """
    docs_path = Path(request.docs_dir)
    if not docs_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    documents = await document_loader.load_json_documents(request.docs_dir)
    chunked = await document_loader.chunk_documents(documents)
    await vector_store.add_documents(chunked)

    return IngestResponse(ingested_files=len(documents), status="complete")


@router.get("/collection-info", response_model=CollectionInfo)
async def collection_info():
    """
    Get vector DB collection info
    """
    info = await vector_store.get_collection_info()
    logger_info.info(f">>>>> Collection info received")
    return CollectionInfo(**info)
