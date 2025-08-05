import asyncio

from app.ai_engine_service.intent import extract_intent
from app.ai_engine_service.rag_engine import task


async def test_add_operation():
    print("Testing ADD operation...")

    # Test queries for adding new content
    test_queries = [
        "add a new function called test_function",
        "add a new section about error handling",
        "add documentation for the new API endpoint",
        "add a new class called DataProcessor",
    ]

    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        print("=" * 60)

        try:
            # Test intent extraction
            print("1. Testing intent extraction...")
            intent = await extract_intent(query)
            print(f"Intent: {intent}")

            # Test the full RAG pipeline
            print("2. Testing full RAG pipeline...")
            result = await task.task_runner(query)
            print(f"Result    : {result}")

            # Check if documents were found
            docs_found = len(result.get("documents_to_update", []))
            print(f"Documents to update: {docs_found}")

            if docs_found > 0:
                for i, doc in enumerate(result["documents_to_update"]):
                    print(f"Document {i+1}: {doc.file}")
                    print(f"      Action: {doc.action}")
                    print(f"      Reason: {doc.reason}")
                    print(
                        f"      Original content length: {len(doc.original_content or '')}"
                    )
                    print(f"      New content length: {len(doc.new_content or '')}")
            else:
                print("No documents found to update")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()


async def test_specific_add_query():
    print("\nTesting specific ADD query...")

    query = "add a new function called run_demo_in_loop that replaces run_demo_loop"

    try:
        # Test intent extraction
        intent = await extract_intent(query)
        print(f"Intent: {intent}")

        # Test RAG pipeline
        result = await task.task_runner(query)
        print(f"Result: {result}")

        # Check the response structure
        if "documents_to_update" in result:
            for doc in result["documents_to_update"]:
                print(f"\nDocument: {doc.file}")
                print(f"Action: {doc.action}")
                print(f"Original: {doc.original_content[:200]}...")
                print(f"New: {doc.new_content[:200]}...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_add_operation())
    asyncio.run(test_specific_add_query())
