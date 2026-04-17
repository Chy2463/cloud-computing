# Architecture

## Components

### Container Services
- Presentation Service: user form submit + status view
- Workflow Service: system entrypoint, record creation, query, and async trigger
- Data Service: record storage and CRUD APIs

### Serverless Functions
- Submission Event Function: receives submission_id and invokes Processing
- Processing Function: applies validation rules and produces result
- Result Update Function: writes result back via Workflow

## End-to-end Flow

1. User submits form to Presentation Service.
2. Presentation calls Workflow `POST /api/submissions`.
3. Workflow calls Data `POST /records` to create the initial record (result starts as PENDING).
4. Workflow asynchronously invokes Submission Event Function with:
   ```json
   { "submission_id": "..." }
   ```
5. Submission Event Function invokes Processing Function.
6. Processing Function fetches submission input from Workflow `GET /api/submissions/<id>`, computes:
   - status: APPROVED | NEEDS_REVISION | INCOMPLETE
   - category: OPPORTUNITY | ACADEMIC | SOCIAL | GENERAL
   - priority: HIGH | MEDIUM | NORMAL
   - note: short explanation
7. Result Update Function calls Workflow `POST /api/submissions/<id>/result` to persist the final result.
8. User opens the status page; Presentation fetches current state via Workflow `GET /api/submissions/<id>`.

