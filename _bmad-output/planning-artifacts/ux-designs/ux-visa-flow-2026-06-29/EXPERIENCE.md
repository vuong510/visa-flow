---
title: VisaFlow — Experience & Behavior Specification
product: "AI Visa Consulting — Japan & China"
platform: "MoMo mini app (iOS / Android) + responsive web"
version: 0.1.0
status: draft
updated: 2026-06-29
cross-reference: DESIGN.md
---

# VisaFlow Experience Specification

## 1. Foundation

**Platform:** MoMo mini app. The product runs inside the MoMo iOS and Android container as a mini app. It is also accessible as a standalone responsive web page for non-MoMo users.

**Viewport:** Design target is 375px width (iPhone SE). Content is capped at 430px max-width and centered on wider displays. No horizontal scrolling anywhere.

**Language:** Vietnamese throughout. All UI copy, error messages, system states, and microcopy are in Vietnamese. Internal admin/operator tools may be English.

**Orientation:** Portrait only. The flow does not support landscape — do not implement landscape layouts.

**Operating environment assumptions:**
- Touch-first interaction (no hover states as primary feedback)
- MoMo wallet is available for payment (the user already has MoMo — this is a MoMo mini app)
- Camera access is required for document upload (request permission at the upload step, not upfront)
- Network may be unreliable — all loading states must handle failure gracefully

**Core design constraint:** The product is AI-powered and must always say so. AI disclosure is not a compliance footnote — it is a brand promise. See §Voice and Tone for how to phrase it.

---

## 2. Information Architecture

### Full Screen Inventory

| # | Screen | Gate type | Reversible? |
|---|---|---|---|
| 01 | Landing | — | — |
| 02 | Destination Picker | — | Yes |
| 03–08 | Profile Questions (6 screens) | — | Yes, via Back |
| 09 | Eligibility Result | Pre-payment gate 1 | Pass → continue; Fail → educational exit |
| 10 | Travel Dates | — | Yes |
| 11 | Feasibility Check | Pre-payment gate 2 | Pass → continue; Fail → date adjustment offered |
| 12 | Price Screen | — | Yes |
| 13 | Payment (MoMo wallet) | Payment gate | No — payment is final |
| 14 | Document Checklist | — | Yes |
| 15 | Document Upload | — | Yes, per item |
| 16 | AI Review | — | Automatic |
| 17 | Fix Loop | — | Yes, per item |
| 18 | Submit to Agency | — | No — submission is final |
| 19 | Status Timeline | — | Passive / informational |
| 20 | Result | — | Passive / informational |

### Navigation rules

- Back navigation is available on every screen except 01 (Landing), 13 (Payment confirmation), 18 (Submit), 19 (Status Timeline), and 20 (Result).
- Back on screens 03–08 returns to the previous question — answers are preserved in session state.
- After Payment (screen 13), the user cannot go back to change profile, dates, or destination. The service has been purchased.
- The NavHeader back chevron is the only back mechanism. Do not add swipe-back on screens where back is disabled.

### Deep link entry points

| Entry | Lands on | Context |
|---|---|---|
| MoMo mini app cold open | Screen 01 — Landing | Fresh session |
| "Track my application" notification | Screen 19 — Status Timeline | Requires auth |
| "Your document has an issue" notification | Screen 17 — Fix Loop | Requires auth, links to specific document |

---

## 3. Voice and Tone

### Character

VisaFlow speaks like a knowledgeable colleague who works inside an immigration office — not a government official, and not a salesperson. The voice is:

- **Calm:** No exclamation points except where absolutely necessary. No "Amazing!" or "Looks great!"
- **Direct:** State the fact first, then the reason. Not "Due to the regulations that the embassy enforces..." but "Đại sứ quán Nhật Bản yêu cầu..." then the consequence.
- **Protective:** When something is wrong, the product says so before the user spends money. It frames this as protection, not rejection.
- **Honest about AI:** Always says "AI" when referring to its own assessments. Never implies human review when it is AI. Never implies certainty when there is none.

### Confidence language rules

The product **never** uses:
- "Đảm bảo" (guaranteed)
- "Chắc chắn được duyệt" (definitely approved)
- "Tôi đảm bảo" (I promise)
- Specific bank balance thresholds stated as official embassy policy

