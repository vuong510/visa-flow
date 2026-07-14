# Kiến trúc Backend — Visa Flow

> Đọc giả: session Claude sau cần thiết kế eval plan. Mọi claim kèm `file:line`. Cập nhật: 2026-07-14.

## Executive summary

Visa Flow là API FastAPI đơn tiến trình (monolith) cho sản phẩm tư vấn visa du lịch Nhật/Trung của Sông Hàn Tourist. Backend chứa **2 thế hệ sản phẩm song song**:

1. **Luồng consumer hiện hành** (`api/routers/*`, prefix `/api`): tạo Application → profile → eligibility (Haiku) → thanh toán demo → checklist (deterministic) → upload/review tài liệu (Sonnet vision) → điền PDF MOFA → submit → theo dõi trạng thái. Kèm chatbot Thu Diễm.
2. **Pipeline multi-agent cũ** (`api/routes/__init__.py`, prefix `/api/v1`): 6 agents (Gatekeeper→Inspector→Detective∥Navigator→Analyst, + Librarian quản lý policy) chấm hồ sơ demo với **mock OCR** — chưa từng được document, vẫn được mount trong `api/main.py:35`.

Không có auth ở bất kỳ endpoint nào (xem `docs/api-contracts-api.md`).

## Tech stack

| Thành phần | Phiên bản | Nguồn |
|---|---|---|
| Python + FastAPI | fastapi==0.135.2 | `requirements.txt:4` |
| SQLAlchemy (ORM) | 2.0.48 | `requirements.txt:1` |
| anthropic SDK | 0.86.0 | `requirements.txt:3` |
| PyMuPDF (điền PDF) | >=1.24.0 | `requirements.txt:9` |
| pypdf (đọc text CV) | 6.9.2 | `requirements.txt:8` |
| httpx (fetch web admin + jobs API) | 0.28.1 | `requirements.txt:5` |
| psycopg2-binary (Postgres option) | 2.9.11 | `requirements.txt:6` |
| uvicorn | 0.42.0 | `requirements.txt:13` |
| Deploy | Railway, nixpacks, `uvicorn api.main:app`, healthcheck `/health` | `railway.toml:1-8` |
| Model Sonnet | `claude-sonnet-4-6` (const `SONNET`) | `core/config.py:6` |
| Model Haiku | `claude-haiku-4-5-20251001` (const `HAIKU`) | `core/config.py:7` |

## Entry point + middleware

- App tạo tại `api/main.py:21-26`; `lifespan` gọi `init_db()` (create_all + migration ALTER TABLE thủ công, `db/session.py:10-21`).
- **CORS mở hoàn toàn**: `allow_origins=["*"]`, mọi method/header (`api/main.py:28-33`). Không có middleware nào khác (không auth, không rate-limit, không logging).
- Router mount: `/api/v1` (agents cũ + cv-jobs) `api/main.py:35-36`; `/api` (5 router hiện hành) `api/main.py:37-41`.
- Serve frontend React build từ `visa-client/dist` + SPA fallback catch-all `api/main.py:43-62` (fallback nuốt mọi path lạ, trả index.html).

## AI SURFACES (phần quan trọng nhất cho eval)

Tất cả client Anthropic khởi tạo module-level: `api/ai.py:15`, `api/routers/admin.py:10`, `api/routes/cv_jobs.py:15`, `agents/base.py:6`.

### 1. Eligibility assessment — `assess_eligibility` (`api/ai.py:30-76`)
- **Model**: Haiku, max_tokens 1024. **LLM áp luật deterministic** — prompt tiếng Việt inline (`ai.py:36-66`) chứa 4 luật cứng: từ chối <180 ngày cùng nước → not_eligible; khởi hành <10 ngày làm việc → not_eligible; freelancer → edge_case; còn lại eligible. **Phép đếm ngày làm việc giao cho LLM** — điểm eval quan trọng.
- Input: `profile_json`, `travel_dates`, `destination` (từ DB). Output JSON: `result/headline/bullets/reason/confidence_label`; headline eligible phải đúng nguyên văn "Hồ sơ của bạn trông tốt ✓" (`ai.py:57`). Cấm nêu ngưỡng số dư (`ai.py:66`).
- Gọi từ `POST /api/application/{id}/eligibility` (`api/routers/application.py:77-94`), kết quả lưu `eligibility_result` + `eligibility_data`.

