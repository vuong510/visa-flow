# Data Models & Storage — Visa Flow

> Schema từ `db/models.py` (113 dòng). ORM SQLAlchemy 2.0 declarative, không Alembic — `init_db()` dùng `create_all` + 2 câu ALTER TABLE nuốt lỗi (`db/session.py:10-21`). Cập nhật: 2026-07-14.

## Tổng quan: 5 bảng

| Bảng | Thuộc thế hệ | file:line | Quan hệ |
|---|---|---|---|
| `applications` | Consumer flow hiện hành | models.py:88-105 | 1—n `documents` (qua FK) |
| `documents` | Consumer flow hiện hành | models.py:108-113 | FK `application_id → applications.id` (FK duy nhất toàn schema) |
| `visa_cases` | Pipeline agents cũ | models.py:7-59 | Không FK |
| `policy_rules` | Librarian cũ | models.py:62-70 | Không FK (link mềm qua `source="Draft #id"`) |
| `policy_drafts` | Librarian cũ | models.py:73-82 | Không FK |

Không khai báo `relationship()` nào — mọi join làm tay bằng query.

## `applications` (models.py:88-105)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | Integer PK | app_id dùng trong mọi URL — tự tăng, đoán được (IDOR) |
| session_id | String(36), index, NOT NULL | UUID sinh lúc start (`application.py:47`) — **không bao giờ được dùng để authz** |
| destination | String(10) | "japan" \| "china", không validate |
| profile_json | JSON | Shape thực tế (do frontend + tests, `tests/api/test_checklist.py:10-16`): `{employment_type: "employee"\|"student"\|"business_owner"\|"freelancer"\|"homemaker"\|"retired", passport_expiry: "YYYY-MM-DD", has_previous_visa: bool, monthly_income: int, bank_balance: int, prior_denial?: bool, denial_country?: str, denial_date?: str, has_prior_stamps?: bool}` — dict tự do, không Pydantic schema phía ghi (`application.py:28`) |
| eligibility_result | String(20) | "eligible" \| "not_eligible" \| "edge_case" |
| eligibility_data | JSON | Nguyên response Haiku: `{result, headline, bullets[], reason, confidence_label}` |
| travel_dates | JSON | `{"departure": "YYYY-MM-DD", "return": "YYYY-MM-DD"}` (comment models.py:96) |
| feasibility_ok | Boolean, default False | Set True cùng lúc demo payment |
| payment_status | String(30), default "pending" | "pending" \| "demo_completed" |
| checklist_json | JSON | Cache output `generate_checklist`: `{items: [checklist item — xem schema dưới], confidence_note: str\|null}`. **Không invalidate** khi đổi profile/destination; cũng là nguồn bơm vào prompt chat (`chat.py:54`) |
| submission_status | String(30), default "pending" | Lifecycle — xem dưới |
| submitted_at | DateTime | Set lúc submit |
| itinerary_json | JSON | List `[{activities: [str], accommodation: {name, phone}}]` mỗi ngày — do user confirm từ AI (`application.py:321-328`); thêm bằng ALTER TABLE (`session.py:14`) |
| extracted_info_json | JSON | PII trích từ passport/CCCD (Sonnet vision): family_name, given_name, date_of_birth, gender, id_number/passport_number, passport_issue/expiry_date, place_of_birth, home_address — merge tích lũy (`application.py:303-305`); ALTER TABLE (`session.py:15`) |
| created_at | DateTime | default utcnow |

### Lifecycle Application

Trạng thái phân tán trên 4 cột (không có state machine duy nhất, không enforce thứ tự — mọi endpoint gọi được ở bất kỳ lúc nào):

1. `POST /start` → row mới, mọi thứ pending.
2. `destination` + `profile_json`/`travel_dates` được PATCH/PUT tự do.
3. `eligibility` → `eligibility_result` + `eligibility_data`.
4. `payment/demo` → `payment_status="demo_completed"`, `feasibility_ok=True`.
5. `checklist` → `checklist_json` cache.
6. Upload/review documents → bảng `documents`.
7. `submit` → `submission_status="submitted"` + `submitted_at`.
8. Sau submit, `submission_status` dự kiến tiến qua: `"submitted" → "agency_submitted" → "processing" → "approved"|"rejected"|"quota_rejected"` (comment models.py:100) — **nhưng không có endpoint nào set các trạng thái sau "submitted"** (chỉ đổi tay trong DB); timeline UI map tại `application.py:359-388`, terminal = approved/rejected/quota_rejected (`application.py:355`).

