# Campus Buzz — Hybrid Cloud Mini System

Campus Buzz is a small hybrid-cloud (containers + serverless) system for campus event submissions. A user submits an event, the system stores an initial submission record, runs automated checks asynchronously, and then shows the final review result back to the user.

This repository is intentionally minimal: no complex authentication, no large frontend framework, and no third‑party APIs as core logic.

## Requirements (Project Constraints)

- Hybrid execution model: containers + serverless functions
- Exactly 6 components:
  - 3 container services:
    - Presentation Service
    - Workflow Service
    - Data Service
  - 3 serverless functions:
    - Submission Event Function
    - Processing Function
    - Result Update Function
- Fixed workflow:
  1. User submits
  2. Workflow creates a submission record
  3. Submission Event Function is triggered
  4. Processing Function evaluates rules
  5. Result Update Function writes the final result back
  6. User views the updated result

## Tech Stack

- Containers: Python 3.12 + Flask (HTTP/JSON)
- Data persistence: SQLite (file-backed)
- Serverless: AWS Lambda (Python 3.12)
- Local orchestration / EC2: Docker Compose

## Repository Structure

```
cloud-computing/
  docker-compose.yml
  .env.example
  presentation-service/
  workflow-service/
  data-service/
  functions/
    submission_event/
    processing/
    result_update/
  docs/
    architecture.md
    api.md
    test-cases.md
```

## Services and Functions

### Presentation Service (Container)

- UI for submitting an event and viewing the result.
- Calls Workflow APIs.

Endpoints:
- `GET /` submission form
- `POST /submit` submits to Workflow
- `GET /status/<submission_id>` renders current status/result
- `GET /health`

### Workflow Service (Container)

- System entrypoint and orchestration layer.
- Creates records via Data Service.
- Exposes submission read APIs for UI and for Lambda.
- Asynchronously invokes `SubmissionEventFunction`.

Endpoints:
- `GET /health`
- `POST /api/submissions`
- `GET /api/submissions/<submission_id>`
- `POST /api/submissions/<submission_id>/result`

### Data Service (Container)

- Storage API backed by SQLite.
- Stores `input` and `result` per submission.

Endpoints:
- `GET /health`
- `POST /records`
- `GET /records/<submission_id>`
- `PATCH /records/<submission_id>/result`

### Submission Event Function (AWS Lambda)

- Receives `{ "submission_id": "..." }`.
- Invokes Processing, then invokes Result Update.

### Processing Function (AWS Lambda)

Fetches the submission input from Workflow, applies rules, and returns:

- `status`: `APPROVED | NEEDS_REVISION | INCOMPLETE`
- `category`: `OPPORTUNITY | ACADEMIC | SOCIAL | GENERAL`
- `priority`: `HIGH | MEDIUM | NORMAL`
- `note`: short explanation

### Result Update Function (AWS Lambda)

Writes `{status, category, priority, note}` back to Workflow.

## Environment Variables

Use `.env.example` as a template and create a local `.env` file (do not commit secrets).

### Docker Compose / Containers

- `PRESENTATION_PORT` (default `8080`)
- `WORKFLOW_PORT` (default `8081`)
- `DATA_PORT` (default `8082`)
- `WORKFLOW_BASE_URL` (default `http://workflow-service:8081`)
- `DATA_BASE_URL` (default `http://data-service:8082`)
- `SQLITE_PATH` (default `/data/campus_buzz.sqlite`)
- `AWS_REGION` (e.g. `us-east-1`)
- `SUBMISSION_EVENT_FUNCTION_NAME` (e.g. `SubmissionEventFunction`)

### Lambda Functions

ProcessingFunction and ResultUpdateFunction:
- `WORKFLOW_BASE_URL` (e.g. `http://<EC2_EIP>:8081`)

SubmissionEventFunction:
- `AWS_REGION` (e.g. `us-east-1`)
- `PROCESSING_FUNCTION_NAME` (default `ProcessingFunction`)
- `RESULT_UPDATE_FUNCTION_NAME` (default `ResultUpdateFunction`)

