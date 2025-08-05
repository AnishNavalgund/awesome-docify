import asyncio

from app.ai_engine_service.intent import extract_intent
from app.ai_engine_service.rag_engine import task
from app.database import AsyncSessionLocal
from app.models import DocumentChunk
from sqlalchemy import select


async def debug_add_operation():
    print("Debugging ADD operation issues...")

    # Test query
    query = "add a new function called test_function"

    print(f"Query: {query}")
    print("=" * 50)

    print("1. Testing intent extraction...")
    try:
        intent = await extract_intent(query)
        print(f"Intent: {intent}")
        print(f"Action: {intent.action}")
        print(f"Target: {intent.target}")
        print(f" Object type: {intent.object_type}")
    except Exception as e:
        print(f"   Intent extraction failed: {e}")
        return

    print("\n2. Testing PostgreSQL search...")
    try:
        async with AsyncSessionLocal() as session:
            # Search for the target keyword
            stmt = select(DocumentChunk.chunk_id).where(
                DocumentChunk.content.ilike(f"%{intent.target}%")
            )
            result = await session.execute(stmt)
            chunk_ids = [str(row[0]) for row in result.fetchall()]

            print(f"   Found {len(chunk_ids)} chunks containing '{intent.target}'")
            if chunk_ids:
                print(f"   Chunk IDs: {chunk_ids[:3]}...")
            else:
                print("   No chunks found - this might be the issue!")

    except Exception as e:
        print(f"  PostgreSQL search failed: {e}")

    print("\n3. Testing full RAG pipeline...")
    try:
        result = await task.task_runner(query)
        print("   RAG pipeline completed")
        print(f"   Documents to update: {len(result.get('documents_to_update', []))}")

        if "documents_to_update" in result and result["documents_to_update"]:
            for i, doc in enumerate(result["documents_to_update"]):
                print(f"   Document {i+1}: {doc.file}")
                print(f"      Action: {doc.action}")
                print(
                    f"      Original content length: {len(doc.original_content or '')}"
                )
                print(f"      New content length: {len(doc.new_content or '')}")
        else:
            print("   No documents to update - this is the problem!")

    except Exception as e:
        print(f"   RAG pipeline failed: {e}")
        import traceback

        traceback.print_exc()


async def test_different_add_queries():
    print("\ nTesting different ADD queries...")

    test_queries = [
        "add a new function called test_function",
        "add documentation for the API",
        "add a new section about error handling",
        "add a new class called DataProcessor",
        "add a new method to the existing class",
    ]

    for query in test_queries:
        print(f"\n--- Testing: {query} ---")
        try:
            intent = await extract_intent(query)
            print(f"Intent: {intent.action} -> {intent.target}")

            async with AsyncSessionLocal() as session:
                stmt = select(DocumentChunk.chunk_id).where(
                    DocumentChunk.content.ilike(f"%{intent.target}%")
                )
                result = await session.execute(stmt)
                chunk_count = len(result.fetchall())
                print(f"Chunks found: {chunk_count}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_add_operation())
    asyncio.run(test_different_add_queries())
