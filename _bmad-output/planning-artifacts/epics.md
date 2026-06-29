---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories", "step-04-final-validation"]
status: final
inputDocuments:
  - prds/prd-vuongnguyen-2026-06-29/prd.md
  - architecture/architecture-visa-flow-2026-06-29/ARCHITECTURE-SPINE.md
  - ux-designs/ux-visa-flow-2026-06-29/DESIGN.md
  - ux-designs/ux-visa-flow-2026-06-29/EXPERIENCE.md
---

# AI Visa Consulting Flow — Japan & China: Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the AI Visa Consulting Flow, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**FR-A: Eligibility Gate (pre-payment)**

FR1. System collects applicant profile data: destination (Japan / China), employment type, prior denial history, travel history (prior Japan/China stamps), travel dates, passport expiry.

FR2. System evaluates profile against structural eligibility signals: employment type, prior denial recency (Japan 6-month reapplication ban), travel date feasibility, passport validity.

FR3. System returns one of three eligibility outcomes: Eligible (proceed to payment), Likely eligible edge case (proceed with lower-confidence flag + optional human escalation), Not eligible (blocked pre-payment with specific reason, no charge).

FR4. System never states specific financial thresholds or coaches financial preparation. Gate assesses employment type and whether anchor documents can structurally exist — not whether finances are "sufficient."

FR5. Prior denial gate: if applicant was denied Japan visa within last 6 months, system hard-blocks the application and explains the reapplication waiting period. Same logic for China on recent denial.

FR6. If profile type is Freelancer or informal self-employed, system flags as high-effort edge case with lower confidence score and offers option to escalate to human review.

FR7. Returning travellers with prior Japan/China stamps receive a higher confidence signal; system surfaces this to the user as a positive indicator.

FR8. Group/family applications assessed as a compound profile; system evaluates how each member's profile interacts and flags any member with a structural gap. *(Deferred to post-v1 per architecture spine.)*

**FR-B: Conditional Document Checklist**

FR9. After eligibility pass, system generates a document checklist specific to the applicant's profile type and visa category.

FR10. Checklist is conditional — different requirements rendered per profile type. No generic list is presented to any user.

FR11. Each checklist item includes: document name, required contents, acceptable format (original / scan / certified copy), and plain-language explanation of why it is required.

FR12. For Employee profile: checklist includes leave approval letter and explicitly requires stated travel dates match the visa application travel dates.

FR13. For Student profile: checklist includes parent guarantee letter template and specifies that parent's financial documents must accompany.

FR14. For Freelancer profile: checklist is advisory (most common document set for informal workers); user is warned that officer judgment applies and confidence is lower.

FR15. Checklist updates automatically if embassy requirements change (fed by embassy monitoring).

**FR-C: Document Review**

FR16. Applicant uploads documents against each checklist item.

FR17. System reviews each uploaded document for: completeness, required fields present, date validity, consistency with stated profile (e.g., travel dates on leave letter match application dates).

FR18. System returns per-document status: Pass / Fail / Needs Clarification, with specific failure reason.

FR19. System surfaces an overall readiness score before submission: "Hồ sơ của bạn đã sẵn sàng" or "X vấn đề cần giải quyết trước khi nộp."

FR20. Freelancer/edge-case profile document review states confidence explicitly: "AI review confidence: medium — a human will perform a secondary check before submission."

FR21. System never approves submission for a profile flagged as ineligible in the eligibility gate. Gate cannot be bypassed.

**FR-D: Status Tracking**

FR22. After hard copy submission by partner agency, applicant receives status updates at each stage: documents received by agency / documents submitted to embassy / result received.

FR23. Result notification: approved (with pickup instructions) or rejected (with stated reason where embassy provides one).

FR24. If quota rejection (strong profile but embassy quota exhausted), system communicates this specifically — differentiates from profile-based rejection and does not suggest reapplication without clarifying what the user can do.

**FR-E: Embassy Requirement Monitoring**

FR25. System monitors Japan embassy Vietnam website and China embassy Vietnam website for changes to visa requirements, fee schedules, and accepted document types.

FR26. When a requirement change is detected, system flags affected in-progress applications and updates checklists for new applications.

FR27. Internal alert to operator when a monitored change is detected.

**FR-F: Trust & Transparency**

FR28. Every user-facing interaction discloses that they are talking to an AI system. Disclosure is explicit on first session, persistent in UI — not buried in fine print.

FR29. Eligibility gate result includes a plain-language explanation of how the decision was reached (not a black box).

FR30. Confidence levels are surfaced to the user at eligibility screening and document review — not hidden.

FR31. Product never promises approval. Language consistently frames outcomes as "high chance" / "meets requirements" — not "guaranteed."

FR32. Firm owner demo flow: a complete walkthrough of one full AI conversation (eligibility → checklist → document review) is available for the agency partner to review before committing to partnership.

---

### NonFunctional Requirements

NFR1. **Availability.** System must be available 24/7. Maximum downtime: 30 minutes per month.

NFR2. **Latency.** Eligibility gate response under 10 seconds. Document checklist generation under 5 seconds.

NFR3. **Data handling.** Applicant documents (identity documents, financial records) are sensitive PII. Must not be stored longer than necessary for the active application. Storage and access scoped to minimum required.

NFR4. **AI accuracy.** Document review checks are rule-based (not LLM hallucination risk). Eligibility gate rules must be auditable and version-controlled. Any rules change must be logged with date and reason.

NFR5. **Escalation path.** For every AI decision, a human-review escalation path must exist. Especially required for Freelancer profiles, edge-case eligibility outcomes, and rejection notifications.

NFR6. **Language.** All user-facing content in Vietnamese. Internal admin/operator tools may be English.

---

### Additional Requirements

*(Architecture requirements from ARCHITECTURE-SPINE.md — AD-1 through AD-12)*

**AR1 (AD-2) — Frontend stack.** React + Vite SPA. No SSR. One component per screen (~20 screens). React Context for session state. No Redux or additional state libraries.

