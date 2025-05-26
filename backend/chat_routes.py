from flask import Blueprint, request, jsonify
from db import create_new_chat, add_message_to_chat, get_chat, list_chats
from bson import ObjectId
from db import chats_collection



chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chats", methods=["POST"])
def start_new_chat():
    chat_id = create_new_chat()
    return jsonify({"chat_id": chat_id})

@chat_bp.route("/chats/<chat_id>/messages", methods=["POST"])
def add_message(chat_id):
    data = request.json

    if not data or "role" not in data or "content" not in data:
        return jsonify({"error": "Missing 'role' or 'content' in request"}), 400

    success = add_message_to_chat(chat_id, data["role"], data["content"])
    if not success:
        return jsonify({"error": "Failed to add message. Invalid chat_id?"}), 400

    return jsonify({"status": "message added"})

@chat_bp.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    result = chats_collection.delete_one({"_id": ObjectId(chat_id)})
    if result.deleted_count:
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Chat not found"}), 404

@chat_bp.route("/chats/<chat_id>", methods=["GET"])
def fetch_chat(chat_id):
    chat = get_chat(chat_id)
    if chat:
        chat["_id"] = str(chat["_id"])
        return jsonify(chat)
    return jsonify({"error": "Chat not found"}), 404

@chat_bp.route("/chats", methods=["GET"])
def fetch_all_chats():
    chats = list_chats()
    for chat in chats:
        chat["_id"] = str(chat["_id"])
    return jsonify(chats)
