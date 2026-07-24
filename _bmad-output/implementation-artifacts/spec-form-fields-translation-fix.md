---
title: 'Sửa lỗi form visa: dịch tiếng Việt hardcode + field trống do sai tên key'
type: 'bugfix'
created: '2026-07-24'
status: 'done'
context: []
baseline_commit: '3ed91493158b26b9975dfea1c58cc7765d190fba'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Tester báo (kèm ảnh PDF thật) 2 lỗi trên đơn visa sinh ra: (1) 2 ô "Place of issue"/"Issuing authority" bị in tiếng Việt có dấu "Cục Quản lý Xuất nhập cảnh" thay vì tiếng Anh; (2) nhiều ô trống dù user đã điền ở Bước 1 (SĐT di động, email, địa chỉ hiện tại, địa chỉ/SĐT công ty, SĐT khách sạn, số CCCD).

**Approach:** Đã điều tra: backend (`_build_info`, `VISA_TEXT_MAP`) đã map đúng gần hết các field này tới đúng widget PDF — gốc lỗi chỉ có 2 chỗ: (a) chuỗi tiếng Việt hardcode trong `form_filler.py`, dịch sang "Immigration Department"; (b) `FormFillingScreen.jsx` Bước 1 dùng sai tên key so với `PersonalInfo` (`birth_place`≠`place_of_birth`, `permanent_address`≠`home_address`, `accommodation_name`≠`accommodation` — bị pydantic âm thầm bỏ qua) và hoàn toàn không có ô nhập cho `mobile`/`email`/`company_address`/`accommodation_phone`/`id_number` dù backend đã sẵn field. Thêm mới field `company_phone` (PersonalInfo + widget `emp_tel[0]` đã có sẵn trong `VISA_TEXT_MAP` nhưng chưa từng được set) để khớp ô "Tel." dưới mục nhà tuyển dụng cũng đang trống trong ảnh tester gửi.

## Boundaries & Constraints

**Always:**
- Test bằng PDF thật: sau khi sửa, tải 1 file ZIP thật qua flow đầy đủ, mở `don_xin_visa.pdf`, soi từng field bằng mắt — không chỉ dựa vào build/pytest xanh (CLAUDE.md: "KHÔNG thay đổi PDF form logic khi chưa test").
- Giữ nguyên toàn bộ layout/thứ tự field hiện có của các field không đổi tên; field đổi tên key giữ nguyên label/vị trí trong danh sách, chỉ đổi `key`.
- Field mới thêm phải optional (`required: false`), không chặn luồng Bước 1 của user đã điền dở dang trước đó.

**Ask First:**
- Không phát sinh — các quyết định (dịch "Immigration Department", thêm field nào, field nào cố ý để trống) đã chốt với user trước khi viết spec.

**Never:**
- Không đổi logic tìm widget (`_find_widget`, `_field_matches`) hay cấu trúc `VISA_TEXT_MAP` ngoài phạm vi đã nêu.
- Không thêm UI cho "Certificate of Eligibility No." — cố ý để trống (áp dụng long-stay visa, không áp dụng visa du lịch qua đại lý).
- Không thêm field "phone" (T97[0], ô "Tel." landline dưới địa chỉ hiện tại, tách biệt với "Mobile No.") — không có field nguồn tương ứng trong `PersonalInfo`, để trống có chủ đích thay vì bịa liên kết với `mobile`.
- Không đụng `contact_in_japan` (field rời rạc hiện tại, đã bị silently-drop tương tự nhưng không nằm trong danh sách tester báo) — để riêng, không mở rộng scope.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| User điền đủ field mới (mobile/email/company_address/accommodation_phone/id_number/company_phone) | Text input hợp lệ | ZIP sinh ra có đúng giá trị ở widget T3[0]/T3[1]/emp_adr[0]/emp_tel[1]/T37[0]/emp_tel[0] | N/A |
| User để trống field mới (đều optional) | "" | Widget tương ứng để trống, không lỗi | N/A |
| User đã có OCR hộ chiếu điền `place_of_birth`/`home_address`/`accommodation` qua flow cũ (trước fix) | Dữ liệu cũ trong `extractedInfo`/state | Sau fix, key đổi tên vẫn nhận đúng giá trị vì `emptyPersonal()` tự sinh theo `PERSONAL_FIELDS` mới — không có state cũ nào persist qua bug này (bug này chưa từng lưu được dữ liệu key sai) | N/A |
| Mọi PDF sinh ra (kể cả không sửa gì khác) | Bất kỳ | "Place of issue"/"Issuing authority" luôn là "Immigration Department", không còn tiếng Việt | N/A |

## Code Map