**AR2 (AD-3) — Backend.** FastAPI (Python), REST API only. All endpoints under `/api/*`. Every new feature is a new router file in `api/routers/`. No logic in `main.py`.

**AR3 (AD-4) — Database.** SQLite via SQLAlchemy for demo. Two tables: `Application` (id, session_id, destination, profile_json, eligibility_result, travel_dates, feasibility_ok, payment_status, submission_status, created_at) and `Document` (id, application_id, doc_type, file_path, review_status, review_notes). All queries via SQLAlchemy ORM — no raw SQL in route handlers.

**AR4 (AD-5) — File storage.** Uploaded files stored to Railway ephemeral volume. `Document.file_path` holds relative path on disk. Storage behind a single `storage.py` module for future swap (Cloudflare R2).

**AR5 (AD-6) — AI pipeline.** Stage 1 (Haiku): eligibility gate + checklist, input profile_json, output decision + checklist JSON, deterministic rule-based prompt. Stage 2 (Sonnet): document review, input file + expected spec, output pass/fail/needs-clarification + reason string.

**AR6 (AD-8) — Authentication.** No login for demo. `session_id` generated on first page load, stored in `localStorage`, sent with every API call. Production: replace `session_id` with MoMo `user_id` at that layer only.

**AR7 (AD-9) — Payment.** Placeholder for demo. "Thanh toán" button renders but dispatches no action. Production: replace with MoMo deeplink redirect.

**AR8 (AD-11) — Deployment.** FastAPI backend → Railway ($5/month) via nixpacks. React frontend → Vercel (free tier) via GitHub integration. No Docker, no custom build scripts unless defaults fail.

**AR9 (AD-12) — API key security.** API keys live in Railway environment variables only. Frontend never calls Claude API directly.

**AR10 — Build order (12 steps).** DB schema → FastAPI skeleton → eligibility gate endpoint → React SPA scaffold → profile input + eligibility screens → checklist endpoint + screen → file upload endpoint + disk storage → document review endpoint + Sonnet → review screen + readiness score → price screen + placeholder payment → submission confirmation → Railway + Vercel deploy.

**AR11 — Deferred post-v1.** Do not build: PostgreSQL migration, Cloudflare R2, MoMo payment SDK, admin dashboard, MoMo mini app SDK, multi-language, push notifications, automated embassy monitoring, group/family compound profile.

---

### UX Design Requirements

*(From DESIGN.md and EXPERIENCE.md)*

**Tokens**

UX-DR1. **Color tokens** (exact values): primary #1A2E4A, cta #2563EB, cta-hover #1D4ED8, cta-pressed #1E40AF, surface #FFFFFF, background #F5F7FA, success #16A34A, success-light #DCFCE7, warning #D97706, warning-light #FEF3C7, error #DC2626, error-light #FEE2E2, text-primary #1A1A2E, text-secondary #374151, text-muted #6B7280, border #E5E7EB, border-focus #2563EB.

UX-DR2. **Typography font.** Load "Be Vietnam Pro" (weights 400, 500, 600, 700) via Google Fonts. Minimum text size: 13px. Minimum line-height: 1.45. No weight below 400.

UX-DR3. **Typography scale.** h1=24px/700/lh1.30, h2=20px/600/lh1.35, h3=17px/600/lh1.40, body-lg=16px/400/lh1.55, body=15px/400/lh1.55, body-sm=14px/400/lh1.50, caption=13px/400/lh1.45, label=12px/500/lh1.40.

UX-DR4. **Spacing tokens.** xs=4px, sm=8px, md=16px, lg=24px, xl=32px, xxl=48px, screen-h-pad=20px, screen-v-pad=24px, card-inner=20px, stack-tight=8px, stack-loose=16px, section-gap=24px.

UX-DR5. **Radius tokens.** card=16px, button=12px, input=10px, chip=20px, modal=20px, tag=6px. No additional radius values.

UX-DR6. **Motion tokens.** duration-fast=150ms, duration-base=250ms, duration-slow=400ms, easing-default=cubic-bezier(0.2,0,0,1), easing-spring=cubic-bezier(0.34,1.56,0.64,1), easing-exit=cubic-bezier(0.4,0,1,1).

UX-DR7. **Shadow tokens.** Three levels only — card: "0 1px 3px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.04)"; card-raised: "0 4px 12px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.06)"; modal: "0 16px 48px rgba(26,46,74,0.20)". No additional variants.

**Components**

UX-DR8. **NavHeader.** Height 56px, background #1A2E4A. Back chevron left-aligned 44×44px tap target, white. Title centered, type.h3, white. AI badge right-aligned, permanent pill labelled "AI", #2563EB bg, white text, radius.chip. Tapping badge opens bottom sheet with AI disclosure. Badge appears on every screen without exception.

UX-DR9. **ProgressBar.** Height 4px, flush below NavHeader. Track #E5E7EB, fill #2563EB. Right-aligned step label type.caption color.text-muted, format "Bước 4/10". Fill transitions 250ms easing-default. Present on all flow screens after Landing; absent on Landing and Status Timeline. After payment, relabel as "Đã tải lên 3/7 tài liệu." Never pre-fill to 100% unless genuinely complete.

UX-DR10. **EligibilityCard — Pass.** Background #DCFCE7, border 1px #86EFAC. Headline type.h2, color #16A34A. Bullet list type.body. Disclaimer type.caption italic: "Đây là đánh giá AI — không phải bảo đảm phê duyệt."

UX-DR11. **EligibilityCard — Fail.** Background #FEE2E2, border 1px #FCA5A5. Headline type.h2, color #DC2626. One-sentence plain-Vietnamese reason type.body-lg. Protective statement "Các đại lý vẫn sẽ nhận tiền của bạn — chúng tôi thì không." always present. Secondary link "Xem cách cải thiện →" opens bottom sheet — not a button, not a navigation.

