# ContentIQ Full-Stack Integration, Verification & Testing Guide

## 1. System Architecture & Page-to-Endpoint Mapping

ContentIQ is organized into a modular FastAPI backend serving REST endpoints at `/api/v1/` and a React + Vite single-page frontend. All page actions interact with verified API endpoints with JWT authentication and Role-Based Access Control (RBAC).

| Frontend Page / Component | User Action | Backend Endpoint | HTTP Method | RBAC Roles | Description |
|---|---|---|---|---|---|
| **Text Analysis** (`TextAnalysis.jsx`) | Submit essay / code snippet | `/api/v1/analysis/text` | `POST` | Any Authenticated | Multi-dimensional linguistic analysis, sentence heatmaps, reading metrics |
| **Media Analysis** (`MediaAnalysis.jsx`) | Upload image/video file | `/api/v1/media/upload` | `POST` | Any Authenticated | Magic-byte validation, size limits (20MB/100MB), async storage |
| **Media Analysis** (`MediaAnalysis.jsx`) | Submit for deepfake analysis | `/api/v1/media/submit` | `POST` | Reviewer, Admin | Celery async worker queue ingestion with detector selection |
| **Media Analysis** (`MediaAnalysis.jsx`) | Poll job status & findings | `/api/v1/media/jobs/{id}` | `GET` | Reviewer, Admin | Frame-level anomalies, bounding boxes, spectrogram deviations |
| **Media Analysis** (`MediaAnalysis.jsx`) | Run instant preview | `/api/v1/analysis/media` | `POST` | Reviewer, Admin | Synchronous heuristic deepfake indicator check |
| **FP/FN Simulator** (`FPFNSimulator.jsx`) | Adjust decision threshold slider | `/api/v1/analysis/simulator` | `POST` | Any Authenticated | Confusion matrix, precision/recall, and false positive trade-offs |
| **Rubric Engine** (`Shortlisting.jsx`) | Create or edit rubric | `/api/v1/rubrics` | `POST` / `PUT` | Reviewer, Admin | Weight validation (must sum to 1.0), versioning, scales |
| **Rubric Engine** (`Shortlisting.jsx`) | Validate draft rubric | `/api/v1/rubrics/validate` | `POST` | Reviewer, Admin | Dry-run validation of criteria weights and scales |
| **Shortlisting** (`Shortlisting.jsx`) | Evaluate batch submissions | `/api/v1/shortlisting/batch-evaluate` | `POST` | Reviewer, Admin | Per-criterion scoring, evidence excerpts, weighted ranking |
| **Shortlisting** (`Shortlisting.jsx`) | Fetch shortlist ranking | `/api/v1/shortlisting/results` | `GET` | Reviewer, Admin | Ranked submissions with tie handling and decision status |
| **Audit & Review** (`AuditTrail.jsx`) | Apply reviewer override | `/api/v1/audit/reviews/override` | `POST` | Reviewer, Admin | Override decision with mandatory rationale; appends to ledger |
| **Audit & Review** (`AuditTrail.jsx`) | Query audit trail events | `/api/v1/audit/events` | `GET` | Reviewer, Admin | Append-only SHA-256 tamper-evident log |
| **Batch Processing** (`BatchProcessing.jsx`) | Create submission batch | `/api/v1/batches` | `POST` | Reviewer, Admin | Group submission ingest from upload, LMS, or form |
| **Batch Processing** (`BatchProcessing.jsx`) | Run async batch jobs | `/api/v1/batches/{id}/run` | `POST` | Reviewer, Admin | Orchestrates asynchronous analysis of all batch items |
| **Batch Processing** (`BatchProcessing.jsx`) | View cohort report | `/api/v1/batches/{id}/report` | `GET` | Reviewer, Admin | Population statistics with privacy suppression (<5 items) |
| **Batch Processing** (`BatchProcessing.jsx`) | Export cohort data | `/api/v1/batches/{id}/export` | `GET` | Reviewer, Admin | CSV/JSON export with formula injection sanitization |
| **Integrations** | Register external platform | `/api/v1/integrations` | `POST` | Reviewer, Admin | Google Forms, Typeform, Canvas LMS, Moodle, Blackboard, Mock |
| **Integrations** | Test platform connection | `/api/v1/integrations/{id}/test` | `POST` | Reviewer, Admin | Health check through official APIs; secrets never leaked |
| **Webhooks** | Register webhook endpoint | `/api/v1/webhooks/endpoints` | `POST` | Reviewer, Admin | HMAC-SHA256 signed delivery endpoint registration |
| **Webhooks** | Deliver test ping | `/api/v1/webhooks/endpoints/{id}/test` | `POST` | Reviewer, Admin | Generates signed ping with timestamp and signature |
| **Webhooks** | Verify signature header | `/api/v1/webhooks/verify` | `POST` | Reviewer, Admin | Client verification tool with replay attack tolerance |

---

## 2. Distinction of Working Features vs. External Integrations

ContentIQ is architected with clear boundaries between **fully working offline/heuristic features** and **external API/model dependencies**:

### Truly Working Out-of-the-Box (No External Keys or Model Downloads Required)
1. **Linguistic Heuristic Engine (`/api/v1/analysis/text`)**:
   - Perplexity indicators, vocabulary diversity, burstiness, syntax patterns, and sentence-level heatmaps.
