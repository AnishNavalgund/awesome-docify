from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import query
from app.routes import debug
from app.utils import simple_generate_unique_route_id
from app.database import create_db_and_tables
from app.data_ingestion_service import vector_store, document_loader
from openai import OpenAI
from pathlib import Path
from app.utils import logger_info, logger_error

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
    await create_db_and_tables()
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        client.models.list()
        logger_info.info("OpenAI API key is valid")
        await vector_store.create_collection()
        collection_info = await vector_store.get_collection_info()
        if collection_info.get("points_count", 0) == 0:
            docs_dir = "../local-shared-data/docs"
            if Path(docs_dir).exists():
                logger_info.info(f"Vector store is empty. Ingesting from {docs_dir}...")
                await document_loader.ingest_documents(docs_dir)
    except Exception as e:
        logger_error.error(f"Startup warning: {e}")