### 2. Checklist generation — `generate_checklist` (`api/ai.py:79-101`) — **DETERMINISTIC, không gọi LLM**
- Đọc `static/checklists/{destination}.json` (`ai.py:10-13`), ghép `by_employment[employment_type]` (fallback employee, `ai.py:87`) + `universal` có nội suy `{departure}/{return_date}` vào description (`ai.py:92-96`), kèm `confidence_notes[employment_type]`.
- Endpoint cache vào `Application.checklist_json`, lần sau trả cache (`application.py:114-115`). Lưu ý: message lỗi endpoint ghi "AI service error" (`application.py:123`) dù không có AI.

### 3. Document vision review — `review_document_image` (`api/ai.py:352-392`)
- **Model**: Sonnet vision, max_tokens 256. Prompt tiếng Việt generic (`ai.py:356-369`): trả `{status: pass|fail|needs_clarification, reason}`; nghiêng về needs_clarification khi không chắc. **Không được cấp yêu cầu cụ thể từ checklist** — chỉ nhận `doc_type`, `employment_type`, `destination` trong user text (`ai.py:380-383`).
- Gọi từ `POST .../documents/{doc_id}/review` (`application.py:236-310`): ảnh gửi thẳng; PDF render trang 1 → PNG 150dpi qua fitz (`application.py:269-287`); lỗi AI → fallback `needs_clarification` (`application.py:265-267`).
- Side-flow: nếu `doc_type=="passport"` là ảnh → gọi thêm `extract_id_info` và merge vào `extracted_info_json` (`application.py:297-307`).

### 4. ID extraction — `extract_id_info` (`api/ai.py:295-349`)
- **Model**: Sonnet vision, max_tokens 512. Prompt tiếng Anh (`ai.py:297-329`): trích CCCD hoặc passport thành JSON (tên uppercase Latin, ngày YYYY-MM-DD); trả `{"error": "not_id_document"|"cannot_read"}` khi ảnh sai loại/mờ.
- Gọi từ 2 nơi: `POST /api/extract-id` (`api/routers/extract.py:10-37`, HEIC bị **relabel thành jpeg không convert** `extract.py:24-25` — khả năng fail thật với bytes HEIC) và passport review ở trên.

### 5. Chat — `chat_with_haiku` (`api/ai.py:131-203`)
- **Model**: Haiku, max_tokens 512. Persona "Thu Diễm"; system prompt `ai.py:156-195` gồm FACTS Nhật Bản, compliance (không tư vấn hồ sơ mạnh/yếu), cấm địa chỉ lãnh sự quán, ≤150 từ, không markdown. **Behavior spec đầy đủ đã có tại `docs/chatbot-behavior-spec.md` — xem đó cho eval chat, không lặp lại ở đây.**
- Chống prompt-injection: sanitize `screen`/`employment_type` ≤40 ký tự bỏ newline (`ai.py:134,139`); checklist ép 1 dòng, cắt 300 ký tự, tối đa 20 item (`ai.py:104-128`).
- Router `POST /api/chat` (`api/routers/chat.py:20-57`): history do **client gửi nguyên** (không lưu server); nếu context có `applicationId` thì bơm `checklist_json` server-side vào prompt (`chat.py:54-56`).

