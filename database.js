import os
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://esramer2009_db_user:@cluster0.fkw1q0y.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]

settings_collection = db["guild_settings"]
economy_collection = db["economy_data"]

def get_guild_setting(guild_id, key, default=None):
    guild_id = str(guild_id)
    doc = settings_collection.find_one({"guild_id": guild_id})
    if doc and key in doc:
        return doc[key]
    return default

def set_guild_setting(guild_id, key, value):
    guild_id = str(guild_id)
    settings_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {key: value}},
        upsert=True
    )

def load_data():
    doc = economy_collection.find_one({"_id": "global_economy"})
    if not doc:
        return {"balances": {}, "shops": {}}
    return {"balances": doc.get("balances", {}), "shops": doc.get("shops", {})}

def save_data(data):
    economy_collection.update_one(
        {"_id": "global_economy"},
        {"$set": {"balances": data.get("balances", {}), "shops": data.get("shops", {})}},
        upsert=True
    )
