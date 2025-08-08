import asyncio

from app.database import AsyncSessionLocal
from app.models import Document, DocumentVersion
from sqlalchemy import select


async def check_database():
    async with AsyncSessionLocal() as session:
        print("CHECKING DOCUMENTS TABLE")
        result = await session.execute(select(Document))
        docs = result.scalars().all()
        print(f"Total documents: {len(docs)}")

        for doc in docs[:3]:
            print(f"Doc ID: {doc.doc_id}")
            print(f"File: {doc.file_name}")
            print(f"Title: {doc.title}")
            print(f"Content length: {len(doc.content) if doc.content else 0}")
            print(f"Updated at: {doc.updated_at}")
            print("---")

        print("\nCHECKING DOCUMENT_VERSIONS TABLE")
        result = await session.execute(select(DocumentVersion))
        versions = result.scalars().all()
        print(f"Total versions: {len(versions)}")

        for version in versions[:3]:
            print(f"Version ID: {version.id}")
            print(f"Document ID: {version.document_id}")
            print(f"File: {version.file_name}")
            print(f"Updated by: {version.updated_by}")
            print(f"Updated at: {version.updated_at}")
            print(f"Notes: {version.notes}")
            print("---")


if __name__ == "__main__":
    asyncio.run(check_database())