The product **uses instead:**
- "Hồ sơ của bạn trông tốt" (your profile looks good) — not "sẽ được duyệt"
- "Có cơ hội cao" (strong chance) — not "chắc chắn"
- "Đáp ứng yêu cầu thông thường" (meets typical requirements) — not "đủ điều kiện tuyệt đối"
- "Theo kinh nghiệm của chúng tôi..." (based on our experience) when citing patterns

### AI transparency phrases

Use these consistently across all AI-generated outputs:

| Context | Phrase |
|---|---|
| Eligibility result header | "Đây là đánh giá AI — không phải bảo đảm phê duyệt" |
| Document checklist intro | "Danh sách này được tạo tự động dựa trên hồ sơ của bạn bởi AI" |
| Document review result | "Đánh giá này được thực hiện bởi AI. Nhân viên sẽ kiểm tra lại trước khi nộp." |
| Lower confidence case | "Độ tin cậy AI: Trung bình — hồ sơ loại này cần xem xét thêm" |
| Freelancer escalation | "AI đề nghị xem xét thủ công cho hồ sơ của bạn" |

### Microcopy patterns

**Eligibility pass (quiet signal — not celebration):**
> Hồ sơ của bạn trông tốt ✓

**Eligibility fail (protective framing):**
> Chúng tôi phát hiện một vấn đề ⚠
> [Specific reason in one sentence]
> Các đại lý vẫn sẽ nhận tiền của bạn — chúng tôi thì không.

**Japan 6-month reapplication ban (specific case):**
> Theo quy định của Đại sứ quán Nhật Bản, bạn cần chờ đủ 6 tháng kể từ lần bị từ chối gần nhất trước khi nộp đơn lại. Dựa trên thông tin bạn cung cấp, bạn chưa đủ thời gian chờ.
> Xem khi nào bạn có thể nộp lại →

**Feasibility block (date too close):**
> Thời gian xử lý thị thực Nhật Bản thường mất 5–9 ngày làm việc. Với ngày khởi hành của bạn, chúng tôi không thể đảm bảo hồ sơ kịp xử lý.
> Ngày khởi hành sớm nhất có thể: [date]
> [Điều chỉnh ngày] [Thoát]

**Freelancer lower-confidence:**
> Hồ sơ của bạn có thể được duyệt, nhưng hồ sơ tự do/freelancer thường khó đánh giá hơn. AI của chúng tôi đề nghị xem xét thủ công để tăng độ chính xác.

**Quota rejection (distinct from profile rejection):**
> Đại sứ quán đã từ chối đơn của bạn vì đã đủ chỉ tiêu trong đợt này — không phải vì vấn đề hồ sơ cá nhân. Đây là quyết định hành chính, không phản ánh chất lượng hồ sơ của bạn.

**Document fail (specific):**
> Giấy xác nhận công việc: Thiếu ngày nghỉ phép khớp với ngày đi. Cần cập nhật và tải lại.

### Phrases to avoid

| Avoid | Because |
|---|---|
| "Chúc mừng! Bạn đủ điều kiện!" | Too celebratory — calm confidence is the target tone |
| "Hồ sơ của bạn hoàn hảo" | "Perfect" implies 100% certainty — AI cannot know this |
| "Số dư ngân hàng tối thiểu là X triệu đồng" | Embassy does not publish this threshold — fabricates policy |
| "Bạn cần nạp thêm tiền vào tài khoản" | Financial coaching violates embassy rules |
| "Chúng tôi đảm bảo thành công" | Never promise approval |
| "AI đã xác nhận hồ sơ hợp lệ" | "Confirmed valid" overstates AI certainty |
| "Điền vào form bên dưới" | Cold, bureaucratic — use "Trả lời câu hỏi bên dưới" |

---

## 4. Component Patterns

### ProgressBar behavior

- Step count covers the pre-payment portion of the flow (screens 02–12) as "Bước X/10" where 10 = destination + 6 questions + eligibility + dates + feasibility + price.
- After payment, re-label as "Hồ sơ của bạn" phase — progress bar shows document upload completion as a percentage fill ("Đã tải lên 3/7 tài liệu").
- Never show "100%" on a progress bar unless the user has genuinely completed everything — do not pre-fill to create false momentum.

