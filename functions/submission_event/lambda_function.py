import json
import os

import boto3


def lambda_handler(event, context):
    submission_id = (event or {}).get("submission_id")
    if not submission_id:
        return {"error": "MISSING_SUBMISSION_ID", "updated": False}

    region = os.environ.get("AWS_REGION", "us-east-1")
    processing_function_name = os.environ.get("PROCESSING_FUNCTION_NAME", "ProcessingFunction")
    result_update_function_name = os.environ.get("RESULT_UPDATE_FUNCTION_NAME", "ResultUpdateFunction")

    client = boto3.client("lambda", region_name=region)

    print(json.dumps({"stage": "submission_event_received", "submission_id": submission_id}))

    processing_resp = client.invoke(
        FunctionName=processing_function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps({"submission_id": submission_id}).encode("utf-8"),
    )
    processing_payload_raw = processing_resp.get("Payload").read()
    processing_payload = json.loads(processing_payload_raw.decode("utf-8") or "{}")

    print(json.dumps({"stage": "processing_done", "submission_id": submission_id, "result": processing_payload.get("result")}))

    result_update_resp = client.invoke(
        FunctionName=result_update_function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(processing_payload).encode("utf-8"),
    )
    result_update_payload_raw = result_update_resp.get("Payload").read()
    result_update_payload = json.loads(result_update_payload_raw.decode("utf-8") or "{}")

    print(json.dumps({"stage": "result_update_done", "submission_id": submission_id, "updated": result_update_payload.get("updated")}))

    return {
        "submission_id": submission_id,
        "result": processing_payload.get("result"),
        "updated": bool(result_update_payload.get("updated")),
    }