UX-DR12. **EligibilityCard — Edge/lower-confidence.** Background #FEF3C7, border 1px #FCD34D. Headline type.h2, color #D97706. StatusChip "Độ tin cậy AI: Trung bình" warning variant. Two CTAs below card: primary "Tiếp tục", secondary text "Yêu cầu xem xét thủ công."

UX-DR13. **ProfileQuestion wrapper.** One question per screen without exception. Question text type.h2, no trailing period. Optional helper text type.body color.text-muted. AI disclosure note type.caption on Q1 (employment type) and Q4 (prior denial). Auto-advance on single-select tap. Q4 exception: inline follow-up date input + country selector if "Có" selected before advancing. Validation on advance, not on tap. Inline error below input — not toast.

UX-DR14. **OptionButton.** Full-width, min-height 56px. Default: bg white, border 1px #E5E7EB, radius 12px, label type.body-lg left-aligned 16px padding. Selected: border 2px #2563EB, bg rgba(37,99,235,0.06), checkmark icon, shadow card-raised. Disabled: bg #F5F7FA, label text-muted. Press animation: scale(0.98) for 150ms.

UX-DR15. **CTAButton — Primary.** Height 52px, bg #2563EB, radius 12px, label type.body-lg weight 600 white centered. Hover/pressed: bg #1E40AF, scale(0.98). Disabled: bg #E5E7EB, label text-muted. Loading: 20px white spinner, non-interactive. Always full-width in fixed Bottom Action Area (white bg, 1px top border #E5E7EB, padding 16px top/bottom 20px sides, safe-area-inset-bottom applied).

UX-DR16. **CTAButton — Secondary text.** Transparent bg, no border, label #2563EB type.body-lg weight 500. Use only for secondary actions below a primary CTA.

