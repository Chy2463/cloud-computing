import json
import os
import urllib.error
import urllib.request


def lambda_handler(event, context):
    submission_id = (event or {}).get("submission_id")
    result = (event or {}).get("result")
    if not submission_id or not isinstance(result, dict):
        return {"error": "INVALID_EVENT", "updated": False}

    workflow_base_url = os.environ.get("WORKFLOW_BASE_URL", "").rstrip("/")
    if not workflow_base_url:
        return {"submission_id": submission_id, "error": "MISSING_WORKFLOW_BASE_URL", "updated": False}

    url = f"{workflow_base_url}/api/submissions/{submission_id}/result"
    body = json.dumps(result).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            status_code = getattr(resp, "status", 200)
    except urllib.error.HTTPError as e:
        status_code = e.code
    except Exception:
        return {"submission_id": submission_id, "error": "WORKFLOW_UNAVAILABLE", "updated": False}

    if status_code == 404:
        return {"submission_id": submission_id, "error": "NOT_FOUND", "updated": False}
    if status_code >= 400:
        return {"submission_id": submission_id, "error": "WORKFLOW_ERROR", "http_status": status_code, "updated": False}

    return {"submission_id": submission_id, "updated": True}

