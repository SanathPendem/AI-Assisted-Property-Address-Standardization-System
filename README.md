# AI-Assisted Property Address Standardization System
## Comprehensive Technical Documentation
### Human-in-the-Loop Address Deduplication & Continuous Learning Pipeline

- **Project:** AI-Assisted Property Address Standardization
- **Assignment:** Human-in-the-Loop Address Standardization System
- **Stack:** NestJS + Python (FastAPI) + PostgreSQL + LightGBM
- **Date:** June 2026
- **Version:** 1.0.0

---

## 1. Project Overview

The **AI-Assisted Property Address Standardization System** is a production-grade, full-stack pipeline designed to unify disparate property records from multiple source databases. Property data frequently contains addresses in varied formats, with abbreviations, typos, missing components, and inconsistent quality. This system resolves all such variants into a single canonical address representation per unique property.

For example, all three of the following records describe the same property and are resolved to one master record:
- `45 W 34 St Apt 2, NY 12308`
- `45 West 34th Street #2, New York, NY 12308`
- `45 W. Thirty Fourth St Apt 2 12308`

### 1.1 Objectives
- Accept raw property addresses from multiple source systems.
- Generate the most likely standardized (canonical) address using AI/ML.
- Assign a confidence score (0–1) to each prediction.
- Route low-confidence matches for human validation via a review queue.
- Learn continuously from accepted and corrected human feedback (HITL loop).
- Maintain a full audit trail of all predictions, decisions, and retraining events.

### 1.2 Key Goals
- **Match Accuracy:** High precision in resolving address variants to canonical forms.
- **Human-in-the-Loop:** Uncertainty-based routing ensures humans handle ambiguous cases.
- **Continuous Learning:** Model retrains periodically as human feedback accumulates.
- **Scalability:** Docker-composed microservices scale independently.
- **Auditability:** Immutable audit log tracks every system event.

### 1.3 Source Data
The system ingests two real-world property database tables with different schemas and quality levels:

| Table | Columns | Rows | Quality Notes |
|---|---|---|---|
| `address-table1.csv` | county_name, street_nbr, street_name, zip5 | 155,453 | 29% exact duplicates; 5,710 unusable house numbers; 16% missing ZIP; no city/state columns |
| `address-table2.csv` | city, countyOrParish, stateOrProvince, address, shortAddress | 16,105 | 258 exact duplicates; 3 sentinel rows; clean address field used as ground truth |

---

## 2. System Architecture

The system follows a microservices architecture with four containerized services orchestrated via Docker Compose.

### 2.1 High-Level Architecture Diagram

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │                           EXTERNAL CLIENTS                           │
 │               (REST API consumers / human reviewers)                 │
 └─────────────────────────────┬────────────────────────────────────────┘
                               │ HTTP :3000
                               ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                         NestJS BACKEND (:3000)                       │
 │ • Standardization Coordinator       • Review Queue Manager          │
 │ • Confidence Router                 • Audit Trail Logger             │
 │ • Feedback Collector                • Model Registry Manager         │
 └────────┬──────────────────────────────┬──────────────────────────────┘
          │ HTTP :8000                   │ SQL / TypeORM
          ▼                              ▼
 ┌─────────────────────┐ ┌──────────────────────────────────────────┐
 │  Python ML Service  │ │      PostgreSQL + pgvector (:5432)        │
 │       (:8000)       │ │ • canonical_addresses (master records)   │
 │                     │ │ • raw_addresses (ingested inputs)        │
 │  POST /standardize  │ │ • standardization_results                │
 │  POST /retrain      │ │ • review_queue                           │
 │  POST /embed        │ │ • feedback (training data)               │
 │  GET /model/metrics │ │ • audit_trail                            │
 │  ┌───────────────┐  │ │ • model_registry                         │
 │  │   libpostal   │  │ └──────────────────────────────────────────┘
 │  │   LightGBM    │  │                                          
 │  │   Sentence    │  │ ┌──────────────────────────────────────────┐
 │  │  Transformer  │  │ │              Redis (:6379)              │
 │  └───────────────┘  │ │ Background job queue for async tasks     │
 └─────────────────────┘ └──────────────────────────────────────────┘
