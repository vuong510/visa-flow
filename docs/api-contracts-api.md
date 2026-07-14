# API Contracts — Visa Flow Backend

> Catalog toàn bộ endpoints. Prefix mount tại `api/main.py:35-41`. Cột AI: 🤖 = gọi LLM, ⚙️ = deterministic. Cập nhật: 2026-07-14.

## ⚠️ Auth & IDOR (đã biết, áp toàn cục)

- **Không có authentication/authorization ở BẤT KỲ endpoint nào.** `Application.session_id` được sinh (`api/routers/application.py:47`) nhưng **không bao giờ được kiểm tra** — mọi endpoint chỉ cần `app_id` integer tự tăng → đoán được → đọc/ghi hồ sơ, tài liệu, extracted-info (PII hộ chiếu) của người khác (IDOR).
- `POST /api/chat` nhận `context.applicationId` từ client, tự bơm checklist của app đó vào prompt (`api/routers/chat.py:29-34`) — IDOR nhẹ.
- `POST /api/admin/verify-checklist/*` không auth dù tên "admin" — trigger được outbound HTTP + Sonnet call (đốt tiền/DoS) (`api/routers/admin.py:35`).
- CORS `allow_origins=["*"]` (`api/main.py:28-33`).

## Luồng consumer hiện hành — prefix `/api`

### application.py (`api/routers/application.py`)

| # | Method + Path | Request → Response | AI | Side effects | file:line |
|---|---|---|---|---|---|
| 1 | GET `/api/health` | — → `{status:"ok"}` | ⚙️ | — | application.py:40-42 |
| 2 | POST `/api/application/start` | — → `{application_id, session_id}` | ⚙️ | INSERT Application | application.py:45-52 |
| 3 | PATCH `/api/application/{app_id}/destination` | `{destination}` → `{ok}` | ⚙️ | UPDATE destination (không validate giá trị) | application.py:55-62 |
| 4 | PUT `/api/application/{app_id}/profile` | `{profile_json, travel_dates?}` → `{ok}` | ⚙️ | UPDATE profile_json/travel_dates (dict tự do, không schema) | application.py:65-74 |
| 5 | POST `/api/application/{app_id}/eligibility` | — → `{result, headline, bullets, reason, confidence_label}` | 🤖 Haiku | UPDATE eligibility_result + eligibility_data; lỗi AI → 503 | application.py:77-94 |
| 6 | POST `/api/application/{app_id}/payment/demo` | — → `{ok}` | ⚙️ | payment_status="demo_completed", feasibility_ok=True — **thanh toán giả, không gate gì phía sau** | application.py:97-105 |
| 7 | POST `/api/application/{app_id}/checklist` | — → `{items[], confidence_note}` | ⚙️ (đọc static JSON) | Cache vào checklist_json lần đầu; **cache không invalidate khi đổi profile/destination** | application.py:108-126 |
| 8 | POST `/api/application/{app_id}/documents` | multipart `file` + `doc_type` → `{document_id, doc_type, status:"pending"}` | ⚙️ | Ghi file `uploads/{app_id}/{doc_type}_{hex8}_{filename}`; INSERT Document. Chỉ check extension (`:140-145`), không check magic bytes/size | application.py:129-165 |
| 9 | POST `/api/application/{app_id}/documents/skip` | `{doc_type}` → `{document_id, doc_type, status}` | ⚙️ | Doc mới nhất pass/pending → trả nguyên; ngược lại set skipped, `file_path=None` (**file vật lý không xóa** `:187`) | application.py:168-200 |
| 10 | POST `/api/application/{app_id}/documents/unskip` | `{doc_type}` → `{ok}` | ⚙️ | DELETE các Document skipped cùng doc_type | application.py:203-214 |
| 11 | GET `/api/application/{app_id}/documents` | — → `[{id, doc_type, review_status, review_notes}]` | ⚙️ | — (không 404 khi app không tồn tại — trả `[]`) | application.py:217-233 |
| 12 | POST `/api/application/{app_id}/documents/{doc_id}/review` | — → `{status, reason}` | 🤖 Sonnet vision (+ Sonnet extract nếu passport) | UPDATE review_status/review_notes; PDF → render trang 1 PNG; passport → merge extracted_info_json (`:297-307`); mọi lỗi AI → needs_clarification (không 5xx) | application.py:236-310 |
| 13 | GET `/api/application/{app_id}/extracted-info` | — → dict PII đã trích (family_name, passport_number...) | ⚙️ | — | application.py:313-318 |
| 14 | PATCH `/api/application/{app_id}/itinerary` | `{itinerary: list}` → `{ok}` | ⚙️ | UPDATE itinerary_json (list tự do) | application.py:321-328 |
| 15 | POST `/api/application/{app_id}/submit` | — → `{ok}` | ⚙️ | submission_status="submitted", submitted_at=now — **không kiểm tra đã đủ tài liệu/thanh toán** | application.py:331-339 |
| 16 | GET `/api/application/{app_id}/status` | — → `{submission_status, nodes[4], is_terminal}` | ⚙️ | Timeline 4 node map từ submission_status (`_build_timeline` :359-388) | application.py:342-357 |

### chat.py, forms.py, extract.py, admin.py

