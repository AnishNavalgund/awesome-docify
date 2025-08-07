import datetime
import json
import uuid
from pathlib import Path

from app.config import settings
from app.utils import logger_error, logger_info
from langchain.schema import Document
from langchain.text_splitter import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

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

            if metadata.get("language", "en") != "en" or not markdown.strip():
                continue  # Skip non-English or empty docs
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(file.resolve())))
            metadata.update(
                {
                    "file_path": (
                        str(file) if file else metadata.get("sourceURL", "unknown")
                    ),
                    "file_size": (
                        file.stat().st_size
                        if file
                        else metadata.get("fileSize", "unknown")
                    ),
                    "last_modified": (
                        datetime.datetime.fromtimestamp(file.stat().st_mtime)
                        if file
                        else None
                    ),
                    "title": (
                        metadata.get("title") or file.stem.replace("_", " ").title()
                        if file
                        else "Untitled"
                    ),
                    "doc_id": doc_id,
                    "version": datetime.datetime.now().isoformat(),
                    "source_url": metadata.get("sourceURL", "unknown"),
                }
            )

            docs.append(Document(page_content=markdown, metadata=metadata))
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return docs


# === Step 2: Chunk Text ===
async def chunk_documents(docs):
    all_chunks = []

    # Step 1: Setup splitters
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
    )
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    # Step 2: Split each document
    for doc in docs:
        header_chunks = header_splitter.split_text(doc.page_content)

        for chunk in header_chunks:
            # Step 2a: Start with a copy of original doc metadata
            base_metadata = doc.metadata.copy()
            base_metadata.update(
                chunk.metadata
            )  # If header_splitter added section info

            content = chunk.page_content
            # Split only when exceeding configured chunk size
            if len(content) > settings.CHUNK_SIZE:
                sub_chunks = recursive_splitter.split_text(content)
                for idx, sub in enumerate(sub_chunks):
                    metadata = base_metadata.copy()
                    metadata["chunk_id"] = str(uuid.uuid4())
                    metadata["chunk_index"] = idx
                    metadata["chunk_type"] = "recursive"
                    all_chunks.append(Document(page_content=sub, metadata=metadata))
            else:
                base_metadata["chunk_id"] = str(uuid.uuid4())
                base_metadata["chunk_index"] = 0
                base_metadata["chunk_type"] = "header"
                all_chunks.append(
                    Document(page_content=content, metadata=base_metadata)
                )

    return all_chunks


# === Step 3: Embed & Store in Qdrant ===
async def ingest_to_qdrant(docs):
    logger_info.info(f"Processing {len(docs)} document chunks...")

    # Initialize embeddings with batch processing
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        chunk_size=settings.EMBEDDING_BATCH_SIZE,
    )

    # Initialize Qdrant client with local file storage
    qdrant_path = Path(settings.QDRANT_PATH)
    qdrant_path.mkdir(parents=True, exist_ok=True)

    client = QdrantClient(path=str(qdrant_path))

    # Create collection if it doesn't exist
    try:
        client.get_collection(QDRANT_COLLECTION_NAME)
        logger_info.info(f"Collection '{QDRANT_COLLECTION_NAME}' already exists")
    except Exception:
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.VECTOR_DIMENSION, distance=Distance.COSINE
            ),
        )
        logger_info.info(f"Created collection '{QDRANT_COLLECTION_NAME}'")

    # Initialize vector store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embedding=embeddings,
    )

    # Flatten metadata to ensure top-level payload
    flattened_docs = []
    # chunk_id_log_path = Path("chunk_ids.txt")
    for doc in docs:
        flat_metadata = {**doc.metadata}  # ensure no nested 'metadata' inside
        chunk_id = flat_metadata.get("chunk_id")
        if not chunk_id:
            logger_error.error("Missing chunk_id in document metadata!")
        flattened_docs.append(
            Document(page_content=doc.page_content, metadata=flat_metadata)
        )

    # Add documents to the vector store in batches
    for i in range(0, len(flattened_docs), settings.INGESTION_BATCH_SIZE):
        batch = flattened_docs[i : i + settings.INGESTION_BATCH_SIZE]
        # logger_info.info("Ingesting chunk_ids:")
        # for doc in batch:
        #    logger_info.info(f"  - {doc.metadata.get('chunk_id')}")
        vector_store.add_documents(batch)
        logger_info.info(
            f"Processed batch {i//settings.INGESTION_BATCH_SIZE + 1}/{(len(flattened_docs) + settings.INGESTION_BATCH_SIZE - 1)//settings.INGESTION_BATCH_SIZE} ({len(batch)} chunks)"
        )

    print(f"Ingested {len(flattened_docs)} chunks into Qdrant!")
