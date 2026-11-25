import asyncio

from pymongo import AsyncMongoClient
from app.core.config import settings


async def test_connection():
    client = AsyncMongoClient(settings.MONGODB_URI)

    try:
        await client.admin.command("ping")
        print("MongoDB connected successfully!")

        database = client[settings.MONGODB_DATABASE]
        print(f"Database selected: {database.name}")

    except Exception as error:
        print(f"Connection failed: {type(error).__name__}: {error}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_connection())