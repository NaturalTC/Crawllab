from __future__ import annotations

from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient

jwt = JWTManager()
cors = CORS()
_mongo_client: MongoClient | None = None


def get_db():
    return _mongo_client.get_default_database()


def init_mongo(app):
    global _mongo_client
    _mongo_client = MongoClient(
        app.config["MONGO_URI"],
        uuidRepresentation="standard",
    )
    _mongo_client[app.config["MONGO_DBNAME"]]  # touch to verify connection
    app.config["MONGO_CLIENT"] = _mongo_client