### ProfileQuestion behavior

- One question per screen. Do not put two questions on one screen.
- Auto-advance to next screen when a single-select OptionButton is tapped — do not require a separate "Continue" tap for single-select questions.
- Exception: Q4 (prior denial history) — if user selects "Có" (yes), a follow-up date input appears inline before advancing. The question does not auto-advance until both the yes/no answer and the date are provided.
- Input validation happens on advance, not on tap. Show error inline below the input, not as a toast.

### EligibilityCard behavior

- The pass/fail/edge state is determined server-side before the screen renders. Do not animate a "calculating..." fake delay beyond the natural API response time.
- If API is slow (> 3s), show a loading skeleton for the card with the caption "AI đang đánh giá hồ sơ của bạn..."
- The card's CTA is always below the card, in the Bottom Action Area — not embedded in the card.
- On fail state: the "Xem cách cải thiện" link opens a bottom sheet with educational content. It does not navigate away from the result screen.
- On edge state: two CTAs in the Bottom Action Area. Primary: "Tiếp tục" (continue with lower-confidence flag). Secondary text CTA: "Yêu cầu xem xét thủ công" (routes to human escalation queue).

### DocumentItem behavior

- Tapping the row expands it. Tap again or tap outside to collapse.
- Upload action: opens the native OS media picker (camera or file — user chooses). Do not build a custom camera UI.
- Upload in progress: replace StatusChip with "processing" variant and a small spinner. Row is non-interactive during upload.
- After AI review completes per document: StatusChip updates to pass/fail. On fail, row auto-expands to show failure reason inline.
- A document with status "fail" cannot be submitted. The Submit CTA in the Bottom Action Area remains disabled until all required documents are "pass."
- Optional documents (marked with "(Tùy chọn)") do not block submission if absent.

### StatusTimeline behavior

- Data is polled every 5 minutes while the screen is active. Do not require a manual refresh.
- On status change: the active node transitions with a brief 400ms fill animation (pending → active) or (active → completed).
- If result is "Rejected — quota," the final node reads "Từ chối do hết chỉ tiêu" and the card below explains this is an administrative decision, not a profile issue. This language is distinct from profile rejection.
- If result is "Approved," the final node turns `{color.success}` and a bottom card shows pickup instructions (location, hours, what to bring).

---

## 5. State Patterns

### Empty states

| Screen | Empty condition | Message |
|---|---|---|
| Document Checklist | No documents uploaded yet | "Bạn chưa tải lên tài liệu nào. Bắt đầu với tài liệu đầu tiên trong danh sách." |
| Status Timeline | Application just submitted | "Hồ sơ của bạn đã được gửi. Chúng tôi sẽ thông báo khi có cập nhật." |

Empty states always include a next action. No dead-end empty screens.

### Loading states

| Trigger | Loading UI |
|---|---|
| Eligibility API call | Card skeleton with "AI đang đánh giá hồ sơ của bạn..." caption |
| Checklist generation | List skeleton (5 rows), "Đang tạo danh sách tài liệu..." caption |
| Document AI review | Per-item StatusChip shows "processing" variant; overall: "AI đang kiểm tra tài liệu của bạn" |
| MoMo payment processing | Full-screen loading overlay, "Đang xử lý thanh toán..." — do not allow back navigation |
| Status Timeline poll | Subtle inline refresh indicator — do not replace timeline with full skeleton |

Loading states use `{motion.duration-slow}` fade-in (400ms). Never flash loading states for sub-300ms operations.

### Error states

**Network error (any screen):**
- Toast at bottom: "Không có kết nối. Kiểm tra mạng và thử lại."
- Retry button in toast
- Toast persists until dismissed or connection restored

**API error on eligibility gate:**
- Replace EligibilityCard skeleton with: "Không thể đánh giá hồ sơ lúc này. Thử lại hoặc liên hệ hỗ trợ."
- Two CTAs: "Thử lại" (primary) | "Liên hệ hỗ trợ" (secondary)

**Document upload failure:**
- Inline below DocumentItem: "Tải lên thất bại. Thử lại."
- Row reverts to "pending" StatusChip

**Payment failure:**
- Full screen: "Thanh toán không thành công." + reason from MoMo + "Thử lại"
- Do not lose the user's profile data — session is preserved