```

### 2.2 Service Responsibilities

| Service | Technology | Port | Responsibility |
|---|---|---|---|
| **NestJS Backend** | Node.js / NestJS | 3000 | API gateway, business logic, confidence routing, queue management, audit logging |
| **Python ML Service** | Python / FastAPI | 8000 | Address parsing (`libpostal`), feature extraction, LightGBM scoring, embeddings, model retraining |
| **PostgreSQL** | `pgvector/pg15` | 5432 | Persistent storage for all entities; vector similarity search via `pgvector` extension |
| **Redis** | Redis 7 Alpine | 6379 | Background job queues (Bull) for async retraining and notification tasks |

### 2.3 Inter-Service Communication
- **NestJS → ML Service:** Synchronous HTTP POST to `/standardize` for each incoming address.
- **NestJS → ML Service:** HTTP POST to `/retrain` when feedback threshold is reached (50 corrections).
- **NestJS → PostgreSQL:** TypeORM over TCP for all entity persistence and queries.
- **NestJS → Redis:** Bull job queue for async background processing.
- **ML Service → PostgreSQL:** Direct `psycopg2` connection for reading training data during retrain.

---

## 3. Data Flow & Process

### 3.1 Address Standardization Flow

```
 Client POST /addresses/standardize
                 │
                 ▼
 ┌─────────────────────────────────┐
 │        1. NestJS Backend        │
 │  Validate DTO                   │
 │  Log raw_address to DB          │
 └──────────────┬──────────────────┘
                │ POST /standardize
                ▼
 ┌─────────────────────────────────┐
 │      2. ML Service (FastAPI)    │
 │  a) libpostal parse             │
 │  b) Rule-based normalization    │
 │  c) Format canonical string     │
 │  d) Extract 8 features          │
 │  e) LightGBM → confidence       │
 └──────────────┬──────────────────┘
                │ {standardized_address, confidence, features}
                ▼
 ┌─────────────────────────────────┐
 │   3. NestJS Confidence Router   │
 │                                 │
 │  confidence >= 0.80? ──────────► AUTO-ACCEPT
 │                                  Find/Create Canonical
 │                                  Link raw → canonical
 │  0.50 ≤ confidence < 0.80?      │
 │  ──────────────────────────────► PENDING_REVIEW Queue
 │                                  Priority = 1 - |C - 0.65|
 │  confidence < 0.50?             │
 │  ──────────────────────────────► FLAGGED Queue
 │                                  Warning notes
 └──────────────┬──────────────────┘
                │
                ▼
 ┌─────────────────────────────────┐
 │   4. Save Result + Audit Log    │
 │   → standardization_results     │
 │   → audit_trail                 │
 └─────────────────────────────────┘
```

### 3.2 Confidence Routing Matrix

| Confidence Score | Routing Decision | Database Action | Status |
|---|---|---|---|
| $C \ge 0.80$ | `auto_accepted` | Find or create canonical master address; link raw record | Resolved immediately |
| $0.50 \le C < 0.80$ | `pending_review` | Add to review queue with medium priority | Awaiting human review |
| $C < 0.50$ | `flagged` | Add to review queue with warning context notes | Requires manual resolution |

### 3.3 Human-in-the-Loop Review Flow

```
 Reviewer GET /review/queue?status=pending
          │ (sorted by priority_score DESC)
          ▼
 ┌─────────────────────────────────────────┐
 │ Review Item Displayed:                  │
 │ • Raw address text                      │
 │ • Predicted canonical address           │
 │ • Confidence score                      │
 │ • Parsed components (libpostal)         │
 │ • Similar canonical addresses           │
 │ • Context notes                         │
 └──────────────────┬──────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    [ACCEPT]    [CORRECT]   [REJECT]
        │           │           │
        ▼           ▼           ▼
 POST /review/:id/decide {decision, correctedAddress, reviewerId, rationale}
                    │
                    ▼
 ┌─────────────────────────────────────────┐
 │ Save to feedback table                  │
 │ Update review_queue status              │
 │ Log to audit_trail                      │
 │ If CORRECT/REJECT → used_in_training=F  │
 │ Increment unused feedback counter       │
 │ If counter >= 50 → trigger /retrain     │
 └─────────────────────────────────────────┘
