# Hackathon submission — Maintenance Agent

Paste-ready text for the All Things Agentic Hackathon form. Demo video is recorded separately.

---

## Category

**Taskmaster**

---

## Project description

### Problem being solved

Industrial plants generate continuous machine telemetry, but maintenance teams still spend most of their time manually investigating alerts, checking history and manuals, prioritizing severity, creating work orders, and coordinating technicians. Alerts create noise; the real work—investigation and action—stays human and slow. When a bearing starts to degrade, minutes of delay can turn a planned repair into unplanned downtime.

### Target users

Maintenance supervisors and plant operations teams who need abnormal machine events turned into investigated, actionable maintenance work with minimal hand-holding. The demo is built for judges to follow one complete incident end to end.

### Features

- Event-driven autonomy: abnormal telemetry alone starts the agent (no chatbot prompt required)
- Multi-step investigation with real tool calls (machine context, telemetry trends, maintenance history, manuals, inventory)
- Real actions: create work orders, notify technicians, update machine status, log every step
- React operations dashboard: fleet health, incident detail, agent activity timeline, telemetry charts
- Closed loop: after repair, agent verifies healthy telemetry and resolves the incident
- Human-in-the-loop safety: CRITICAL shutdown recommendations require explicit Approve / Reject
- Google Cloud production path: Cloud Run, Firestore, Pub/Sub push, Vertex AI (Gemini)

### Autonomous workflow

```text
telemetry → anomaly detection → incident → ADK agent investigates
  → diagnose + severity → check inventory → create work order
  → notify technician → update machine status
  → (after repair) verify telemetry → resolve incident
```

Primary demo scenario: **PUMP-04** drive-end bearing degradation. The simulator ramps vibration, temperature, and motor current; the detector opens an incident; the agent runs without a manual “Investigate …” prompt; the dashboard shows the live timeline of tool calls and outcomes.

### Technologies

| Layer | Choice |
|-------|--------|
| Model | Gemini 3.5 Flash (`gemini-3.5-flash`) via Vertex AI |
| Agent framework | Google Agent Development Kit (ADK) |
| Backend | FastAPI on Google Cloud Run |
| Persistence | Cloud Firestore |
| Events | Google Pub/Sub (push to Cloud Run) + `POST /events/telemetry` |
| Frontend | React (Vite), served from the same Cloud Run service |
| CI/CD | GitHub Actions → Cloud Run (Workload Identity Federation) |

### External data sources

- **Simulated industrial fleet telemetry** (temperature, vibration, motor current) for machines such as PUMP-04, CNC-02, FAN-01, CONV-03
- **Seeded domain data:** machine metadata, maintenance history snippets, spare-parts inventory, and searchable manual excerpts

Integrations are simulated for the hackathon, but the agent and workflows genuinely execute: tools write work orders, notifications, status changes, and approvals into the store that the dashboard reads.

### Findings / learnings

- Framing the product as an **event-driven agent** (not a chat UI) makes autonomy and judging criteria clearer: tools and state changes are the deliverable.
- **Google ADK** kept Gemini tool-calling and instructions in one place; the backend only triggers the agent and persists results.
- **Human approval for shutdown** is a strong demo of responsible autonomy without blocking the main HIGH-severity work-order path.
- **Firestore** made demos reproducible across restarts; a single **Cloud Run** service for API + static dashboard kept deploy and GCP proof simple.
- Visible **agent activity timeline** in the UI matters as much as the model: judges need to see decisions and actions, not only a final paragraph.

### Value (one line)

The agent understands the goal, investigates across systems, decides severity, takes maintenance actions, and closes the loop—so operators spend less time on repetitive incident triage.

---

## Repository & reproducibility

- Setup, env vars, local run, and Cloud Run deploy: see root [README.md](../README.md)
- Architecture diagram: [architecture.md](architecture.md)

**Live service (GCP proof):**

https://maintenance-agent-786907268086.europe-west1.run.app

For the demo video, also show Google Cloud Console: Cloud Run service `maintenance-agent`, Firestore data, Pub/Sub topic/subscription, and Cloud Logging / Vertex usage as available.