### Success states

- **Eligibility pass:** EligibilityCard with `{color.success}` styling — calm, not celebratory. No confetti. No animation beyond the card fade-in.
- **Payment success:** Brief 1-second success screen ("Thanh toán thành công ✓") then automatic transition to Document Checklist. No lingering on the success screen.
- **Document AI review — all pass:** "Hồ sơ của bạn đã sẵn sàng" banner at top of checklist screen. Submit CTA becomes active.
- **Application submitted:** Transition to Status Timeline with a top banner: "Hồ sơ của bạn đã được gửi. Chúng tôi sẽ thông báo khi có cập nhật."

---

## 6. Interaction Primitives

### Tap targets

- Minimum tap target: 44×44px for all interactive elements (WCAG 2.5.5 AAA / Apple HIG minimum).
- OptionButtons: full-width rows — the entire row is the tap target, not just the label.
- DocumentItem rows: the expand tap target is the entire row. The "Tải lên" link inside the row is a separate tap target — ensure they do not overlap when the row is collapsed.
- StatusChip on NavHeader: 44×44px tap area even though the chip is visually 24px tall.

### Transitions

| Transition | Type | Duration | Easing |
|---|---|---|---|
| Screen push (forward) | Slide left | 250ms | `{motion.easing-default}` |
| Screen pop (back) | Slide right | 200ms | `{motion.easing-exit}` |
| Bottom sheet open | Slide up + fade scrim | 300ms | `{motion.easing-spring}` |
| Bottom sheet close | Slide down + fade scrim | 250ms | `{motion.easing-exit}` |
| OptionButton select | Scale 0.98 + border animate | 150ms | `{motion.easing-default}` |
| ProgressBar fill | Width expand | 250ms | `{motion.easing-default}` |
| StatusChip change | Cross-fade | 250ms | `{motion.easing-default}` |
| Card fade-in on load | Opacity 0 → 1, translateY 8px → 0 | 300ms | `{motion.easing-default}` |

### Haptic feedback (MoMo mini app)

- OptionButton tap: light impact (iOS: UIImpactFeedbackGenerator .light)
- CTAButton tap: medium impact
- Eligibility result reveal: medium impact (pass) or warning notification feedback (fail)
- Payment confirmation: success notification feedback
- Document review fail: error notification feedback

### Pull-to-refresh

- Enabled only on Status Timeline (screen 19). No other screen supports pull-to-refresh.
- On refresh: inline spinner in NavHeader, timeline data refetched.

---

## 7. Accessibility Floor

The following are minimum requirements — not aspirational goals.

| Requirement | Implementation |
|---|---|
| Color is never the sole differentiator | Every StatusChip uses icon + color + text label. Every EligibilityCard state uses icon + color + headline. |
| Touch target minimum | 44×44px on all interactive elements — see §6 |
| Text contrast | `{color.text-primary}` on `{color.surface}`: 17.9:1. `{color.text-muted}` on `{color.surface}`: 4.6:1. `{color.cta}` on `{color.surface}`: 4.6:1. All pass WCAG AA. |
| Keyboard / assistive navigation | All interactive elements are reachable via VoiceOver (iOS) and TalkBack (Android). Tab order follows visual reading order top to bottom. |
| Vietnamese screen reader support | Use lang="vi" on the root element. Test with VoiceOver Vietnamese voice — diacritics must be read correctly. |
| Dynamic text | Layout must not break when iOS/Android text size is set to "Larger Accessibility Sizes" (+3 steps). Use relative font units. |
| Error communication | Every form error is announced via `aria-live="assertive"` region, not just styled with color. |
| Motion | Respect `prefers-reduced-motion`. Replace slide transitions with simple fade when enabled. Keep functional animations (progress bar, status pulse) but reduce distance and duration by 70%. |

---

## 8. Key Flows

### Minh's Journey — Full Flow Walkthrough

**Who is Minh:** 28 years old. Works at a software company in Hanoi. Planning a 10-day trip to Japan with two friends. He's never been to Japan before. He looked at traditional agencies and felt uneasy — the fees seemed high and no one could give him a straight answer about whether his profile was strong enough. He found VisaFlow on MoMo at 10:30pm on a Tuesday.

---

#### Screen 01 — Landing

