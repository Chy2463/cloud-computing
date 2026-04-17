import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Flask, Response, jsonify, request


def create_app() -> Flask:
    app = Flask(__name__)
    sqlite_path = os.environ.get("SQLITE_PATH", "/data/campus_buzz.sqlite")

    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _connect() -> sqlite3.Connection:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db() -> None:
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS submissions (
                    submission_id TEXT PRIMARY KEY,
                    input_json TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "submission_id": row["submission_id"],
            "input": json.loads(row["input_json"]),
            "result": json.loads(row["result_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    _init_db()

    @app.get("/health")
    def health() -> str:
        return "ok"

    @app.post("/records")
    def create_record() -> Response:
        body = request.get_json(silent=True) or {}
        if not isinstance(body, dict):
            return jsonify({"error": "INVALID_JSON"}), 400

        input_payload = body.get("input")
        if not isinstance(input_payload, dict):
            return jsonify({"error": "INVALID_INPUT"}), 400

        submission_id = str(uuid.uuid4())
        now = _now_iso()
        result = {"status": "PENDING", "category": "GENERAL", "priority": "NORMAL", "note": "Pending processing"}

        with _connect() as conn:
            conn.execute(
                "INSERT INTO submissions (submission_id, input_json, result_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (submission_id, json.dumps(input_payload), json.dumps(result), now, now),
            )

        return (
            jsonify(
                {
                    "submission_id": submission_id,
                    "input": input_payload,
                    "result": result,
                    "created_at": now,
                    "updated_at": now,
                }
            ),
            201,
        )

    @app.get("/records/<submission_id>")
    def get_record(submission_id: str) -> Response:
        with _connect() as conn:
            row = conn.execute(
                "SELECT submission_id, input_json, result_json, created_at, updated_at FROM submissions WHERE submission_id=?",
                (submission_id,),
            ).fetchone()

        if row is None:
            return jsonify({"error": "NOT_FOUND"}), 404

        return jsonify(_row_to_record(row))

    @app.patch("/records/<submission_id>/result")
    def patch_result(submission_id: str) -> Response:
        body = request.get_json(silent=True) or {}
        if not isinstance(body, dict):
            return jsonify({"error": "INVALID_JSON"}), 400

        result_payload = body.get("result")
        if not isinstance(result_payload, dict):
            return jsonify({"error": "INVALID_RESULT"}), 400

        now = _now_iso()

        with _connect() as conn:
            row = conn.execute(
                "SELECT submission_id, input_json, result_json, created_at, updated_at FROM submissions WHERE submission_id=?",
                (submission_id,),
            ).fetchone()
            if row is None:
                return jsonify({"error": "NOT_FOUND"}), 404

            conn.execute(
                "UPDATE submissions SET result_json=?, updated_at=? WHERE submission_id=?",
                (json.dumps(result_payload), now, submission_id),
            )

        return jsonify({"submission_id": submission_id, "updated": True, "updated_at": now})

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8082)