### 6. Itinerary — 2 hàm
- **`suggest_itinerary_chat`** (`ai.py:257-292`): trigger khi message chat chứa keyword `["lịch trình","đi đâu","gợi ý","kế hoạch đi","plan","itinerary"]` (`chat.py:11,28`) VÀ app có travel_dates đủ. Gọi **2 lần Haiku**: (a) reply tiếng Việt persona Thu Diễm, prompt riêng ít guardrail hơn chat chính (`ai.py:268-276`); (b) `generate_itinerary` cho data form. Lỗi → silent fall-through về chat thường (`chat.py:49-50`).
- **`generate_itinerary`** (`ai.py:206-254`): Haiku, prompt tiếng Anh sinh JSON array `[{activities[], accommodation{name,phone}}]` mỗi ngày, activity ≤55 ký tự, bắt buộc English (font PDF MOFA không render dấu tiếng Việt). Parse fail → trả `[]` (`ai.py:248-254`).

### 7. Admin checklist verify — `verify_checklist` (`api/routers/admin.py:35-105`)
- **Model**: Sonnet, max_tokens 1500, **không có system prompt** (user message duy nhất `admin.py:62-86`). Fetch trang lãnh sự quán bằng httpx (cắt 12000 ký tự, `admin.py:25-32`) rồi so với checklist JSON hiện tại → `{status, issues[], summary, recommendation}`. **Không auth** — ai cũng trigger được outbound fetch + Sonnet call.

### 8. CV skills (legacy) — `claude_extract_skills` (`api/routes/cv_jobs.py:30-49`)
- Sonnet **hardcode string** `"claude-sonnet-4-6"` (`cv_jobs.py:32`), client `anthropic.Anthropic()` không truyền key tường minh (`cv_jobs.py:15`). Trích ≤15 skills từ CV text.

## FORM FILLER (`api/form_filler.py`, 644 dòng) — luồng điền PDF MOFA

1. `POST /api/application/{id}/forms/download` (`api/routers/forms.py:117-165`) — chỉ cho `destination=="japan"` (`forms.py:123-124`).
2. `_build_info` (`forms.py:44-114`) merge personal_info từ request body + profile/travel_dates từ DB: nationality hardcode "vietnam", purpose "Tourism", port_of_entry "Narita", occupation map từ employment_type (`forms.py:71-79`).
3. Itinerary: dùng `itinerary_json` cache nếu có, không thì gọi `generate_itinerary` (`forms.py:136-145`). **BUG**: `json.loads(application.travel_dates)` trên JSON column (đã là dict) → TypeError bị nuốt → `_td={}` → itinerary luôn sinh với ngày rỗng, fallback 7 ngày (`forms.py:129-134` + `ai.py:210-212`).
4. `fill_visa_form` (`form_filler.py:283-370`): mở `static/visa_form_blank.pdf` (XFA, 41+34 widgets), match widget theo suffix XFA qua map `VISA_TEXT_MAP` (`form_filler.py:220-249`). Đặc thù: nationality là XFA ComboBox từ chối update → **white-out rect + vẽ text overlay** (`form_filler.py:130-163`, ISO lookup `:49-103`); radio giới tính/hôn nhân/loại hộ chiếu chọn theo **tọa độ x** vì export value trùng nhau (`:316-365`); trang 2 điền guarantor/inviter, ngày nộp = hôm nay, và **6 câu hỏi tiền án RB5[0-5] luôn tick "No"** (`:411-432`) — rủi ro compliance nếu khách có tiền án.
5. `fill_schedule` (`form_filler.py:437-540`): điền 16 hàng ngày (date/activity/contact/accommodation) từ itinerary AI; thiếu thì dùng activity mặc định tiếng Anh xoay vòng (`:468-483`); phone dài → font 7 (`:522-528`).
6. Đóng gói zip `don_xin_visa.pdf` + `lich_trinh.pdf` (`forms.py:155-165`).
7. `fill_visa_forms_for_group` (`form_filler.py:545-588`) + sơ đồ quan hệ nhóm ≥3 người (`:591-644`) — **không có endpoint nào gọi**, dead code từ luồng cũ.

## AGENTS PIPELINE (`agents/*.py`) — chưa từng được document

