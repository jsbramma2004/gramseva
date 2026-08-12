"""
app/database.py
Async MongoDB connection using Motor.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME", "gramseva")

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Create MongoDB connection on app startup."""
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    # ── Create indexes ────────────────────────────────────────
    await db.reports.create_index([("ticket_id", ASCENDING)], unique=True)
    await db.reports.create_index([("category", ASCENDING)])
    await db.reports.create_index([("status", ASCENDING)])
    await db.reports.create_index([("created_at", DESCENDING)])
    await db.reports.create_index([("district", ASCENDING)])

    print(f"✅  Connected to MongoDB  →  {DB_NAME}")


async def close_db():
    """Close MongoDB connection on app shutdown."""
    global client
    if client:
        client.close()
        print("🔌  MongoDB connection closed.")


def get_db():
    return db
