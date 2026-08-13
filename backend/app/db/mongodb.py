"""
Async Mongo connection, managed as a module-level singleton.

Why motor and not pymongo: pymongo's calls are blocking (sync) I/O. Call a
blocking function inside an `async def` and it does NOT raise an error -
it just runs synchronously and freezes the entire event loop for every
other request until it returns. motor is a wrapper around the same driver
internals but every call is a real `await`, so it yields control back to
the event loop while waiting on the network - same shape as using an async
DB client in Node instead of a sync one.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings


class Database:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


db = Database()


async def connect_to_mongo() -> None:
    settings = get_settings()
    db.client = AsyncIOMotorClient(settings.mongodb_uri)
    db.db = db.client[settings.mongodb_db_name]
    # ping forces a round trip now, so a bad URI/credentials/network fails
    # fast at startup instead of on the first request that touches Mongo.
    await db.client.admin.command("ping")


async def close_mongo_connection() -> None:
    if db.client is not None:
        db.client.close()


def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency: hand a route the live database handle."""
    assert db.db is not None, "Database not initialized - did startup run?"
    return db.db
