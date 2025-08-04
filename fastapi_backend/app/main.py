import datetime
from pathlib import Path

from app.config import settings
from app.data_ingestion_service import (
    chunk_documents,
    ingest_to_qdrant,
    load_documents_from_dir,
)
from app.database import (
    AsyncSessionLocal,
    clear_existing_data,
    create_db_and_tables,
    save_chunks_to_postgres,
)
from app.models import Document
from app.routes import debug, query
from app.utils import logger_error, simple_generate_unique_route_id
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

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
async def root():
    return {"message": "Welcome to awesome-docify API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Mount query endpoints
app.include_router(query.router)

# Mount debug endpoints
app.include_router(debug.router)


# Startup logic
@app.on_event("startup")
async def startup_event():
    try:
        # Create database tables
        await create_db_and_tables()

        await clear_existing_data()

        print("Tables truncated. Ingesting fresh data...")

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
                        version=meta.get(
                            "version", datetime.datetime.now().isoformat()
                        ),
                        last_modified=meta.get(
                            "last_modified", datetime.datetime.now().isoformat()
                        ),
                        source_url=meta.get("source_url", "unknown"),
                        content_type=meta.get("content_type"),
                        status_code=meta.get("status_code"),
                        scrape_id=meta.get("scrape_id"),
                        content=doc.page_content,
                    )
                    session.add(document)
                await session.commit()

                # chunk and save to document_chunks
                chunked_docs = await chunk_documents(docs)
                await save_chunks_to_postgres(chunked_docs, session)
                await ingest_to_qdrant(chunked_docs)

                print("Documents and chunks ingested into PostgreSQL and Qdrant")
        else:
            print("No documents found to ingest")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        client.models.list()
        print("OpenAI API key is valid")

    except Exception as e:
        logger_error.error(f"Startup warning: {e}")
