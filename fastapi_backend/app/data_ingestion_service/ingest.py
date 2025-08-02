import json
from pathlib import Path
from datetime import datetime
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from app.config import settings

# === Config ===
DOCS_DIR = settings.DOCUMENT_LOADER_DIR
QDRANT_COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME

# === Step 1: Load and Parse JSON Files ===
async def load_documents_from_dir(directory: str):
    docs = []
    for file in Path(directory).glob("*.json"):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            markdown = data.get("markdown", "")
            metadata = data.get("metadata", {})
            if metadata.get("language", "en") != "en":
                continue  # skip non-English

            metadata.update({
                "file_path": str(file),
                "file_size": file.stat().st_size,
                "last_modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })

            docs.append(Document(page_content=markdown, metadata=metadata))
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return docs

# === Step 2: Chunk Text ===
async def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_documents(docs)

# === Step 3: Embed & Store in Qdrant ===
async def ingest_to_qdrant(docs):
    print(f"Processing {len(docs)} document chunks...")
    
    # Initialize embeddings with batch processing
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL, 
        openai_api_key=settings.OPENAI_API_KEY,
        chunk_size=settings.EMBEDDING_BATCH_SIZE
    )
    
    # Initialize Qdrant client with local file storage
    qdrant_path = Path(settings.QDRANT_PATH)
    qdrant_path.mkdir(parents=True, exist_ok=True)
    
    client = QdrantClient(path=str(qdrant_path))
    
    # Create collection if it doesn't exist
    try:
        client.get_collection(QDRANT_COLLECTION_NAME)
        print(f"Collection '{QDRANT_COLLECTION_NAME}' already exists")
    except Exception:
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=settings.VECTOR_DIMENSION, distance=Distance.COSINE),
        )
        print(f"Created collection '{QDRANT_COLLECTION_NAME}'")
    
    # Initialize vector store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embedding=embeddings,
    )
    
    # Add documents to the vector store in batches
    for i in range(0, len(docs), settings.INGESTION_BATCH_SIZE):
        batch = docs[i:i + settings.INGESTION_BATCH_SIZE]
        vector_store.add_documents(batch)
        print(f"Processed batch {i//settings.INGESTION_BATCH_SIZE + 1}/{(len(docs) + settings.INGESTION_BATCH_SIZE - 1)//settings.INGESTION_BATCH_SIZE} ({len(batch)} chunks)")
    
    print(f"✅ Ingested {len(docs)} chunks into Qdrant!")
