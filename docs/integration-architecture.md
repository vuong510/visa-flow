# Integration Architecture — Visa Flow

Cách 2 part giao tiếp và dữ liệu chảy end-to-end. Cập nhật 2026-07-14.

## Tổng quan

- **client → api:** REST/JSON qua `fetch`, base URL `API_BASE` (AppContext). Không GraphQL, không WebSocket, không streaming.
- **Auth:** KHÔNG có. `session_id` UUID sinh ở client (localStorage) nhưng backend **không bao giờ kiểm tra**; `applicationId` là int tự tăng → **IDOR toàn cục** (đã ghi deferred-work). Eval/pentest cần tính đến.
- **CORS:** mở hoàn toàn (`api/main.py`).

## Điểm tích hợp theo bước flow

| # | Màn (client) | Endpoint | AI surface | Ghi chú |
|---|---|---|---|---|
| 1 | landing → destination | `POST /api/application` | — | Tạo application mới (reload = tạo mới, ghi đè ID cũ) |
| 2 | profile-questions Q1-Q6 | `PUT /api/application/{id}/profile` | — | Ngày đi/về là Q3 (không có màn TripForm riêng) |
| 3 | eligibility | `POST /api/application/{id}/eligibility` | `assess_eligibility` (Haiku) | StrictMode dev có thể double-POST |
| 4 | price | `POST /api/application/{id}/payment` | — | Demo payment, không gate thật |
| 5 | form-filling (4 sub-step) | `POST /api/extract-id` | `extract_id_info` (Sonnet vision) | OCR hộ chiếu/CCCD → personal_info |
| 6 | checklist | `POST /api/application/{id}/checklist` | `generate_checklist` (deterministic) | Cache vào `checklist_json`, không invalidate |
| 7 | checklist (upload) | `POST /api/application/{id}/documents` → `POST .../documents/{doc_id}/review` | `review_document_image` (Sonnet vision) | PDF → PNG trang 1 qua PyMuPDF |
| 8 | checklist (skip) | `POST .../documents/skip` / `unskip` | — | Optimistic UI, revert khi server từ chối |
| 9 | checklist (submit) | `POST /api/application/{id}/submit` | — | → status-timeline |
| 10 | mọi màn (trừ price) | `POST /api/chat` | `chat_with_haiku` (Haiku) | Context: `{destination, screen, profile, applicationId, visit_purpose}`; server tự bơm `checklist_json`; nhánh keyword "gợi ý/lịch trình" → `suggest_itinerary_chat` |
| 11 | chat (lưu itinerary) | `PATCH /api/application/{id}/itinerary` | — | Từ ChatWidget khi user chốt lịch trình |
| 12 | status-timeline / tải form | `POST /api/application/{id}/forms/download` | `generate_itinerary` (Haiku) nếu chưa cache | Trả ZIP 2 PDF MOFA đã điền (`form_filler.py`); ⚠️ bug `forms.py:130-134` json.loads trên dict → itinerary luôn fallback 7 ngày |

## Luồng dữ liệu chéo đáng chú ý (cho eval)

1. **`static/checklists/{destination}.json` nuôi 3 nơi:** endpoint checklist (UI), system prompt chat (section CHECKLIST HỒ SƠ), và gián tiếp form download. Sửa JSON = đổi hành vi cả 3 — ground truth duy nhất.
2. **`travel_dates` do user nhập chảy vào:** description checklist (nội suy `{departure}`) → UI + chat prompt (đã sanitize 1 dòng/cap độ dài) → form PDF. Chuỗi injection-surface đã vá một phần.
3. **Chat "nhìn thấy" gì:** context client gửi (sanitized ≤40 ký tự) + `checklist_json` server-side + FACTS trong prompt. Chat KHÔNG thấy: eligibility result, trạng thái upload từng tài liệu, personal_info.
4. **Legacy không tích hợp:** `/api/v1/cases` (agents pipeline) và `policies`/`cv-jobs` không được client gọi; pipeline nhận **mock OCR** thay vì file thật → nếu muốn eval agents pipeline phải gọi API trực tiếp, không qua UI.

## Hợp đồng chung

- Client parse lỗi qua `res.ok` + message tiếng Việt trong `detail`.
- JSON columns (`profile_json`, `checklist_json`, `travel_dates`, `personal_info`) là hợp đồng shape ngầm giữa 2 part — xem `docs/data-models-api.md`.
- Model AI cấu hình tại `core/config.py`: Haiku = rẻ/nhanh (eligibility, chat, itinerary), Sonnet = vision (OCR, review) — quy ước trong `project-context.md`.
