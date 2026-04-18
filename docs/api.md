# API

This document lists the HTTP endpoints exposed by the 3 container services.

## Conventions

- Content type: JSON unless stated otherwise.
- `submission_id`: UUID string.
- `result.status`:
  - Terminal states: `APPROVED | NEEDS_REVISION | INCOMPLETE`
  - Transitional state (internal): `PENDING` (initial record state before Lambda write-back)

## Presentation Service (Container)

Base URL (local): `http://localhost:8080`

### GET /
Returns the HTML submission form.

### POST /submit
Accepts form fields, forwards JSON to Workflow, then redirects to the status page.

Form fields:

- `title`, `description`, `location`, `date`, `organiser`

Possible responses:

- `302` redirect to `/status/<submission_id>`
- `400` HTML error page (empty form)
- `503` HTML error page (Workflow unavailable)

### GET /status/<submission_id>
Renders the current submission record and its `result` by calling Workflow `GET /api/submissions/<id>`.

Possible responses:

- `200` HTML status page
- `404` HTML error page (not found)
- `503` HTML error page (Workflow unavailable)

### GET /health
Returns `ok`.

## Workflow Service (Container)

Base URL (local): `http://localhost:8081`

### POST /api/submissions
Creates a submission record via Data Service.

Then triggers asynchronous processing by invoking `SubmissionEventFunction` *only if* `SUBMISSION_EVENT_FUNCTION_NAME` is non-empty.

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
  "message": "created_and_processing_triggered|created_processing_not_triggered",
  "triggered": true
}
```

Common error responses:

- `400` `{ "error": "INVALID_JSON" }`
- `503` `{ "error": "DATA_SERVICE_UNAVAILABLE" }`
- `502` `{ "error": "DATA_SERVICE_ERROR" | "DATA_SERVICE_INVALID_RESPONSE" }`

### GET /api/submissions/<submission_id>
Fetches the submission and current result (Workflow proxies Data Service).

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

Common error responses:

- `404` `{ "error": "NOT_FOUND" }`
- `503` `{ "error": "DATA_SERVICE_UNAVAILABLE" }`
- `502` `{ "error": "DATA_SERVICE_ERROR" | "DATA_SERVICE_INVALID_RESPONSE" }`

### POST /api/submissions/<submission_id>/result
Result write-back endpoint for `ResultUpdateFunction`.

Workflow validates and then forwards the update to Data Service `PATCH /records/<id>/result`.

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

Common error responses:

- `400` `{ "error": "INVALID_JSON|INVALID_STATUS|INVALID_CATEGORY|INVALID_PRIORITY|INVALID_NOTE" }`
- `404` `{ "error": "NOT_FOUND" }`
- `503` `{ "error": "DATA_SERVICE_UNAVAILABLE" }`
- `502` `{ "error": "DATA_SERVICE_ERROR" }`

### GET /health
Returns `ok`.

## Data Service (Container)

Base URL (local): `http://localhost:8082`

### POST /records
Creates an initial record. The stored `result` starts as `PENDING`.

Request JSON:

```json
{
  "input": {
    "title": "string",
    "description": "string",
    "location": "string",
    "date": "string",
    "organiser": "string"
  }
}
```

Response JSON (201):

```json
{
  "submission_id": "string",
  "input": {"title":"","description":"","location":"","date":"","organiser":""},
  "result": {"status":"PENDING","category":"GENERAL","priority":"NORMAL","note":"Pending processing"},
  "created_at": "string",
  "updated_at": "string"
}
```

Errors:

- `400` `{ "error": "INVALID_JSON|INVALID_INPUT" }`

### GET /records/<submission_id>
Fetches a stored record.

Errors:

- `404` `{ "error": "NOT_FOUND" }`

### PATCH /records/<submission_id>/result
Updates only the `result` object for an existing record.

Request JSON:

```json
{
  "result": {
    "status": "APPROVED|NEEDS_REVISION|INCOMPLETE|PENDING",
    "category": "OPPORTUNITY|ACADEMIC|SOCIAL|GENERAL",
    "priority": "HIGH|MEDIUM|NORMAL",
    "note": "string"
  }
}
```

Response JSON (200):

```json
{ "submission_id": "string", "updated": true, "updated_at": "string" }
```

Errors:

- `400` `{ "error": "INVALID_JSON|INVALID_RESULT" }`
- `404` `{ "error": "NOT_FOUND" }`

### GET /health
Returns `ok`.
