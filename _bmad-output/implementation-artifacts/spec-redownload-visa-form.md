---
title: 'Lưu thông tin đơn visa xuống backend để tải lại sau'
type: 'bugfix'
created: '2026-07-23'
status: 'done'
context: []
baseline_commit: 'a1ed14f81b3b7a2d1c78fc741245b0695ca6fa6f'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Ở Bước 5 "Xem lại & Tải xuống" (`FormFillingScreen.jsx`), nút "Tiếp tục →" không phụ thuộc gì vào việc đã bấm "Tải đơn xin visa (ZIP)" chưa. `personalFields` (họ tên/DOB/hộ chiếu user tự sửa) và `declarations` (6 câu khai báo tiền án) chỉ là `useState` cục bộ của `FormFillingScreen` — không nằm trong AppContext, không gửi lên backend lưu ở đâu ngoài body của chính request `/forms/download`. Nếu user bấm "Tiếp tục" mà chưa từng tải, dữ liệu này mất vĩnh viễn — không có màn nào khác gọi lại được `/forms/download` vì không còn gì để gửi.

**Approach:** Thêm cột `form_personal_info_json` (JSON, nullable) vào `Application`. Lưu dữ liệu này ở đúng thời điểm "Tiếp tục →" được bấm (không phụ thuộc download), qua endpoint mới nhẹ (không sinh PDF). Sửa `/forms/download` để `personal_info` trong body trở thành optional: nếu client gửi thì dùng + refresh lưu lại (giữ hành vi cũ nguyên vẹn cho FormFillingScreen), nếu không gửi thì backend tự lấy từ cột đã lưu — cho phép gọi lại từ màn khác mà không cần client giữ state. Thêm nút "Tải lại đơn xin visa" trên `ChecklistScreen.jsx`, chỉ hiện khi `destination === 'japan'` (đúng giới hạn hiện có của form generation) và đã có dữ liệu lưu.

## Boundaries & Constraints

**Always:**
- KHÔNG sửa `api/form_filler.py` (logic điền field PDF) — chỉ chạm phần lưu/đọc dữ liệu quanh nó trong `api/routers/forms.py`.
- Hành vi tải xuống hiện tại từ `FormFillingScreen.jsx` (Step5) phải giữ nguyên y hệt — endpoint vẫn nhận `personal_info` khi được gửi và dùng ngay, không đổi response/side-effect nhìn thấy được từ phía FE cũ.
- Lưu ở "Tiếp tục →" phải là best-effort: lỗi lưu KHÔNG được chặn `navigate('checklist')` — user vẫn đi tiếp bình thường, chỉ mất khả năng redownload sau (không tệ hơn hiện tại).
- Nút redownload trên ChecklistScreen chỉ hiện khi có dữ liệu để tải (đừng hiện nút rồi bấm vào lỗi 400/404 khó hiểu).

**Ask First:**
- Không phát sinh — 2 câu hỏi kiến trúc chính (lưu DB vs AppContext; vị trí nút) đã chốt với user trước khi viết spec này (lưu DB, đặt ở ChecklistScreen).

**Never:**
- Không đổi cấu trúc PDF sinh ra hay field mapping.
- Không thêm nút redownload ở StatusTimeline/ResultScreen trong đợt này (ngoài scope đã chốt).
- Không migrate schema bằng Alembic (project không dùng) — dựa vào `Base.metadata.create_all` hiện có; cột mới nullable nên không cần backfill dữ liệu cũ.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Bấm "Tiếp tục" ở Step5, chưa từng bấm tải | `personalFields`, `declarations`, `extractedInfo` đầy đủ | POST lưu `form_personal_info_json`, sau đó `navigate('checklist')` dù lưu thành công hay không | Lưu lỗi (network/500) → nuốt lỗi, vẫn navigate bình thường, không alert |
| Bấm "Tải đơn xin visa (ZIP)" ở Step5 (như cũ) | Body có `personal_info` đầy đủ | Sinh ZIP như cũ; đồng thời refresh `form_personal_info_json` | Giữ nguyên `alert('Không thể tạo đơn...')` hiện có nếu fail |
| Bấm "Tải lại đơn xin visa" ở ChecklistScreen, đã từng lưu | `application.form_personal_info_json` tồn tại, `destination === 'japan'` | POST `/forms/download` không kèm `personal_info` → backend tự lấy từ DB, trả ZIP | — |
| Bấm "Tải lại" nhưng chưa từng lưu (edge case hiếm — vd data cũ trước khi có cột này) | `form_personal_info_json` là `null` | Nút không hiện (FE check trước); nếu vẫn gọi được, backend trả 404 rõ ràng | `HTTPException(404, "Chưa có thông tin đơn để tải lại")`, FE hiện alert tương tự pattern lỗi tải hiện có |
| `destination !== 'japan'` | Trung Quốc | Nút redownload không hiện trên ChecklistScreen | — |

## Code Map

- `db/models.py` -- thêm `form_personal_info_json = Column(JSON)` vào `Application`
- `api/routers/forms.py` -- `PersonalInfo` optional trong `FormsRequest`; `download_forms` fallback đọc/ghi cột mới; thêm endpoint `PATCH /application/{id}/form-info` (save-only, không sinh PDF)
- `visa-client/src/screens/FormFillingScreen.jsx` -- `handleFinish` mới ở component chính (dòng ~580-591), gọi save trước khi `navigate('checklist')`; truyền xuống Step5 thay cho `onFinish={() => navigate('checklist')}` trực tiếp
- `visa-client/src/screens/ChecklistScreen.jsx` -- nút "Tải lại đơn xin visa", gọi lại `/forms/download` không kèm `personal_info`, chỉ hiện khi `destination === 'japan'`

