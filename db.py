import os
from datetime import datetime
from typing import Optional

import certifi
from pymongo import ASCENDING, MongoClient, ReturnDocument
from pymongo.errors import ServerSelectionTimeoutError


MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://dikshaparab2005_db_user:dikshaparab_2004@cluster0.5kmcorg.mongodb.net/"
    "?appName=EventManegementCluster",
)
MONGO_DB = os.getenv("MONGO_DB", "event_management")
MONGO_CONNECT_TIMEOUT_MS = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "10000"))
MONGO_SOCKET_TIMEOUT_MS = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "20000"))
MONGO_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "10000")
)
MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "50"))


_client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
    connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
    socketTimeoutMS=MONGO_SOCKET_TIMEOUT_MS,
    maxPoolSize=MONGO_MAX_POOL_SIZE,
    tls=True,
    tlsCAFile=certifi.where(),
)
_db = _client[MONGO_DB]


def get_db():
    return _db


def ensure_connection() -> None:
    try:
        _client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        raise RuntimeError(
            "MongoDB connection failed. This is almost always caused by "
            "Atlas Network Access (IP not allowed), SSL inspection by a "
            "proxy/antivirus, or blocked outbound TLS to MongoDB Atlas. "
            "Verify your Atlas IP allowlist and try a different network "
            "if possible."
        ) from exc


def get_next_sequence(name: str) -> int:
    doc = _db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["seq"])


def init_db():
    ensure_connection()
    # Indexes for stable lookups and to enforce uniqueness.
    _db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
    _db.users.create_index([("id", ASCENDING)], unique=True, sparse=True)
    _db.food_items.create_index([("id", ASCENDING)], unique=True, sparse=True)
    _db.bookings.create_index([("id", ASCENDING)], unique=True, sparse=True)
    _db.booking_food.create_index([("id", ASCENDING)], unique=True, sparse=True)

    # Seed admin user if missing.
    if _db.users.count_documents({"role": "admin"}, limit=1) == 0:
        admin_id = get_next_sequence("users")
        _db.users.insert_one(
            {
                "id": admin_id,
                "fullname": "Admin",
                "email": "admin@gmail.com",
                "password": "1234",
                "role": "admin",
                "created_at": datetime.utcnow(),
            }
        )

    # Seed food items if empty.
    if _db.food_items.estimated_document_count() == 0:
        items = [
            {"id": 1, "name": "Batata Vada", "category": "Startup", "price": 30.00},
            {"id": 2, "name": "Paneer Tikka", "category": "Startup", "price": 120.00},
            {"id": 3, "name": "Veg Thali", "category": "Main", "price": 150.00},
            {"id": 4, "name": "Butter Chicken", "category": "Main", "price": 220.00},
            {"id": 5, "name": "Gulab Jamun", "category": "Dessert", "price": 10.00},
            {"id": 6, "name": "Jalebi", "category": "Dessert", "price": 5.00},
        ]
        _db.food_items.insert_many(items)
        _db.counters.update_one(
            {"_id": "food_items"},
            {"$set": {"seq": 6}},
            upsert=True,
        )
