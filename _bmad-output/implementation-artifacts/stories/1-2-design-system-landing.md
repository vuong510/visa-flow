---
status: done
baseline_commit: NO_VCS
---

# Story 1.2 — Design System + Landing Screen

## Story
**As a** user,
**I want** to see a polished landing screen with clear branding,
**so that** I feel confident using the visa consulting service.

## Acceptance Criteria
- [x] React+Vite project scaffolded in `visa-client/`
- [x] CSS design tokens defined: colors, typography (Be Vietnam Pro), spacing
- [x] NavHeader component with AI badge and back button support
- [x] ProgressBar "Bước N/10" component
- [x] CTAButton component (primary variant)
- [x] BottomSheet component with `open` prop guard
- [x] Landing screen: headline, subtext, destination cards (Japan/China)
- [x] Destination selection navigates to profile flow
- [x] Mobile-first layout, max-width 430px

## Tasks/Subtasks
- [x] Scaffold React+Vite project with npm
- [x] Configure `index.css` with CSS custom properties (tokens)
- [x] Import Be Vietnam Pro from Google Fonts
- [x] Create `components/NavHeader.jsx` with back + title + rightAction
- [x] Create `components/ProgressBar.jsx`
- [x] Create `components/CTAButton.jsx`
- [x] Create `components/BottomSheet.jsx` with `open` guard
- [x] Create `context/AppContext.jsx` with screen/navigate, applicationId, sessionId
- [x] Create `screens/LandingScreen.jsx` with destination selection
- [x] Wire App.jsx switch/case router

## Dev Notes
- Screen routing via React Context `screen` state — no React Router
- `BottomSheet` MUST check `if (!open) return null` as first line
- Be Vietnam Pro imported via `<link>` in index.html
- CSS tokens in `:root {}` block in `index.css`
- `AppContext` exports `useApp()` hook

## Dev Agent Record

### Completion Notes
All UI components and landing screen implemented. Design system tokens established.

## File List
- `visa-client/src/index.css`
- `visa-client/src/App.jsx`
- `visa-client/src/context/AppContext.jsx`
- `visa-client/src/components/NavHeader.jsx`
- `visa-client/src/components/ProgressBar.jsx`
- `visa-client/src/components/CTAButton.jsx`
- `visa-client/src/components/BottomSheet.jsx`
- `visa-client/src/screens/LandingScreen.jsx`
- `visa-client/index.html`

## Change Log
- 2026-06-29: Story completed

## Status
Done
