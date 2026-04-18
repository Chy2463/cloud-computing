# Simple Testing Guide

This document provides quick, minimal steps to test the system without any special tooling.

## Prerequisites

- The 3 container services are running (locally via Docker Compose or on EC2).
- The 3 AWS Lambda functions are deployed and configured:
  - `SubmissionEventFunction`
  - `ProcessingFunction`
  - `ResultUpdateFunction`
- Workflow can invoke `SubmissionEventFunction`.
- Lambda functions can reach Workflow via HTTP using `WORKFLOW_BASE_URL`.

## What “Success” Looks Like

For a submitted event:

1. The record is created and initially shows `PENDING`.
2. After a few seconds, the record automatically updates to one of:
   - `APPROVED`
   - `NEEDS_REVISION`
   - `INCOMPLETE`
3. The UI shows the final fields:
   - `status`, `category`, `priority`, `note`

## Option A — Test via UI (Fastest Demo)

1. Open the submission form:
   - Local: `http://localhost:8080/`
   - EC2: `http://<EC2_EIP>:8080/`

2. Submit a valid event:
   - Title: `Internship Opportunity`
   - Description: `This is a test description with more than forty characters.`
   - Location: `Campus`
   - Date: `2026-04-17`
   - Organiser: `Alice`

3. You will be redirected to:
   - `/status/<submission_id>`

4. Refresh the page after a few seconds.
   - The result should update from `PENDING` to a final status.

## Option B — Test via Workflow API (No Browser)

Use any HTTP client. Examples below use `curl`.

PowerShell note (Windows):

- `curl` may be an alias of `Invoke-WebRequest` in some environments.
- If `curl` behaves unexpectedly, use the PowerShell examples in Option B (PowerShell).

### 1) Create a submission

```bash
curl -s -X POST http://localhost:8081/api/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "E2E Test",
    "description": "This is an end-to-end test description with more than forty characters.",
    "location": "Campus",
    "date": "2026-04-17",
    "organiser": "Bob"
  }'
```

Expected response (example):
```json
{
  "submission_id": "...",
  "message": "created_and_processing_triggered",
  "triggered": true
}
```

### 2) Query status (immediately)

```bash
curl -s http://localhost:8081/api/submissions/<submission_id>
```

Expected: `result.status` is `PENDING`.

### 3) Query status again (after a few seconds)

Wait ~5–15 seconds, then:

```bash
curl -s http://localhost:8081/api/submissions/<submission_id>
```

Expected: `result.status` is now one of `APPROVED | NEEDS_REVISION | INCOMPLETE`.

## Option C — Test Lambda Functions Individually (AWS Console)

This is useful for debugging when the UI stays `PENDING`.

### ProcessingFunction test event

```json
{ "submission_id": "<submission_id>" }
```

Expected response:

```json
{
  "submission_id": "<submission_id>",
  "result": {
    "status": "APPROVED|NEEDS_REVISION|INCOMPLETE",
    "category": "OPPORTUNITY|ACADEMIC|SOCIAL|GENERAL",
    "priority": "HIGH|MEDIUM|NORMAL",
    "note": "..."
  }
}
```

### ResultUpdateFunction test event

```json
{
  "submission_id": "<submission_id>",
  "result": {
    "status": "APPROVED",
    "category": "GENERAL",
    "priority": "NORMAL",
    "note": "manual test writeback"
  }
}
```

Expected response:

```json
{ "submission_id": "<submission_id>", "updated": true }
```

### SubmissionEventFunction test event

```json
{ "submission_id": "<submission_id>" }
```

Expected response includes:
- `result` from Processing
- `updated: true`

## Troubleshooting (Most Common)

### Status stays PENDING

1. Check CloudWatch Logs for:
   - `SubmissionEventFunction`
   - `ProcessingFunction`
   - `ResultUpdateFunction`
2. Confirm Lambda environment variables:
   - ProcessingFunction: `WORKFLOW_BASE_URL=http://<EC2_EIP>:8081`
   - ResultUpdateFunction: `WORKFLOW_BASE_URL=http://<EC2_EIP>:8081`
3. Confirm EC2 Security Group allows inbound `8081`.
4. Confirm Workflow container has:
   - `SUBMISSION_EVENT_FUNCTION_NAME=SubmissionEventFunction`
   - `AWS_REGION=<region>`

### ResultUpdateFunction returns WORKFLOW_ERROR

This usually means the write-back endpoint returned HTTP >= 400.

Verify the endpoint is reachable:

```bash
curl -i http://<EC2_EIP>:8081/health
```

And verify the write-back endpoint exists:

```bash
curl -i -X POST http://<EC2_EIP>:8081/api/submissions/<submission_id>/result \
  -H "Content-Type: application/json" \
  -d '{"status":"APPROVED","category":"GENERAL","priority":"NORMAL","note":"test"}'
```

## Option B (PowerShell) — Test via Workflow API (Windows)

### 1) Create a submission

```powershell
$body = @{
  title = "E2E Test"
  description = "This is an end-to-end test description with more than forty characters."
  location = "Campus"
  date = "2026-04-17"
  organiser = "Bob"
} | ConvertTo-Json

$resp = Invoke-RestMethod -Method Post -Uri "http://localhost:8081/api/submissions" -ContentType "application/json" -Body $body
$resp
```

Expected: `submission_id` is returned, and `triggered` is `true` when Lambda triggering is enabled.

### 2) Query status (immediately)

```powershell
$id = $resp.submission_id
Invoke-RestMethod -Method Get -Uri "http://localhost:8081/api/submissions/$id" | ConvertTo-Json -Depth 10
```

Expected: `result.status` is `PENDING`.

### 3) Query status again (after a few seconds)

```powershell
Start-Sleep -Seconds 10
Invoke-RestMethod -Method Get -Uri "http://localhost:8081/api/submissions/$id" | ConvertTo-Json -Depth 10
```

Expected: `result.status` becomes one of `APPROVED | NEEDS_REVISION | INCOMPLETE`.