```

### 3.4 Model Retraining Flow

```
 Feedback counter reaches 50 (or manual POST /ml/retrain)
                    │
                    ▼
 ┌─────────────────────────────────────────┐
 │ NestJS: collect unused feedback rows    │
 │ Send to ML Service POST /retrain        │
 └──────────────────┬──────────────────────┘
                    │
                    ▼
 ┌─────────────────────────────────────────┐
 │ ML Service retraining.py                │
 │ 1. Load existing training_data.csv      │
 │ 2. Augment with human feedback pairs    │
 │ 3. Parse new samples with libpostal     │
 │ 4. Extract features for all samples     │
 │ 5. Train LGBMClassifier (80/20 split)   │
 │ 6. Evaluate on held-out 20%             │
 │ 7. Save new lgbm_model.pkl              │
 └──────────────────┬──────────────────────┘
                    │
                    ▼
 ┌─────────────────────────────────────────┐
 │ NestJS: register new model version      │
 │ Update model_registry (is_active=TRUE)  │
 │ Mark feedback used_in_training=TRUE     │
 │ Log retrain event to audit_trail        │
 └─────────────────────────────────────────┘
```

---

## 4. Technical Implementation

### 4.1 ML Pipeline: Address Parsing (`libpostal`)
The first stage of ML processing uses `libpostal`, an open-source C library trained on OpenStreetMap data, to parse raw address strings into structured components. The `parser.py` module wraps `libpostal` with a pure-Python regex fallback.

| `libpostal` Tag | Meaning | Example Input | Example Output |
|---|---|---|---|
| `house_number` | Street number | 45 W 34 St | 45 |
| `road` | Street name + suffix | 45 W 34 St | W 34 St |
| `unit` | Apartment/suite number | Apt 2 | 2 |
| `suburb` / `city_district` | Neighborhood | Brooklyn, NY | Brooklyn |
| `city` | City name | New York, NY | New York |
| `state` | State abbreviation | NY 12308 | NY |
| `postcode` | ZIP code | NY 12308 | 12308 |

### 4.2 Rule-Based Standardization (`standardizer.py`)
After parsing, the `standardizer.py` module applies a multi-stage rule pipeline to normalize each component into a canonical form:
1. **Directional Expansion:** W → West, NE → Northeast, SW → Southwest (8 directions)
2. **Street Suffix Expansion:** St → Street, Ave → Avenue, Blvd → Boulevard (12 suffix types)
3. **Unit Type Normalization:** Apt → Apartment, Ste → Suite, # → Unit
4. **State Normalization:** NY → New York (supports both 2-letter code and full name input)
5. **Ordinal Normalization:** 34 → 34th, Thirty Fourth → 34th (handles numeric and written forms)
6. **Component Assembly:** formatted into `{number} {dir} {name} {suffix}, {unit}, {city}, {state} {zip}`

Final output canonical string:
```text
45 West 34th Street, Apartment 2, New York, NY 12308
```

### 4.3 Feature Engineering (`features.py`)
Eight numerical features are extracted to compare the raw address against the standardized output for the LightGBM classifier:

| Feature Name | Description | Range | Rationale |
|---|---|---|---|
| `jaccard_similarity` | Token-level Jaccard similarity between raw and standardized | 0.0 – 1.0 | Measures word-level overlap; high similarity = likely correct standardization |
| `edit_distance_ratio` | Character-level edit distance ratio (`difflib SequenceMatcher`) | 0.0 – 1.0 | Detects character-level transformations; abbreviation expansion yields medium scores |
| `length_diff_ratio` | Absolute length difference / max length | 0.0 – 1.0 | Large expansion (abbrev→full) indicates normalization happened; near 0 = minimal change |
| `has_zip` | 1.0 if ZIP code was successfully parsed, else 0.0 | 0.0 or 1.0 | Presence of ZIP significantly improves match certainty |
| `has_house_num` | 1.0 if house number was parsed, else 0.0 | 0.0 or 1.0 | Missing house number indicates rural/lot-style addressing or parse failure |
| `zip_in_raw` | 1.0 if parsed ZIP appears verbatim in raw input, else 0.0 | 0.0 or 1.0 | Confirms ZIP was provided (not imputed); increases confidence |
| `directional_expanded` | 1.0 if directional was expanded (W→West) during normalization | 0.0 or 1.0 | Signals abbreviation was resolved; expected in well-formed addresses |
| `suffix_expanded` | 1.0 if street suffix was expanded (St→Street) during normalization | 0.0 or 1.0 | Common transformation; combined with others indicates routine standardization |

### 4.4 LightGBM Confidence Classifier (`model.py`)
A gradient-boosted decision tree model (`LGBMClassifier`) is trained to predict the probability that a standardization is correct.

- **Algorithm:** `LGBMClassifier` (gradient boosting, leaf-wise tree growth)
- **Hyperparameters:** `n_estimators=100`, `learning_rate=0.05`, `max_depth=5`, `random_state=42`
- **Input:** 8 numeric features (`FEATURE_ORDER` vector)
- **Output:** $P(\text{correct}) \in [0, 1]$ — used as confidence score $C$
- **Fallback:** Weighted heuristic (`0.5*edit_dist + 0.3*jaccard + 0.1*zip + 0.1*house_num`)
- **Training Split:** 80% train / 20% internal validation

### 4.5 Address Embeddings (`embeddings.py`)
Each canonical address is encoded into a dense vector representation using `sentence-transformers` (`all-MiniLM-L6-v2`). Embeddings are stored in PostgreSQL using the `pgvector` extension, enabling cosine similarity searches to assist reviewers.

---

## 5. Database Design (ER Diagram)

### 5.1 Entity Relationship Overview

```
 ┌──────────────────────┐        ┌──────────────────────────┐
 │  canonical_addresses │◄───────┤       raw_addresses      │
 │──────────────────────│  0..*  │──────────────────────────│
 │ id (PK, UUID)        │        │ id (PK, UUID)            │
 │ house_number         │        │ raw_text                 │
 │ pre_directional      │        │ source_system            │
 │ street_name          │        │ source_record_id         │
 │ street_suffix        │        │ parsed_components (JSONB)│
 │ post_directional     │        │ canonical_id (FK)        │
 │ unit_type            │        └──────────┬───────────────┘
 │ unit_number          │                   │
 │ city, state, zip     │                   │ 1
 │ full_address         │                   │
 │ normalized_key (UQ)  │        ┌──────────▼───────────────┐
 │ source_count         │        │ standardization_results  │
 │ embedding (vector)   │        │──────────────────────────│
 └──────────────────────┘        │ id (PK, UUID)            │
                                 │ raw_address_id (FK)      │
                                 │ canonical_id (FK)        │
                                 │ predicted_address        │
                                 │ confidence_score         │
                                 │ routing_decision (ENUM)  │
                                 │ feature_vector (JSONB)   │
                                 │ model_version            │
                                 │ processing_time_ms       │
                                 └──────────┬───────────────┘
                                            │ 1
        ┌───────────────────────────────────┼──────────────────┐
        │                                   │                  │
 ┌──────▼──────────────┐             ┌──────▼──────────┐ ┌─────▼────────────┐
 │    review_queue     │             │     feedback    │ │    audit_trail    │
 │─────────────────────│             │─────────────────│ │──────────────────│
 │ id (PK)             │             │ id (PK)         │ │ id (PK)          │
 │ standardization_id  │             │ review_queue_id │ │ event_type       │
 │ raw_address_text    │             │ raw_address_text│ │ raw_address_text │
 │ predicted_address   │             │ original_pred.  │ │ predicted_address│
 │ confidence_score    │             │ human_decision  │ │ final_address    │
 │ routing_decision    │             │ corrected_addr  │ │ routing_decision │
 │ priority_score      │             │ reviewer_id     │ │ human_decision   │
 │ review_status (ENUM)│             │ used_in_training│ │ model_version    │
 │ reviewer_id         │             │ training_batch  │ │ metadata (JSONB) │
 └─────────────────────┘             └─────────────────┘ └──────────────────┘

 ┌─────────────────────────────┐
 │       model_registry        │
 │─────────────────────────────│
 │ id, version (UQ)            │
 │ artifact_path               │
 │ training_samples            │
 │ accuracy / precision / F1   │
 │ is_active (BOOL)            │
 └─────────────────────────────┘
