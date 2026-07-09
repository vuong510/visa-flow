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
- `api/ai.py` — Claude API helpers (eligibility, checklist, review)
- `db/models.py` — Application + Document SQLAlchemy models
- `db/session.py` — engine + get_db dependency
- `core/config.py` — ANTHROPIC_API_KEY, SONNET, HAIKU constants

### Frontend (`/visa-client/src`)
- `App.jsx` — Router: switch/case on `screen` state (no React Router)
- `context/AppContext.jsx` — global state: applicationId, sessionId, screen, profile, checklist
- `screens/` — one file per screen
- `components/` — shared UI (NavHeader, ProgressBar, CTAButton, StatusChip, etc.)

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
```
