from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def get_database():
    return db.client.visionpay
