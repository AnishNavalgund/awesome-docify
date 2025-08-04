import datetime
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ───────────────────────────────
# Enums
# ───────────────────────────────


class ChunkType(str, enum.Enum):
    header = "header"
    recursive = "recursive"


# ───────────────────────────────
# Document Table
# ───────────────────────────────


class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    file_size = Column(Integer)
    language = Column(String(10), default="en")
    version = Column(String)
    last_modified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    content = Column(Text)

    # For scraped metadata (optional)
    file_name = Column(String)
    source_url = Column(String)
    content_type = Column(String)
    status_code = Column(Integer)
    scrape_id = Column(String)
    updated_at = Column(DateTime)

    # Relationships
    versions = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


# ───────────────────────────────
# Document Versions Table
# ───────────────────────────────


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.doc_id", ondelete="CASCADE")
    )

    # Snapshot of document fields
    title = Column(Text)
    file_name = Column(String)
    language = Column(String(10))
    source_url = Column(String)
    content_type = Column(String)
    status_code = Column(Integer)
    scrape_id = Column(String)
    content = Column(Text)
    updated_by = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow())
    notes = Column(Text)

    document = relationship("Document", back_populates="versions")


# ───────────────────────────────
# Chunk Table
# ───────────────────────────────


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.doc_id", ondelete="CASCADE")
    )

    chunk_index = Column(Integer)
    chunk_type = Column(Enum(ChunkType))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())

    document = relationship("Document", back_populates="chunks")
