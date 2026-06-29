---
status: done
baseline_commit: NO_VCS
---

# Story 3.2 — AI Document Review

## Story
**As a** user,
**I want** my uploaded documents to be automatically reviewed by AI,
**so that** I get immediate feedback on whether they are acceptable.

## Acceptance Criteria
- [x] `POST /api/application/{id}/documents/{doc_id}/review` triggers Sonnet vision review for images
- [x] Non-image files (PDF, etc.) get status="pass" automatically without AI call
- [x] Returns `{status, reason}` where status is pass|fail|needs_clarification
- [x] Document DB record updated with review_status and review_notes
- [x] Frontend shows "reviewing" StatusChip during API call
- [x] StatusChip updates to pass/fail/needs_clarification after review
- [x] fail/needs_clarification shows inline red reason box in DocumentItem

## Tasks/Subtasks
- [x] Write `review_document_image()` in `api/ai.py` using Sonnet with base64 image
- [x] Add review endpoint in `api/routers/application.py`
- [x] Implement IMAGE_TYPES check to skip non-images
- [x] Create `_guess_media_type()` helper
- [x] Update DocumentItem to show fail reason inline
- [x] Wire `reviewDoc()` in ChecklistScreen to auto-call after upload

## Dev Notes
- Sonnet model (`claude-sonnet-4-6`) used for vision — NOT Haiku (Haiku lacks vision quality)
- base64 encode image bytes before sending to Anthropic
- media_type needed for Anthropic image source: detected from file extension
- Review prompt instructs: "when unsure → needs_clarification, not fail"
- Reason text in Vietnamese, specific and actionable
- Auto-review triggered immediately after upload completes (no user action needed)

## Dev Agent Record

### Completion Notes
Sonnet vision review working. Images reviewed immediately after upload. Non-images pass automatically.

## File List
- `api/ai.py` (review_document_image function)
- `api/routers/application.py` (review endpoint)
- `visa-client/src/components/DocumentItem.jsx` (fail reason display)
- `visa-client/src/screens/ChecklistScreen.jsx` (reviewDoc function)

## Change Log
- 2026-06-29: Story completed

## Status
Done
