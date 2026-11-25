from pymongo import AsyncMongoClient

from app.core.config import settings


client: AsyncMongoClient | None = None


async def connect_to_mongodb():
    global client

    client = AsyncMongoClient(settings.MONGODB_URI)

    try:
        await client.admin.command("ping")
        print("MongoDB connected successfully!")

    except Exception:
        await client.close()
        client = None
        raise


async def close_mongodb_connection():
    global client

    if client is not None:
        await client.close()
        client = None
        print("MongoDB connection closed")


def get_database():
    if client is None:
        raise RuntimeError("MongoDB client is not initialized")

    return client[settings.MONGODB_DATABASE]

async def create_database_indexes():
    database = get_database()
    users_collection = database["users"]

    await users_collection.create_index(
        "email",
        unique=True
    )

    print("Database indexes created successfully!")