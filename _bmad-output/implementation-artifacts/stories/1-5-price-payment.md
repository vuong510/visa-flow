---
status: done
baseline_commit: NO_VCS
---

# Story 1.5 — Price Screen & Demo Payment

## Story
**As a** user,
**I want** to see the service price and complete a demo payment,
**so that** I can proceed to the document checklist.

## Acceptance Criteria
- [x] PriceScreen shows Bước 8/10
- [x] Price breakdown: Phí dịch vụ 990.000 ₫ + Phí lãnh sự 550.000 ₫ = Tổng 1.540.000 ₫
- [x] "Thanh toán (Demo)" button triggers full-screen overlay
- [x] Overlay: spinner 1.5s → success checkmark 1s → navigate to checklist
- [x] `POST /api/application/{id}/payment/demo` called, sets payment_status="demo_completed"
- [x] feasibility_ok set to True on payment completion

## Tasks/Subtasks
- [x] Add payment/demo endpoint in `api/routers/application.py`
- [x] Create `visa-client/src/screens/PriceScreen.jsx`
- [x] Implement full-screen payment overlay with spinner + success states
- [x] Add `@keyframes spin` to index.css
- [x] Wire navigate('checklist') after overlay completes

## Dev Notes
- Full-screen overlay (position: fixed, z-index: 9999) prevents interaction during "payment"
- Overlay phases: loading (0–1500ms) → success (1500–2500ms) → navigate
- No actual payment gateway — demo only
- feasibility_ok=True unlocks checklist generation

## Dev Agent Record

### Completion Notes
Price screen and demo payment flow implemented and tested.

## File List
- `api/routers/application.py` (payment/demo endpoint)
- `visa-client/src/screens/PriceScreen.jsx`
- `visa-client/src/index.css` (@keyframes spin)

## Change Log
- 2026-06-29: Story completed

## Status
Done
