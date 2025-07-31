from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

# ---------- API MODELS ----------

class QueryRequest(BaseModel):
    query: str
    target_file: Optional[str] = None

class QueryResponse(BaseModel):
    suggested_diff: str
    confidence: float
    fallback_used: bool

class SaveChangeRequest(BaseModel):
    original_code: str
    updated_code: str
    diff: str
    approved_by: str
    timestamp: datetime

class SaveChangeResponse(BaseModel):
    status: str

class IngestRequest(BaseModel):
    docs_dir: str

class IngestResponse(BaseModel):
    ingested_files: int
    status: str

class CollectionInfo(BaseModel):
    name: str
    vectors_count: int
    points_count: int
    status: str

# ---------- Service MODELS ----------

class Intent(BaseModel):
    action: Literal["add", "remove", "modify"]
    target: str = Field(..., description="The function/class/section to act on")
    file: Optional[str] = Field(None, description="Optional file name (e.g. 'vector_store.py')")
    object_type: Optional[Literal["function", "class", "section", "line"]] = Field(
        None, description="Type of element to act on"
    )