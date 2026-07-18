# AI-Assisted Property Address Standardization System

A production-grade, full-stack address standardization pipeline that unifies property records, routes low/medium confidence matches for human-in-the-loop validation, and continuously learns from human feedback.

## Architecture Overview

```
                          ┌────────────────────────┐
                          │    Raw Address Ingest  │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │     NestJS Backend     │
                          │   (Standardization    │
                          │     Coordinator)       │
                          └─────┬───────────▲──────┘
                                │           │
               POST /standardize│           │ HTTP Responses
                                ▼           │
                          ┌────────────────────────┐
                          │    Python ML Service   │
                          │ (FastAPI + libpostal + │
                          │  LightGBM Classifier)  │
                          └────────────────────────┘
```

The system consists of two primary components:
1. **NestJS Backend**: Exposes the external standardization API, maintains queues, logs audit trails, and stores canonical master address records in PostgreSQL.
2. **Python ML Service**: A high-performance FastAPI service that uses `libpostal` to parse addresses, extracts custom features, score standardizations using a LightGBM classifier, and generates vector embeddings.

## Confidence Routing Matrix

Each standardized address receives a predicted confidence score $C \in [0, 1]$:

| Score | Routing Decision | Database Action | Status |
|---|---|---|---|
| $C \ge 0.80$ | `auto_accepted` | Find or create canonical master address | Linked directly |
| $0.50 \le C < 0.80$ | `pending_review` | Send to review queue | `pending` |
| $C < 0.50$ | `flagged` | Send to manual queue with warning details | `pending` |

## Active Learning & RETRAINING LOOP

- **Priority Queue Scoring**: Review queue priorities are dynamically computed as $1.0 - |C - 0.65|$ to select items nearest to the decision boundary (Uncertainty Sampling).
- **Auto Retraining**: The system tracks unused feedback items. Once 50 human validation corrections are logged, the backend triggers an automatic retraining process on the ML service, saving a new LightGBM model version.

---

## Quick Start (Docker Compose)

### Prerequisite
Make sure Docker and Docker Compose are installed on your machine.

### Instructions

1. **Clone/Move to the project directory**:
   Make sure you are in the workspace root directory:
   ```bash
   cd C:\Users\sanat\.gemini\antigravity\scratch\address-standardization
   ```

2. **Launch the Docker Stack**:
   ```bash
   docker-compose up --build -d
   ```
   This will spin up:
   - **PostgreSQL (pgvector)**: Exposing port `5432` with initialized schemas and similarity lookup functions.
   - **Redis**: Exposing port `6379` for background job execution.
   - **ML Service**: Exposing port `8000` (FastAPI).
   - **Backend**: Exposing port `3000` (NestJS).

---

## API Endpoints

### 1. Standardization Coordinator

- **Standardize Address**
  - **Method**: `POST`
  - **Path**: `/addresses/standardize`
  - **Payload**:
    ```json
    {
      "rawAddress": "45 W 34 St Apt 2, NY 12308",
      "sourceSystem": "property_db",
      "sourceRecordId": "REC-12345"
    }
    ```

- **Get Standardization Result**
  - **Method**: `GET`
  - **Path**: `/addresses/:id`

- **List Standardizations**
  - **Method**: `GET`
  - **Path**: `/addresses?page=1&limit=20`

### 2. Human-In-The-Loop Validation Queue

- **Get Review Queue**
  - **Method**: `GET`
  - **Path**: `/review/queue?page=1&limit=10&status=pending`

- **Submit Review Decision**
  - **Method**: `POST`
  - **Path**: `/review/:id/decide`
  - **Payload**:
    ```json
    {
      "decision": "corrected",
      "correctedAddress": "45 West 34th Street, Apartment 2, New York, NY 12308",
      "reviewerId": "reviewer-001",
      "rationale": "Corrected street abbreviation"
    }
    ```

### 3. Active Learning & Audit

- **Model Retraining Status**
  - **Method**: `GET`
  - **Path**: `/ml/status`

- **Manual Model Retrain**
  - **Method**: `POST`
  - **Path**: `/ml/retrain`

- **Audit Trail**
  - **Method**: `GET`
  - **Path**: `/audit?eventType=reviewed&page=1`
