from app.config import settings
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

client = QdrantClient(path=settings.QDRANT_PATH)

relevant_chunk_ids = [
    "7f3bef39-ab4d-4e58-9b2c-c1d72411e5a3",
    "83641496-709c-4cb3-a16a-340764ddab1c",
    "73bc7fd4-f7a0-4368-a69e-d3829c506b53",
]

for chunk_id in relevant_chunk_ids:
    filter = Filter(
        must=[FieldCondition(key="chunk_id", match=MatchValue(value=chunk_id))]
    )

    result = client.scroll(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        scroll_filter=filter,
        with_payload=True,
        limit=1,
    )

    print(f"\n=== Chunk ID: {chunk_id} ===")
    if not result[0]:
        print("Not found in Qdrant")
    else:
        point = result[0][0]
        print("Found in Qdrant")
        print("Content:", point.payload.get("page_content", "[No content]"))
        print("Doc ID:", point.payload.get("doc_id"))
        print("Chunk Type:", point.payload.get("chunk_type"))
        print("Other Keys:", list(point.payload.keys()))
