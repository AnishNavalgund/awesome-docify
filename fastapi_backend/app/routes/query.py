from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from app.schemas import (
    QueryRequest,
    QueryResponse,
    SaveChangeRequest,
    SaveChangeResponse,
    SavedChange,
    CollectionInfo,
    DocumentUpdate,
)
from app.ai_engine_service.rag_engine import orchestrator
from app.utils import logger_info, logger_error
from qdrant_client import QdrantClient
from app.config import settings

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
                section=None
            )
        ]
        return QueryResponse(
            query=request.query,
            analysis=f"Error occurred while analyzing query: {request.query}",
            documents_to_update=fallback_docs,
            total_documents=1
        )


@router.post("/save-change", response_model=SaveChangeResponse)
async def save_change(request: SaveChangeRequest):
    """
    Save the user-approved changes to in-memory storage
    """
    try:
        saved_count = 0
        
        for doc_update in request.document_updates:
            # Create unique key for each saved change
            key = f"{doc_update.file}_{datetime.now().timestamp()}_{saved_count}"
            
            # Create SavedChange object
            saved_change = SavedChange(
                document_update=doc_update,
                approved_by=request.approved_by,
                timestamp=request.timestamp,
                status="accepted"
            )
            
            # Store in memory
            saved_changes[key] = saved_change
            logger_info.info(f"Saved change for {doc_update.file}")
            saved_count += 1
            
        
        return SaveChangeResponse(
            status="success", 
            saved_count=saved_count
        )
        
    except Exception as e:
        logger_error.error(f"Error saving changes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save changes: {str(e)}")


#@router.get("/saved-changes", response_model=GetSavedChangesResponse)
#async def get_saved_changes():
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
#@router.post("/ingest", response_model=IngestResponse)
#async def manual_ingest(request: IngestRequest):
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
            "status": "active"
        }
        
        logger_info.info(f">>>>> Collection info received: {info}")
        return CollectionInfo(**info)
        
    except Exception as e:
        logger_error.error(f"Error getting collection info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get collection info: {str(e)}")
