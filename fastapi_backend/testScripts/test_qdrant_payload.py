from app.config import settings
from qdrant_client import QdrantClient


def examine_qdrant_payloads():
    print(" Examining Qdrant payload structure...")

    client = QdrantClient(path=settings.QDRANT_PATH)

    # Get a few sample points
    results = client.scroll(
        collection_name=settings.QDRANT_COLLECTION_NAME, with_payload=True, limit=5
    )

    print(f" Found {len(results[0])} points in Qdrant")

    for i, point in enumerate(results[0]):
        print(f"\n=== Point {i+1} ===")
        print(f"ID: {point.id}")
        print(f"Payload keys: {list(point.payload.keys())}")
        print(f"Payload: {point.payload}")

        # Check for specific fields
        if "chunk_id" in point.payload:
            print(f"chunk_id found: {point.payload['chunk_id']}")
        else:
            print("chunk_id NOT found in payload")

        if "page_content" in point.payload:
            print(f"page_content found: {point.payload['page_content'][:100]}...")
        else:
            print("page_content NOT found in payload")

        if "metadata" in point.payload:
            print(f"metadata found: {point.payload['metadata']}")
        else:
            print("metadata NOT found in payload")


if __name__ == "__main__":
    examine_qdrant_payloads()
