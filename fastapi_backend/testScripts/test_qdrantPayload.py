from app.config import settings
from qdrant_client import QdrantClient

client = QdrantClient(path=settings.QDRANT_PATH)

scroll_results = client.scroll(
    collection_name=settings.QDRANT_COLLECTION_NAME, limit=3, with_payload=True
)

for point in scroll_results[0]:
    print("Payload:", point.payload)
