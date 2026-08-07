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

The agent can independently call several tools against the in-memory store:

- `get_machine_context`
- `get_telemetry_history`
- `get_maintenance_history`
- `search_machine_manual`
- `check_inventory`
- `create_work_order`
- `update_machine_status`
- `notify_technician`

You still only prompt with something like `Investigate PUMP-04.` — Gemini chooses which tools to use.

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

Authenticate with Application Default Credentials (needed for Phase 1 and Phase 3):

```powershell
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
```

Enable the Vertex AI API and billing on the project.

## Run Phase 2 (no AI)

From `backend/`:

```powershell
python run_phase2.py
```

Expected: abnormal PUMP-04 telemetry creates an `OPEN` incident and sets machine status to `WARNING`.

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
    store/               # In-memory store (Firestore later)
    services/            # anomaly_detector.py
    seed.py              # Fake PUMP-04 demo data
    runtime.py           # Shared store singleton for tools
  run_phase1.py
  run_phase2.py
  run_phase3.py
```
