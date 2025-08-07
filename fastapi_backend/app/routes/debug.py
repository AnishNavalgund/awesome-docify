import json
from pathlib import Path

from app.config import settings
from app.schemas import CollectionInfo, JSONFileContentResponse, JSONFileListResponse
from fastapi import APIRouter, HTTPException

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

        return {"markdown": markdown, "metadata": metadata}
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")


@router.get("/qdrant-status", response_model=CollectionInfo)
async def check_qdrant_status():
    """
    Check local Qdrant database status and collection info
    """
    try:
        # Initialize Qdrant client
        qdrant_path = Path(settings.QDRANT_PATH)

        if not qdrant_path.exists():
            raise HTTPException(status_code=404, detail="Qdrant directory not found")

        # Use singleton client to prevent multiple instances
        from app.ai_engine_service.rag_engine import get_qdrant_client

        client = get_qdrant_client()

        # Get collection info
        collection_info = client.get_collection(settings.QDRANT_COLLECTION_NAME)

        info = {
            "name": settings.QDRANT_COLLECTION_NAME,
            "vectors_count": collection_info.vectors_count,
            "points_count": collection_info.points_count,
            "status": "active",
        }

        print(f">>>>> Qdrant Debug Info: {info}")
        return CollectionInfo(**info)

    except Exception as e:
        print(f">>>>> Qdrant Debug Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get Qdrant status: {str(e)}"
        )
