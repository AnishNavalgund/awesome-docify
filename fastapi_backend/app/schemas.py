from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, List, Dict, Any

# ---------- API MODELS ----------

class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query from user")

class DocumentUpdate(BaseModel):
    """Represents a document that needs to be updated"""
    file: str = Field(..., description="Document file name")
    action: Literal["add", "delete", "modify"] = Field(..., description="Type of action needed")
    reason: str = Field(..., description="Why this document needs to be updated")
    section: Optional[str] = Field(None, description="Specific section that needs changes")
    original_content: Optional[str] = Field(None, description="Original content from the document")
    new_content: Optional[str] = Field(None, description="Suggested new content")
    line_numbers: Optional[List[int]] = Field(None, description="Line numbers where changes should be made")

class QueryResponse(BaseModel):
    """Simple response showing which documents need updates"""
    query: str = Field(..., description="Original user query")
    analysis: str = Field(..., description="What the AI found and analyzed")
    documents_to_update: List[DocumentUpdate] = Field(..., description="List of documents that need changes")
    total_documents: int = Field(..., description="Total number of documents that need updates")

class SaveChangeRequest(BaseModel):
    original_code: str = Field(..., description="Original code to be modified")
    updated_code: str = Field(..., description="Updated code after modification")
    diff: str = Field(..., description="Diff between original and updated code")
    approved_by: str = Field(..., description="Name of the person who approved the change")
    timestamp: datetime = Field(..., description="Timestamp of the change")

class SaveChangeResponse(BaseModel):
    status: str = Field(..., description="Status of the change")

class IngestRequest(BaseModel):
    docs_dir: str = Field(..., description="Directory containing JSON files to ingest")

class IngestResponse(BaseModel):
    ingested_files: int = Field(..., description="Number of files ingested")
    status: str = Field(..., description="Status of the ingestion process")

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

class Intent(BaseModel):
    action: Literal["add", "delete", "modify"]
    target: str = Field(..., description="The function/class/section to act on")
    file: Optional[str] = Field(None, description="Optional file name (e.g. 'vector_store.py')")
    object_type: Optional[Literal["function", "class", "section", "line"]] = Field(
        None, description="Type of element to act on"
    )


class ContentChange(BaseModel):
    """Structured output for content changes"""
    original_content: str = Field(description="The original content as is")
    new_content: str = Field(description="The new content with changes")

