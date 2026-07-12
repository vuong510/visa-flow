
## Cập nhật bảng giá visa mới (deferred 2026-07-12)
- Nguồn: feedback tester — "đổi lại theo bảng giá visa mới"
- Chờ: bảng giá final từ user (phí tư vấn + phí nộp hồ sơ, có thể khác nhau giữa Nhật/Trung)
- Vị trí sửa: `visa-client/src/screens/PriceScreen.jsx:9-12` (hardcode 990.000 / 550.000 / tổng 1.540.000 ₫)

## Deferred từ review skip-document-upload (2026-07-12)
- `itineraryJson` chỉ nằm in-memory trong AppContext, không rehydrate sau reload — lịch trình đã tạo hiển thị lại "AI tạo" khi reload trang (lỗi có sẵn trước story này).
- Cân nhắc unique constraint `(application_id, doc_type)` cho bảng `documents` (cần migration) để chặn row trùng ở tầng DB.
- Row `skipped` cũ vẫn còn trong `GET /documents` sau khi khách upload lại cùng doc_type (FE dedupe last-wins nên không ảnh hưởng UI; chỉ ảnh hưởng staff-view tương lai — cân nhắc dọn row skipped khi upload).
- Race 2 tab giữa `review_document` và `skip_document` (check-then-act không atomic) — cần transaction/lock nếu app lên production.