## Tasks & Acceptance

**Execution:**
- [x] `db/models.py` -- thêm cột `form_personal_info_json` (JSON, nullable) vào `Application` -- nền tảng lưu trữ
- [x] `api/routers/forms.py` -- `FormsRequest.personal_info: Optional[PersonalInfo] = None`; trong `download_forms`, nếu có body thì dùng + persist (`application.form_personal_info_json = body.personal_info.dict(); db.commit()`), nếu không thì load từ cột, 404 nếu cột rỗng -- cho phép gọi lại không cần FE giữ state
- [x] `api/routers/forms.py` -- thêm `PATCH /application/{application_id}/form-info` nhận `PersonalInfo`, chỉ lưu cột, không sinh PDF -- endpoint nhẹ cho bước "Tiếp tục"
- [x] `visa-client/src/screens/FormFillingScreen.jsx` -- `handleFinish` gọi PATCH trên (best-effort, try/catch nuốt lỗi) rồi `navigate('checklist')` -- đảm bảo lưu xảy ra bất kể có tải hay không
- [x] `visa-client/src/screens/ChecklistScreen.jsx` -- nút redownload gọi POST `/forms/download` với body rỗng (`{}`), xử lý blob giống `handleDownload` hiện có ở FormFillingScreen -- điểm truy cập lại

**Acceptance Criteria:**
- Given user hoàn tất Step 1-4 và bấm "Tiếp tục" ở Step5 mà KHÔNG bấm tải, when user vào ChecklistScreen, then nút "Tải lại đơn xin visa" xuất hiện (destination=japan) và tải được đúng file ZIP có dữ liệu đã điền.
- Given user đã bấm tải ở Step5 rồi mới bấm "Tiếp tục", when redownload ở ChecklistScreen, then nội dung ZIP khớp dữ liệu đã điền (không rỗng/không lỗi).
- Given destination là Trung Quốc, when vào ChecklistScreen, then nút redownload không hiện (giữ đúng giới hạn `destination != "japan"` hiện có ở backend).
- Given backend lưu `form-info` thất bại (giả lập lỗi mạng), when user bấm "Tiếp tục", then vẫn chuyển màn checklist bình thường, không có alert/chặn nào.

## Verification

**Commands:**
- `cd /Users/vuongnguyen/Desktop/visa-flow && source venv/bin/activate && python3 -m pytest tests/ -k "forms or download"` -- expected: pass, không có test nào vỡ do đổi `FormsRequest.personal_info` thành optional
- `cd visa-client && npm run build` -- expected: build sạch

**Manual checks (if no CLI):**
- Chạy live qua browser: hoàn tất flow tới Step5, bấm "Tiếp tục" KHÔNG tải, vào Checklist, bấm "Tải lại đơn xin visa" — kiểm tra file ZIP tải về mở được, đúng dữ liệu đã nhập ở Step1/Step4.

## Suggested Review Order

**Migration — cột mới trên DB đã tồn tại**

- Điểm vào: thiếu dòng này khiến mọi fetch `Application` vỡ trên DB thật (không phải DB test tự tạo mới) — phát hiện qua review adversarial, đã tái hiện lỗi bằng DB giả lập schema cũ.
  [`db/session.py:16`](../../db/session.py#L16)

- Cột mới tương ứng ở model ORM.
  [`db/models.py:101`](../../db/models.py#L101)

**Backend — optional personal_info + fallback đọc/ghi DB**

- Route chính: nhận `personal_info` optional, dùng ngay nếu có (giữ hành vi cũ), rơi vào fallback đọc DB nếu không.
  [`api/routers/forms.py:136`](../../api/routers/forms.py#L136)

- Ghi `form_personal_info_json` dời xuống SAU khi sinh PDF thành công — tránh lưu đè bản hỏng lên bản còn dùng được nếu generation throw.
  [`api/routers/forms.py:184`](../../api/routers/forms.py#L184)

- Endpoint save-only mới, có destination check mirror đúng `download_forms` (China không lưu được, tránh state chết không đọc lại được).
  [`api/routers/forms.py:208`](../../api/routers/forms.py#L208)

**Frontend — lưu độc lập với tải, cờ trạng thái cho nút redownload**

- `handleFinish`: PATCH best-effort trước khi navigate, set `formInfoSaved` khi thành công, `console.warn` khi fail (không alert, không chặn).
  [`FormFillingScreen.jsx:598`](../../visa-client/src/screens/FormFillingScreen.jsx#L598)

- Cờ `formInfoSaved` sống trong AppContext — nguồn thật để biết có dữ liệu redownload hay không, thay vì suy đoán qua `destination`.
  [`AppContext.jsx:19`](../../visa-client/src/context/AppContext.jsx#L19)

- Nút redownload chỉ hiện khi cả `destination === 'japan'` VÀ `formInfoSaved` — đúng yêu cầu "FE check trước" trong spec.
  [`ChecklistScreen.jsx:331`](../../visa-client/src/screens/ChecklistScreen.jsx#L331)

- Message lỗi tách riêng case 404 (chưa có dữ liệu — cần điền lại) khỏi lỗi tạm thời (thử lại được).
  [`ChecklistScreen.jsx:88`](../../visa-client/src/screens/ChecklistScreen.jsx#L88)

**Peripherals**

- 3 test mới: 404 khi chưa lưu, redownload thành công sau khi lưu, 400 khi non-Japan.
  [`test_forms_itinerary.py:146`](../../tests/api/test_forms_itinerary.py#L146)

- `dist/` build output regenerate theo source mới.
  [`dist/index.html`](../../visa-client/dist/index.html)

</frozen-after-approval>
