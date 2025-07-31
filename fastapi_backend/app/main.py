from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .utils import simple_generate_unique_route_id
from app.config import settings
from app.routes import examples
from app.database import create_db_and_tables
from app.data_ingestion_service import vector_store, document_loader
import asyncio
from pathlib import Path

app = FastAPI(
    title="awesome-docify",
    description="Awesome Docify API",
    version="1.0.0",
    generate_unique_id_function=simple_generate_unique_route_id,
    openapi_url=settings.OPENAPI_URL,
)

# Middleware for CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to awesome-docify API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/hello")
async def hello():
    return {"message": "Hello from awesome-docify API!"}


# Include routes
app.include_router(examples.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Create database tables and load documents at startup"""
    # Create database tables
    await create_db_and_tables()
    
    # Initialize vector database collection
    try:
        await vector_store.create_collection()
        print("Vector database collection initialized")
        
        # Load JSON documents from local directory
        docs_dir = "../local-shared-data/docs"
        docs_path = Path(docs_dir)
        
        if docs_path.exists():
            print(f"Loading documents from {docs_dir}...")
            await document_loader.ingest_documents(docs_dir)
            print("Document ingestion completed at startup")
        else:
            print(f"Document directory {docs_dir} not found, skipping ingestion")
            
    except Exception as e:
        print(f"Warning: Could not initialize vector database or load documents: {e}")