```

### 5.2 Key Design Decisions
- `normalized_key`: A pipe-delimited composite key (`house|dir|name|suffix|unit|city|state|zip`) enables O(1) deduplication lookup.
- **JSONB columns:** `parsed_components` and `feature_vector` stored as JSONB for flexible schema evolution.
- **`pgvector` extension:** Enables cosine similarity search over canonical address embeddings.
- **Routing ENUM:** `routing_decision` is a PostgreSQL ENUM ensuring database-level integrity.
- **`priority_score` index:** Partial index on `review_queue` (`WHERE review_status='pending'`) for fast queue retrieval.
- **Audit trail immutability:** Append-only design with no `UPDATE` operations on `audit_trail`.

---

## 6. Backend Architecture (NestJS)

### 6.1 Module Structure
```
AppModule
 ├── AddressesModule (POST /standardize, GET /addresses)
 ├── ReviewModule (GET /review/queue, POST /review/:id/decide)
 ├── FeedbackModule (GET /feedback)
 ├── MlModule (GET /ml/status, POST /ml/retrain)
 ├── AuditModule (GET /audit)
 ├── HealthModule (GET /health)
 └── DatabaseModule (TypeORM Entities)
```

### 6.2 REST API Reference

| Method | Endpoint | Module | Description |
|---|---|---|---|
| `POST` | `/addresses/standardize` | Addresses | Standardize a raw address; triggers ML pipeline & confidence routing |
| `GET` | `/addresses` | Addresses | List all standardization results with pagination |
| `GET` | `/addresses/:id` | Addresses | Get a specific standardization result by ID |
| `GET` | `/review/queue` | Review | Get pending review items sorted by priority (uncertainty sampling) |
| `POST` | `/review/:id/decide` | Review | Submit human decision (accepted/corrected/rejected) for a queue item |
| `GET` | `/feedback` | Feedback | List all human feedback records |
| `GET` | `/ml/status` | ML | Get active model version and current metrics |
| `POST` | `/ml/retrain` | ML | Manually trigger model retraining |
| `GET` | `/audit` | Audit | Query immutable audit trail with filters |
| `GET` | `/health` | Health | Health check for all services |

### 6.3 Active Learning Priority Scoring
The review queue implements uncertainty sampling:
$$\text{priority\_score} = 1.0 - |\text{confidence} - 0.65|$$

Assigns maximum priority (1.0) to items with confidence near $0.65$ (the center of the review range).

---

## 7. Technical Stack

| Layer | Component | Technologies |
|---|---|---|
| **Backend** | NestJS Coordinator | NestJS, TypeScript, TypeORM, Axios, Bull Queue |
| **ML Service** | FastAPI ML Service | Python 3.10+, FastAPI, `libpostal`, LightGBM, `sentence-transformers`, `pandas` |
| **Database** | PostgreSQL + pgvector | PostgreSQL 15, `pgvector`, Redis 7 Alpine |
| **Infrastructure** | Containerization | Docker, Docker Compose |

---

## 8. Deployment & Quick Start

### 8.1 Launching the Stack
```bash
docker-compose up --build -d
```

### 8.2 Service Port Mapping
- **Web Dashboard & Backend API:** `http://localhost:3000`
- **Swagger Documentation:** `http://localhost:3000/api/docs`
- **Python ML Service:** `http://localhost:8000`
- **PostgreSQL Database:** `localhost:5432`
- **Redis:** `localhost:6379`
