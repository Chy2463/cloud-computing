def lambda_handler(event, context):
    submission_id = (event or {}).get("submission_id")
    return {
        "submission_id": submission_id,
        "result": {
            "status": "NEEDS_REVISION",
            "category": "GENERAL",
            "priority": "NORMAL",
            "note": "Not implemented"
        }
    }