- `api/form_filler.py` -- dịch chuỗi hardcode "Cục Quản lý Xuất nhập cảnh" → "Immigration Department" (dòng ~307-314)
- `api/routers/forms.py` -- thêm field `company_phone: str = ""` vào `PersonalInfo`; thêm `"company_phone": personal.company_phone,` vào `_build_info()` return dict
- `visa-client/src/screens/FormFillingScreen.jsx` -- sửa 3 key sai tên (`birth_place`→`place_of_birth`, `permanent_address`→`home_address`, `accommodation_name`→`accommodation`) trong `PERSONAL_FIELDS`; thêm 6 field mới (`mobile`, `email`, `id_number`, `company_address`, `company_phone`, `accommodation_phone`)

## Tasks & Acceptance

**Execution:**
- [x] `api/form_filler.py` -- đổi 2 giá trị hardcode T57[0]/T57[1] từ "Cục Quản lý Xuất nhập cảnh" sang "Immigration Department" -- xoá nguồn tiếng Việt duy nhất trên form
- [x] `api/routers/forms.py` -- thêm `company_phone: str = ""` vào class `PersonalInfo`, thêm dòng tương ứng vào `_build_info()` -- khớp widget `emp_tel[0]` đã sẵn có trong VISA_TEXT_MAP
- [x] `visa-client/src/screens/FormFillingScreen.jsx` -- sửa 3 `key` sai tên trong `PERSONAL_FIELDS`, giữ nguyên `label`/vị trí -- nối đúng dữ liệu user điền tới `PersonalInfo`
- [x] `visa-client/src/screens/FormFillingScreen.jsx` -- thêm 6 entry mới vào `PERSONAL_FIELDS` (`mobile` "Số điện thoại di động", `email` "Email", `id_number` "Số CCCD/CMND", `company_address` "Địa chỉ công ty (tiếng Anh)", `company_phone` "SĐT công ty", `accommodation_phone` "SĐT khách sạn"), tất cả `required: false`, đặt cạnh field liên quan (id_number cạnh passport_number; mobile/email cạnh permanent info; company_phone cạnh company_address; accommodation_phone cạnh accommodation_address) -- thu thập đủ dữ liệu backend đã sẵn sàng nhận

**Acceptance Criteria:**
- Given user đi hết Bước 1-5 với đầy đủ field mới, when tải ZIP (từ FormFilling hoặc redownload ở Checklist), then `don_xin_visa.pdf` không còn ký tự tiếng Việt ở bất kỳ ô nào, và các ô Mobile/Email/địa chỉ hiện tại/công ty/SĐT khách sạn/CCCD đều có giá trị đúng như đã nhập.
- Given user để trống toàn bộ field mới (optional), when tải ZIP, then vẫn sinh thành công, các ô tương ứng trống, không lỗi 422/500.
- Given PDF cũ đã sinh trước đợt fix, when so sánh field layout, then vị trí/label field không đổi (chỉ nội dung/field mới thêm), không phá layout hiện có.

## Verification

**Commands:**
- `cd /Users/vuongnguyen/Desktop/visa-flow && source venv/bin/activate && python3 -m pytest tests/ -k "forms or download"` -- expected: pass
- `cd visa-client && npm run build` -- expected: build sạch

**Manual checks:**
- Chạy live qua browser hết flow tới Bước 5, điền đủ toàn bộ field (kể cả field mới), tải ZIP thật, mở `don_xin_visa.pdf` bằng PDF reader thật (không chỉ đọc field_value qua script) — soi bằng mắt xác nhận: (1) không còn chữ có dấu tiếng Việt ở "Place of issue"/"Issuing authority"; (2) Mobile No./Email/địa chỉ hiện tại/employer Tel-Address/SĐT khách sạn/CCCD đều đúng giá trị đã điền, không trống.

## Suggested Review Order

**Dịch tiếng Việt hardcode**

- Điểm vào: nguồn tiếng Việt duy nhất trên form, đã render ảnh thật so khớp với ảnh tester gửi để xác nhận.
  [`form_filler.py:307-314`](../../api/form_filler.py#L307)

**Nối đúng dữ liệu Bước 1 → PersonalInfo**

- 3 key đổi tên để hết bị pydantic âm thầm bỏ qua — đây là gốc gây "field trống dù đã điền".
  [`FormFillingScreen.jsx:48-61`](../../visa-client/src/screens/FormFillingScreen.jsx#L48)

- `company_phone` field mới, khớp widget `emp_tel[0]` đã có sẵn trong VISA_TEXT_MAP nhưng chưa từng được set.
  [`forms.py:35`](../../api/routers/forms.py#L35)
  [`forms.py:112`](../../api/routers/forms.py#L112)

**Patch sau review — tap-target/UX nhỏ**

- 3 field số điện thoại thêm `type: 'tel'`; `id_number` dời cạnh `passport_number` đúng ý spec gốc; nhóm lại thứ tự field theo chủ đề (định danh → liên hệ → hộ chiếu → công việc → lưu trú).
  [`FormFillingScreen.jsx:48-63`](../../visa-client/src/screens/FormFillingScreen.jsx#L48)

**Peripherals**

- `dist/` build output regenerate theo source mới.
  [`dist/index.html`](../../visa-client/dist/index.html)

</frozen-after-approval>
