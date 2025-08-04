from pathlib import Path
from typing import Dict

from app.ai_engine_service.rag_engine import orchestrator
from app.config import settings
from app.database import AsyncSessionLocal, save_document_version_and_update
from app.models import Document
from app.schemas import (
    CollectionInfo,
    DocumentUpdate,
    QueryRequest,
    QueryResponse,
    SaveChangeRequest,
    SaveChangeResponse,
    SavedChange,
)
from app.utils import logger_error, logger_info
from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient
from sqlalchemy.future import select

router = APIRouter(prefix="/api/v1", tags=["Docify"])

# In-memory storage for saved changes
saved_changes: Dict[str, SavedChange] = {}


@router.post("/query", response_model=QueryResponse)
async def query_docs(request: QueryRequest):
    """
    Accept user query and return which documents need to be updated
    """
    try:
        # Pass the query directly to the vanilla RAG pipeline
        result = await orchestrator(request.query)
        return QueryResponse(**result)
    except Exception as e:
        logger_error.error(f"RAG orchestrator error: {e}")
        # Create fallback response
        fallback_docs = [
            DocumentUpdate(
                file="unknown_document.json",
                action="modify",
                reason=f"Error occurred while analyzing query: {request.query}",
                section=None,
            )
        ]
        return QueryResponse(
            query=request.query,
            analysis=f"Error occurred while analyzing query: {request.query}",
            documents_to_update=fallback_docs,
            total_documents=1,
        )


@router.post("/save-change", response_model=SaveChangeResponse)
async def save_change(request: SaveChangeRequest):
    print(">>>>> Saving changes")
    """
    Save the user-approved changes to the database (with versioning)
    """
    try:
        saved_count = 0
        async with AsyncSessionLocal() as session:
            for doc_update in request.document_updates:
                # Look up document by file_name instead of ID
                result = await session.execute(
                    select(Document).where(Document.file_name == doc_update.file)
                )
                doc = result.scalar_one_or_none()
                if not doc:
                    continue

                # Update content if provided
                if doc_update.new_content is not None:
                    doc.content = doc_update.new_content

                # Save version and update
                await save_document_version_and_update(
                    session=session,
                    document_id=doc.doc_id,
                    new_content=doc.content,  # use the possibly updated content
                    updated_by=request.approved_by,
                    notes=doc_update.reason,
                )
                saved_count += 1

        print(">>>>> Saved in the database!!!")

        return SaveChangeResponse(status="success", saved_count=saved_count)

    except Exception as e:
        logger_error.error(f"Error saving changes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save changes: {str(e)}")


# @router.get("/saved-changes", response_model=GetSavedChangesResponse)
# async def get_saved_changes():
#    """
#    Retrieve all saved changes from in-memory storage
#    """
#    try:
#        saved_changes_list = list(saved_changes.values())
#        return GetSavedChangesResponse(
#            saved_changes=saved_changes_list,
#            total_count=len(saved_changes_list)
#        )
#    except Exception as e:
#        logger_error.error(f"Error retrieving saved changes: {e}")
#        raise HTTPException(status_code=500, detail=f"Failed to retrieve saved changes: {str(e)}")

# For future use
# @router.post("/ingest", response_model=IngestResponse)
# async def manual_ingest(request: IngestRequest):
#    """
#    Manually trigger ingestion from a directory
#    """
#    docs_path = Path(request.docs_dir)
#    if not docs_path.exists():
#        raise HTTPException(status_code=404, detail="Directory not found")
#
#    documents = await document_loader.load_json_documents(request.docs_dir)
#    chunked = await document_loader.chunk_documents(documents)
#    await vector_store.add_documents(chunked)
#
#    return IngestResponse(ingested_files=len(documents), status="complete")


@router.get("/collection-info", response_model=CollectionInfo)
async def collection_info():
    """
    Get vector DB collection info
    """
    try:
        # Initialize Qdrant client
        qdrant_path = Path(settings.QDRANT_PATH)
        client = QdrantClient(path=str(qdrant_path))

        # Get collection info
        collection_info = client.get_collection(settings.QDRANT_COLLECTION_NAME)

        info = {
            "name": settings.QDRANT_COLLECTION_NAME,
            "vectors_count": collection_info.vectors_count,
            "points_count": collection_info.points_count,
            "status": "active",
        }

        logger_info.info(f">>>>> Collection info received: {info}")
        return CollectionInfo(**info)

    except Exception as e:
        logger_error.error(f"Error getting collection info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get collection info: {str(e)}"
        )
