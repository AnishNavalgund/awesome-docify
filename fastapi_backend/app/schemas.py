from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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