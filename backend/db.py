from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

client = MongoClient("mongodb://localhost:27017/")
db = client["sarvam_chat"]
chats_collection = db["chats"]

def create_new_chat():
    new_chat = {
        "created_at": datetime.utcnow(),
        "messages": []
    }
    result = chats_collection.insert_one(new_chat)
    return str(result.inserted_id)

def add_message_to_chat(chat_id, role, content):
    try:
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        result=chats_collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$push": {"messages": message}}
        )
        return result.modified_count > 0
    except InvalidId:
        return False

def get_chat(chat_id):
    try:
        return chats_collection.find_one({"_id": ObjectId(chat_id)})
    except InvalidId:
        return None

def list_chats():
    return list(chats_collection.find({}, {"messages": 0}))
