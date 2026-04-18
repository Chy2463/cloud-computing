# End-to-End Evidence (Containers + Serverless)

This document is the evidence pack for MiniProject 1. It proves the required hybrid-cloud workflow using:

- EC2 + Docker Compose for 3 container services
- AWS Lambda for 3 serverless functions
- CloudWatch Logs (Lambda) and container logs (EC2) as runtime proof

## Evidence Metadata

- Evidence date (UTC): `<YYYY-MM-DD>`
- EC2 public IP / EIP: `<EC2_EIP>`
- One traced submission_id: `<submission_id>`

All screenshots and log snippets below must include the same `submission_id`.

## Required Workflow (What Must Be Proven)

The project requires the following fixed flow:

1. User submits an event (Presentation Service)
2. Workflow creates an initial submission record (Workflow Service → Data Service)
3. Submission Event Function is triggered (Workflow Service → Lambda)
4. Processing Function evaluates the submission (Lambda → Workflow Service)
5. Result Update Function writes the final result (Lambda → Workflow Service → Data Service)
6. User views the final status/category/priority/note (Presentation Service → Workflow Service)

## Evidence Set Overview

The attached screenshots/logs provide:

- CloudWatch Logs:
  - SubmissionEventFunction (successful run)
  - ProcessingFunction (successful run)
  - ResultUpdateFunction (successful run)
- EC2 container logs:
  - Presentation service requests
  - Workflow service API calls (create, query, write-back)
  - Data service storage operations (create record, patch result)

Each evidence item below includes the same `submission_id` and can be traced across components.

## Evidence 0 — UI Proof (Presentation Service on EC2)

Attach:

- Screenshot A: `http://<EC2_EIP>:8080/` (submission form)
- Screenshot B: `http://<EC2_EIP>:8080/status/<submission_id>` showing initial `PENDING`
- Screenshot C: same URL after refresh showing final `APPROVED | NEEDS_REVISION | INCOMPLETE`

Notes:

- The project expects the status to start as `PENDING` and update after a few seconds.

## Evidence 1 — SubmissionEventFunction (CloudWatch Logs)

## Evidence 1 — SubmissionEventFunction (CloudWatch Logs)

What to look for:

- A log entry confirming the function received the event with a `submission_id`.
- A log entry after Processing is invoked, showing `processing_done` and the computed `result`.
- A log entry after Result Update is invoked, showing `result_update_done` with `updated: true`.

Why this proves correctness:

- Confirms the serverless chain is executed in the correct order:
  - SubmissionEvent → Processing → ResultUpdate
- Confirms the event payload contract uses `submission_id`.
- Confirms downstream processing returned a structured `result` and the write-back step completed.

## Evidence 2 — ProcessingFunction (CloudWatch Logs)

What to look for:

- A successful invocation (START/END/REPORT lines).
- Absence of runtime import errors.
- (Optional) Any prints that confirm it fetched submission input via:
  - `GET /api/submissions/<submission_id>` on Workflow Service

Why this proves correctness:

- Confirms the automated review rules execute in a serverless environment.
- Confirms Processing is able to reach Workflow Service over HTTP using `WORKFLOW_BASE_URL`.

## Evidence 3 — ResultUpdateFunction (CloudWatch Logs)

What to look for:

- A successful invocation (START/END/REPORT lines).
- The function returns `updated: true` (or logs showing a successful HTTP status).
- (Optional) Any message indicating it posted the final result to:
  - `POST /api/submissions/<submission_id>/result` on Workflow Service

Why this proves correctness:

- Confirms the final status/category/priority/note is persisted back to the system through Workflow Service (not directly to the Data Service), matching the intended orchestration design.

## Evidence 4 — EC2 Container Logs (Docker Compose)

What to look for in the EC2 logs:

### 4.1 Presentation Service

- Requests for the UI and submission flow:
  - `GET /` (submission form page)
  - `POST /submit` (form submit from user)
  - `GET /status/<submission_id>` (result page)

This proves:

- The user interaction and UI are running in a container on EC2.

### 4.2 Workflow Service

- Submission creation endpoint:
  - `POST /api/submissions` returning `201`
- Query endpoint polled by the UI:
  - `GET /api/submissions/<submission_id>` returning `200`
- Write-back endpoint called by ResultUpdateFunction:
  - `POST /api/submissions/<submission_id>/result` returning `200`

This proves:

- Workflow Service is the orchestration gateway for both the UI and Lambda.
- The “create → trigger → query → write-back” API surface matches the project design.

### 4.3 Data Service

- Record creation:
  - `POST /records` returning `201`
- Record query:
  - `GET /records/<submission_id>` returning `200`
- Result persistence:
  - `PATCH /records/<submission_id>/result` returning `200`

This proves:

- Submission records are persisted in the Data Service (SQLite-backed).
- The final review result is stored (not just computed).

## Cross-Component Traceability

To demonstrate end-to-end traceability:

1. Pick a single `submission_id` shown in the CloudWatch logs.
2. Find the same `submission_id` in EC2 container logs for:
   - `POST /api/submissions` (creation)
   - `GET /api/submissions/<id>` (polling / view)
   - `POST /api/submissions/<id>/result` and `PATCH /records/<id>/result` (write-back)
3. Open the UI status page:
   - `http://<EC2_EIP>:8080/status/<submission_id>`
4. Confirm the displayed fields match the final stored result:
   - `status`, `category`, `priority`, `note`

## Collection Commands (Copy/Paste)

Run on EC2 (from repository root) to capture container logs:

```bash
docker compose ps
docker compose logs --tail=200 presentation-service
docker compose logs --tail=200 workflow-service
docker compose logs --tail=200 data-service
```

Optional: verify the record state via Workflow API:

```bash
curl -s http://127.0.0.1:8081/api/submissions/<submission_id> | python3 -m json.tool
```

CloudWatch Logs:

- Open each Lambda log group and search for the same `submission_id`.
- Copy/paste the relevant START/END/REPORT lines and the JSON log lines (or attach screenshots).

## Conclusion

Together, the CloudWatch Logs and EC2 container logs provide runtime evidence that:

- The system uses the required hybrid-cloud model (containers + serverless).
- Exactly 6 components participate in the workflow as required.
- The fixed end-to-end processing flow executes correctly.
- The final result is persisted and visible to the user.
