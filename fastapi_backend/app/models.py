
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Document(Base):
    """Model for storing document information"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    language = Column(String(10), default="en")
    source_url = Column(String(1000), nullable=True)
    content_type = Column(String(100), nullable=True)
    status_code = Column(Integer, nullable=True)
    scrape_id = Column(String(100), nullable=True)
    content = Column(Text, nullable=True)  # Store the markdown content
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DocumentVersion(Base):
         """Model for storing document versions"""
         __tablename__ = "document_versions"
         id = Column(Integer, primary_key=True, index=True)
         document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
         file_name = Column(String(255), nullable=True)
         title = Column(String(500), nullable=True)
         language = Column(String(10), nullable=True)
         source_url = Column(String(1000), nullable=True)
         content_type = Column(String(100), nullable=True)
         status_code = Column(Integer, nullable=True)
         scrape_id = Column(String(100), nullable=True)
         content = Column(Text, nullable=False)
         updated_by = Column(String(255), nullable=True)
         updated_at = Column(DateTime, default=datetime.utcnow)
         notes = Column(Text, nullable=True)