UX-DR17. **StatusChip.** Height 24px, padding 0 10px, radius 20px, label type.label (12px/500), optional leading icon 12px. Five variants: pass (bg #DCFCE7, text #16A34A, border #86EFAC), fail (bg #FEE2E2, text #DC2626, border #FCA5A5), warning (bg #FEF3C7, text #D97706, border #FCD34D), pending (bg #F5F7FA, text #6B7280, border #E5E7EB), processing (bg rgba(37,99,235,0.08), text #2563EB, border rgba(37,99,235,0.20)). Every StatusChip uses icon + color + text — color is never the sole differentiator.

UX-DR18. **DocumentItem.** Min-height 72px, padding 16px. Left icon 40×40px rounded square (radius 6px), bg #F5F7FA. Primary label type.body weight 500. Sub-label type.body-sm text-muted, up to 2 lines. StatusChip right-aligned. Action link "Tải lên" / "Xem lại" type.body-sm. Fail state: tapping chip expands row to show failure reason type.caption color.error. Row separator 1px #E5E7EB except last item. Upload opens native OS media picker. During upload: processing StatusChip, row non-interactive. Fail status blocks Submit CTA until corrected.

UX-DR19. **StatusTimeline.** 4-node vertical timeline. Completed node: filled #16A34A. Active node: filled #2563EB + CSS pulse ring. Pending node: #E5E7EB fill, #D1D5DB stroke. Connector: 2px #E5E7EB, dotted on completed→active gap. Step label type.body. StatusChip right-aligned per row. Timestamp type.caption below completed steps. Estimated date below active step. Data polled every 5 minutes while active. Node transition 400ms fill animation. Pull-to-refresh enabled on this screen only.

**Layout**

UX-DR20. **Screen canvas.** Always #F5F7FA background. 20px horizontal margins. Content capped 430px max-width, centered. No horizontal scrolling.

UX-DR21. **Screen anatomy.** OS status bar → NavHeader (56px) → ProgressBar (4px, multi-step screens) → 24px screen-v-pad → content cards (24px section-gap) → 24px screen-v-pad → Bottom Action Area (fixed, safe area inset).

UX-DR22. **Cards.** Background #FFFFFF, shadow.card, radius 16px, padding 20px. No full-bleed content except NavHeader and ProgressBar.

**Transitions**

UX-DR23. **Screen transitions.** Push: slide left 250ms easing-default. Pop: slide right 200ms easing-exit. Bottom sheet open: slide up + fade scrim 300ms easing-spring. Bottom sheet close: slide down 250ms easing-exit. Card fade-in on load: opacity 0→1 + translateY 8px→0, 300ms. StatusChip change: cross-fade 250ms.

UX-DR24. **Loading states.** Never flash for sub-300ms. Eligibility card skeleton shows "AI đang đánh giá hồ sơ của bạn..." when API exceeds 3 seconds. Checklist: list skeleton 5 rows + "Đang tạo danh sách tài liệu..." Document review: per-item processing chip + "AI đang kiểm tra tài liệu của bạn." MoMo payment: full-screen overlay, back disabled.

UX-DR25. **Error states.** Network error → persistent bottom toast "Không có kết nối. Kiểm tra mạng và thử lại." + Retry. API error on eligibility gate → replace skeleton with "Không thể đánh giá hồ sơ lúc này. Thử lại hoặc liên hệ hỗ trợ." + two CTAs. Upload failure → inline "Tải lên thất bại. Thử lại." Row reverts to pending chip.

UX-DR26. **Success states.** Eligibility pass → EligibilityCard fade-in only, no confetti. Payment success → 1-second success screen then auto-transition to checklist. All docs pass → "Hồ sơ của bạn đã sẵn sàng ✓" banner, Submit CTA activates. Submitted → transition to StatusTimeline with top banner.

UX-DR27. **Back navigation disabled on:** Landing (01), Payment confirmation (13), Submit (18), Status Timeline (19), Result (20).

**Accessibility**

UX-DR28. All interactive elements minimum 44×44px tap target.

UX-DR29. Color is never the sole differentiator: every StatusChip uses icon + color + text.

UX-DR30. Text contrast: text-primary on surface 17.9:1 (AAA), text-muted on surface 4.6:1 (AA), cta on surface 4.6:1 (AA). All pass WCAG AA minimum.

UX-DR31. All elements reachable via VoiceOver/TalkBack. Tab order follows visual reading order. Set `lang="vi"` on root element.

UX-DR32. Layout must not break at iOS/Android Larger Accessibility Sizes (+3 steps). Use relative font units.

UX-DR33. Every form error announced via `aria-live="assertive"` — not just color.

UX-DR34. Respect `prefers-reduced-motion`: replace slide transitions with fade. Keep functional animations but reduce distance/duration by 70%.

UX-DR35. No gradients on primary UI except Landing hero may use subtle #1A2E4A → #223A5E gradient (max 15% shift). No decorative gradients elsewhere.

UX-DR36. **Haptic feedback (MoMo mini app).** OptionButton tap = light impact, CTAButton tap = medium impact, eligibility pass = medium impact, eligibility fail = warning notification, payment confirmation = success notification, document review fail = error notification.

**Vietnamese copy rules**

UX-DR37. Question labels sentence case, no trailing period.

UX-DR38. Button labels as action verbs: "Tiếp tục", "Tải lên", "Xác nhận nộp hồ sơ."

UX-DR39. State AI confidence on every AI-generated result. Use exact approved phrases for EligibilityCard, checklist intro, and document review.

UX-DR40. **Forbidden approval phrases.** Never use: "Đảm bảo", "Chắc chắn được duyệt", "Tôi đảm bảo", "AI đã xác nhận hồ sơ hợp lệ." Use instead: "Hồ sơ của bạn trông tốt", "Có cơ hội cao", "Đáp ứng yêu cầu thông thường."

UX-DR41. **Never state bank balance thresholds.** Income range (Q6) is a pattern signal only. Q6 note must read: "Thông tin này giúp chúng tôi đánh giá hồ sơ theo kinh nghiệm thực tế. Chúng tôi không tư vấn về số dư ngân hàng tối thiểu vì Đại sứ quán không công bố ngưỡng chính thức."

UX-DR42. **Quota rejection language.** Must use: "Đại sứ quán đã từ chối đơn của bạn vì đã đủ chỉ tiêu trong đợt này — không phải vì vấn đề hồ sơ cá nhân." Do not frame as product failure.

UX-DR43. **No celebratory tone.** Never "Chúc mừng!", "Tuyệt vời!", "Hồ sơ của bạn hoàn hảo." Eligibility pass headline: "Hồ sơ của bạn trông tốt ✓" — calm, not celebratory. No confetti, no bounce animations.

UX-DR44. **No ALL CAPS.** No countdown timers. No fake social proof.

UX-DR45. **Full Vietnamese diacritics everywhere.** Do not strip tone marks.

---

### FR Coverage Map

FR1 → Epic 1 — Profile data collection (destination, employment, denial history, travel history, travel dates, passport expiry)
FR2 → Epic 1 — Structural eligibility evaluation including travel date feasibility (single Haiku call)
FR3 → Epic 1 — Three-outcome eligibility result (eligible / edge case / not eligible)
FR4 → Epic 1 — No bank balance thresholds; profile structure assessment only
FR5 → Epic 1 — Prior denial gate; Japan 6-month reapplication ban
FR6 → Epic 1 — Freelancer edge-case flag with lower confidence + escalation option
FR7 → Epic 1 — Returning traveller positive confidence signal
FR8 → Deferred post-v1 — Group/family compound assessment
FR9 → Epic 2 — Checklist generated after payment, specific to profile type
FR10 → Epic 2 — Conditional checklist; no generic list
FR11 → Epic 2 — Per-item: name, required contents, format, plain-language reason
FR12 → Epic 2 — Employee profile: leave letter + travel date match requirement
FR13 → Epic 2 — Student profile: parent guarantee letter + parent financial docs
FR14 → Epic 2 — Freelancer profile: advisory checklist with lower-confidence warning
FR15 → Epic 2 — Checklist auto-update when embassy requirements change (depends on Epic 5)
FR16 → Epic 3 — Document upload against each checklist item
FR17 → Epic 3 — Per-document review: completeness, fields, date validity, profile consistency
FR18 → Epic 3 — Per-document status: Pass / Fail / Needs Clarification + reason
FR19 → Epic 3 — Overall readiness score before submission
FR20 → Epic 3 — Freelancer review: explicit AI confidence statement
FR21 → Epic 3 — Ineligible profiles cannot bypass gate to submit
FR22 → Epic 4 — Status updates: received / submitted / result
FR23 → Epic 4 — Result notification: approved (pickup) or rejected (reason)
FR24 → Epic 4 — Quota rejection distinguished from profile rejection
FR25 → Epic 5 (post-v1) — Monitor Japan + China embassy Vietnam websites
FR26 → Epic 5 (post-v1) — Flag affected applications + update checklists on change
FR27 → Epic 5 (post-v1) — Internal operator alert on detected change
FR28 → Epic 1 — AI disclosure persistent in UI from first session
FR29 → Epic 1 — Plain-language eligibility decision explanation
FR30 → Epic 1 — Confidence levels surfaced at eligibility screening
FR31 → Epic 1 — No approval guarantees; language frames outcomes as "high chance"
FR32 → Cross-cutting — Firm owner demo = complete product working end-to-end (Epics 1–3)

---

## Epic List

### Epic 1: Foundation & Profile Screening
Applicant discovers the service, enters their full profile (including travel dates), gets an AI eligibility + feasibility decision in one Haiku call, sees the price, and pays (placeholder). This is the core "know before you pay" value prop and the standalone foundation all other epics build on.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR28, FR29, FR30, FR31

### Epic 2: Personalized Document Checklist
After paying, applicant immediately receives their profile-specific, conditional document checklist — not a generic list. Each item tells them exactly what the document must contain and why.
**FRs covered:** FR9, FR10, FR11, FR12, FR13, FR14, FR15

### Epic 3: Document Upload & AI Review
Applicant uploads their documents, receives Sonnet-powered per-document review, sees an overall readiness score, fixes flagged issues, and submits to the partner agency.
**FRs covered:** FR16, FR17, FR18, FR19, FR20, FR21
**Cross-cutting:** FR32 (firm owner demo validated here — full end-to-end flow complete)

### Epic 4: Application Status Tracking
Applicant knows what is happening at every stage after submission — from agency receipt through embassy decision — with quota rejection distinguished from profile rejection.
**FRs covered:** FR22, FR23, FR24

### Epic 5: Embassy Monitoring *(post-v1 — deferred per architecture spine)*
Operator monitors Japan and China embassy Vietnam websites for requirement changes; affected applications are flagged and checklists updated automatically.
**FRs covered:** FR25, FR26, FR27

**Deferred:** FR8 (group/family compound assessment) — post-v1

---

## Epic 1: Foundation & Profile Screening

Applicant discovers the service, enters their full profile (including travel dates), gets an AI eligibility + feasibility decision in one Haiku call, sees the price, and pays (placeholder). This is the core "know before you pay" differentiator and the foundation all other epics build on.

### Story 1.1: Backend Foundation & API Skeleton

As a developer,
I want the FastAPI backend and SQLite database initialized with a session management layer,
So that all subsequent stories have a working API and persistent storage to build on.

**Acceptance Criteria:**

**Given** the backend starts
**When** `GET /api/health` is called
**Then** it returns HTTP 200 with `{"status": "ok"}`

**Given** the backend initializes
**When** the SQLite database is created
**Then** the `Application` table exists with columns: id, session_id, destination, profile_json, eligibility_result, travel_dates, feasibility_ok, payment_status, submission_status, created_at

**Given** the backend initializes
**When** the SQLite database is created
**Then** the `Document` table exists with columns: id, application_id, doc_type, file_path, review_status, review_notes

**Given** a client makes any API call
**When** no `session_id` is present
**Then** the backend generates a new UUID `session_id` and returns it in the response so the frontend can store it in `localStorage`

**Given** `POST /api/application/start` is called with a `session_id`
**When** the request is processed
**Then** a new `Application` record is created and the `application_id` is returned

**Given** any route handler
**When** written
**Then** all business logic lives in `api/routers/` — nothing in `main.py` except app initialization and router registration; all DB queries go through SQLAlchemy ORM, no raw SQL

---

### Story 1.2: Design System & Landing Screen

As an applicant,
I want to arrive at a trustworthy landing screen that explains the service,
So that I understand what I'm getting and decide whether to proceed.

**Acceptance Criteria:**

**Given** the React app loads
**When** the Landing screen renders
**Then** Be Vietnam Pro (weights 400/500/600/700) is loaded via Google Fonts, all color tokens are applied (primary #1A2E4A, cta #2563EB, background #F5F7FA, surface #FFFFFF), border-radius tokens applied (card=16px, button=12px, input=10px, chip=20px), shadow tokens applied (card, card-raised, modal), and motion tokens defined (duration-fast=150ms, duration-base=250ms, duration-slow=400ms)

**Given** the Landing screen
**When** rendered
**Then** the screen background is #F5F7FA, all content is within 20px horizontal margins, capped at 430px max-width, no horizontal scroll

**Given** the Landing screen
**When** rendered
**Then** the NavHeader (height 56px, bg #1A2E4A) shows the product title centered in type.h3 white, and a persistent "AI" pill badge right-aligned (#2563EB bg, white text, radius.chip, 44×44px tap target)

**Given** the Landing screen
**When** I tap the "AI" badge
**Then** a bottom sheet opens with the exact text: "Dịch vụ này sử dụng AI để đánh giá hồ sơ của bạn. Kết quả được giải thích rõ ràng và không phải là bảo đảm phê duyệt."

**Given** the Landing screen
**When** rendered
**Then** two value props are clearly visible: (1) cheaper than agencies, (2) available 24/7 — no approval guarantee language anywhere

**Given** the Landing screen
**When** I tap the primary CTA
**Then** `POST /api/application/start` is called, the returned `application_id` and `session_id` are stored in React Context and `localStorage`, and I navigate to Destination Selection with a slide-left transition (250ms easing-default)

**Given** the Landing screen
**When** I attempt to navigate back
**Then** back navigation is disabled — no back chevron shown

**Given** the Destination Selection screen
**When** rendered
**Then** two OptionButtons appear: "Nhật Bản 🇯🇵" and "Trung Quốc 🇨🇳", each full-width min-height 56px, no ProgressBar on this screen

**Given** any screen in the app
**When** built
**Then** all interactive elements have minimum 44×44px tap targets, `lang="vi"` is set on the root `<html>` element, every form error is announced via `aria-live="assertive"`, color is never the sole differentiator for status indicators (icon + color + text always together), and when `prefers-reduced-motion` is enabled slide transitions are replaced with fade-only transitions at 70% reduced distance/duration

**Given** the Landing screen hero area
**When** rendered
**Then** the only permitted gradient is a subtle #1A2E4A → #223A5E on the hero background (max 15% shift) — no decorative gradients anywhere else in the app

---

### Story 1.3: Profile Question Flow

As an applicant,
I want to answer questions about my situation one screen at a time,
So that the system has everything it needs to assess my eligibility.

**Acceptance Criteria:**

**Given** I select a destination
**When** I tap "Nhật Bản" or "Trung Quốc"
**Then** the selection is auto-advanced (no separate Continue tap), `Application.destination` is updated, and I am navigated to Q1

**Given** any profile question screen
**When** rendered
**Then** one question appears per screen (no exceptions), the NavHeader shows a back chevron, the ProgressBar shows the current step in format "Bước N/10", and the question text uses type.h2 with no trailing period

**Given** Q1 (employment type)
**When** rendered
**Then** OptionButtons show: "Nhân viên / Công ty", "Sinh viên", "Chủ doanh nghiệp", "Freelancer / Tự kinh doanh", "Nội trợ", "Đã nghỉ hưu" — and an AI disclosure note in type.caption reads "Câu trả lời này ảnh hưởng đến đánh giá hồ sơ của bạn."

**Given** Q4 (prior visa denial — "Bạn đã từng bị từ chối visa không?")
**When** I select "Có"
**Then** an inline follow-up appears: a date picker and country selector; both must be completed before I can advance; the AI disclosure note appears on this screen

**Given** Q4
**When** I select "Không"
**Then** I auto-advance immediately with no follow-up

**Given** any single-select question
**When** I tap an OptionButton
**Then** the button shows selected state (border 2px #2563EB, bg rgba(37,99,235,0.06), checkmark icon, shadow card-raised) and I auto-advance to the next screen

**Given** any profile question
**When** I tap the back chevron
**Then** I return to the previous question with my prior answer pre-selected

**Given** Q6 (income range — "Thu nhập hàng tháng của bạn khoảng bao nhiêu?")
**When** the screen renders
**Then** the helper note reads exactly: "Thông tin này giúp chúng tôi đánh giá hồ sơ theo kinh nghiệm thực tế. Chúng tôi không tư vấn về số dư ngân hàng tối thiểu vì Đại sứ quán không công bố ngưỡng chính thức." — no specific amount is ever shown or implied

**Given** all profile questions answered (destination, employment type, prior denial, prior stamps, travel dates, passport expiry, income range)
**When** the last answer is submitted
**Then** `PUT /api/application/{id}/profile` is called with the complete `profile_json` and I am navigated to the eligibility loading screen

**Given** any date input (denial date, travel dates, passport expiry)
**When** I enter an invalid date (e.g. past date for travel, future date for denial)
**Then** an inline error appears below the input — not a toast — and I cannot advance until corrected

---

### Story 1.4: AI Eligibility Decision

As an applicant,
I want to receive an AI assessment of my eligibility before paying,
So that I don't waste money on an application that is unlikely to succeed.

**Acceptance Criteria:**

**Given** `profile_json` is complete
**When** I am navigated to the eligibility screen
**Then** `POST /api/application/{id}/eligibility` is called immediately using Claude Haiku

**Given** the eligibility API call is in progress
**When** the call exceeds 3 seconds
**Then** the screen shows a skeleton card with "AI đang đánh giá hồ sơ của bạn..."

**Given** the Haiku call returns `eligible`
**When** the result renders
**Then** an EligibilityCard (pass state) appears: bg #DCFCE7, border 1px #86EFAC, headline type.h2 color #16A34A set to "Hồ sơ của bạn trông tốt ✓", bullet list of positive signals, and disclaimer in type.caption italic: "Đây là đánh giá AI — không phải bảo đảm phê duyệt."

**Given** the Haiku call returns `not_eligible`
**When** the result renders
**Then** an EligibilityCard (fail state) appears: bg #FEE2E2, border 1px #FCA5A5, headline type.h2 color #DC2626, one-sentence plain-Vietnamese reason, the protective statement "Các đại lý vẫn sẽ nhận tiền của bạn — chúng tôi thì không.", and secondary link "Xem cách cải thiện →" that opens a bottom sheet — no Continue CTA, no charge

**Given** the Haiku call returns `edge_case`
**When** the result renders
**Then** an EligibilityCard (edge state) appears: bg #FEF3C7, border 1px #FCD34D, headline color #D97706, StatusChip "Độ tin cậy AI: Trung bình" in warning variant, and two CTAs: "Tiếp tục" (primary) and "Yêu cầu xem xét thủ công" (secondary text)

**Given** `profile_json` contains a Japan visa denial within the last 6 months
**When** the eligibility call runs
**Then** the result is `not_eligible` with a reason explaining the 6-month reapplication waiting period

**Given** `profile_json` contains `employment_type = "freelancer"`
**When** the eligibility call runs
**Then** the result is `edge_case` with lower confidence

**Given** `profile_json` contains prior Japan or China stamps
**When** the eligibility call runs
**Then** the result includes a positive signal noting prior travel history

**Given** travel dates in `profile_json` are within 10 business days of today
**When** the eligibility call runs
**Then** the result is `not_eligible` with a reason explaining insufficient preparation time

**Given** the eligibility result — any outcome
**When** rendered
**Then** the result NEVER states a specific bank balance threshold or minimum income amount

**Given** the eligibility API call fails
**When** the error occurs
**Then** the loading skeleton is replaced with "Không thể đánh giá hồ sơ lúc này. Thử lại hoặc liên hệ hỗ trợ." and two CTAs: Retry and Contact

**Given** an `eligible` or `edge_case` result
**When** rendered
**Then** `Application.eligibility_result` is stored and a "Tiếp tục" CTA in the Bottom Action Area navigates to the Price screen

---

### Story 1.5: Price Display & Placeholder Payment

As an eligible applicant,
I want to see the service price and confirm my commitment,
So that I can unlock my personalized document checklist.

**Acceptance Criteria:**

**Given** an `eligible` or `edge_case` eligibility result
**When** I tap "Tiếp tục"
**Then** I am navigated to the Price screen showing the service fee in a card (bg #FFFFFF, shadow.card, radius 16px, padding 20px)

**Given** the Price screen
**When** rendered
**Then** the destination is confirmed, a summary of what's included is shown, and the language never includes "Đảm bảo", "Chắc chắn được duyệt", or any approval guarantee — approved framing like "Có cơ hội cao" is acceptable

**Given** the Price screen
**When** I tap "Thanh toán"
**Then** a full-screen loading overlay appears, back navigation is disabled, after 1.5 seconds it transitions to a 1-second success state ("Thanh toán thành công"), then auto-navigates to the Document Checklist screen

**Given** the placeholder payment completes
**When** `Application` is updated
**Then** `Application.payment_status = "demo_completed"` and `Application.feasibility_ok = true`

---

## Epic 2: Personalized Document Checklist

After paying, applicant receives their profile-specific, conditional document checklist — not a generic list. Each item tells them exactly what the document must contain and why.

### Story 2.1: Generate Personalized Checklist

As an applicant who has paid,
I want to receive a document checklist tailored to my specific profile,
So that I know exactly what to prepare without guessing.

**Acceptance Criteria:**

**Given** `Application.payment_status = "demo_completed"`
**When** the Checklist screen loads
**Then** `POST /api/application/{id}/checklist` is called using Claude Haiku and a list skeleton (5 rows) shows "Đang tạo danh sách tài liệu..."

**Given** `employment_type = "employee"`
**When** the checklist generates
**Then** the list includes: passport, employment certificate, leave approval letter (with note that travel dates must match application), recent payslips, bank statements — no financial sufficiency statement or balance threshold

**Given** `employment_type = "student"`
**When** the checklist generates
**Then** the list includes: passport, student ID, parent guarantee letter, parent employment certificate, parent bank statements

**Given** `employment_type = "business_owner"`
**When** the checklist generates
**Then** the list includes: passport, business license, company financial statements — not just personal bank statement

**Given** `employment_type = "freelancer"`
**When** the checklist generates
**Then** the list includes a best-effort document set with a prominent advisory chip "Độ tin cậy AI: Trung bình" and notice "Hồ sơ freelancer có độ biến động cao. Nhân viên sẽ kiểm tra lại trước khi nộp."

**Given** the checklist renders
**When** displayed
**Then** each DocumentItem shows: document name (type.body weight 500), what it must contain (type.body-sm, up to 2 lines), accepted format (original/scan/certified copy), StatusChip "pending", and a "Tải lên" action link

**Given** the checklist header
**When** rendered
**Then** it reads "Danh sách này được tạo tự động dựa trên hồ sơ của bạn bởi AI" — no approval guarantee language

**Given** the Haiku checklist call fails
**When** the error occurs
**Then** an inline error with a Retry CTA appears — the user is not permanently blocked

---

### Story 2.2: Checklist Item Detail

As an applicant reviewing their checklist,
I want to understand exactly what each document must contain,
So that I prepare the right version the first time.

**Acceptance Criteria:**

**Given** the checklist is rendered
**When** I tap "Tại sao cần?" on any DocumentItem
**Then** a bottom sheet opens with a plain-Vietnamese explanation of why the embassy requires that specific document

**Given** `employment_type = "employee"` and I view the leave approval letter item
**When** the detail opens
**Then** it explicitly states "Ngày nghỉ phép ghi trong thư phải khớp với ngày đi trong đơn xin visa"

**Given** `employment_type = "student"` and I view the parent guarantee letter item
**When** the detail opens
**Then** it states that the parent's financial documents must accompany the student application

**Given** the Checklist screen
**When** rendered
**Then** the ProgressBar shows "Đã tải lên 0/N tài liệu" where N is the total count of checklist items

**Given** a DocumentItem
**When** I tap "Tải lên"
**Then** the native OS media picker opens (camera or file — no custom camera UI)

---

## Epic 3: Document Upload & AI Review

Applicant uploads their documents, receives Sonnet-powered per-document review, sees an overall readiness score, fixes flagged issues, and submits to the partner agency.

### Story 3.1: Document Upload

As an applicant,
I want to upload each required document from my phone,
So that it can be reviewed by AI before submission.

**Acceptance Criteria:**

**Given** I tap "Tải lên" on a DocumentItem
**When** I select a file from the native picker
**Then** the upload begins: the DocumentItem StatusChip switches to the "processing" variant and the row becomes non-interactive

**Given** the upload succeeds
**When** the file lands on Railway disk
**Then** a `Document` record is created (`application_id`, `doc_type`, `file_path`, `review_status = "pending"`) and the StatusChip switches to the "pending" variant awaiting AI review

**Given** the upload fails (network error or server error)
**When** the error occurs
**Then** an inline message "Tải lên thất bại. Thử lại." appears below the row and the row reverts to its pre-upload state with "Tải lên" action link

**Given** a document has been uploaded successfully
**When** the checklist screen re-renders
**Then** the ProgressBar updates to "Đã tải lên N/M tài liệu"

---

### Story 3.2: AI Document Review

As an applicant,
I want each uploaded document reviewed by AI,
So that I catch problems before the agency submits on my behalf.

**Acceptance Criteria:**

**Given** `Document.review_status = "pending"`
**When** a document upload completes
**Then** `POST /api/application/{id}/documents/{doc_id}/review` is called automatically using Claude Sonnet with the uploaded file

**Given** the Sonnet review returns `pass`
**When** the result is applied
**Then** `Document.review_status = "pass"`, the StatusChip updates to pass variant (bg #DCFCE7, text #16A34A), and the action link changes to "Xem lại"

**Given** the Sonnet review returns `fail`
**When** the result is applied
**Then** `Document.review_status = "fail"`, the StatusChip updates to fail variant (bg #FEE2E2, text #DC2626), and tapping the chip expands the row to show the specific failure reason in type.caption color.error

**Given** the Sonnet review returns `needs_clarification`
**When** the result is applied
**Then** the StatusChip shows the warning variant and the expanded row prompts the user to re-upload or add clarification

**Given** `employment_type = "freelancer"` and the review completes
**When** the result is shown
**Then** the result includes the note "Đánh giá này được thực hiện bởi AI. Nhân viên sẽ kiểm tra lại trước khi nộp."

**Given** a document has `review_status = "fail"`
**When** the Submit CTA is evaluated
**Then** the Submit CTA is disabled until the document is re-uploaded and passes review

**Given** the Sonnet review API call fails
**When** the error occurs
**Then** the DocumentItem shows an error state with a "Thử lại" action — the user can retry without re-uploading

---

### Story 3.3: Readiness Score & Submission

As an applicant whose documents are all reviewed,
I want to see my overall readiness and submit,
So that I can hand off confidently to the partner agency.

**Acceptance Criteria:**

**Given** at least one document has been reviewed
**When** the Checklist screen renders
**Then** a readiness banner appears above the document list summarizing pass/fail/pending counts

**Given** all documents have `review_status = "pass"`
**When** the banner renders
**Then** it reads "Hồ sơ của bạn đã sẵn sàng ✓" (bg #DCFCE7) and the "Xác nhận nộp hồ sơ" CTAButton activates in the Bottom Action Area

**Given** any document has `review_status = "fail"`
**When** the banner renders
**Then** it reads "X vấn đề cần giải quyết trước khi nộp" and the Submit CTA is disabled

**Given** the readiness banner
**When** rendered
**Then** it includes "Đánh giá này được thực hiện bởi AI. Nhân viên sẽ kiểm tra lại trước khi nộp." — no approval guarantee

**Given** all documents pass and I tap "Xác nhận nộp hồ sơ"
**When** confirmed
**Then** `Application.submission_status = "submitted"` and I am navigated to the Status Timeline screen

**Given** the submission confirmation screen
**When** rendered
**Then** back navigation is disabled

---

## Epic 4: Application Status Tracking

Applicant knows what is happening at every stage after submission — from agency receipt through embassy decision — with quota rejection distinguished from profile rejection.

### Story 4.1: Status Timeline

As an applicant who has submitted,
I want to see a live timeline of my application's progress,
So that I'm not in the dark after handing off my documents.

**Acceptance Criteria:**

**Given** `Application.submission_status = "submitted"`
**When** the Status Timeline screen loads
**Then** a 4-node vertical timeline renders: "Tài liệu đã nhận" → "Đã nộp lên Đại sứ quán" → "Đang xử lý" → "Có kết quả"

**Given** the status timeline
**When** the active node renders
**Then** it shows a CSS pulse ring animation (opacity 0→0.4, scale 1→1.6, 1.5s loop, color #2563EB) and completed nodes show filled #16A34A circles

**Given** the status timeline
**When** rendered
**Then** each completed step shows a timestamp (type.caption, text-muted) and the active step shows "Dự kiến: DD/MM/YYYY"

**Given** the Status Timeline screen is open
**When** the screen is active
**Then** `GET /api/application/{id}/status` is polled every 5 minutes; on status change the timeline updates with a 400ms fill animation for the node transition
**And** for demo purposes, status changes are applied manually by the operator via direct SQLite update — no webhook or push mechanism is required in v1

**Given** the Status Timeline screen
**When** rendered
**Then** no ProgressBar is shown, no back chevron is shown, and back navigation is disabled

**Given** the Status Timeline screen
**When** I pull to refresh
**Then** the status is fetched immediately regardless of the poll interval

---

### Story 4.2: Result Notification

As an applicant,
I want to be notified of the embassy's decision with clear next steps,
So that I know exactly what to do after the result.

**Acceptance Criteria:**

**Given** `Application.submission_status = "approved"`
**When** the result renders
**Then** the Result screen shows: headline "Visa của bạn đã được chấp thuận ✓", pickup instructions from the agency, and next steps — no "Chúc mừng!" or celebratory language

**Given** `Application.submission_status = "rejected"`
**When** the result renders
**Then** the Result screen shows: headline "Đơn của bạn chưa được chấp thuận", the embassy-stated reason if provided, and a visible escalation path (link/CTA) to contact a human consultant

**Given** `Application.submission_status = "quota_rejected"`
**When** the result renders
**Then** the Result screen shows the exact required text: "Đại sứ quán đã từ chối đơn của bạn vì đã đủ chỉ tiêu trong đợt này — không phải vì vấn đề hồ sơ cá nhân." — this phrasing is non-negotiable

**Given** any result screen
**When** rendered
**Then** back navigation is disabled and the language never uses "Chúc mừng!", "Tuyệt vời!", or any celebratory framing

---

## Validation Summary

### FR Coverage

| FR | Epic | Story | Status |
|---|---|---|---|
| FR1–FR7 | Epic 1 | 1.3, 1.4 | ✅ Covered |
| FR8 | — | — | ⏸ Deferred post-v1 |
| FR9–FR14 | Epic 2 | 2.1, 2.2 | ✅ Covered |
| FR15 | Epic 2 | — | ⏸ Blocked by Epic 5 deferral |
| FR16–FR21 | Epic 3 | 3.1, 3.2, 3.3 | ✅ Covered |
| FR22–FR24 | Epic 4 | 4.1, 4.2 | ✅ Covered |
| FR25–FR27 | Epic 5 | — | ⏸ Deferred post-v1 |
| FR28–FR31 | Epic 1 | 1.2, 1.4 | ✅ Covered |
| FR32 | Cross-cutting | 3.3 completion | ✅ Covered |

**31 in-scope FRs covered. FR8, FR15, FR25–FR27 deferred to post-v1.**

### NFR Coverage

| NFR | Coverage | Note |
|---|---|---|
| NFR1 (24/7 uptime) | Railway + Vercel deployment | Not story-testable; infra concern |
| NFR2 (latency) | Story 1.4 loading state at 3s | Full < 10s test is integration-level |
| NFR3 (PII handling) | Railway ephemeral disk for demo | Production: swap to Cloudflare R2 |
| NFR4 (auditable AI rules) | Haiku prompt in version-controlled file | Review on every rule change |
| NFR5 (escalation path) | Story 1.4 edge case, Story 4.2 rejection | Human consultant CTA required |
| NFR6 (Vietnamese) | All story ACs use Vietnamese copy | ✅ |

### Story Count

| Epic | Stories | Key user value |
|---|---|---|
| Epic 1 | 5 (1.1–1.5) | Discover + screen eligibility + pay |
| Epic 2 | 2 (2.1–2.2) | Get personalized document list |
| Epic 3 | 3 (3.1–3.3) | Upload + AI review + submit |
| Epic 4 | 2 (4.1–4.2) | Track status + receive result |
| **Total** | **12 stories** | |

### Dependency Chain

1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 2.1 → 2.2 → 3.1 → 3.2 → 3.3 → 4.1 → 4.2

Each story depends only on stories before it. No forward dependencies. ✅