Minh opens the mini app. He does not see a form.

He sees a value pitch with two propositions:
1. "Rẻ hơn đại lý truyền thống" — cheaper than traditional agencies
2. "Sẵn sàng 24/7 — không cần đợi giờ làm việc" — available at 10:30pm

Below the pitch: a short AI disclosure. "Dịch vụ này sử dụng AI để đánh giá hồ sơ và kiểm tra tài liệu. Kết quả được giải thích rõ ràng." This is not hidden in a footer — it is in the body of the landing screen.

CTA: "Kiểm tra hồ sơ miễn phí" — the eligibility check costs nothing. Minh does not need to create an account before checking.

Design notes:
- Background: subtle `{color.primary}` → `#223A5E` gradient on the top hero area (max 15% shift). Cards below on `{color.background}`.
- No carousels, no feature lists beyond the two value props, no testimonials in v1.
- The AI badge in NavHeader is present even on Landing.

---

#### Screen 02 — Destination Picker

Two destination cards side by side:

```
┌───────────┐  ┌───────────┐
│  🇯🇵      │  │  🇨🇳      │
│  Nhật Bản │  │  Trung    │
│           │  │  Quốc    │
└───────────┘  └───────────┘
```

Below destination: visa type selector (Tourist / Business) appears after destination is tapped.

Minh taps "Nhật Bản" → "Du lịch." Auto-advance after both are selected.

---

#### Screens 03–08 — Profile Questions

Six questions, one per screen. ProgressBar shows "Bước X/10."

**Q1 — Loại hình công việc** (Employment type)
Options: Nhân viên công ty, Sinh viên, Chủ doanh nghiệp, Tự do/Freelancer, Nội trợ, Đã nghỉ hưu.
AI disclosure note shown: "Câu trả lời này ảnh hưởng đến đánh giá hồ sơ của bạn."
Minh selects "Nhân viên công ty." Auto-advance.

**Q2 — Mục đích chuyến đi** (Travel purpose)
Options: Du lịch, Thăm người thân/bạn bè, Công tác.
Minh selects "Du lịch." Auto-advance.

**Q3 — Lịch sử đi nước ngoài** (Prior international travel)
Question: "Bạn đã từng có dấu visa hoặc tem nhập cảnh nước ngoài chưa?"
Options: Chưa bao giờ, Đã đi (không phải Nhật/Trung), Đã đi Nhật Bản hoặc Trung Quốc.
Minh selects "Đã đi (không phải Nhật/Trung)." This is a mild positive signal. Auto-advance.

**Q4 — Lịch sử bị từ chối visa** (Prior denial — critical question)
Question: "Bạn đã từng bị từ chối visa bao giờ chưa?"
AI disclosure note: "Câu trả lời này rất quan trọng với đánh giá hồ sơ của bạn."
Options: Chưa bao giờ, Có.
If "Có" is selected: a follow-up date input appears inline — "Lần từ chối gần nhất: [MM/YYYY]" and a country selector "Bị từ chối bởi quốc gia nào?" The advance button becomes available only after both sub-fields are filled.

*Why this matters — Japan 6-month ban:* If user reports a Japan visa denial within the last 6 months, the system flags this for the eligibility gate. This is a hard rule — the gate will block regardless of other positive signals. The system will calculate the elapsed time server-side from the reported month and compare to the application date.

Minh selects "Chưa bao giờ." Auto-advance.

**Q5 — Hiệu lực hộ chiếu** (Passport validity)
Question: "Hộ chiếu của bạn còn hiệu lực đến khi nào?"
Input: date picker (MM/YYYY). Validation: passport must be valid at least 6 months beyond the travel period. If expiry is too soon, a soft warning inline: "Hộ chiếu của bạn có thể hết hạn trong thời gian xử lý visa." Does not block at this point — will factor into eligibility gate.
Minh enters a date 3 years out. Auto-advance.

**Q6 — Thu nhập hàng tháng** (Monthly income range)
Question: "Thu nhập hàng tháng của bạn vào khoảng bao nhiêu?"
Options: Dưới 10 triệu, 10–20 triệu, 20–40 triệu, Trên 40 triệu.
Note below: "Thông tin này giúp chúng tôi đánh giá hồ sơ theo kinh nghiệm thực tế. Chúng tôi không tư vấn về số dư ngân hàng tối thiểu vì Đại sứ quán không công bố ngưỡng chính thức."

