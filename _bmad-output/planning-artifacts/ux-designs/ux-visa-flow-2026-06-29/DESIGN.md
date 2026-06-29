---
# ── Meta ──────────────────────────────────────────────────────────────────────
title: VisaFlow Design System
product: "AI Visa Consulting — Japan & China"
platform: "MoMo mini app (iOS / Android) + responsive web"
version: 0.1.0
status: draft
updated: 2026-06-29

# ── Design Tokens ─────────────────────────────────────────────────────────────
tokens:
  color:
    primary:          "#1A2E4A"   # deep navy — authority, trust, official
    cta:              "#2563EB"   # electric blue — interactive, progress, action
    cta-hover:        "#1D4ED8"
    cta-pressed:      "#1E40AF"
    surface:          "#FFFFFF"
    background:       "#F5F7FA"   # light gray canvas — breathing room between cards
    success:          "#16A34A"
    success-light:    "#DCFCE7"
    success-border:   "#86EFAC"
    warning:          "#D97706"
    warning-light:    "#FEF3C7"
    warning-border:   "#FCD34D"
    error:            "#DC2626"
    error-light:      "#FEE2E2"
    error-border:     "#FCA5A5"
    text-primary:     "#1A1A2E"
    text-secondary:   "#374151"
    text-muted:       "#6B7280"
    text-inverse:     "#FFFFFF"
    text-link:        "#2563EB"
    border:           "#E5E7EB"
    border-focus:     "#2563EB"
    border-strong:    "#D1D5DB"
    overlay:          "rgba(26, 46, 74, 0.48)"
    scrim:            "rgba(0, 0, 0, 0.32)"

  typography:
    family: "'Be Vietnam Pro', system-ui, -apple-system, 'Helvetica Neue', sans-serif"
    # Be Vietnam Pro is preferred — warm rounded letterforms, full Vietnamese diacritic support.
    # Falls back to system-ui: SF Pro on iOS, Roboto on Android — both acceptable.
    scale:
      h1:      { size: "24px", weight: 700, line-height: 1.30, letter-spacing: "-0.01em" }
      h2:      { size: "20px", weight: 600, line-height: 1.35 }
      h3:      { size: "17px", weight: 600, line-height: 1.40 }
      body-lg: { size: "16px", weight: 400, line-height: 1.55 }
      body:    { size: "15px", weight: 400, line-height: 1.55 }
      body-sm: { size: "14px", weight: 400, line-height: 1.50 }
      caption: { size: "13px", weight: 400, line-height: 1.45 }
      label:   { size: "12px", weight: 500, line-height: 1.40, letter-spacing: "0.02em" }

  radius:
    card:   "16px"
    button: "12px"
    input:  "10px"
    chip:   "20px"
    modal:  "20px"
    tag:    "6px"
    avatar: "50%"

  spacing:
    xs:            "4px"
    sm:            "8px"
    md:            "16px"
    lg:            "24px"
    xl:            "32px"
    xxl:           "48px"
    screen-h-pad:  "20px"   # horizontal padding on all full-bleed screens
    screen-v-pad:  "24px"   # top/bottom padding below nav header
    card-inner:    "20px"   # padding inside a card
    stack-tight:   "8px"    # between closely related items
    stack-loose:   "16px"   # between independent items
    section-gap:   "24px"   # between card sections on a screen

  shadow:
    none:        "none"
    card:        "0 1px 3px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.04)"
    card-raised: "0 4px 12px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.06)"
    modal:       "0 16px 48px rgba(26, 46, 74, 0.20)"
    nav:         "0 1px 0 #E5E7EB"

  motion:
    duration-fast:  "150ms"
    duration-base:  "250ms"
    duration-slow:  "400ms"
    easing-default: "cubic-bezier(0.2, 0, 0, 1)"
    easing-spring:  "cubic-bezier(0.34, 1.56, 0.64, 1)"
    easing-exit:    "cubic-bezier(0.4, 0, 1, 1)"

  breakpoint:
    target:      "375px"    # iPhone SE — design at this width
    max-content: "430px"    # cap content width on larger screens
---

# VisaFlow Design System

## 1. Brand & Style

VisaFlow is a **service**, not a government counter.

The product exists because agencies take money from ineligible applicants. VisaFlow does not. That honesty is the brand. Every design decision must reinforce it: clear information over decorative confidence; calm over excitement; protection over salesmanship.

**Design character:** Warm but official. Trustworthy but not cold. Clinical but not bureaucratic. The emotional reference is a good doctor delivering a clear diagnosis — not a chatbot, not a travel agency promotional banner.

