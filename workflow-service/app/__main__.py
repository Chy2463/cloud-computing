import json
import os
from typing import Any

import boto3
import requests
from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, Response, jsonify, request


def create_app() -> Flask:
    app = Flask(__name__)
    data_base_url = os.environ.get("DATA_BASE_URL", "http://data-service:8082").rstrip("/")
    submission_event_function_name = os.environ.get("SUBMISSION_EVENT_FUNCTION_NAME", "").strip()
    aws_region = os.environ.get("AWS_REGION", "us-east-1").strip() or "us-east-1"

    lambda_client = boto3.client("lambda", region_name=aws_region)

    def _data_url(path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{data_base_url}{path}"

    def _data_request(method: str, path: str, json_body: dict[str, Any] | None = None) -> requests.Response:
        return requests.request(
            method=method,
            url=_data_url(path),
            json=json_body,
            timeout=5,
        )

    def _invoke_submission_event(submission_id: str) -> bool:
        if not submission_event_function_name:
            return False
        payload = {"submission_id": submission_id}
        try:
            lambda_client.invoke(
                FunctionName=submission_event_function_name,
                InvocationType="Event",
                Payload=json.dumps(payload).encode("utf-8"),
            )
            return True
        except (BotoCoreError, ClientError, ValueError):
            return False

    @app.get("/health")
    def health() -> str:
        return "ok"

    @app.post("/api/submissions")
    def create_submission() -> Response:
        body = request.get_json(silent=True) or {}
        if not isinstance(body, dict):
            return jsonify({"error": "INVALID_JSON"}), 400

        input_payload = {
            "title": body.get("title"),
            "description": body.get("description"),
            "location": body.get("location"),
            "date": body.get("date"),
            "organiser": body.get("organiser"),
        }

        try:
            resp = _data_request("POST", "/records", json_body={"input": input_payload})
        except requests.RequestException:
            return jsonify({"error": "DATA_SERVICE_UNAVAILABLE"}), 503

        if resp.status_code >= 400:
            try:
                return jsonify(resp.json()), resp.status_code
            except ValueError:
                return jsonify({"error": "DATA_SERVICE_ERROR"}), 502

        try:
            created = resp.json()
        except ValueError:
            return jsonify({"error": "DATA_SERVICE_INVALID_RESPONSE"}), 502

        submission_id = created.get("submission_id")
        if not submission_id:
            return jsonify({"error": "DATA_SERVICE_INVALID_RESPONSE"}), 502

        triggered = _invoke_submission_event(str(submission_id))
        message = "created_and_processing_triggered" if triggered else "created_processing_not_triggered"
        return jsonify({"submission_id": submission_id, "message": message, "triggered": triggered}), 201

    @app.get("/api/submissions/<submission_id>")
    def get_submission(submission_id: str) -> Response:
        try:
            resp = _data_request("GET", f"/records/{submission_id}")
        except requests.RequestException:
            return jsonify({"error": "DATA_SERVICE_UNAVAILABLE"}), 503

        if resp.status_code >= 400:
            try:
                return jsonify(resp.json()), resp.status_code
            except ValueError:
                return jsonify({"error": "DATA_SERVICE_ERROR"}), 502

        try:
            return jsonify(resp.json())
        except ValueError:
            return jsonify({"error": "DATA_SERVICE_INVALID_RESPONSE"}), 502

    @app.post("/api/submissions/<submission_id>/result")
    def update_submission_result(submission_id: str) -> Response:
        body = request.get_json(silent=True) or {}
        if not isinstance(body, dict):
            return jsonify({"error": "INVALID_JSON"}), 400

        allowed_status = {"APPROVED", "NEEDS_REVISION", "INCOMPLETE"}
        allowed_category = {"OPPORTUNITY", "ACADEMIC", "SOCIAL", "GENERAL"}
        allowed_priority = {"HIGH", "MEDIUM", "NORMAL"}

        status = body.get("status")
        category = body.get("category")
        priority = body.get("priority")
        note = body.get("note")

        if status not in allowed_status:
            return jsonify({"error": "INVALID_STATUS"}), 400
        if category not in allowed_category:
            return jsonify({"error": "INVALID_CATEGORY"}), 400
        if priority not in allowed_priority:
            return jsonify({"error": "INVALID_PRIORITY"}), 400
        if not isinstance(note, str) or not note.strip():
            return jsonify({"error": "INVALID_NOTE"}), 400

        try:
            resp = _data_request(
                "PATCH",
                f"/records/{submission_id}/result",
                json_body={
                    "result": {"status": status, "category": category, "priority": priority, "note": note}
                },
            )
        except requests.RequestException:
            return jsonify({"error": "DATA_SERVICE_UNAVAILABLE"}), 503

        if resp.status_code >= 400:
            try:
                return jsonify(resp.json()), resp.status_code
            except ValueError:
                return jsonify({"error": "DATA_SERVICE_ERROR"}), 502

        return jsonify({"submission_id": submission_id, "updated": True})

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8081)