## Run Locally (Docker)

1. Install Docker + Docker Compose.
2. From the repository root:

```bash
cp .env.example .env
docker compose up --build
```

3. Open:
- `http://localhost:8080/`

## Run Locally (Without Docker)

Run each service in a separate terminal.

### Data Service

```bash
cd data-service
export SQLITE_PATH="$(pwd)/storage/campus_buzz.sqlite"
python -m pip install -r requirements.txt
python -m app
```

### Workflow Service

```bash
cd workflow-service
export DATA_BASE_URL="http://127.0.0.1:8082"
export AWS_REGION="us-east-1"
export SUBMISSION_EVENT_FUNCTION_NAME=""
python -m pip install -r requirements.txt
python -m app
```

### Presentation Service

```bash
cd presentation-service
export WORKFLOW_BASE_URL="http://127.0.0.1:8081"
python -m pip install -r requirements.txt
python -m app
```

## AWS Deployment (Minimal EC2 + Lambda)

This is the recommended minimal setup for the course-style project:

- 1 EC2 instance runs 3 containers via `docker compose`
- 3 AWS Lambda functions implement the asynchronous review chain

### EC2

1. Launch an EC2 instance (Ubuntu 22.04 recommended).
2. Attach an IAM Role that allows:
   - `lambda:InvokeFunction` for `SubmissionEventFunction`
3. Security Group (minimal for demo):
   - Inbound: `22` (My IP), `8080` (Anywhere), `8081` (Anywhere for Lambda-to-Workflow HTTP)
   - Optional: keep `8082` closed to the public
4. Clone this repository on EC2.
5. Create `.env` from `.env.example` and set:
   - `AWS_REGION`
   - `SUBMISSION_EVENT_FUNCTION_NAME=SubmissionEventFunction`
6. Start containers:

```bash
docker compose up --build -d
```

EC2 command checklist (Ubuntu-style):

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER
newgrp docker

git clone <YOUR_REPO_URL>
cd cloud-computing
cp .env.example .env

docker compose up --build -d
docker compose ps
```

### Lambda

Create and configure:
- `SubmissionEventFunction`
- `ProcessingFunction`
- `ResultUpdateFunction`

Minimum Lambda environment variables:
- ProcessingFunction: `WORKFLOW_BASE_URL=http://<EC2_EIP>:8081`
- ResultUpdateFunction: `WORKFLOW_BASE_URL=http://<EC2_EIP>:8081`
- SubmissionEventFunction:
  - `AWS_REGION=us-east-1`
  - `PROCESSING_FUNCTION_NAME=ProcessingFunction`
  - `RESULT_UPDATE_FUNCTION_NAME=ResultUpdateFunction`

After deployment:
1. Open `http://<EC2_EIP>:8080/` and submit an event.
2. The status page initially shows `PENDING`.
3. Refresh after a few seconds to see the final result.

## Validation and Test Cases

See [docs/test-cases.md](docs/test-cases.md) for suggested cases.
See [docs/simple-testing.md](docs/simple-testing.md) for quick, minimal test steps.

Minimum acceptance checks:
- Missing required fields → `INCOMPLETE`
- Invalid date format (`YYYY-MM-DD`) → `NEEDS_REVISION`
- Description length < 40 → `NEEDS_REVISION`
- Category assignment → `OPPORTUNITY | ACADEMIC | SOCIAL | GENERAL`
- Priority mapping → `HIGH | MEDIUM | NORMAL`

## Troubleshooting

- Status stays `PENDING`:
  - Check CloudWatch Logs for all 3 Lambda functions.
  - Verify Lambda `WORKFLOW_BASE_URL` points to `http://<EC2_EIP>:8081`.
  - Verify EC2 Security Group allows inbound `8081`.
  - Verify Workflow `.env` has `SUBMISSION_EVENT_FUNCTION_NAME=SubmissionEventFunction`.

## Evidence

See [docs/e2e-evidence.md](docs/e2e-evidence.md) for an end-to-end evidence pack (CloudWatch + EC2 container logs).
