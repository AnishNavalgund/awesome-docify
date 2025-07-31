from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .utils import simple_generate_unique_route_id
from app.config import settings
from app.routes import examples
from app.database import create_db_and_tables

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
    """Create database tables on startup"""
    await create_db_and_tables()
