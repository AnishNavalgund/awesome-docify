from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import query
from app.routes import debug
from app.utils import simple_generate_unique_route_id
from app.database import create_db_and_tables, is_db_empty, save_chunks_to_postgres, clear_existing_data
from app.data_ingestion_service import load_documents_from_dir, chunk_documents, ingest_to_qdrant
from openai import OpenAI
from pathlib import Path
from app.utils import logger_info, logger_error
from qdrant_client import QdrantClient
from app.database import AsyncSessionLocal
from app.models import Document
import datetime
app = FastAPI(
    title="awesome-docify",
    description="Awesome Docify API",
    version="1.0.0",
    generate_unique_id_function=simple_generate_unique_route_id,
    openapi_url=settings.OPENAPI_URL,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root(): return {"message": "Welcome to awesome-docify API"}

@app.get("/health")
async def health_check(): return {"status": "healthy"}

# Mount query endpoints
app.include_router(query.router)

# Mount debug endpoints
app.include_router(debug.router)

# Startup logic
@app.on_event("startup")
async def startup_event():
    # Create database tables
    await create_db_and_tables()

    await clear_existing_data()

    print("Tables truncated. Ingesting fresh data...")

    if await is_db_empty():
        print("PostgreSQL documents table is empty, populating with the data...")
        try:
            docs = await load_documents_from_dir(settings.DOCUMENT_LOADER_DIR)
            if docs:
                async with AsyncSessionLocal() as session:
                    # Insert documents into DB first
                    for doc in docs:
                        meta = doc.metadata
                        document = Document(
                            doc_id=meta["doc_id"], 
                            file_name=Path(meta.get("file_path", "unknown")).name,
                            title=meta.get("title", "Untitled"),
                            file_path=meta.get("file_path", "unknown"),
                            file_size=meta.get("file_size", 0),
                            language=meta.get("language", "en"),
                            version=meta.get("version", datetime.datetime.now().isoformat()),
                            last_modified=meta.get("last_modified", datetime.datetime.now().isoformat()),
                            source_url=meta.get("source_url", "unknown"),
                            content_type=meta.get("content_type"),
                            status_code=meta.get("status_code"),
                            scrape_id=meta.get("scrape_id"),
                            content=doc.page_content
                            )
                        session.add(document)
                    await session.commit()

                    # chunk and save to document_chunks
                    chunked_docs = await chunk_documents(docs)
                    await save_chunks_to_postgres(chunked_docs, session)

                print("Documents and chunks ingested into PostgreSQL")
            else:
                print("No documents found to ingest")
        except Exception as e:
            logger_error.error(f"PostgreSQL ingestion failed: {e}")
    else:
        print("PostgreSQL documents table already contains data, skipping population")
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        client.models.list()
        print("OpenAI API key is valid")
        
        # Check if chunks are already ingested using local Qdrant
        qdrant_client = None
        try:
            qdrant_client = QdrantClient(path=settings.QDRANT_PATH)
            collection_info = qdrant_client.get_collection(settings.QDRANT_COLLECTION_NAME)
            points_count = collection_info.points_count
            print(f"Collection '{settings.QDRANT_COLLECTION_NAME}' has {points_count} documents")
            has_documents = points_count > 0
        except Exception as e:
            logger_error.error(f"Collection check failed: {e}")
            has_documents = False
        finally:
            if qdrant_client:
                qdrant_client.close()
        
        if has_documents:
            print("Embeddings already ingested to Qdrant, skipping ingestion!")
        else:
            print("No documents found in collection, starting ingestion...")
            # Load and ingest documents using the ingest functions
            docs = await load_documents_from_dir(settings.DOCUMENT_LOADER_DIR)
            print(f"Loaded {len(docs)} documents in english language only")
            if docs:
                await ingest_to_qdrant(chunked_docs)
                print("Embeddings ingestion to Qdrant completed")
            else:
                print("No documents found to ingest")
            
    except Exception as e:
        logger_error.error(f"Startup warning: {e}")