*This constraint is non-negotiable:* The system uses income range as a profile pattern signal only. It does not output a specific threshold or advise the user to adjust their bank balance. The note on this question makes the constraint explicit to the user.

Minh selects "20–40 triệu." Auto-advance.

---

#### Screen 09 — Eligibility Result (The climax)

This is the moment of truth for Minh — and the moment that defines the product's value.

The screen transitions in. The EligibilityCard fades in over 400ms (no fake "calculating" animation — the API call was made during the previous question transition).

**Minh's result: Pass.**

```
┌─────────────────────────────────────────────────────┐
│  ✓  Hồ sơ của bạn trông tốt                        │
│                                                     │
│  Các tín hiệu tích cực:                             │
│  • Nhân viên công ty — hồ sơ rõ ràng               │
│  • Có kinh nghiệm du lịch nước ngoài                │
│  • Hộ chiếu còn hiệu lực đủ dài                     │
│  • Chưa có lịch sử từ chối visa                     │
│                                                     │
│  Đây là đánh giá AI — không phải bảo đảm phê duyệt │
└─────────────────────────────────────────────────────┘
```

The headline is `{type.h1}`, `{color.success}`. Not "Chúc mừng!" Not "Tuyệt vời!" Just: "Hồ sơ của bạn trông tốt." A doctor's tone.

Haptic feedback: medium impact.

Bottom Action Area CTA: "Tiếp tục — nhập ngày đi"

**Alternative: Minh's result — Fail (Japan 6-month ban scenario)**

```
┌─────────────────────────────────────────────────────┐
│  ⚠  Chúng tôi phát hiện một vấn đề                 │
│                                                     │
│  Bạn bị từ chối visa Nhật Bản 4 tháng trước.        │
│  Đại sứ quán Nhật Bản yêu cầu chờ đủ 6 tháng       │
│  trước khi nộp đơn lại.                             │
│                                                     │
│  Các đại lý vẫn sẽ nhận tiền của bạn —             │
│  chúng tôi thì không.                               │
│                                                     │
│  Xem khi nào bạn có thể nộp lại →                  │
└─────────────────────────────────────────────────────┘
```

Bottom Action Area: No payment CTA. Single secondary CTA: "Xem cách cải thiện" → opens bottom sheet with next steps.

The protective statement ("Các đại lý vẫn sẽ nhận tiền của bạn — chúng tôi thì không.") is not self-promotional. It is framing the fail as protection. It must appear on every hard fail state.

**Alternative: Edge case — Freelancer**

EligibilityCard shows warning state. Below it, confidence badge: "Độ tin cậy AI: Trung bình."

Two CTAs: Primary "Tiếp tục" | Secondary "Yêu cầu xem xét thủ công"

If Minh chooses manual review: his profile is queued for a human consultant. Estimated response time shown ("Thường trong 1 ngày làm việc"). He does not proceed to the payment flow until the human review is complete.

---

#### Screen 10 — Travel Dates

Two date pickers: "Ngày khởi hành" and "Ngày về."

Date pickers use the native OS date picker component — do not build a custom calendar widget.

Validation:
- Return date must be after departure date
- Trip must not be longer than the visa validity window (Japan tourist: typically 15 or 30 days — flag if trip exceeds this)
- Minimum lead time check feeds Screen 11

CTA: "Tiếp tục"

---

#### Screen 11 — Feasibility Check

Server-side: calculates business days between today and departure date, accounting for weekends. Japan tourist processing is 5–9 business days plus agency preparation time.

**Pass state:**
```
┌─────────────────────────────────────────────────────┐
│  ✓  Có đủ thời gian xử lý                          │
│                                                     │
│  Ngày khởi hành: 25/08/2026                        │
│  Thời gian xử lý ước tính: 5–9 ngày làm việc       │
│  Hạn chót nộp hồ sơ: 12/08/2026                   │
│                                                     │
│  Hãy hoàn thành hồ sơ và tải tài liệu trước ngày  │
│  này để đảm bảo kịp.                               │
└─────────────────────────────────────────────────────┘
```