2. **Deterministic FP/FN Simulator (`/api/v1/analysis/simulator`)**:
   - Mathematical model calculating exact True/False Positives and Negatives across threshold sweeps.
3. **Rubric Authoring & Scoring Engine (`/api/v1/rubrics`, `/api/v1/shortlisting`)**:
   - Criterion weight validation, scale mapping, benchmark matching, heuristic scoring, and weighted shortlisting.
4. **Append-Only Tamper-Evident Audit Ledger (`/api/v1/audit`)**:
   - SHA-256 state chaining, cryptographic lineage hashes, reviewer decision recording, and override audit trails.
5. **Batch Orchestration & Privacy-Preserving Cohort Reporting (`/api/v1/batches`)**:
   - Asynchronous batch execution, small-group privacy suppression (< 5 items), score histograms, and formula-injection-sanitized CSV/JSON exports.
6. **Integration Adapter Layer & Mock Client (`/api/v1/integrations`)**:
   - Fernet AES-128 secret encryption, adapter interface validation, and deterministic mock platform tests.
7. **HMAC-SHA256 Signed Webhooks Engine (`/api/v1/webhooks`)**:
   - Secret generation, HMAC payload signing, timestamp verification, and replay attack prevention.

### Features Requiring External API Keys or Heavy Model Downloads
1. **Commercial Media AI Detectors (Sightengine / Deepware)**:
   - Configured via `SIGHTENGINE_API_USER` and `SIGHTENGINE_API_SECRET`.
   - When not configured, the system marks the adapter as `not_configured` or returns `inconclusive`. It **never fabricates fake scores**.
2. **LLM-Based Rubric Evaluator (OpenAI GPT-4o)**:
   - Configured via `OPENAI_API_KEY`.
   - When unavailable or not configured, falls back to the deterministic heuristic evaluator without fabricating LLM certainty.
3. **Cloud S3 Object Storage**:
   - Configured via `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `S3_BUCKET_NAME`.
   - Local storage fallback (`uploads/` directory) is used by default.

---

## 3. Security & Safety Principles

1. **Decoupled Indicators**:
   - Text AI indicators, media anomalies, similarity matches, and rubric compliance scores are maintained in separate fields. They are **never collapsed into a single automated verdict**.
2. **Human-in-the-Loop Override**:
   - AI outputs are strictly decision-support cues. Reviewers can override any decision, provided they enter a substantive reason (minimum 5 characters) that is permanently recorded in the audit trail.
3. **No Secret Leakage**:
   - Credentials (API keys, OAuth tokens) stored in the database are encrypted at rest with Fernet and **never returned in API responses**.
4. **Spreadsheet Formula Injection Protection**:
   - In CSV exports, any cell value beginning with `=`, `+`, `-`, or `@` is prepended with a single quote (`'`) to prevent formula execution in Microsoft Excel or Google Sheets.

---

## 4. Frontend Testing Steps

To test the application with full backend connectivity:

### Step 1: Start the Backend Service
In a terminal:
```powershell
cd Backend
C:\Python314\python.exe -m uvicorn app.main:app --reload --port 8000
```
Verify the backend is healthy:
- Open `http://localhost:8000/api/v1/health` in your browser. It should return `{"status": "healthy"}`.
- Interactive API Docs are available at `http://localhost:8000/docs`.

### Step 2: Start the Frontend Application
In a second terminal:
```powershell
npm run dev
```
Open `http://localhost:5173` in your browser.

### Step 3: Test Interactive Features
1. **Text Analysis**:
   - Navigate to the **Text Analysis** tab.
   - Enter or paste a technical essay or proposal.
   - Click **Run Multi-Signal Analysis**.
   - Observe the sentence heatmaps (green/amber/red spans), dimension breakdown bars, and decision-support caveat.
2. **Media Analysis**:
   - Navigate to the **Media Analysis** tab.
   - Drag and drop a PNG, JPG, or MP4 file.
   - Verify file upload and review the detected anomalies (e.g. Face Boundary gradient, A/V sync offset).
3. **FP/FN Simulator**:
   - Navigate to the **FP/FN Simulator** tab.
   - Drag the threshold slider between `0.1` and `0.9`.
   - Watch the confusion matrix and false positive/negative rates dynamically recompute from the backend.
4. **Shortlisting & Rubrics**:
   - Navigate to the **Shortlisting** tab.
   - Create or preview a rubric with custom criteria and weights.
   - Test evaluating candidate submissions and view the ranked shortlist.
5. **Audit Trail**:
   - Navigate to the **Audit Trail** tab.
   - View the immutable ledger of previous analysis events, review decisions, and tamper-evident SHA-256 hashes.
   - Submit an override with a custom rationale and observe the new record appended to the ledger.
6. **Batch Processing**:
   - Navigate to the **Batch Processing** tab.
   - Create a new batch, attach items, and click **Export Report (CSV)**.
   - Open the downloaded CSV to verify proper formatting and formula-sanitized values.

---

## 5. Running with Docker Compose

To run the entire platform (PostgreSQL, Redis, FastAPI Backend, Celery Worker, and Frontend) in Docker:

```bash
docker-compose up --build
```

The application will be accessible at:
- **Frontend**: `http://localhost:5173` or `http://localhost`
- **Backend API & Docs**: `http://localhost:8000/docs`
- **Postgres Database**: `localhost:5432`
- **Redis Service**: `localhost:6379`
