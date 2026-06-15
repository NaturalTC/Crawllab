from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
from datetime import datetime, timezone

auth_bp = Blueprint("auth", __name__)


def _users():
    client = current_app.config["MONGO_CLIENT"]
    db_name = current_app.config["MONGO_DBNAME"]
    return client[db_name].users


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if _users().find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    result = _users().insert_one({
        "email": email,
        "password_hash": hashed,
        "created_at": datetime.now(timezone.utc),
    })

    token = create_access_token(identity=str(result.inserted_id))
    return jsonify({"token": token, "email": email}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = _users().find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user["_id"]))
    return jsonify({"token": token, "email": user["email"]}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    from bson import ObjectId
    user = _users().find_one({"_id": ObjectId(user_id)}, {"password_hash": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user["_id"] = str(user["_id"])
    user["created_at"] = user["created_at"].isoformat()
    return jsonify(user), 200
