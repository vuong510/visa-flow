---
status: done
baseline_commit: NO_VCS
---

# Story 1.1 — Backend Skeleton

## Story
**As a** developer,
**I want** a FastAPI backend with SQLite and session management,
**so that** all subsequent stories have a stable foundation to build on.

## Acceptance Criteria
- [x] FastAPI app runs on port 8000 with CORS enabled for localhost:5173
- [x] SQLite DB created via SQLAlchemy with Application and Document tables
- [x] `POST /api/application/start` creates Application record, returns `{application_id, session_id}`
- [x] `PATCH /api/application/{id}/destination` updates destination field
- [x] `PUT /api/application/{id}/profile` stores profile_json
- [x] `ANTHROPIC_API_KEY` loaded from env via `core/config.py`
- [x] Virtual environment with all dependencies installed

## Tasks/Subtasks
- [x] Create project directory structure: `api/`, `db/`, `core/`, `uploads/`
- [x] Write `db/models.py` with Application + Document SQLAlchemy models
- [x] Write `db/session.py` with engine, SessionLocal, get_db dependency
- [x] Write `core/config.py` loading ANTHROPIC_API_KEY, HAIKU, SONNET constants
- [x] Write `api/main.py` with FastAPI app, CORS, router mount
- [x] Write `api/routers/application.py` with start, destination, profile endpoints
- [x] Create `requirements.txt` and install into venv
- [x] Verify server starts and endpoints respond correctly

## Dev Notes
- Uses `python-multipart` for future file upload support
- `session_id` is UUID4 generated server-side on `POST /start`
- DB file: `visa_flow.db` at project root
- Venv path: `/Users/vuongnguyen/Desktop/visa-flow/venv`
- Profile stored as JSON column; no validation — raw dict from frontend

## Dev Agent Record

### Completion Notes
Backend skeleton implemented and verified working. All three initial endpoints operational.

## File List
- `api/main.py`
- `api/routers/application.py`
- `db/models.py`
- `db/session.py`
- `core/config.py`
- `requirements.txt`
- `.env` (ANTHROPIC_API_KEY)

## Change Log
- 2026-06-29: Story completed

## Status
Done
