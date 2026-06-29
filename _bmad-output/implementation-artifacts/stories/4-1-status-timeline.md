---
status: done
baseline_commit: NO_VCS
---

# Story 4.1 — Status Timeline

## Story
**As a** user,
**I want** to see a visual timeline of my application status,
**so that** I know where my application is in the process.

## Acceptance Criteria
- [x] 4 timeline nodes: Đã nhận hồ sơ → Đang xử lý → Đã nộp lãnh sự → Kết quả
- [x] Node states: completed (green dot), active (blue pulsing dot), pending (gray dot)
- [x] `GET /api/application/{id}/status` returns timeline data + is_terminal flag
- [x] Auto-refresh every 5 minutes via setInterval
- [x] Manual refresh via ↻ button in NavHeader rightAction
- [x] Timestamp footer: "Cập nhật lúc HH:MM:SS · Tự động làm mới sau 5 phút"
- [x] is_terminal=true → navigate('result')
- [x] No ProgressBar (post-submission screen)

## Tasks/Subtasks
- [x] Add status endpoint with `_build_timeline()` helper in `api/routers/application.py`
- [x] Create `visa-client/src/screens/StatusTimelineScreen.jsx`
- [x] Implement 4 TimelineNode components with state-based styling
- [x] Add `@keyframes pulse-ring` to index.css for active node animation
- [x] Wire NavHeader `rightAction` refresh button
- [x] Wire setInterval(fetchStatus, 5*60*1000) + clearInterval on unmount
- [x] Wire is_terminal check → navigate('result')

## Dev Notes
- Timeline nodes: submitted → agency_submitted → processing → completed/rejected
- _build_timeline() maps submission_status → 4 nodes with state
- pulse-ring: radial animation on active (blue) node
- clearInterval in useEffect cleanup to prevent memory leak
- Refresh button calls fetchStatus() manually
- resultStatus set in AppContext before navigating to result

## Dev Agent Record

### Completion Notes
Status timeline implemented with polling and pulse animation.

## File List
- `api/routers/application.py` (_build_timeline, status endpoint)
- `visa-client/src/screens/StatusTimelineScreen.jsx`
- `visa-client/src/index.css` (@keyframes pulse-ring)

## Change Log
- 2026-06-29: Story completed

## Status
Done
