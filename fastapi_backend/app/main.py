from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from pydantic import BaseModel
from app.schemas import QueryRequest, QueryResponse, SaveChangeRequest, SaveChangeResponse, IngestRequest, IngestResponse, CollectionInfo
from typing import Optional, List
from pathlib import Path
from datetime import datetime

from app.query_extractor_service.intent import extract_intent
from openai import OpenAI

from .utils import simple_generate_unique_route_id
from app.config import settings
from app.database import create_db_and_tables
from app.data_ingestion_service import vector_store, document_loader

app = FastAPI(
    title="awesome-docify",
    description="Awesome Docify API",
    version="1.0.0",
    generate_unique_id_function=simple_generate_unique_route_id,
    openapi_url=settings.OPENAPI_URL,
)

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to awesome-docify API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from awesome-docify API!"}

# ---------- MAIN ROUTER ----------

router = APIRouter(prefix="/api/v1", tags=["Docify"])

@router.post("/query", response_model=QueryResponse)
async def query_docs(request: QueryRequest):
    """
    Accept user query and return AI-generated diff suggestion
    """
    # Step 1: Extract intent from natural language query
    intent = await extract_intent(request.query)
    print("Intent extracted:", intent.model_dump())

    # TODO: Pass intent into your RAG pipeline and generate actual diff

    # Temporary placeholder response
    return QueryResponse(
        suggested_diff=f"Action: {intent.action}, Target: {intent.target}",
        confidence=0.85,
        fallback_used=False
    )

@router.post("/save-change", response_model=SaveChangeResponse)
async def save_change(request: SaveChangeRequest):
    """
    Save the user-approved change to DB or file system
    """
    # TODO: persist changes
    return SaveChangeResponse(status="success")

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
    return CollectionInfo(**info)

# Mount router
app.include_router(router)

# ---------- STARTUP EVENT ----------
@app.on_event("startup")
async def startup_event():
    await create_db_and_tables()
    
    try:
        # Test OpenAI API key first
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # Simple test call
        client.models.list()
        print("OpenAI API key is valid")
        
        await vector_store.create_collection()
        print("Vector database collection initialized")
        
        # Check if vector store is empty
        collection_info = await vector_store.get_collection_info()
        points_count = collection_info.get("points_count", 0)
        print(f"Current collection info: {collection_info}")
        
        if points_count == 0:
            # Only ingest if vector store is empty
            docs_dir = "../local-shared-data/docs"
            docs_path = Path(docs_dir)
            
            if docs_path.exists():
                print(f"Vector store is empty. Loading documents from {docs_dir}...")
                await document_loader.ingest_documents(docs_dir)
                print("Document ingestion completed at startup")
                
                # Check collection info again after ingestion
                updated_collection_info = await vector_store.get_collection_info()
                print(f"Updated collection info after ingestion: {updated_collection_info}")
            else:
                print(f"Document directory {docs_dir} not found, skipping ingestion")
        else:
            print(f"Vector store already contains {points_count} documents. Skipping ingestion.")
            
    except Exception as e:
        print(f"Warning: Could not initialize vector database or load documents: {e}")
        print("Application will start without document ingestion. Please check your OpenAI API key and try again.")