**What the product is not:**
- Not playful — avoid emojis as decoration, bright gradients, bounce animations
- Not cold — avoid all-caps form labels, dense bureaucratic layouts, gray walls of text
- Not startup-casual — avoid "Hey there! Let's get started 🎉" copy or overly informal microcopy

**Visual references:** MoMo, Grab, Techcombank — card-based, high-contrast CTAs, clean separation of information zones. Airbnb's checkout flow is a useful reference for trust-building on step screens.

**AI identity:** The product is AI-powered and says so. The AI badge in the NavHeader is permanent — never hidden, never reduced to fine print. This is a brand asset, not a disclaimer.

**Voice:** Calm. Direct. Protective. See EXPERIENCE.md §Voice and Tone for full microcopy rules.

---

## 2. Colors

### Primary Palette

| Token | Value | Use |
|---|---|---|
| `color.primary` | `#1A2E4A` | NavHeader background, primary text on dark, brand identity |
| `color.cta` | `#2563EB` | All interactive elements: primary buttons, links, progress fill, focus rings, selected states |
| `color.surface` | `#FFFFFF` | Card backgrounds, input fields, modal surfaces |
| `color.background` | `#F5F7FA` | Screen canvas behind cards — always this, never bare white |

### Semantic Palette

| Token | Value | Use |
|---|---|---|
| `color.success` | `#16A34A` | Pass state labels, success icons, timeline completed nodes |
| `color.success-light` | `#DCFCE7` | EligibilityCard pass background tint |
| `color.warning` | `#D97706` | Edge case badges, lower-confidence indicators, timeline pending |
| `color.warning-light` | `#FEF3C7` | EligibilityCard edge case background tint |
| `color.error` | `#DC2626` | Fail state labels, document review fail icons |
| `color.error-light` | `#FEE2E2` | EligibilityCard fail background tint, input error state |

### Text

| Token | Value | Use |
|---|---|---|
| `color.text-primary` | `#1A1A2E` | All primary body text |
| `color.text-secondary` | `#374151` | Secondary descriptions, sub-labels |
| `color.text-muted` | `#6B7280` | Placeholder text, helper copy, timestamps |
| `color.text-inverse` | `#FFFFFF` | Text on `color.primary` or `color.cta` backgrounds |

### Borders

| Token | Value | Use |
|---|---|---|
| `color.border` | `#E5E7EB` | Default card border, input border, dividers |
| `color.border-focus` | `#2563EB` | Input focus ring (2px, not inset) |
| `color.border-strong` | `#D1D5DB` | Selected option button border |

### Accessibility

