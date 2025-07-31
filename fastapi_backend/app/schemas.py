from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, List, Dict, Any

# ---------- API MODELS ----------

class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query from user")

class QueryResponse(BaseModel):
    suggested_diff: str = Field(..., description="AI-generated diff suggestion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    fallback_used: bool = Field(..., description="Whether fallback response was used")
    score_breakdown: Optional[Dict[str, float]] = Field(None, description="Detailed confidence score breakdown")

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
    action: Literal["add", "remove", "modify"]
    target: str = Field(..., description="The function/class/section to act on")
    file: Optional[str] = Field(None, description="Optional file name (e.g. 'vector_store.py')")
    object_type: Optional[Literal["function", "class", "section", "line"]] = Field(
        None, description="Type of element to act on"
    )

