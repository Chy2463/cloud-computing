# Workflow Service

Orchestration gateway for the system.

## Responsibilities

- Create submission records via Data Service
- Trigger asynchronous processing by invoking `SubmissionEventFunction` (AWS Lambda)
- Serve query API for Presentation Service and ProcessingFunction
- Accept result write-back from ResultUpdateFunction

## Environment Variables

- `DATA_BASE_URL` (default `http://data-service:8082`)
- `AWS_REGION` (e.g. `us-east-1`)
- `SUBMISSION_EVENT_FUNCTION_NAME` (empty disables triggering)

## Run (without Docker)

```bash
cd workflow-service
python -m pip install -r requirements.txt
export DATA_BASE_URL="http://127.0.0.1:8082"
export AWS_REGION="us-east-1"
export SUBMISSION_EVENT_FUNCTION_NAME=""
python -m app
```

## Endpoints

- `GET /health`
- `POST /api/submissions`
- `GET /api/submissions/<submission_id>`
- `POST /api/submissions/<submission_id>/result`