**Fail state (dates too close):**
```
┌─────────────────────────────────────────────────────┐
│  ⚠  Thời gian không đủ                             │
│                                                     │
│  Ngày khởi hành của bạn là 05/07/2026. Chúng tôi   │
│  không thể đảm bảo hồ sơ kịp xử lý.               │
│                                                     │
│  Ngày khởi hành sớm nhất có thể: 18/07/2026        │
└─────────────────────────────────────────────────────┘
```

Two CTAs on fail: "Điều chỉnh ngày đi" (goes back to Screen 10) | "Thoát" (exits flow, no charge)

---

#### Screen 12 — Price Screen

Displayed only after both gates pass. Not before.

```
┌─────────────────────────────────────────────────────┐
│  Phí dịch vụ                                        │
│                                                     │
│  Visa Nhật Bản — Du lịch                           │
│  ——————————————————————————                         │
│  Đánh giá hồ sơ AI           Miễn phí              │
│  Tạo danh sách tài liệu       Miễn phí              │
│  Kiểm tra tài liệu bằng AI   Bao gồm               │
│  Nộp hồ sơ qua đại lý        Bao gồm               │
│  Theo dõi trạng thái          Bao gồm               │
│  ——————————————————————————                         │
│  Tổng cộng                    XXX.000 VNĐ           │
│                                                     │
│  Phí đại sứ quán trả riêng (không qua chúng tôi)  │
└─────────────────────────────────────────────────────┘
```

- "Đánh giá hồ sơ AI" and "Tạo danh sách tài liệu" shown as free — they happened before payment to demonstrate value first.
- Embassy fee is explicitly separated — VisaFlow does not handle it.
- Visa fee amount is a placeholder (XXX.000 VNĐ) — fill from config before launch.

CTA: "Tiếp tục thanh toán"

---

#### Screen 13 — Payment (MoMo wallet)

Delegates to MoMo's native payment UI. VisaFlow does not build a custom payment screen — it triggers the MoMo mini app payment SDK.

On success: brief success screen (1 second), then auto-transition to Screen 14.

On failure: error screen from MoMo SDK is shown, then "Thử lại" returns to Screen 12.

---

#### Screen 14 — Document Checklist

Generated per Minh's profile (Nhân viên công ty, Du lịch, Japan). The checklist is not generic — it is specific to his employment type.

Example items for Minh's profile:
1. Hộ chiếu bản gốc + 2 bản sao
2. Ảnh thẻ (2 ảnh, nền trắng, 4×3cm)
3. Đơn xin visa (mẫu Nhật Bản, điền đủ)
4. Giấy xác nhận công việc (có ngày nghỉ phép khớp ngày đi)
5. Sao kê tài khoản ngân hàng (3 tháng gần nhất)
6. Vé máy bay (xác nhận đặt chỗ)
7. Đặt phòng khách sạn
8. Bảo hiểm du lịch (khuyến nghị)

Each item shows a DocumentItem component with StatusChip "pending."

The "Giấy xác nhận công việc" item has a prominent note: "Ngày nghỉ phép trong thư phải khớp đúng ngày 25/08–04/09/2026 theo đơn xin visa của bạn." This is pulled from the travel dates Minh entered on Screen 10.

CTA at bottom: "Bắt đầu tải tài liệu" — navigates into the upload flow, starting with item 1.

---

#### Screens 15–17 — Upload, AI Review, Fix Loop

**Upload (Screen 15):**
- One document at a time, guided flow. Minh taps a DocumentItem and is taken to the upload screen for that specific item.
- Upload screen shows: document name, what it must contain, acceptable format (original / scan / photo), and a large upload zone.
- Camera or file picker — OS native, not custom.
- On upload: StatusChip changes to "processing," AI review triggers immediately.

**AI Review (Screen 16):**
- Results appear per document as they complete — not as a single batch reveal.
- Overall readiness banner appears when all required items have been reviewed:
  - All pass: "Hồ sơ của bạn đã sẵn sàng ✓" — Submit CTA activates
  - Issues found: "X tài liệu cần sửa" — Submit CTA remains disabled

**Fix Loop (Screen 17):**
- Minh's bank statement is flagged: "Sao kê ngân hàng: Không thể đọc chữ ở trang 2. Vui lòng tải lại ảnh rõ hơn."
- He re-uploads. AI re-reviews. StatusChip updates.
- There is no limit on re-upload attempts.
- A document that passes after a fix does not revert unless the user explicitly deletes and replaces it.

