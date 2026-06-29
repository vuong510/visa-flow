---
title: 'Chat Support Widget'
type: 'feature'
created: '2026-06-29'
status: 'in-progress'
baseline_commit: '4d7e51e321b0b1a795a33fa1c216783cd967baf2'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users hit dead ends inside the wizard — they don't understand a document requirement or how to obtain it, and have no way to ask questions without leaving the app.

**Approach:** Add a floating chat button (all screens, z-index 20) that opens a multi-turn AI panel powered by Haiku. The backend receives the message + conversation history + user context (destination, current screen, profile summary) so answers are personalized, not generic.

## Boundaries & Constraints

**Always:**
- Use Haiku (`claude-haiku-4-5-20251001`) — not Sonnet. Chat is high-frequency, cost must stay low.
- Chat history stored in component state only — never persisted to DB.
- Backend must never reveal specific bank balance thresholds or embassy policy numbers (same rule as eligibility gate — AD-7).
- Widget renders on all screens including Landing.
- Multi-turn: full history sent with every request so Haiku has context.

**Ask First:**
- If Haiku response exceeds a reasonable length (>400 chars), consider truncating — confirm approach with user before implementing a hard truncation.

**Never:**
- Persist chat history to database.
- Use Sonnet for chat responses.
- Replace or modify the existing wizard flow.
- Add a separate page/route for chat — it must be an overlay.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy path | User sends question with destination=japan, screen=checklist | Haiku reply referencing Japan visa context | N/A |
| No context yet | User sends question on Landing (no destination/profile) | Haiku gives generic visa consulting answer | N/A |
| Empty input | User taps Send with empty field | Do nothing — no API call | N/A |
| API error | Network failure or 5xx | Display "Có lỗi xảy ra, thử lại nhé." in chat | Inline error, keep history intact |
| Long conversation | 20+ turns in history | Send full history — no client-side truncation | N/A |

</frozen-after-approval>

## Code Map

- `api/ai.py` — add `chat_with_haiku(messages, context)` helper following existing Haiku call pattern
- `api/routers/chat.py` — new router: `POST /api/chat`
- `api/main.py` — include chat router at prefix `/api`
- `visa-client/src/components/ChatWidget.jsx` — floating button + collapsible panel, multi-turn UI
- `visa-client/src/App.jsx` — mount `<ChatWidget />` as sibling to `<Router />` inside `<AppProvider>`
- `visa-client/src/context/AppContext.jsx` — read-only: source of `destination`, `profile`, `screen` for context payload

## Tasks & Acceptance

**Execution:**
- [ ] `api/ai.py` -- add `chat_with_haiku(messages: list, context: dict) -> str` using `HAIKU`; system prompt instructs Haiku to act as a visa consulting assistant for Vietnamese users, use context dict (destination, screen, profile summary) to personalize, never disclose specific financial thresholds
- [ ] `api/routers/chat.py` -- create `POST /api/chat` accepting `{message: str, history: [{role, content}], context: {screen, destination, profile}}`, call `chat_with_haiku`, return `{reply: str}`
- [ ] `api/main.py` -- include chat router: `app.include_router(chat_router, prefix="/api")`
- [ ] `visa-client/src/components/ChatWidget.jsx` -- floating button fixed bottom-right (z-index 20, above NavHeader z-index 10); clicking opens panel; panel shows conversation history + input; on send: POST to `${API_BASE}/api/chat` with message + history + context from `useApp()`; show loading state while waiting; append reply to history; use design tokens (`--color-primary`, `--color-cta`, `--color-surface`, `--shadow-modal`, `--radius-card`)
- [ ] `visa-client/src/App.jsx` -- add `<ChatWidget />` as sibling to `<Router />` inside `<AppProvider>` wrapper

**Acceptance Criteria:**
- Given any screen, when user taps the floating chat button, then the chat panel opens as an overlay above all content
- Given panel open, when user types a message and taps Send, then a loading indicator appears and Haiku responds within 10s
- Given a response, when user's destination is set, then the reply references that destination context
- Given an empty input, when user taps Send, then nothing happens (no API call)
- Given an API error, when response fails, then "Có lỗi xảy ra, thử lại nhé." appears inline in the chat
- Given 3+ turns of conversation, when user sends another message, then full history is included and Haiku maintains continuity

## Design Notes

**Floating button:** 56×56px circle, `--color-cta` background, chat icon (💬 or SVG), fixed `bottom: 24px; right: 20px`. When panel open, button becomes ✕.

**Panel:** Slides up from bottom or appears as a card `bottom: 88px; right: 20px; width: 320px; max-height: 480px`. Header "Hỏi về visa", scrollable message list, sticky input row at bottom.

**Message bubbles:** User messages right-aligned (`--color-cta` bg, white text). Assistant messages left-aligned (`--color-surface` bg, border).

## Verification

**Commands:**
- `cd visa-client && npm run build` -- expected: build succeeds with no errors
- `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message":"Xin visa Nhật cần giấy tờ gì?","history":[],"context":{"screen":"landing","destination":null,"profile":null}}'` -- expected: `{"reply": "..."}` with non-empty string

**Manual checks:**
- Open app, tap chat button on Landing screen → panel opens
- Send "Tôi muốn xin visa Nhật" → Haiku replies in Vietnamese
- Send follow-up "Giấy xác nhận việc làm lấy ở đâu?" → reply maintains context from previous turn
- Close panel, navigate to another screen, reopen → history preserved within session
