from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from app.schemas import JSONFileListResponse, JSONFileContentResponse

router = APIRouter(prefix="/api/v1/debug", tags=["Debug"])

DOCS_DIR = Path("../local-shared-data/docs")  # docs path

@router.get("/json-files", response_model=JSONFileListResponse)
async def list_json_files():
    """
    List all JSON files in the documentation folder
    """
    if not DOCS_DIR.exists():
        raise HTTPException(status_code=404, detail="Docs directory not found")

    files = [f.name for f in DOCS_DIR.glob("*.json")]
    print(f">>>>>> Found {len(files)} JSON files: {files}")
    return {"files": files}


@router.get("/json-files/{filename}", response_model=JSONFileContentResponse)
async def read_json_file(filename: str):
    """
    Return content of a specific JSON file
    """
    file_path = DOCS_DIR / filename
    print(f">>>>> File exists: {file_path.exists()}")

    if not file_path.exists():
        print(f">>>>> File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        print(f">>>>> Content keys: {list(content.keys())}")
        
        # Extract markdown and metadata from the content
        markdown = content.get("markdown", "")
        metadata = content.get("metadata", {})
        
        return {
            "markdown": markdown,
            "metadata": metadata
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
