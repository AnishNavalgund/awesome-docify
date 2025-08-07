from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# ---------- API MODELS ----------


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query from user")


class DocumentUpdate(BaseModel):
    """Represents a document that needs to be updated"""

    file: str = Field(..., description="Document file name")
    action: Literal["add", "delete", "modify"] = Field(
        ..., description="Type of action needed"
    )
    reason: str = Field(..., description="Why this document needs to be updated")
    section: Optional[str] = Field(
        None, description="Specific section that needs changes"
    )
    original_content: Optional[str] = Field(
        None, description="Original content from the document"
    )
    new_content: Optional[str] = Field(None, description="Suggested new content")


class QueryResponse(BaseModel):
    """Simple response showing which documents need updates"""

    query: str = Field(..., description="Original user query")
    keyword: Optional[str] = Field(
        None, description="Target keyword extracted from query"
    )
    analysis: str = Field(..., description="What the AI found and analyzed")
    documents_to_update: List[DocumentUpdate] = Field(
        ..., description="List of documents that need changes"
    )
    total_documents: int = Field(
        ..., description="Total number of documents that need updates"
    )


class SaveChangeRequest(BaseModel):
    document_updates: List[DocumentUpdate] = Field(
        ..., description="List of document updates to save"
    )
    approved_by: str = Field(
        ..., description="Name of the person who approved the change"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the change"
    )


class SaveChangeResponse(BaseModel):
    status: str = Field(..., description="Status of the change")
    saved_count: int = Field(..., description="Number of changes saved")


class SavedChange(BaseModel):
    """Represents a saved change in memory"""

    document_update: DocumentUpdate
    approved_by: str
    timestamp: datetime
    status: str = "accepted"


class CollectionInfo(BaseModel):
    name: str = Field(..., description="Name of the vector database collection")
    vectors_count: int = Field(..., description="Number of vectors in the collection")
    points_count: int = Field(..., description="Number of points in the collection")
    status: str = Field(..., description="Status of the collection")


# ---------- Debug MODELS ----------


class JSONFileListResponse(BaseModel):
    files: List[str] = Field(..., description="List of JSON file names")


class JSONFileContentResponse(BaseModel):
    markdown: str = Field(..., description="Markdown content of the file")
    metadata: Dict[str, Any] = Field(..., description="Metadata of the file")


# ---------- Service MODELS ----------

# RAGDocumentUpdate schema removed - no longer using structured output parsing
