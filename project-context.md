# Project Context: AI Visa Consulting Flow

## Tech Stack
- **Backend**: Python 3.14, FastAPI, SQLAlchemy, SQLite (`visa_flow.db`), python-multipart
- **Frontend**: React 18 + Vite, vanilla CSS (no component library), `Be Vietnam Pro` font
- **AI**: Anthropic SDK 0.86.0 — `claude-haiku-4-5-20251001` (fast), `claude-sonnet-4-6` (review)
- **Storage**: Local `uploads/{app_id}/` dir (Railway volume in prod)

## Architecture

### Backend (`/api`)
- `api/main.py` — FastAPI app, CORS, router mount at `/api`
- `api/routers/application.py` — all REST endpoints
- `api/routers/feedback.py` — `POST /api/feedback`, idempotent by `client_id`
- `api/ai.py` — Claude API helpers (eligibility, checklist, review)
- `db/models.py` — Application + Document + Feedback SQLAlchemy models
- `db/session.py` — engine + get_db dependency; safe-migration `ALTER TABLE` list for new columns on existing tables
- `core/config.py` — ANTHROPIC_API_KEY, SONNET, HAIKU constants

### Frontend (`/visa-client/src`)
- `App.jsx` — Router: switch/case on `screen` state (no React Router)
- `context/AppContext.jsx` — global state: applicationId, sessionId, screen, profile, checklist
- `screens/` — one file per screen
- `components/` — shared UI (NavHeader, ProgressBar, CTAButton, StatusChip, etc.)
- `components/ChatWidget.jsx` — persistent AI chat FAB, bottom-right; hides on `screen === 'price'`
- `components/FeedbackWidget.jsx` — persistent user-feedback FAB, bottom-left (🚩); always renders on every screen (no hide logic), separate from ChatWidget on purpose (see Key Conventions)

### Ops tooling (`/tools`)
- `tools/feedback_triage.py` — CLI for the review-to-fix workflow: `list-pending` (untriaged `Feedback` rows) → dev/Claude Code investigates manually → `assign-batch` (records root cause/confidence/proposed fix/impact for a group of ids, writes to `_bmad-output/implementation-artifacts/feedback-triage.md`) → `set-status` (approve/dismiss) → `generate-spec` (approved batch → plain `intent-<slug>.md` brief, no frontmatter, meant to be ingested as fresh raw intent by `bmad-quick-dev`, not resumed as a draft)

## Key Conventions
- No login — `session_id` UUID in localStorage, passed with every API call
- `applicationId` initialized synchronously from localStorage (`useState(() => localStorage.getItem(...))`)
- ProgressBar shows "Bước N/10" (steps 1-6 = profile questions, 7 = eligibility, 8 = price, 9 = checklist)
- All AI text in Vietnamese; never mention specific balance/income thresholds
- Models: Haiku for eligibility + checklist; Sonnet for document vision review
- Checklist is deterministic (loaded from `static/checklists/{destination}.json` per employment_type), NOT a Haiku call
- Checklist items support `optional: true` field — shown as "Không bắt buộc" badge in UI
- ChecklistScreen: users can skip non-passport items via "Tôi chưa có"; skipped required items trigger confirm dialog on submit
- Itinerary item shown in checklist as "Tự động tạo" (not uploadable — auto-generated at form download)
- File uploads: multipart POST, saved to `uploads/{app_id}/`. Upload endpoint rejects non-image/non-PDF (HTTP 400). Images and PDFs sent to Sonnet for review (PDFs converted page-1→PNG via PyMuPDF before review).
- BottomSheet requires `open={true}` prop — conditionally render + pass open flag together
- `navigate(screenName)` via AppContext — no URL changes
- Feedback capture: `FeedbackWidget` is deliberately its own component/route, not folded into `ChatWidget`/`/chat` — avoids the AI bot misinterpreting a complaint as a question, avoids ChatWidget's `price`-screen hide bug, avoids coupling feedback delivery to the AI backend. Every submit carries a client-generated `client_id` (idempotency key); backend returns the existing row on retry instead of erroring. Optimistic ack shown only once the local queue write (or the network call) actually succeeds — not unconditionally. Failed sends queue in `localStorage['visa_feedback_queue']` (capped, oldest dropped first) and flush on next mount/submit; 4xx responses are dropped (not retried forever), only network/5xx are requeued.
- Review-to-fix triage (`tools/feedback_triage.py`) never auto-diagnoses — a human (or Claude Code) always investigates first; the tool only records state. `generate-spec`'s output is intentionally NOT a `spec-template.md`-shaped draft (a placeholder-filled draft would get silently preserved verbatim by `bmad-quick-dev`'s draft-resume path) — it's a plain intent brief so `bmad-quick-dev` does real planning from scratch.

## Running Locally
```bash
# Backend (from /visa-flow)
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (from /visa-flow/visa-client)
npm run dev -- --port 5173
```

## DB Schema
```
Application: id, session_id, destination, profile_json, eligibility_result,
             eligibility_data, travel_dates, feasibility_ok, payment_status,
             checklist_json, submission_status, submitted_at, created_at
Document: id, application_id, doc_type, file_path, review_status, review_notes, created_at
Feedback: id, application_id (nullable), session_id, screen, message, client_id (unique,
          idempotency key), triage_batch (nullable), triage_status (nullable —
          pending|approved|dismissed), created_at
```

## API Endpoints
```
POST /api/application/start
PATCH /api/application/{id}/destination
PUT   /api/application/{id}/profile
POST  /api/application/{id}/eligibility       → Haiku
POST  /api/application/{id}/payment/demo
POST  /api/application/{id}/checklist         → deterministic
POST  /api/application/{id}/documents         → multipart upload
GET   /api/application/{id}/documents
POST  /api/application/{id}/documents/{doc_id}/review  → Sonnet (images + PDFs via PyMuPDF page-1 render)
POST  /api/application/{id}/submit
GET   /api/application/{id}/status
POST  /api/feedback                           → idempotent by client_id (200 existing / 201 new)
```
