---
status: done
baseline_commit: NO_VCS
---

# Story 1.3 — Profile Question Flow

## Story
**As a** user,
**I want** to answer 6 questions about myself and my travel plans,
**so that** the system can assess my visa eligibility accurately.

## Acceptance Criteria
- [x] 6 question screens in order: employment type, travel dates (departure+return), passport validity, prior denial, prior stamps, bank balance indicator
- [x] ProgressBar shows Bước 1/10 through Bước 6/10
- [x] Each screen has NavHeader with back navigation
- [x] Answers accumulated in AppContext `profile` state
- [x] Final question screen calls `PUT /api/application/{id}/profile` then navigates to eligibility
- [x] No required field validation — all fields optional (per design)

## Tasks/Subtasks
- [x] Create `screens/Q1EmploymentScreen.jsx`
- [x] Create `screens/Q2TravelDatesScreen.jsx`
- [x] Create `screens/Q3PassportScreen.jsx`
- [x] Create `screens/Q4DenialScreen.jsx`
- [x] Create `screens/Q5StampsScreen.jsx`
- [x] Create `screens/Q6BankScreen.jsx`
- [x] Add all 6 cases to App.jsx switch
- [x] Wire profile accumulation in AppContext
- [x] Wire `PUT /profile` API call on final screen

## Dev Notes
- employment_type values: employee | student | business_owner | freelancer | homemaker | retired
- Travel dates stored as `{departure: "YYYY-MM-DD", return: "YYYY-MM-DD"}` in profile
- Profile sent as flat JSON to backend: `{employment_type, departure, return_date, passport_valid_months, prior_denial, denial_country, denial_date, has_prior_stamps, bank_balance_ok}`
- Navigate sequence: q1 → q2 → q3 → q4 → q5 → q6 → eligibility-loading

## Dev Agent Record

### Completion Notes
All 6 question screens implemented with proper ProgressBar steps and navigation.

## File List
- `visa-client/src/screens/Q1EmploymentScreen.jsx`
- `visa-client/src/screens/Q2TravelDatesScreen.jsx`
- `visa-client/src/screens/Q3PassportScreen.jsx`
- `visa-client/src/screens/Q4DenialScreen.jsx`
- `visa-client/src/screens/Q5StampsScreen.jsx`
- `visa-client/src/screens/Q6BankScreen.jsx`

## Change Log
- 2026-06-29: Story completed

## Status
Done
