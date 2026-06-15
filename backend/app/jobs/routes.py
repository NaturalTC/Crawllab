from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from .service import start_job, get_progress

jobs_bp = Blueprint("jobs", __name__)


def _cols():
    client = current_app.config["MONGO_CLIENT"]
    db = client[current_app.config["MONGO_DBNAME"]]
    return db.jobs, db.results


def _serialize_job(job: dict) -> dict:
    job["_id"] = str(job["_id"])
    job["user_id"] = str(job["user_id"])
    if "created_at" in job:
        job["created_at"] = job["created_at"].isoformat()
    if job.get("completed_at") is not None:
        job["completed_at"] = job["completed_at"].isoformat()
    else:
        job["completed_at"] = None
    return job


@jobs_bp.get("")
@jwt_required()
def list_jobs():
    jobs_col, _ = _cols()
    user_id = ObjectId(get_jwt_identity())
    jobs = list(jobs_col.find({"user_id": user_id}, sort=[("created_at", -1)]))
    return jsonify([_serialize_job(j) for j in jobs]), 200


@jobs_bp.post("")
@jwt_required()
def create_job():
    data = request.get_json(silent=True) or {}
    seed = (data.get("seed_url") or "").strip()
    max_pages = int(data.get("max_pages") or 30)
    workers = int(data.get("workers") or 10)
    repeats = int(data.get("repeats") or 3)

    if not seed.startswith("http"):
        return jsonify({"error": "seed_url must be a valid URL"}), 400
    if not (5 <= max_pages <= 100):
        return jsonify({"error": "max_pages must be between 5 and 100"}), 400
    if not (1 <= workers <= 20):
        return jsonify({"error": "workers must be between 1 and 20"}), 400
    if not (1 <= repeats <= 5):
        return jsonify({"error": "repeats must be between 1 and 5"}), 400

    jobs_col, results_col = _cols()
    user_id = ObjectId(get_jwt_identity())

    result = jobs_col.insert_one({
        "user_id": user_id,
        "seed_url": seed,
        "max_pages": max_pages,
        "workers": workers,
        "repeats": repeats,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
        "error": None,
    })

    job_id = str(result.inserted_id)
    start_job(job_id, seed, max_pages, workers, repeats, jobs_col, results_col)

    job = jobs_col.find_one({"_id": result.inserted_id})
    return jsonify(_serialize_job(job)), 201


@jobs_bp.get("/<job_id>")
@jwt_required()
def get_job(job_id: str):
    jobs_col, results_col = _cols()
    user_id = ObjectId(get_jwt_identity())

    try:
        oid = ObjectId(job_id)
    except Exception:
        return jsonify({"error": "Invalid job ID"}), 400

    job = jobs_col.find_one({"_id": oid, "user_id": user_id})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    payload = _serialize_job(job)

    if job["status"] == "done":
        res = results_col.find_one({"job_id": oid}, {"_id": 0, "job_id": 0})
        payload["results"] = res

    return jsonify(payload), 200


@jobs_bp.delete("/<job_id>")
@jwt_required()
def delete_job(job_id: str):
    jobs_col, results_col = _cols()
    user_id = ObjectId(get_jwt_identity())

    try:
        oid = ObjectId(job_id)
    except Exception:
        return jsonify({"error": "Invalid job ID"}), 400

    job = jobs_col.find_one({"_id": oid, "user_id": user_id})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    jobs_col.delete_one({"_id": oid})
    results_col.delete_one({"job_id": oid})
    return jsonify({"deleted": job_id}), 200


@jobs_bp.get("/<job_id>/stream")
@jwt_required()
def stream_progress(job_id: str):
    jobs_col, _ = _cols()
    user_id = ObjectId(get_jwt_identity())

    try:
        oid = ObjectId(job_id)
    except Exception:
        return jsonify({"error": "Invalid job ID"}), 400

    job = jobs_col.find_one({"_id": oid, "user_id": user_id})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    @stream_with_context
    def generate():
        while True:
            msg = get_progress(job_id)
            data = json.dumps({"progress": msg})
            yield f"data: {data}\n\n"
            if msg in ("done", "") or msg.startswith("error:"):
                break
            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
