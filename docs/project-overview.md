# Project Overview — Visa Flow (AI Visa Consulting)

**Sản phẩm:** Web app tư vấn xin visa du lịch (Nhật Bản, Trung Quốc) cho khách Việt Nam của **Sông Hàn Tourist** (đại lý ủy thác chính thức). Khách tự đi qua flow: khai hồ sơ → AI đánh giá khả năng đậu → thanh toán (demo) → OCR giấy tờ → checklist tài liệu + AI review từng file → gửi hồ sơ cho tư vấn viên → theo dõi tiến trình → tải form MOFA đã điền sẵn. Kèm chatbot Thu Diễm hỗ trợ xuyên suốt.

**Mục đích bộ docs này:** cho Claude session sau hiểu toàn bộ sản phẩm để thiết kế eval plan (xem `index.md` để điều hướng).

## Cấu trúc

- **Kiểu repo:** multi-part, 2 phần: `api` (Python/FastAPI) + `client` (React 19/Vite 8)
- **AI:** Anthropic SDK 0.86 — Haiku (`claude-haiku-4-5-20251001`) cho chat/eligibility/itinerary, Sonnet (`claude-sonnet-4-6`) cho vision (OCR, document review)
- **Deploy:** Railway, SQLite, không auth (demo-grade)

## 8 AI surfaces (đối tượng chính của eval plan)

| Surface | Hàm (`api/ai.py`) | Model | Bản chất |
|---|---|---|---|
| Eligibility | `assess_eligibility` | Haiku | LLM đánh giá khả năng đậu — có phép đếm ngày (rủi ro logic) |
| Checklist | `generate_checklist` | — | **Deterministic** từ `static/checklists/*.json` (không LLM) |
| Document review | `review_document_image` | Sonnet | Vision pass/fail/needs_clarification từng tài liệu |
| OCR giấy tờ | `extract_id_info` | Sonnet | Trích passport/CCCD → personal_info |
| Chat (Thu Diễm) | `chat_with_haiku` | Haiku | Hợp đồng hành vi đầy đủ: `chatbot-behavior-spec.md` |
| Itinerary | `suggest_itinerary_chat`, `generate_itinerary` | Haiku | Chat gợi ý (VN) + data form (EN); ⚠️ bug forms.py → luôn 7 ngày |
| Admin verify checklist | `verify_checklist` | Sonnet | Không system prompt, không auth |
| Agents pipeline (legacy) | `agents/pipeline.py` (6 agent) | Haiku+Sonnet | Chấm hồ sơ đa agent — chỉ gọi qua `/api/v1/cases`, input **mock OCR** |

## Phát hiện trọng yếu cho eval (từ deep scan 2026-07-14)

1. **Bug thật:** `forms.py:130-134` — `json.loads()` trên dict → itinerary trong PDF luôn fallback 7 ngày bất kể chuyến đi thật
2. **Compliance:** form PDF tự tick "No" cả 6 câu tiền án (`form_filler.py:411-432`) — không hỏi khách
3. **Bảo mật:** IDOR toàn cục (session_id không kiểm tra); admin endpoints không auth; CORS mở
4. **Vận hành:** railway.toml không khai volume → redeploy có thể mất DB + uploads
5. **Test:** e2e `checklist_skip.spec.ts` helper lỗi thời so UI thật (khả năng fail toàn suite); pytest không có trong venv
6. **Kiến trúc:** 2 thế hệ backend song song — client chỉ dùng `routers/`; `routes/` + `agents/` là legacy sống nhưng chạy mock
7. Dead code: `PersonalInfoModal.jsx`; reload = mất flow (chỉ applicationId/sessionId persist)

## Tài liệu liên quan có sẵn từ trước

- `project-context.md` — quy ước dev cho AI (đọc đầu session)
- `docs/chatbot-behavior-spec.md` — hợp đồng hành vi chatbot (persona, FACTS, 10 guardrails, regression seeds)
- `_bmad-output/implementation-artifacts/` — specs từng story + `deferred-work.md` (việc treo)
- `~/docs/vi-ux-style-guide.md` — style guide copy tiếng Việt
- `~/japan-visa-bot/` — dự án chị em: nguồn kiến thức (knowledge_base, personas.json eval format)
