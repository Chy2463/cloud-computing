import os
import re
import urllib.error
import urllib.request
import json
from typing import Any


def _pick_category(text: str) -> str:
    t = text.lower()
    opportunity = ("intern", "internship", "job", "career", "hiring", "apply", "scholarship", "volunteer", "opportunity")
    academic = ("lecture", "seminar", "workshop", "research", "conference", "exam", "study", "academic")
    social = ("party", "meetup", "club", "social", "gathering", "dinner", "game", "music")

    if any(k in t for k in opportunity):
        return "OPPORTUNITY"
    if any(k in t for k in academic):
        return "ACADEMIC"
    if any(k in t for k in social):
        return "SOCIAL"
    return "GENERAL"


def _priority_for_category(category: str) -> str:
    mapping = {"OPPORTUNITY": "HIGH", "ACADEMIC": "MEDIUM", "SOCIAL": "NORMAL", "GENERAL": "NORMAL"}
    return mapping.get(category, "NORMAL")

def _http_get_json(url: str, timeout_s: int = 5) -> tuple[int, dict[str, Any] | None]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = getattr(resp, "status", 200)
            raw = resp.read().decode("utf-8", errors="replace")
            return status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
            return e.code, json.loads(raw) if raw else {}
        except Exception:
            return e.code, None
    except Exception:
        return 0, None


def lambda_handler(event, context):
    submission_id = (event or {}).get("submission_id")
    if not submission_id:
        return {"error": "MISSING_SUBMISSION_ID"}

    workflow_base_url = os.environ.get("WORKFLOW_BASE_URL", "").rstrip("/")
    if not workflow_base_url:
        return {"submission_id": submission_id, "error": "MISSING_WORKFLOW_BASE_URL"}

    status_code, data = _http_get_json(f"{workflow_base_url}/api/submissions/{submission_id}", timeout_s=5)
    if status_code == 0:
        return {"submission_id": submission_id, "error": "WORKFLOW_UNAVAILABLE"}
    if status_code == 404:
        return {"submission_id": submission_id, "error": "NOT_FOUND"}
    if status_code != 200:
        return {"submission_id": submission_id, "error": "WORKFLOW_ERROR", "http_status": status_code}
    if not isinstance(data, dict):
        return {"submission_id": submission_id, "error": "WORKFLOW_INVALID_RESPONSE"}

    input_data: dict[str, Any] = data.get("input") or {}
    title = str(input_data.get("title") or "").strip()
    description = str(input_data.get("description") or "").strip()
    location = str(input_data.get("location") or "").strip()
    date = str(input_data.get("date") or "").strip()
    organiser = str(input_data.get("organiser") or "").strip()

    combined_text = f"{title} {description}".strip()
    category = _pick_category(combined_text)
    priority = _priority_for_category(category)

    missing = []
    if not title:
        missing.append("title")
    if not description:
        missing.append("description")
    if not location:
        missing.append("location")
    if not date:
        missing.append("date")
    if not organiser:
        missing.append("organiser")

    if missing:
        return {
            "submission_id": submission_id,
            "result": {
                "status": "INCOMPLETE",
                "category": category,
                "priority": priority,
                "note": f"Missing required fields: {', '.join(missing)}",
            },
        }

    date_ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", date))
    desc_ok = len(description) >= 40
    if not date_ok or not desc_ok:
        issues = []
        if not date_ok:
            issues.append("Date must be in YYYY-MM-DD format")
        if not desc_ok:
            issues.append("Description must be at least 40 characters")
        return {
            "submission_id": submission_id,
            "result": {
                "status": "NEEDS_REVISION",
                "category": category,
                "priority": priority,
                "note": "; ".join(issues),
            },
        }

    return {
        "submission_id": submission_id,
        "result": {
            "status": "APPROVED",
            "category": category,
            "priority": priority,
            "note": "Approved",
        },
    }