---

#### Screen 18 — Submit to Agency

Pre-submission summary:
- Destination and visa type
- Applicant name (pulled from profile)
- Number of documents: X/X uploaded and verified
- Processing estimate

Disclosure card:
> "Hồ sơ của bạn sẽ được nộp bởi một đại lý được phép của chúng tôi. Đây là yêu cầu bắt buộc của Đại sứ quán Nhật Bản — tất cả hồ sơ phải được nộp qua đại lý được ủy quyền."

CTA: "Xác nhận nộp hồ sơ"

After confirmation: transition to Screen 19.

---

#### Screen 19 — Status Timeline

Minh's waiting period. The product's job here is to reduce anxiety, not to fill silence with platitudes.

StatusTimeline component with four nodes. Active node pulses.

At the top: estimated result date. "Dự kiến có kết quả: 10/09/2026"

A note below the timeline: "Đại sứ quán không cung cấp lý do từ chối chi tiết trong hầu hết các trường hợp. Chúng tôi sẽ thông báo ngay khi có kết quả."

Push notifications are triggered at each status transition. Notification copy matches the timeline step language exactly.

---

#### Screen 20 — Result

**Approved:**
```
✓  Visa của bạn đã được phê duyệt

Hướng dẫn nhận visa:
• Địa điểm: [Agency address]
• Giờ làm việc: [Hours]
• Mang theo: Hộ chiếu bản gốc + biên lai

Thời hạn nhận: [Date]
```

**Rejected — profile basis:**
```
⚠  Đơn visa của bạn không được phê duyệt

[Reason if embassy provided one — or "Đại sứ quán không cung cấp lý do chi tiết."]

Chúng tôi sẽ hỗ trợ bạn đánh giá lại hồ sơ và 
cải thiện cho lần nộp tiếp theo nếu bạn muốn.

[Đánh giá lại hồ sơ →]
```

**Rejected — quota:**
```
ℹ  Đại sứ quán đã từ chối do hết chỉ tiêu

Đây không phải vấn đề hồ sơ của bạn. Đại sứ quán 
có giới hạn số lượng visa mỗi đợt — hồ sơ của 
bạn đáp ứng yêu cầu nhưng không nằm trong đợt này.

Bạn có thể nộp lại trong đợt tiếp theo. Chúng tôi 
sẽ liên hệ khi có thể tiếp nhận hồ sơ mới.
```

The quota rejection screen must not feel like a product failure. The language clearly separates structural (embassy quota) from substantive (profile issue) rejection. This distinction matters for brand trust and user retention.

---

## Appendix A — Eligibility Gate Rules Summary

| Signal | Source | Pass condition | Fail condition | Note |
|---|---|---|---|---|
| Employment type | Q1 | All types except flagged | Freelancer → edge, not hard fail | Freelancer triggers lower-confidence path |
| Prior denial — Japan | Q4 | No denial, or denial > 6 months ago | Japan denial within last 6 months | Hard block — 6-month ban is official embassy rule |
| Prior denial — other country | Q4 | No denial | Recent denial of any country | Soft flag only — not a hard block |
| Passport validity | Q5 | Valid ≥ 6 months beyond trip return date | Expires before or during trip + 6mo buffer | Warn if borderline, block if invalid |
| Travel history | Q3 | Prior stamps to any country | No history | Positive signal only — absence is not a fail |
| Prior Japan/China stamp | Q3 | Yes | N/A — positive signal only | Raises AI confidence score |
| Financial profile | Q6 | Income range collected — pattern signal only | N/A — no hard threshold stated | Cannot advise specific amounts per embassy rules |
| Travel date feasibility | Screen 10+11 | Departure ≥ [processing days + buffer] from today | Too soon | Hard block before payment |

### What the eligibility gate cannot do

- State a specific bank balance minimum as official policy
- Coach users to increase their bank balance before applying
- Guarantee approval for any profile
- Bypass the gate for any reason once a Japan 6-month ban is detected
- Assess group/family compound profiles differently per member without explicit group mode (v1 handles each applicant individually — group mode is out of scope)
