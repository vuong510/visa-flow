---
status: done
baseline_commit: NO_VCS
---

# Story 2.1 — Checklist Generation

## Story
**As a** user,
**I want** to receive a personalized document checklist,
**so that** I know exactly what documents to prepare for my visa application.

## Acceptance Criteria
- [x] `POST /api/application/{id}/checklist` returns checklist items
- [x] Checklist is deterministic per employment_type (no Haiku call)
- [x] Cached in `checklist_json` DB column — second call returns same data
- [x] ChecklistScreen shows Bước 9/10
- [x] Skeleton loading list shown while fetching
- [x] ReadinessBanner "Đã tải lên N/M tài liệu" visible
- [x] Freelancer gets `confidence_note` warning shown in banner area
- [x] Checklist items: id, name, description, format, why

## Tasks/Subtasks
- [x] Write `generate_checklist()` in `api/ai.py` with hardcoded items per employment_type
- [x] Add checklist endpoint in `api/routers/application.py`
- [x] Add `checklist_json` JSON column to Application model
- [x] Create `visa-client/src/screens/ChecklistScreen.jsx` (skeleton + banner + list)
- [x] Fix lazy useState initialization in AppContext for applicationId
- [x] Add `@keyframes shimmer` + `.skeleton` class to index.css

## Dev Notes
- 6 employment types with hardcoded document lists (employee/student/business_owner/freelancer/homemaker/retired)
- Cache check: `if app.checklist_json: return cached`
- Bug fix: `applicationId` must use lazy init `useState(() => localStorage.getItem(...))` to avoid null on first render
- freelancer gets extra confidence_note field: "Hồ sơ freelancer có độ biến động cao..."

## Dev Agent Record

### Completion Notes
Checklist generation implemented as deterministic lookup (no AI cost per generation). Lazy init bug fixed in AppContext.

### Debug Log
- Bug: "Không thể tạo danh sách" error on fresh page load — caused by applicationId=null from eager useState(null). Fixed with lazy initializer.

## File List
- `api/ai.py` (generate_checklist function)
- `api/routers/application.py` (checklist endpoint)
- `db/models.py` (checklist_json column)
- `visa-client/src/context/AppContext.jsx` (lazy init fix)
- `visa-client/src/screens/ChecklistScreen.jsx`
- `visa-client/src/index.css`

## Change Log
- 2026-06-29: Story completed; lazy init bug fixed

## Status
Done