- **Gọi từ đâu**: duy nhất `POST /api/v1/cases` (`api/routes/__init__.py:138-224`). Input là form fields + file upload nhưng **file KHÔNG được đọc thật** — `mock_ocr` (`routes/__init__.py:17-120`) fabricate văn bản passport/bank/employment/itinerary/photo "đẹp như mơ" từ chính form fields. Toàn pipeline chấm dữ liệu giả.
- **Base**: `agents/base.py:8-29` — mọi agent 1 call `messages.create` max_tokens 4096, ép JSON, strip code fence + regex extract object.
- **Orchestration** `agents/pipeline.py:17-63` (`VisaPipeline.run`):
  1. **Gatekeeper** (Haiku, `gatekeeper.py`): eligibility + case_type standard/elevated/complex; hard rule `prior_refusals>=3` chặn **không cần API** (`gatekeeper.py:31-39`). Not eligible → status `disqualified`, dừng.
  2. **Inspector** (Sonnet, `inspector.py`): review 5 tài liệu text, `overall fail` + blocking_issues → status `not_ready`, dừng.
  3. **Detective ∥ Navigator** chạy song song ThreadPoolExecutor (`pipeline.py:35-39`). Detective (Sonnet, `detective.py`): mâu thuẫn tài chính, benchmark 3.5tr VND/ngày, output `risk_level`. Navigator (Haiku, `navigator.py`): validate itinerary (vague/unrealistic/budget/copy-paste) + tự đề xuất itinerary thay thế.
  4. **Analyst** (Sonnet, `analyst.py`): tổng hợp narrative + email cho khách; bị cấm dùng từ "approve/reject" (`analyst.py:11-13`).
  5. Quyết định code cứng (`pipeline.py:48-52`): `risk_level=="low" and case_type!="complex"` → `auto_approve`, còn lại `human_review`.
- **Librarian** (Sonnet, `librarian.py`) đứng ngoài pipeline: trích rule change từ thông báo đại sứ quán → `PolicyDraft`, human approve mới ghi `PolicyRule` (`routes/__init__.py:302-358`). PolicyRule **không được đọc lại ở bất kỳ agent nào** — vòng lặp policy chưa khép.

## Error handling patterns

- Endpoint gọi AI: `try/except Exception → HTTPException 503` (`application.py:83-90,116-123`), forms 500 (`forms.py:152-153`), extract 500/422 (`extract.py:27-35`), pipeline 502 (`routes/__init__.py:190-195`).
- Fallback im lặng phổ biến: review lỗi → `needs_clarification` (`application.py:265-267,285-287`); itinerary chat lỗi → rơi về chat thường (`chat.py:49-50`); `generate_itinerary` parse fail → `[]`; passport extract lỗi → `pass` nuốt (`application.py:306-307`).
- Parse JSON từ LLM: regex tự chế `_parse_json` (`ai.py:18-27`) và bản tương tự `base.py:14-29`, `admin.py:95-100` — không dùng tool-use/structured output; JSON hỏng → exception lan lên 503.

## Testing hiện có

- `tests/conftest.py`: TestClient + SQLite riêng `test_visa_flow.db`, override `get_db`.
- `tests/api/test_chat_format.py` (unit, không gọi API thật): sanitize checklist vào prompt — chống injection, cắt dòng/độ dài, cap 20 item.
- `tests/api/test_checklist.py` (151 dòng): nội dung checklist theo feedback Sông Hàn (ảnh 4.5×3.5cm...) — đi qua endpoint thật nhưng eligibility gọi Haiku thật (cần API key).
- `tests/api/test_documents.py` (138 dòng): upload/validate extension, flow start→submit→status.
- `tests/e2e/*.spec.ts` (Playwright): ChatWidget UI + checklist skip flow, chạy trên `localhost:5173`.
- **Không có test nào cho**: form_filler, agents pipeline, eligibility logic (ngày làm việc), vision review, itinerary.
