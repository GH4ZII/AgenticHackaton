# Maintenance Agent — Phase 1

Local Google ADK agent using Gemini 3.5 Flash on Vertex AI.

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

Authenticate with Application Default Credentials:

```powershell
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
```

Enable the Vertex AI API and billing on the project.

## Run

From `backend/`:

```powershell
adk run maintenance_agent
```

Or one-shot verification:

```powershell
python run_phase1.py
```

Success prompt:

```text
Investigate PUMP-04.
```

The agent should call the fake tools and return a maintenance decision.

Optional UI:

```powershell
adk web --port 8000
```
