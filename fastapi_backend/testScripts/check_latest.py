import asyncio

from app.database import AsyncSessionLocal
from sqlalchemy import text


async def check_latest():
    async with AsyncSessionLocal() as session:
        print("LATEST CHANGES CHECK")

        # Check latest version records
        result = await session.execute(
            text(
                """
            SELECT id, file_name, updated_by, updated_at, notes
            FROM document_versions
            ORDER BY updated_at DESC
            LIMIT 3
        """
            )
        )
        rows = result.fetchall()

        print("Latest 3 version records:")
        for row in rows:
            print(f"  ID: {row[0]}, File: {row[1]}, By: {row[2]}, At: {row[3]}")
            print(f"  Notes: {row[4]}")
            print("  ---")

        # Check latest document updates
        result = await session.execute(
            text(
                """
            SELECT doc_id, file_name, updated_at
            FROM documents
            WHERE updated_at IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 3
        """
            )
        )
        rows = result.fetchall()

        print("\nLatest 3 document updates:")
        for row in rows:
            print(f"  Doc ID: {row[0]}, File: {row[1]}, Updated: {row[2]}")
            print("  ---")


if __name__ == "__main__":
    asyncio.run(check_latest())
