import datetime
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select

from .config import settings
from .models import Base, Document, DocumentChunk, DocumentVersion

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parents[2]

# Create async SQLAlchemy engine
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

logger_error = logging.getLogger(__name__)


@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# async def get_db() -> AsyncGenerator[AsyncSession, None]:
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


# async def populate_db():
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
    document_id: UUID,
    new_content: str,
    updated_by: str = None,
    notes: str = None,
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
        updated_at=datetime.datetime.utcnow(),
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
        if "chunk_id" not in meta:
            logger_error.error(f"Missing chunk_id in chunk metadata: {meta}")
            continue  # Skip this chunk if no chunk_id

        try:
            # Convert string chunk_id to UUID object for database storage
            chunk_id_uuid = (
                UUID(meta["chunk_id"])
                if isinstance(meta["chunk_id"], str)
                else meta["chunk_id"]
            )
            doc_id_uuid = (
                UUID(meta["doc_id"])
                if isinstance(meta["doc_id"], str)
                else meta["doc_id"]
            )

            db_chunk = DocumentChunk(
                chunk_id=chunk_id_uuid,
                doc_id=doc_id_uuid,
                chunk_index=meta["chunk_index"],
                chunk_type=meta.get("chunk_type", "recursive"),
                content=chunk.page_content,
            )
            session.add(db_chunk)
        except (ValueError, TypeError) as e:
            logger_error.error(
                f"Invalid UUID format for chunk_id {meta.get('chunk_id')} or doc_id {meta.get('doc_id')}: {e}"
            )
            continue

    await session.commit()
