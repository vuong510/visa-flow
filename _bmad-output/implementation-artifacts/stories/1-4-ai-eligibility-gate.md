---
status: done
baseline_commit: NO_VCS
---

# Story 1.4 — AI Eligibility Gate

## Story
**As a** user,
**I want** to receive an AI-powered eligibility assessment,
**so that** I know whether to proceed with my visa application.

## Acceptance Criteria
- [x] `POST /api/application/{id}/eligibility` calls Haiku with profile data
- [x] Returns `{result, headline, bullets, reason, confidence_label}` 
- [x] Three result states: eligible (green), edge_case (yellow), not_eligible (red)
- [x] Skeleton loading card shown when response takes >3s
- [x] EligibilityScreen shows Bước 7/10
- [x] eligible/edge_case → "Tiếp tục" CTA → navigate price
- [x] not_eligible → no CTA, shows contact link
- [x] Haiku hard-blocks: 180-day denial ban, <10 business days departure
- [x] freelancer → always edge_case
- [x] confidence_label: eligible → "Cao", edge_case → "Trung bình", not_eligible → "Cao"

## Tasks/Subtasks
- [x] Write `api/ai.py` with `assess_eligibility()` using Haiku
- [x] Add eligibility endpoint in `api/routers/application.py`
- [x] Add `eligibility_data` JSON column to Application model
- [x] Create `visa-client/src/screens/EligibilityScreen.jsx`
- [x] Create EligibilityCard component (3 color states)
- [x] Create SkeletonCard with shimmer animation
- [x] Add `@keyframes shimmer` to index.css
- [x] Wire confidence_label mapping in Haiku system prompt

## Dev Notes
- Haiku system prompt includes explicit rule chain — stops at first match
- confidence_label mapping embedded in system prompt as explicit rule (not post-processed)
- Shimmer animation: 3s timer sets showSkeleton=true while awaiting API
- edge_case headline: "Hồ sơ của bạn có thể đủ điều kiện"
- eligible headline: MUST be exactly "Hồ sơ của bạn trông tốt ✓"
- eligibility_data stored in DB for audit trail

## Dev Agent Record

### Completion Notes
Eligibility gate implemented. Fixed confidence_label bug for edge_case by adding explicit mapping rule to Haiku system prompt.

### Debug Log
- Bug: freelancer was returning confidence_label "Cao" — fixed by adding explicit rule to system prompt: "edge_case → Độ tin cậy AI: Trung bình"

## File List
- `api/ai.py`
- `api/routers/application.py` (eligibility endpoint)
- `db/models.py` (eligibility_data column)
- `visa-client/src/screens/EligibilityScreen.jsx`
- `visa-client/src/index.css` (@keyframes shimmer)

## Change Log
- 2026-06-29: Story completed; confidence_label bug fixed

## Status
Done
