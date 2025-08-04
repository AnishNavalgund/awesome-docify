from typing import AsyncGenerator, List
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlalchemy import text
from .config import settings
from .models import Base, Document, DocumentVersion, DocumentChunk
import datetime
from uuid import UUID

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parents[2]

# Create async SQLAlchemy engine
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

#async def get_db() -> AsyncGenerator[AsyncSession, None]:
#    """Dependency to get async database session"""
#    async with AsyncSessionLocal() as session:
#        yield session

async def create_db_and_tables():
    """Create database tables"""
    async with engine.begin() as conn:
        # Drop all tables with CASCADE to handle foreign key dependencies
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        # Create tables with latest schema
        await conn.run_sync(Base.metadata.create_all)

async def clear_existing_data():
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE document_chunks CASCADE"))
        await conn.execute(text("TRUNCATE TABLE document_versions CASCADE"))
        await conn.execute(text("TRUNCATE TABLE documents CASCADE"))

async def is_db_empty():
    """Check if the documents table is empty"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Document))
        return result.first() is None

#async def populate_db():
#    """Populate the database with initial data"""
#    docs_path = ROOT_DIR / "local-shared-data" / "docs"
#    if not docs_path.exists():
#        print(f"Directory not found: {docs_path}")
#        return
#
#    async with AsyncSessionLocal() as session:
#        for json_file in docs_path.glob("*.json"):
#            with open(json_file, 'r') as f:
#                data = json.load(f)
#                metadata = data.get("metadata", {})
#                markdown_content = data.get("markdown", "")
#                
#                # Generate and store doc_id
#                doc_id = str(UUID(json_file.stem.encode('utf-8').hex[:32]))  # consistent UUID
#                metadata["doc_id"] = doc_id  # make available to chunks
#
#                document = Document(
#                    doc_id=doc_id,  
#                    file_name=json_file.name,
#                    title=metadata.get("title"),
#                    language=metadata.get("language", "en"),
#                    source_url=metadata.get("sourceURL"),
#                    content_type=metadata.get("contentType"),
#                    status_code=metadata.get("statusCode"),
#                    scrape_id=metadata.get("scrapeId"),
#                    content=markdown_content,
#                )
#                session.add(document)
#
#        await session.commit()


async def save_document_version_and_update(
    session: AsyncSession,
    document_id: int,
    new_content: str,
    updated_by: str = None,
    notes: str = None
):
    # Fetch the current document
    doc = await session.get(Document, document_id)
    if not doc:
        raise ValueError("Document not found")

    # Save the current version to document_versions (all metadata fields)
    version = DocumentVersion(
        document_id=doc.doc_id,
        file_name=doc.file_name,
        title=doc.title,
        language=doc.language,
        source_url=doc.source_url,
        content_type=doc.content_type,
        status_code=doc.status_code,
        scrape_id=doc.scrape_id,
        content=doc.content,
        updated_by=updated_by,
        updated_at=datetime.utcnow(),
        notes=notes,
    )
    session.add(version)

    # Update the document with new content and timestamp
    doc.content = new_content
    doc.updated_at = datetime.datetime.utcnow()
    await session.commit()
    await session.refresh(doc)
    return doc

async def save_chunks_to_postgres(chunks: List[Document], session: AsyncSession):
    for chunk in chunks:
        meta = chunk.metadata
        db_chunk = DocumentChunk(
            chunk_id=meta["chunk_id"],
            doc_id=meta["doc_id"],
            chunk_index=meta["chunk_index"],
            chunk_type=meta.get("chunk_type", "recursive"),
            content=chunk.page_content
        )
        session.add(db_chunk)
    await session.commit()