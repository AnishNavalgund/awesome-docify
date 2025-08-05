import asyncio

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import DocumentChunk
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue
from sqlalchemy import select


async def check_postgres_chunks():
    """Check chunks in PostgreSQL"""
    print("Checking PostgreSQL chunks...")
    async with AsyncSessionLocal() as session:
        # Get all chunks
        stmt = select(DocumentChunk)
        result = await session.execute(stmt)
        chunks = result.scalars().all()

        print(f"Total chunks in PostgreSQL: {len(chunks)}")

        stmt = select(DocumentChunk).where(
            DocumentChunk.content.ilike("%run_demo_loop%")
        )
        result = await session.execute(stmt)
        relevant_chunks = result.scalars().all()

        print(f"Chunks containing 'run_demo_loop': {len(relevant_chunks)}")

        chunk_ids = []
        for chunk in relevant_chunks:
            chunk_id = str(chunk.chunk_id)
            chunk_ids.append(chunk_id)
            print(f"  - {chunk_id}: {chunk.content[:100]}...")

        return chunk_ids


def check_qdrant_chunks(chunk_ids):
    """Check chunks in Qdrant"""
    print("\nChecking Qdrant chunks...")
    client = QdrantClient(path=settings.QDRANT_PATH)

    # Get collection info
    try:
        collection_info = client.get_collection(settings.QDRANT_COLLECTION_NAME)
        print(f"Total points in Qdrant: {collection_info.points_count}")
    except Exception as e:
        print(f"Error getting collection info: {e}")
        return

    # Check each chunk ID
    found_count = 0
    for chunk_id in chunk_ids:
        filter_condition = Filter(
            must=[FieldCondition(key="chunk_id", match=MatchValue(value=chunk_id))]
        )

        try:
            result = client.scroll(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                scroll_filter=filter_condition,
                with_payload=True,
                limit=1,
            )

            if result[0]:
                found_count += 1
                point = result[0][0]
                print(f"Found chunk_id {chunk_id} in Qdrant")
                print(
                    f"   Content: {point.payload.get('page_content', '[No content]')[:100]}..."
                )
                print(f"   Payload keys: {list(point.payload.keys())}")
            else:
                print(f"Chunk_id {chunk_id} NOT found in Qdrant")

        except Exception as e:
            print(f"Error checking chunk_id {chunk_id}: {e}")

    print(f"\nSummary: {found_count}/{len(chunk_ids)} chunks found in Qdrant")

    # Check for any chunks in Qdrant
    try:
        all_results = client.scroll(
            collection_name=settings.QDRANT_COLLECTION_NAME, with_payload=True, limit=5
        )
        print("\nSample chunks in Qdrant:")
        for i, point in enumerate(all_results[0][:3]):
            print(f"  {i+1}. chunk_id: {point.payload.get('chunk_id', 'N/A')}")
            print(
                f"     content: {point.payload.get('page_content', '[No content]')[:50]}..."
            )
    except Exception as e:
        print(f"Error getting sample chunks: {e}")


async def main():
    print("Starting chunk_ID mismatch investigation...")

    # Check PostgreSQL
    chunk_ids = await check_postgres_chunks()

    if chunk_ids:
        # Check Qdrant
        check_qdrant_chunks(chunk_ids)
    else:
        print("No relevant chunks found in PostgreSQL")


if __name__ == "__main__":
    asyncio.run(main())