| # | Method + Path | Request → Response | AI | Side effects | file:line |
|---|---|---|---|---|---|
| 17 | POST `/api/chat` | `{message, history[], context{destination?, screen?, profile?, applicationId?}}` → `{reply}` hoặc `{reply, itinerary}` | 🤖 Haiku (1 call; nhánh itinerary = 2 call) | Stateless — history do client giữ, server không lưu chat. Keyword itinerary + app có travel_dates → nhánh `suggest_itinerary_chat` (chat.py:38-50) | chat.py:20-57 |
| 18 | POST `/api/application/{application_id}/forms/download` | `{personal_info{17 field}}` → ZIP (`don_xin_visa.pdf` + `lich_trinh.pdf`) | 🤖 Haiku nếu chưa có itinerary_json, ⚙️ nếu có | Chỉ japan (400 nếu khác, forms.py:123). Không ghi DB. Bug parse travel_dates (forms.py:130-134) → itinerary AI luôn nhận ngày rỗng | forms.py:117-165 |
| 19 | POST `/api/extract-id` | multipart `file` + `doc_type`("cccd"\|"passport") → JSON field trích được | 🤖 Sonnet vision | Không ghi DB, không lưu file. Giới hạn 10MB, HEIC relabel jpeg không convert (extract.py:24-25). 422 khi không phải giấy tờ/không đọc được | extract.py:10-37 |
| 20 | POST `/api/admin/verify-checklist/{destination}` | — → `{status, issues[], summary, recommendation, source_urls, checklist_last_verified}` | 🤖 Sonnet | Fetch 1-2 URL lãnh sự quán (httpx, 15s timeout). **Không ghi file checklist** — chỉ báo cáo. Không auth | admin.py:35-105 |

## Pipeline multi-agent cũ — prefix `/api/v1` (`api/routes/__init__.py`)

| # | Method + Path | Request → Response | AI | Side effects | file:line |
|---|---|---|---|---|---|
| 21 | POST `/api/v1/cases` | multipart form 9 field + 5 file optional → `{case_id, status, case_type, risk_level, summary, recommendation, email_to_user, stages{}}` | 🤖 4-5 call (Haiku×2, Sonnet×2-3) | File chỉ lấy filename — nội dung thay bằng **mock_ocr fabricated** (`:17-120`). INSERT VisaCase, chạy sync `VisaPipeline().run` (chậm, block request), lưu kết quả từng stage. Lỗi pipeline → status="error" + 502 | routes/__init__.py:138-224 |
| 22 | GET `/api/v1/cases?status&skip&limit` | — → list case summary | ⚙️ | — | routes/__init__.py:227-252 |
| 23 | GET `/api/v1/cases/{case_id}` | — → full case + stages | ⚙️ | — | routes/__init__.py:255-279 |
| 24 | PATCH `/api/v1/cases/{case_id}/review` | `{decision:"approved"\|"rejected", notes}` → `{case_id, decision}` | ⚙️ | Chỉ khi status=="human_review"; UPDATE reviewer_* + status | routes/__init__.py:282-297 |
| 25 | POST `/api/v1/policies/analyze` | `{announcement_text}` → `{draft_id, result{changes[], summary}}` | 🤖 Sonnet (Librarian) | INSERT PolicyDraft status=pending | routes/__init__.py:302-313 |
| 26 | GET `/api/v1/policies/drafts` | — → list drafts | ⚙️ | — | routes/__init__.py:316-328 |
| 27 | PATCH `/api/v1/policies/drafts/{id}/approve` | `{approved_by}` → `{draft_id, status, changes_applied}` | ⚙️ | INSERT PolicyRule cho add/modify; deactivate rule match substring cho remove (`:348-352`, fuzzy 60 ký tự) | routes/__init__.py:331-358 |
| 28 | PATCH `/api/v1/policies/drafts/{id}/reject` | — → `{draft_id, status}` | ⚙️ | draft.status="rejected" | routes/__init__.py:361-368 |
| 29 | GET `/api/v1/policies/rules?active_only` | — → list rules | ⚙️ | — (rules không được agent nào tiêu thụ) | routes/__init__.py:371-381 |

## CV-jobs (legacy, ngoài phạm vi visa) — prefix `/api/v1` (`api/routes/cv_jobs.py`)

| # | Method + Path | Request → Response | AI | Side effects | file:line |
|---|---|---|---|---|---|
| 30 | POST `/api/v1/cv/extract-skills` | multipart file (PDF/text) → `{skills[]}` | 🤖 Sonnet (hardcode model string :32) | Không lưu | cv_jobs.py:52-63 |
| 31 | POST `/api/v1/cv/search-jobs` | `{skills[]}` → `{jobs[]}` | ⚙️ | Gọi Remotive API + sinh link job boards | cv_jobs.py:70-124 |

## Route tĩnh (`api/main.py`)

| Method + Path | Trả về | file:line |
|---|---|---|
| GET `/health` | `{status:"ok"}` (Railway healthcheck) | main.py:48-50 |
| GET `/cv-jobs` | `frontend/cv-jobs.html` (legacy) | main.py:52-54 |
| GET `/` và `/{full_path:path}` | SPA `visa-client/dist/index.html` | main.py:56-62 |
| `/assets/*` | StaticFiles từ dist | main.py:46 |

**Tổng: 31 endpoint API** (16 application + 4 chat/forms/extract/admin + 9 cases/policies + 2 cv) + 4 route tĩnh. **8 endpoint gọi LLM**: #5, #12, #17, #18 (có điều kiện), #19, #20, #21, #25, #30.
