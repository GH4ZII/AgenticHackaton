# Maintenance Agent

Autonomous industrial maintenance demo: simulated machines emit telemetry, simple code detects anomalies, and a Gemini agent (via Google ADK) investigates and decides what to do.

This is **not** a chatbot. The goal is an event-driven flow:

```text
telemetry → anomaly detection → incident → agent investigates → actions
```

## What exists so far

### Phase 1 — AI agent foundation (needs Gemini / GCP)

A Google ADK agent with Gemini 3.5 Flash. You ask it to investigate PUMP-04; it calls tools and returns a maintenance decision.

### Phase 2 — Core domain (no AI)

Python models for machines, telemetry, incidents, work orders, and inventory, plus fake seed data and a **deterministic** anomaly detector (threshold checks, not ML).

If temperature / vibration / motor current exceed limits → create an incident and set machine status to `WARNING`.

### Phase 3 — Agent tools (needs Gemini / GCP)

The agent can independently call several tools against the domain store:

- `get_machine_context`
- `get_telemetry_history`
- `get_maintenance_history`
- `search_machine_manual`
- `check_inventory`
- `create_work_order`
- `update_machine_status`
- `notify_technician`

You still only prompt with something like `Investigate PUMP-04.` — Gemini chooses which tools to use.

### Phase 4 — Firestore persistence (needs GCP)

Domain data can be stored in Cloud Firestore instead of process memory.

Set `USE_FIRESTORE=true` in `backend/.env` so agent tools read/write Firestore. Restarting the backend then keeps machines, incidents, work orders, inventory, and agent actions.

### Phase 5 — Full incident workflow (needs Gemini / GCP)

Abnormal telemetry alone starts the agent — no manual «Investigate PUMP-04.» prompt.

Flow: telemetry → anomaly detector → new incident → ADK agent auto-runs → diagnosis / inventory / work order / notification.

## Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `GOOGLE_CLOUD_PROJECT` to your GCP project ID.

Use location `eu` (or `global`) for `gemini-3.5-flash` — it is not available in `europe-west1`.

Authenticate with Application Default Credentials (needed for Phase 1, 3, and 4):

```powershell
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
```

Enable APIs and create Firestore (once per project):

```powershell
gcloud services enable aiplatform.googleapis.com firestore.googleapis.com --project <PROJECT_ID>
gcloud firestore databases create --database="(default)" --location=eur3 --type=firestore-native --project <PROJECT_ID>
```

Billing must be enabled on the project.

## Run Phase 2 (no AI, in-memory)

From `backend/`:

```powershell
python run_phase2.py
```

Expected: abnormal PUMP-04 telemetry creates an `OPEN` incident and sets machine status to `WARNING`.

## Run Phase 4 (Firestore persistence)

From `backend/`:

```powershell
python run_phase4.py
```

Expected: writes an incident/work order, opens a new Firestore client (simulated restart), and still finds the documents.

To make the agent use Firestore too, set in `.env`:

```text
USE_FIRESTORE=true
```

## Run Phase 5 (auto workflow, no manual prompt)

From `backend/`:

```powershell
python run_phase5.py
```

Expected: an abnormal PUMP-04 sample creates an incident and automatically invokes the agent (work order / notify / status). A second abnormal sample does not re-run the agent (idempotent).

## Run Phase 1 / Phase 3 (AI agent)

From `backend/`:

```powershell
adk run maintenance_agent
```

Or one-shot verification:

```powershell
python run_phase1.py
python run_phase3.py
```

Success prompt:

```text
Investigate PUMP-04.
```

Phase 3 success: the agent calls at least 4 distinct tools (including an action tool such as work order / notify / status) and returns a maintenance decision.

Optional UI:

```powershell
adk web --port 8000
```

## Project layout (backend)

```text
backend/
  maintenance_agent/     # ADK agent + tools
  app/
    models/              # Machine, Telemetry, Incident, WorkOrder, Inventory
    store/               # MemoryStore + FirestoreStore
    services/            # anomaly_detector, agent_runner, incident_workflow, firestore
    seed.py              # Fake PUMP-04 demo data
    runtime.py           # Shared store singleton (memory or Firestore)
  run_phase1.py
  run_phase2.py
  run_phase3.py
  run_phase4.py
  run_phase5.py
```
