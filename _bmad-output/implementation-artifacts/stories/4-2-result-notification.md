---
status: done
baseline_commit: NO_VCS
---

# Story 4.2 — Result Notification

## Story
**As a** user,
**I want** to see a clear result screen showing whether my visa was approved,
**so that** I know the final outcome of my application.

## Acceptance Criteria
- [x] 3 result states: approved (green 🎉), rejected (red ❌), quota_rejected (yellow 📋)
- [x] Each state has distinct headline, subtext, and visual treatment
- [x] `resultStatus` from AppContext determines which state to show
- [x] Defaults to 'approved' if resultStatus is null (demo fallback)
- [x] No back navigation (terminal screen)
- [x] Contact/support link shown at bottom
- [x] No ProgressBar

## Tasks/Subtasks
- [x] Create `visa-client/src/screens/ResultScreen.jsx` with 3 COPY states
- [x] Wire `resultStatus` from AppContext
- [x] Set default to 'approved' if resultStatus null
- [x] Remove NavHeader back button (or hide back)
- [x] Add 'result' case to App.jsx switch

## Dev Notes
- COPY object: `{approved: {headline, subtext, icon, color}, rejected: {...}, quota_rejected: {...}}`
- resultStatus set by StatusTimelineScreen before navigating here
- No API call needed — result is in statusData from the timeline poll
- This is the end of the user journey — no further navigation

## Dev Agent Record

### Completion Notes
Result screen implemented with 3 distinct visual states.

## File List
- `visa-client/src/screens/ResultScreen.jsx`
- `visa-client/src/App.jsx` (result case added)

## Change Log
- 2026-06-29: Story completed

## Status
Done
