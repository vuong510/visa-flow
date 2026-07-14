---
title: '4 fixes: itinerary parse, review đa trang, khai báo tiền án, eligibility Python-first'
type: 'bugfix'
created: '2026-07-14'
status: 'done'
baseline_commit: '86e59b153d34eeba7575d43d27e9a165ca1516c4'
context: ['{project-root}/project-context.md', '{project-root}/docs/api-contracts-api.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** 4 lỗi từ deep scan 14/07: (1) `forms.py:132` gọi `json.loads` trên `travel_dates` (đã là dict) → TypeError bị nuốt → itinerary PDF luôn fallback 7 ngày; (2) review tài liệu PDF chỉ render trang 1 (`application.py:273`) → sao kê/hồ sơ nhiều trang bị đánh giá thiếu; (3) form MOFA tự tick "No" cả 6 câu tiền án RB5[0-5] (`form_filler.py:411-432`) không hỏi khách — rủi ro compliance; (4) eligibility giao Haiku tự đếm "10 ngày làm việc" và so "180 ngày" bằng văn xuôi — không ổn định.

**Approach:** (1) Parse `travel_dates` bằng guard `isinstance(str)` như `_build_info` đã làm đúng; test: chuyến 4 ngày → `generate_itinerary` nhận đúng ngày và PDF lịch trình ra 4 ngày. (2) Render TẤT CẢ trang PDF (dpi 150) và gửi hết trong MỘT call Sonnet — không cap số trang; lỗi API đã có fallback `needs_clarification` sẵn. (3) Bỏ hardcode "No": thêm bước "Khai báo" vào flow form-filling (trước Tải xuống) với 6 câu Có/Không — nội dung câu trích từ text thật của `static/visa_form_blank.pdf` cạnh từng widget RB5 (không tự bịa thứ tự); 6 boolean đi qua `PersonalInfo` vào `form_filler`, tick Yes/No theo khai báo thật. (4) Tạo `static/vn_holidays.json` (2026-2027, user đã duyệt phương án JSON tĩnh) + module Python đếm ngày làm việc (bỏ T7/CN + lễ); check "180 ngày prior_denial" và "10 ngày làm việc" bằng Python TRƯỚC khi gọi LLM — chỉ khi qua cả 2 mới để LLM xét freelancer→edge_case. Cài pytest vào venv.

## Boundaries & Constraints

**Always:**
- Quy tắc 10 ngày làm việc: đếm ngày làm việc BẮT ĐẦU TỪ NGÀY MAI (hôm nay không tính); mốc = ngày làm việc thứ 10; ngày khởi hành hợp lệ phải SAU mốc (strictly >, không phải đúng ngày thứ 10). Ví dụ: hôm nay T2 13/07 (không lễ) → ngày làm việc thứ 10 là T2 27/07 → khởi hành hợp lệ từ 28/07.
- Quy tắc 180 ngày: `prior_denial=true` VÀ `denial_country == destination` VÀ `0 <= (today - denial_date).days < 180` → `not_eligible` (Python quyết, không qua LLM).
- Kết quả deterministic từ Python phải TRÙNG shape FE đang render: `{result, headline, bullets, reason, confidence_label}` với `result ∈ {eligible, not_eligible, edge_case}` (EligibilityScreen.jsx:32-42), copy tiếng Việt xưng "bạn" theo style guide.
- Nội dung 6 câu khai báo: trích từ text trong `static/visa_form_blank.pdf` gần rect từng nhóm RB5 để map đúng index→câu hỏi; dịch tiếng Việt cho UI, giữ nguyên thứ tự form.
- `vn_holidays.json` có `meta.last_verified` + ghi chú "lịch nghỉ bù cần chị Yến xác nhận"; ngày ngoài phạm vi file (2028+) → degrade: chỉ bỏ T7/CN.
- Test ngày làm việc dùng holidays inject được (tham số hàm), không phụ thuộc lịch thật.
- pytest cài vào venv + ghi `requirements-dev.txt` (không cho vào requirements.txt prod).

**Ask First:**
- Nếu text trong PDF không đủ để xác định 6 câu RB5 (scan không ra) → hỏi user trước khi dùng bộ câu MOFA chuẩn từ nguồn ngoài.
- Nếu cần đổi shape response `/eligibility` hoặc thêm cột DB.

**Never:**
- Không đụng logic khác trong `form_filler.py` (guarantor/inviter/T-fields/fill_schedule — CLAUDE.md cấm đổi PDF logic chưa test).
- Không viết gì liên quan Trung Quốc.
- Không cap số trang PDF ở việc 2 (user chỉ định gửi tất cả).
- Không lưu personal_info/khai báo vào DB (giữ kiến trúc transient qua body /forms/download).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Itinerary 4 ngày | travel_dates dict {departure: D, return: D+3}, chưa có itinerary_json | `generate_itinerary` nhận đúng D/D+3; PDF lịch trình 4 ngày | travel_dates là str JSON → vẫn parse đúng (guard isinstance) |
| Review PDF 5 trang | upload PDF 5 trang, gọi review | 1 call Sonnet với 5 image blocks + 1 text block | PDF hỏng/quá lớn → catch hiện có → needs_clarification |
| Khai báo sạch | 6 câu đều "Không" | RB5[i] tick No (nút phải, x lớn) như cũ | — |
| Khai báo có tiền án | câu i = "Có" | RB5[i] tick Yes (nút trái); các câu khác theo khai báo | Thiếu khai báo trong payload → 422, FE chặn download tới khi trả lời đủ 6 câu |
| Khởi hành đúng mốc | hôm nay+10 ngày làm việc = X, departure = X | `not_eligible` (phải SAU X) | departure không parse được → để LLM xử như cũ |
| Khởi hành sau mốc, có Tết giữa chừng | kỳ nghỉ Tết trong khoảng đếm | mốc lùi ra sau đúng số ngày lễ | năm ngoài file lễ → chỉ bỏ T7/CN |
| Từ chối 100 ngày trước, cùng nước | prior_denial, denial_date = today-100d, denial_country=japan | `not_eligible` deterministic, không gọi LLM | denial_date không parse được → để LLM xử |
| Qua cả 2 check, freelancer | dates OK, employment_type=freelancer | LLM được gọi, kỳ vọng edge_case (prompt không còn luật ngày) | LLM lỗi → 503 như cũ |

</frozen-after-approval>

## Code Map

- `api/routers/forms.py:128-148` — bug json.loads + chỗ gọi generate_itinerary; `_build_info:52-60` có guard đúng để tái dùng
- `api/routers/application.py:236-310` — endpoint review; `:269-284` render trang 1; `:77-94` endpoint eligibility (chèn Python pre-check tại đây)
- `api/ai.py:30-76` — assess_eligibility (bỏ luật 1&2 khỏi prompt); `:352-384` review_document_image (đổi nhận nhiều ảnh)
- `api/form_filler.py:411-432` — khối RB5 (chỉ được đụng khối này); trái x≈502=Yes, phải x≈539=No
- `visa-client/src/screens/FormFillingScreen.jsx` — 4 sub-step (`STEP_LABELS:516`); chèn bước "Khai báo" trước "Tải xuống"; payload download `:425-436`
- `static/visa_form_blank.pdf` — nguồn text 6 câu RB5 (trang 2)
- `tests/conftest.py` — fixtures client/new_application; `tests/api/test_checklist.py` — convention helper setup app
- MỚI: `api/working_days.py`, `static/vn_holidays.json`, `tests/api/test_working_days.py`, `tests/api/test_forms_itinerary.py`, `tests/api/test_review_multipage.py` (nếu mock được), `tests/api/test_form_filler_rb5.py`, `requirements-dev.txt`

## Tasks & Acceptance

**Execution:**
- [x] `venv` — `pip install pytest` + tạo `requirements-dev.txt` (pytest, pin version)
- [x] `static/vn_holidays.json` — lịch nghỉ nhà nước VN 2026-2027: Tết Dương lịch, Tết Nguyên Đán (5 ngày), Giỗ Tổ Hùng Vương, 30/4, 1/5, Quốc khánh 2/9 (+1 ngày liền kề); schema `{meta: {last_verified, note}, years: {"2026": [ISO dates], "2027": [...]}}`; ngày âm lịch/nghỉ bù đánh dấu cần chị Yến xác nhận trong meta.note
- [x] `api/working_days.py` — MỚI: `load_vn_holidays()`, `nth_working_day_after(start_date, n, holidays=None)` (đếm từ ngày mai, bỏ T7/CN + holidays), `check_departure_rule(today, departure, n=10)` → (ok, mốc); `check_prior_denial_rule(profile, destination, today)` → ok/not; docstring ví dụ
- [x] `api/ai.py` — assess_eligibility: bỏ luật 1&2 khỏi system prompt (giữ freelancer→edge_case + default eligible); KHÔNG đổi signature/return shape
- [x] `api/routers/application.py` — endpoint eligibility: gọi 2 check Python trước; fail check nào → trả dict deterministic đúng shape (headline/bullets/reason tiếng Việt giải thích mốc ngày hoặc quy định 180 ngày, `confidence_label: "Độ tin cậy AI: Cao"`), lưu eligibility_result/data như cũ, KHÔNG gọi LLM; qua cả 2 → gọi assess_eligibility như cũ
- [x] `api/routers/forms.py:128-134` — thay khối json.loads bằng parse guard isinstance (tái dùng logic `_build_info`) 
- [x] `api/ai.py` review_document_image — đổi nhận `images: list[tuple[bytes, str]]` (bytes, media_type), build content = N image blocks + 1 text block; cập nhật 2 call site (ảnh đơn → list 1 phần tử)
- [x] `api/routers/application.py:269-284` — render TẤT CẢ trang PDF dpi 150 → list PNG, gửi 1 lần
- [x] `api/form_filler.py:411-432` — CHỈ khối RB5: đọc 6 boolean từ `info` (ví dụ `criminal_q0`..`criminal_q5`); True → tick nút trái (Yes), False → nút phải (No); thiếu key → raise ValueError (không âm thầm default)
- [x] `api/routers/forms.py` — `PersonalInfo` thêm 6 field bool BẮT BUỘC (không default) map RB5[0-5], tên field theo nội dung câu trích từ PDF; đưa vào `_build_info`
- [x] `visa-client/src/screens/FormFillingScreen.jsx` — thêm sub-step "Khai báo" trước "Tải xuống" (STEP_LABELS 5 bước): 6 câu Có/Không tiếng Việt (dịch từ text PDF, xưng "bạn"), mặc định CHƯA chọn, phải trả lời đủ 6 mới Tiếp tục; đưa 6 boolean vào payload personal_info của download
- [x] `tests/api/test_working_days.py` — bảng case: không lễ, có lễ giữa khoảng, departure = mốc (fail), = mốc+1 (pass), năm ngoài file (chỉ T7/CN), holidays inject
- [x] `tests/api/test_forms_itinerary.py` — app 4 ngày (dict) + monkeypatch `api.routers.forms.generate_itinerary` bắt args + trả 4 item → assert nhận đúng departure/return; unzip response, mở lich_trinh.pdf bằng fitz, assert đủ 4 ngày; case travel_dates là chuỗi JSON vẫn đúng
- [x] `tests/api/test_form_filler_rb5.py` — gọi fill_visa_form với 6 boolean trộn Yes/No → mở PDF ra assert field_value từng RB5 đúng phía; thiếu key → ValueError
- [x] `tests/api/test_review_multipage.py` — monkeypatch `review_document_image` bắt args, upload PDF 3 trang (tạo bằng fitz trong test) → assert nhận list 3 ảnh

**Acceptance Criteria:**
- Given application có travel_dates dict 4 ngày và chưa có itinerary_json, when POST /forms/download, then generate_itinerary được gọi với đúng departure/return và PDF lịch trình chứa đủ 4 ngày
- Given PDF 3 trang được upload, when review, then Sonnet nhận đúng 3 image blocks trong 1 request
- Given khách trả lời "Có" ở câu k và "Không" ở các câu còn lại, when tải form, then PDF tick Yes đúng RB5[k] và No ở 5 câu kia; given payload thiếu 1 trong 6 boolean, then backend trả 422
- Given hôm nay + lịch lễ khiến mốc 10 ngày làm việc là X, when departure = X, then not_eligible (deterministic, không có call Anthropic); when departure = X+1 (ngày làm việc), then check ngày pass
- Given prior_denial cùng nước 100 ngày trước, when POST /eligibility, then not_eligible deterministic; given 200 ngày trước, then không bị chặn bởi Python check
- Given qua cả 2 check và employment_type=freelancer, when POST /eligibility, then có đúng 1 call LLM và prompt không còn chứa luật ngày
- `python3 -m pytest tests/api -q` pass toàn bộ trong venv

## Spec Change Log

## Design Notes

- Copy not_eligible do Python sinh cần nêu mốc cụ thể: "Chuyến đi cần khởi hành sau ngày {mốc} (10 ngày làm việc kể từ hôm nay, không tính T7/CN và ngày lễ)" — giúp khách biết chờ đến bao giờ.
- Review đa trang: chi phí token tăng theo trang (~1.6k/trang dpi 150) — chấp nhận theo chỉ định user; PDF quá lớn làm request fail sẽ rơi vào catch hiện có (needs_clarification) nên không cần cap.
- 6 field khai báo đặt tên semantic sau khi trích PDF (ví dụ `conviction_any_crime`, `sentenced_1yr_plus`, `deported_from_japan`, `drug_offense`, `prostitution_related`, `human_trafficking`) — implementer chốt theo thứ tự thật của form.

## Verification

**Commands:**
- `source venv/bin/activate && python3 -m pytest tests/api -q` — expected: pass toàn bộ (test cũ + 4 file test mới)
- `python3 -m py_compile api/ai.py api/working_days.py api/form_filler.py api/routers/forms.py api/routers/application.py` — expected: OK
- `cd visa-client && npx oxlint src/screens/FormFillingScreen.jsx && npm run build` — expected: 0 errors, build pass

**Manual checks (if no CLI):**
- Chạy app: flow form-filling hiện 5 bước, bước Khai báo chặn khi chưa đủ 6 câu; tải PDF mở ra thấy RB5 tick đúng khai báo; màn eligibility với ngày khởi hành quá gần trả kết quả tức thì (không chờ AI)

## Suggested Review Order

**Việc 4 — Eligibility Python-first (nhiều logic nhất, đọc trước)**

- Module đếm ngày làm việc: vn_today (múi giờ VN), nghỉ bù lễ rơi T7/CN, mốc thứ 10 đếm từ ngày mai
  [`working_days.py:25`](../../api/working_days.py#L25) · [`:59`](../../api/working_days.py#L59) · [`:78`](../../api/working_days.py#L78)

- 2 rule check: departure strictly-after mốc; prior denial 180 ngày (normalize country, future date → LLM)
  [`working_days.py:103`](../../api/working_days.py#L103) · [`:120`](../../api/working_days.py#L120)

- Endpoint: precheck deterministic (đúng shape FE, không gọi LLM khi fail) + guard legacy string travel_dates
  [`application.py:118`](../../api/routers/application.py#L118)

- Prompt eligibility đã bỏ 2 luật ngày — chỉ còn freelancer→edge_case
  [`ai.py:38`](../../api/ai.py#L38)

- Data lễ 2026-27 (ngày âm lịch cần chị Yến xác nhận — ghi trong meta.note)
  [`vn_holidays.json:1`](../../static/vn_holidays.json#L1)

**Việc 3 — Khai báo tiền án (rủi ro pháp lý, đọc kỹ nhì)**

- 6 câu trích nguyên văn từ PDF, thứ tự widget RB5[3,0,1,5,4,2] ≠ thứ tự hiển thị
  [`forms.py:41`](../../api/routers/forms.py#L41)

- Khối RB5: tick theo khai báo thật, hard-fail mọi bất thường (thiếu key/widget, non-bool)
  [`form_filler.py:411`](../../api/form_filler.py#L411)

- Bước "Khai báo" mới trên FE: 6 câu bắt buộc, không default
  [`FormFillingScreen.jsx:424`](../../visa-client/src/screens/FormFillingScreen.jsx#L424)

**Việc 1 — Itinerary parse fix**

- Guard isinstance thay json.loads-trên-dict (gốc bug "luôn 7 ngày")
  [`forms.py:146`](../../api/routers/forms.py#L146)

**Việc 2 — Review đa trang**

- Render mọi trang + guard 0 trang → needs_clarification
  [`application.py:346`](../../api/routers/application.py#L346)

- review_document_image nhận list ảnh, 1 call Sonnet
  [`ai.py:350`](../../api/ai.py#L350)

**Tests (92 pass)**

- Ngày làm việc + nghỉ bù + biên 180 ngày
  [`test_working_days.py:1`](../../tests/api/test_working_days.py#L1)

- Itinerary 4 ngày end-to-end tới PDF; RB5 đọc ngược từ PDF; review 3 trang
  [`test_forms_itinerary.py:1`](../../tests/api/test_forms_itinerary.py#L1) · [`test_form_filler_rb5.py:1`](../../tests/api/test_form_filler_rb5.py#L1) · [`test_review_multipage.py:1`](../../tests/api/test_review_multipage.py#L1)
