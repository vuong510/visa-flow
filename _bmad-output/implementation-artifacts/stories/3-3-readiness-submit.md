---
status: done
baseline_commit: NO_VCS
---

# Story 3.3 — Readiness Banner & Submit

## Story
**As a** user,
**I want** to see my upload progress and submit my application when ready,
**so that** I can hand off my documents to the agency.

## Acceptance Criteria
- [x] ReadinessBanner shows "Đã tải lên N/M tài liệu" (uploaded count / total count)
- [x] Submit CTA only appears when ALL checklist items have status="pass"
- [x] "Nộp hồ sơ" button calls `POST /api/application/{id}/submit`
- [x] Submit sets `submission_status="submitted"` and `submitted_at=now()`
- [x] After submit → navigate('status-timeline')
- [x] Submit button disabled/loading during API call

## Tasks/Subtasks
- [x] Add submit endpoint in `api/routers/application.py`
- [x] Add `submitted_at` DateTime column to Application model
- [x] Add `allPass` computed value in ChecklistScreen (all docs have status=pass)
- [x] Conditionally render Submit CTA based on `allPass`
- [x] Wire `handleSubmit()` → POST /submit → navigate('status-timeline')
- [x] ReadinessBanner counts uploaded vs total items

## Dev Notes
- allPass = checklist items count > 0 AND every item has docs[item.id]?.status === "pass"
- Banner always visible (not just when allPass)
- submit endpoint also checks feasibility_ok before accepting (guard against skipping payment)
- submitted_at stored as UTC datetime

## Dev Agent Record

### Completion Notes
Submit flow implemented. allPass gate working correctly — Submit CTA only shows when every document passes review.

## File List
- `api/routers/application.py` (submit endpoint)
- `db/models.py` (submitted_at column)
- `visa-client/src/screens/ChecklistScreen.jsx` (allPass, handleSubmit, ReadinessBanner)

## Change Log
- 2026-06-29: Story completed

## Status
Done
