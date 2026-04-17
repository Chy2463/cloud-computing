# API

## Workflow Service (Container)

### POST /api/submissions
Creates a submission record via Data Service and triggers asynchronous processing.

Request JSON:
```json
{
  "title": "string",
  "description": "string",
  "location": "string",
  "date": "YYYY-MM-DD",
  "organiser": "string"
}
```

Response JSON (201):
```json
{
  "submission_id": "string",
  "message": "created_and_processing_triggered",
  "triggered": true
}
```

Response JSON (503):
```json
{ "error": "DATA_SERVICE_UNAVAILABLE" }
```

### GET /api/submissions/<submission_id>
Fetches the submission and current result for presentation display.

Response JSON (200):
```json
{
  "submission_id": "string",
  "input": {
    "title": "string",
    "description": "string",
    "location": "string",
    "date": "string",
    "organiser": "string"
  },
  "result": {
    "status": "PENDING|APPROVED|NEEDS_REVISION|INCOMPLETE",
    "category": "OPPORTUNITY|ACADEMIC|SOCIAL|GENERAL",
    "priority": "HIGH|MEDIUM|NORMAL",
    "note": "string"
  },
  "created_at": "string",
  "updated_at": "string"
}
```

Response JSON (404):
```json
{ "error": "NOT_FOUND" }
```

### POST /api/submissions/<submission_id>/result
Result write-back endpoint for Result Update Function. Workflow forwards the update to Data Service.

Request JSON:
```json
{
  "status": "APPROVED|NEEDS_REVISION|INCOMPLETE",
  "category": "OPPORTUNITY|ACADEMIC|SOCIAL|GENERAL",
  "priority": "HIGH|MEDIUM|NORMAL",
  "note": "string"
}
```

Response JSON (200):
```json
{ "submission_id": "string", "updated": true }
```

