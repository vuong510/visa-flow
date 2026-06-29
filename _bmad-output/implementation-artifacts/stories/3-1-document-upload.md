---
status: done
baseline_commit: NO_VCS
---

# Story 3.1 — Document Upload

## Story
**As a** user,
**I want** to upload my documents,
**so that** they can be reviewed for completeness and validity.

## Acceptance Criteria
- [x] `POST /api/application/{id}/documents` accepts multipart/form-data with `file` + `doc_type`
- [x] File saved to `uploads/{app_id}/{timestamp}_{original_filename}`
- [x] Document record created in DB with `review_status="pending"`
- [x] `GET /api/application/{id}/documents` returns list of docs with status
- [x] Frontend shows "uploading" StatusChip during upload
- [x] Upload button changes to "Tải lại" after successful upload
- [x] File input accepts images and PDFs

## Tasks/Subtasks
- [x] Add upload + list endpoints in `api/routers/application.py`
- [x] Create `uploads/` directory creation logic (mkdir parents)
- [x] Write `_guess_media_type()` helper for file extension → MIME
- [x] Wire FormData upload in ChecklistScreen `handleFileSelected()`
- [x] Auto-trigger review after upload completes
- [x] Update docs state map `{docType: {id, status, notes}}`

## Dev Notes
- UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
- Filename: `{int(time.time())}_{secure_filename}`
- IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
- Non-image files skip Sonnet review, get status="pass" automatically
- docs state map keyed by doc_type for O(1) lookup in render

## Dev Agent Record

### Completion Notes
Upload and listing endpoints working. Files persisted to disk correctly.

## File List
- `api/routers/application.py` (upload + list endpoints)
- `visa-client/src/screens/ChecklistScreen.jsx` (handleFileSelected, docs state)

## Change Log
- 2026-06-29: Story completed

## Status
Done
