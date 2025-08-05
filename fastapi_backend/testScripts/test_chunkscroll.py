from app.config import settings
from qdrant_client import QdrantClient

client = QdrantClient(path=settings.QDRANT_PATH)

chunk_id_to_check = "398b2020-7adf-4cf8-a14b-436c34669770"

# Perform scroll
scroll_result = client.scroll(collection_name="openai_docs", limit=1, with_payload=True)

print(scroll_result[0][0].payload)  # Print the first point's payload