## `documents` (models.py:108-113)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | Integer PK | |
| application_id | Integer FK, index, NOT NULL | |
| doc_type | String(100) | id item checklist ("photo", "passport", "payslips"...) — nhiều row cùng doc_type khi re-upload (không unique) |
| file_path | String(500) | Path tuyệt đối trên đĩa; NULL khi skipped |
| review_status | String(30), default "pending" | "pending" \| "pass" \| "fail" \| "needs_clarification" \| "skipped" |
| review_notes | Text | Lý do tiếng Việt từ Sonnet, hoặc note skip cố định |
| created_at | DateTime | |

## Storage file upload

- Thư mục `uploads/{app_id}/` cạnh repo root (`application.py:15-16, 147-148`), tên file `{doc_type}_{uuid8}_{tên gốc}` (`application.py:150`) — tên gốc user giữ nguyên trong path.
- Chỉ validate extension `.jpg/.jpeg/.png/.webp/.gif/.pdf` (`application.py:20,140-145`); không giới hạn size, không check magic bytes.
- **File không bao giờ bị xóa**: re-upload tạo file mới, skip chỉ set `file_path=None` (`application.py:187`).
- Không có endpoint download/serve file upload (chỉ AI đọc nội bộ).

## `visa_cases` (models.py:7-59) — pipeline cũ

- Profile: applicant_name (NOT NULL), nationality, occupation, employer, monthly_income_vnd (String!), prior_japan_visits, prior_refusals, declared_budget_vnd, trip_duration_days.
- Documents dạng **Text mô tả** (passport_info, bank_statement_info, employment_letter_info, itinerary_info, photo_info) — nội dung là mock OCR fabricated (`routes/__init__.py:17-120`).
- Outcome: status ("disqualified"\|"not_ready"\|"auto_approve"\|"human_review"\|"approved"\|"rejected"\|"error"), case_type ("standard"\|"elevated"\|"complex"), risk_level ("low"\|"medium"\|"high").
- 5 cột JSON giữ nguyên output từng agent: gatekeeper_result, inspector_result, detective_result, navigator_result, analyst_result (shape = JSON schema trong system prompt mỗi agent, xem `docs/architecture-api.md`).
- Narrative: summary, recommendation, email_to_user, email_sent (Boolean — không có code gửi mail).
- Human review: reviewer_decision, reviewer_notes, reviewed_at.

## `policy_rules` + `policy_drafts` (models.py:62-82)

- `policy_drafts`: source_text (thông báo gốc), librarian_output JSON `{changes: [{type: add|modify|remove, category, old_rule, new_rule, effective_date, source_quote}], summary, effective_date}`, status pending→approved/rejected, approved_by/at.
- `policy_rules`: category (financial|eligibility|documents|processing|general), rule_text, source ("Draft #id"), active. Approve draft → INSERT rule hoặc deactivate theo substring match 60 ký tự (`routes/__init__.py:339-352`). **Không code nào đọc rules để dùng** — bảng chết.

## `static/checklists/*.json` — schema (japan.json, china.json)

```
{
  meta: { destination, last_verified: "2026-06-29", source_urls: [url lãnh sự quán], notes },
  universal: [ChecklistItem × 5 (japan) / 3 (china)],       // áp mọi khách; description có placeholder {departure}/{return_date}
  by_employment: { employee|student|business_owner|freelancer|homemaker|retired: [ChecklistItem × 4-5] },
  confidence_notes: { freelancer: str }                      // note độ tin cậy, hiện chỉ freelancer
}
ChecklistItem = { id, name, description, format, why, how_to_get, source_url, last_verified, optional? }
```
- `id` khớp `doc_type` khi upload. `generate_checklist` (`api/ai.py:79-101`) ghép by_employment + universal (nội suy ngày), fallback employee khi employment_type lạ.
- Nội dung được verify thủ công qua `POST /api/admin/verify-checklist/{destination}` (chỉ báo cáo, không tự sửa file).

## Database file + deploy

- `DATABASE_URL` mặc định `sqlite:///./visa_flow.db` (`core/config.py:5`) — file `visa_flow.db` tại repo root (~184KB). Env var có thể trỏ Postgres (psycopg2-binary đã cài, `requirements.txt:6`); sqlite thêm `check_same_thread=False` (`db/session.py:6-7`).
- **`railway.toml` KHÔNG khai báo volume** (`railway.toml:1-8`) — nếu Railway chạy sqlite mặc định thì DB và `uploads/` **mất khi redeploy**, trừ khi volume được mount qua Railway UI hoặc DATABASE_URL=Postgres được set trong env (không kiểm chứng được từ repo).
- Test dùng DB riêng `sqlite:///./test_visa_flow.db`, drop sau session (`tests/conftest.py:16-36`).