- `color.cta` (#2563EB) on `color.surface` (#FFF): contrast 4.6:1 — passes WCAG AA for UI components and large text. Use weight 600 on interactive button labels.
- `color.text-primary` (#1A1A2E) on `color.surface`: 17.9:1 — passes AAA.
- `color.text-muted` (#6B7280) on `color.surface`: 4.6:1 — passes AA for body text at 15px+.
- `color.success` (#16A34A) on `color.success-light` (#DCFCE7): 4.5:1 — passes AA.

---

## 3. Typography

**Font family:** Be Vietnam Pro (weights 400, 500, 600, 700). Load via Google Fonts. System-ui fallback is acceptable — layout does not break.

**Principles:**
- Vietnamese requires full diacritic support. Be Vietnam Pro covers all tone marks and vowel combinations. Do not substitute decorative fonts that drop diacritics.
- No weight below 400 anywhere. Thin weights feel fragile — wrong for an authority product.
- Line-height minimum 1.45 everywhere. Vietnamese tone marks extend above cap height — tight leading clips them.
- No text smaller than 13px on any user-facing screen.

### Type Scale

| Token | Size / Weight | Line-height | Use |
|---|---|---|---|
| `type.h1` | 24px / 700 | 1.30 | Screen titles — eligibility result headline, landing hero |
| `type.h2` | 20px / 600 | 1.35 | Card titles, question prompts |
| `type.h3` | 17px / 600 | 1.40 | Sub-section headers, NavHeader title |
| `type.body-lg` | 16px / 400 | 1.55 | Primary body copy, option button labels |
| `type.body` | 15px / 400 | 1.55 | Supporting body text, list items |
| `type.body-sm` | 14px / 400 | 1.50 | Document item descriptions, helper text |
| `type.caption` | 13px / 400 | 1.45 | Timestamps, AI disclaimer, fine print |
| `type.label` | 12px / 500 | 1.40 | Status chip labels, badge labels |

---

## 4. Layout & Spacing

**Canvas:** 375px wide. All content within `spacing.screen-h-pad` (20px) horizontal margins. Content never touches screen edges.

**Max content width:** 430px — center and clip on wider viewports. Do not stretch card layouts.

**Screen anatomy (top to bottom):**

```
┌─────────────────────────────────┐  ← OS status bar
│ NavHeader (56px)                │
├─────────────────────────────────┤
│ ProgressBar (4px)               │  ← only on multi-step screens
├─────────────────────────────────┤
│                                 │
│  screen-v-pad: 24px             │
│                                 │
│  Content cards, stacked         │
│  with section-gap: 24px         │
│                                 │
│  screen-v-pad: 24px             │
│                                 │
├─────────────────────────────────┤
│ Bottom Action Area              │  ← CTAButton always here
│ (safe area + 80px)              │
└─────────────────────────────────┘
```

**Card layout:**
- All content lives inside white cards (`color.surface`, `shadow.card`, `radius.card` 16px)
- Cards have `spacing.card-inner` (20px) padding on all sides
- Cards stack with `spacing.section-gap` (24px) between them
- No full-bleed content except NavHeader and ProgressBar

**Bottom Action Area:**
- Fixed to viewport bottom
- White background, 1px top border (`color.border`)
- Padding: 16px top/bottom, 20px sides
- CTAButton is always full-width here
- Add `env(safe-area-inset-bottom)` — do not obscure iOS home indicator

---

## 5. Elevation & Depth

Three levels only. Do not create additional shadow variants.

| Level | Token | Use |
|---|---|---|
| 0 — Flat | `shadow.none` | Background, section labels, dividers |
| 1 — Card | `shadow.card` | Standard content cards, list items |
| 2 — Raised | `shadow.card-raised` | Active/selected cards, OptionButton selected state |
| 3 — Modal | `shadow.modal` | Bottom sheets, dialogs |

Depth communicates interactivity and selection — not decoration. Raised shadows appear only when something is selected or active, never as a default style.

---

## 6. Shapes

| Component | Token | Value | Rationale |
|---|---|---|---|
| Cards | `radius.card` | 16px | Friendly, modern — matches MoMo card language |
| Buttons | `radius.button` | 12px | Slightly less than cards — feels actionable |
| Input fields | `radius.input` | 10px | Approachable without being pill-shaped |
| Chips / badges | `radius.chip` | 20px | Fully pill — distinguishes from other surfaces |
| Modals / sheets | `radius.modal` | 20px | Top-left + top-right only on bottom sheets |
| Tags | `radius.tag` | 6px | Subtle — does not compete with chips |

All values are larger than standard form defaults. The rounded language signals warmth. Do not reduce them "for a more professional look" — the decision is intentional.

---

## 7. Components

### NavHeader

```
┌─────────────────────────────────────┐
│  ← Back    [Screen Title]   [AI]   │
└─────────────────────────────────────┘
```

- Height: 56px
- Background: `color.primary` (#1A2E4A)
- Back chevron: left-aligned, 44×44px tap target, `color.text-inverse`
- Title: center-aligned, `type.h3`, `color.text-inverse`
- AI badge: right-aligned, permanent pill — label "AI", `color.cta` background, `color.text-inverse` text, `radius.chip`. Tap opens informational modal: "Dịch vụ này sử dụng AI để đánh giá hồ sơ của bạn. Kết quả được giải thích rõ ràng và không phải là bảo đảm phê duyệt."
- Do not hide the AI badge on any screen. Do not replace it with a different icon on result screens.
- No hamburger menu, no notification bell. The header carries three elements only.

---

### ProgressBar

```
[████████░░░░░░░░░░░░░░░░] Bước 4/10
```

- Height: 4px, flush below NavHeader
- Track: `color.border`
- Fill: `color.cta`
- Step label: right-aligned, above bar or inline right of bar, `type.caption`, `color.text-muted`. Format: "Bước 4/10"
- Fill width transitions over `motion.duration-base` (250ms) using `motion.easing-default`
- Present on: all flow screens after Landing. Absent on: Landing, Status Timeline.

---

### EligibilityCard

Used on the eligibility result screen. Three states:

**Pass state:**
```
┌─────────────────────────────────────────────────────┐  color.success-light bg
│  ✓  Hồ sơ của bạn trông tốt                        │  h2, color.success
│                                                     │
│  Các tín hiệu tích cực:                             │  body, color.text-secondary
│  • Có lịch sử du lịch nước ngoài                   │
│  • Loại hình công việc phù hợp                      │
│  • Hộ chiếu còn hiệu lực đủ dài                     │
│                                                     │
│  Đây là đánh giá AI — không phải bảo đảm phê duyệt │  caption, color.text-muted
└─────────────────────────────────────────────────────┘
```
- Background: `color.success-light` | Border: 1px `color.success-border`
- Headline: `type.h2`, `color.success`
- Bullet list: `type.body`, `color.text-primary`
- Disclaimer: `type.caption`, `color.text-muted`, italic

**Fail state:**
```
┌─────────────────────────────────────────────────────┐  color.error-light bg
│  ⚠  Chúng tôi phát hiện một vấn đề                 │  h2, color.error
│                                                     │
│  [Specific plain-language reason — one sentence]    │  body-lg, color.text-primary
│                                                     │
│  Các đại lý vẫn sẽ nhận tiền của bạn —             │  body, color.text-secondary
│  chúng tôi thì không.                               │
│                                                     │
│  Xem cách cải thiện →                               │  body, color.text-link
└─────────────────────────────────────────────────────┘
```
- Background: `color.error-light` | Border: 1px `color.error-border`
- Headline: `type.h2`, `color.error`
- Reason: one clear sentence in plain Vietnamese, no jargon
- Secondary CTA link: `color.text-link`, not a button — this is guidance, not a purchase action

**Edge / Lower-confidence state (e.g., Freelancer):**
```
┌─────────────────────────────────────────────────────┐  color.warning-light bg
│  ◐  Hồ sơ của bạn có thể được duyệt               │  h2, color.warning
│                                                     │
│  Nhưng cần xem xét thêm. Hồ sơ tự do/freelancer    │  body, color.text-primary
│  thường có mức độ chắc chắn thấp hơn.               │
│                                                     │
│  [Độ tin cậy AI: Trung bình]  ← StatusChip warning  │
└─────────────────────────────────────────────────────┘
```
- Background: `color.warning-light` | Border: 1px `color.warning-border`
- Headline: `type.h2`, `color.warning`
- Two CTAs below card: Primary "Tiếp tục" + Secondary "Yêu cầu xem xét thủ công"

---

### ProfileQuestion

Wrapper for each of the 6 profile question screens.

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  [Question text]                    type.h2         │
│                                                     │
│  [Helper text — optional]           type.body-muted │
│                                                     │
│  [OptionButton]                                     │
│  [OptionButton]                                     │
│  [OptionButton]                                     │
│  ...                                                │
│                                                     │
│  [AI note if question feeds gate]   type.caption    │
└─────────────────────────────────────────────────────┘
```

- Question text: `type.h2`, no trailing period
- Helper text: `type.body`, `color.text-muted`, optional
- AI disclosure note: `type.caption`, `color.text-muted`. Example: "Câu trả lời này ảnh hưởng đến đánh giá hồ sơ của bạn"
- Show disclosure note on questions Q3 (prior denial) and Q1 (employment type) — these feed the eligibility gate directly

---

### OptionButton

Single-select answer button for ProfileQuestion screens.

**Default state:**
- Full width, min-height 56px
- Background: `color.surface`
- Border: 1px `color.border`
- Border-radius: `radius.button` (12px)
- Label: `type.body-lg`, `color.text-primary`, left-aligned with 16px left padding
- Optional right icon: 20px, `color.text-muted`

**Selected state:**
- Border: 2px `color.cta`
- Background: `rgba(37, 99, 235, 0.06)`
- Label: `color.cta`
- Right icon replaced by checkmark: `color.cta`
- Shadow: `shadow.card-raised`

**Disabled state:**
- Background: `color.background`
- Label: `color.text-muted`
- Border: `color.border`

Press animation: scale(0.98) for `motion.duration-fast` (150ms).

---

### CTAButton

Primary action button. Always full-width inside the Bottom Action Area.

**Primary:**
- Height: 52px
- Background: `color.cta`
- Border-radius: `radius.button` (12px)
- Label: `type.body-lg`, weight 600, `color.text-inverse`, centered
- No shadow — CTA buttons sit in a fixed zone, not floating

**Hover/Pressed:** Background `color.cta-pressed`, scale(0.98) for 150ms

**Disabled:** Background `color.border`, label `color.text-muted`, non-interactive

**Loading:** Background `color.cta`, label replaced by 20px white spinner, non-interactive

**Secondary (text variant):**
- Background: transparent, no border
- Label: `color.cta`, `type.body-lg`, weight 500
- Use for secondary actions below primary CTA only (e.g., "Xem cách cải thiện" on fail state)

---

### StatusChip

Small pill badge for inline status signals.

| Variant | Background | Text color | Border | Use |
|---|---|---|---|---|
| `pass` | `color.success-light` | `color.success` | `color.success-border` | Document pass, eligibility signal positive |
| `fail` | `color.error-light` | `color.error` | `color.error-border` | Document fail, gate blocked |
| `warning` | `color.warning-light` | `color.warning` | `color.warning-border` | Lower confidence, edge case |
| `pending` | `color.background` | `color.text-muted` | `color.border` | Not yet reviewed |
| `processing` | `rgba(37,99,235,0.08)` | `color.cta` | `rgba(37,99,235,0.20)` | In AI review |

- Height: 24px | Padding: 0 10px | Radius: `radius.chip` (20px)
- Label: `type.label` (12px / 500)
- Optional leading icon: 12px, same color as label text

---

### DocumentItem

List row for checklist and document review screens.

```
┌─────────────────────────────────────────────────────┐
│  [Doc icon]  Giấy xác nhận công việc  [StatusChip] │
│              Cần có: thời hạn, chức vụ, chữ ký     │
│              Tải lên ↑                              │
└─────────────────────────────────────────────────────┘
```

- Min-height: 72px | Padding: `spacing.md` (16px) all sides
- Icon: 40×40px rounded square (`radius.tag` 6px), `color.background` fill
- Primary label: `type.body`, `color.text-primary`, weight 500
- Sub-label: `type.body-sm`, `color.text-muted`, up to 2 lines
- StatusChip: right-aligned to primary label row
- Action link ("Tải lên" / "Xem lại"): `type.body-sm`, `color.text-link`
- Fail expansion: tapping a "fail" chip expands the row to show specific failure reason in `type.caption`, `color.error`, below sub-label
- Row separator: 1px `color.border` except below last item

---

### StatusTimeline

Vertical timeline for post-submission tracking.

```
  ●  Đã nhận hồ sơ               [Hoàn thành]    ← color.success node
  │
  ●  Đã nộp lên Đại sứ quán      [Hoàn thành]
  │
  ◉  Đang xử lý                  [Đang xử lý]    ← color.cta node, pulse ring
  │
  ○  Có kết quả                  [Chờ]            ← color.border node
```

- Node size: 14px circle
  - Completed: filled `color.success`
  - Active: filled `color.cta` + CSS pulse ring animation (opacity 0→0.4, scale 1→1.6, 1.5s loop)
  - Pending: `color.border` fill, `color.border-strong` stroke
- Connector line: 2px `color.border`, dotted on completed→active gap
- Step label: `type.body`, `color.text-primary` (completed/active) or `color.text-muted` (pending)
- StatusChip: right-aligned per row
- Timestamp: `type.caption`, `color.text-muted`, below label — shown on completed steps only
- Estimated date: below active step label, `type.caption`, `color.text-muted`. Format: "Dự kiến: DD/MM/YYYY"

---

## 8. Do's and Don'ts

### Visual

**Do:**
- Use `color.background` (#F5F7FA) as the screen canvas. Never render content on bare white without a card container.
- Use card elevation (`shadow.card`) to group related information into scannable units.
- Give every interactive element a minimum 44×44px tap target — even small chip components.
- Reserve `color.cta` for actionable elements only — progress fill, buttons, links, selected states.
- Keep the AI badge in `color.cta`. It signals transparency, not warning.

**Don't:**
- Do not use gradients on primary UI elements. The one exception: Landing hero background may use a subtle `color.primary` → `#223A5E` gradient (max 15% shift).
- Do not mix semantic colors decoratively — success green is only for success states, error red is only for errors.
- Do not use text smaller than 13px anywhere user-facing.
- Do not introduce additional border-radius values. The existing scale covers all cases.
- Do not use full-screen modal overlays for content that belongs on its own screen step.

### Copy & Tone

**Do:**
- Write question labels in sentence case, no trailing period: "Loại hình công việc của bạn là gì"
- Write button labels as action verbs: "Tiếp tục", "Tải lên", "Xác nhận nộp hồ sơ"
- State AI confidence level on every AI-generated result. "Đây là đánh giá AI — không phải bảo đảm" belongs on every EligibilityCard.
- Use full Vietnamese diacritics everywhere — do not strip tones for character count.

**Don't:**
- Do not write "Chúc mừng!" or "Tuyệt vời!" — tone is calm, not celebratory.
- Do not write "được đảm bảo" or "chắc chắn được duyệt." The product never promises approval.
- Do not state specific bank balance thresholds. Embassy policy does not publish minimums. Stating a specific number fabricates official policy and violates embassy rules.
- Do not use ALL CAPS for any label, error, or button text.
- Do not use dark patterns: no countdown timers creating false urgency, no fake social proof ("X người đang nộp đơn ngay bây giờ").
