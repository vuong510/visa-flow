
## Cập nhật bảng giá visa mới (deferred 2026-07-12)
- Nguồn: feedback tester — "đổi lại theo bảng giá visa mới"
- Chờ: bảng giá final từ user (phí tư vấn + phí nộp hồ sơ, có thể khác nhau giữa Nhật/Trung)
- Vị trí sửa: `visa-client/src/screens/PriceScreen.jsx:9-12` (hardcode 990.000 / 550.000 / tổng 1.540.000 ₫)

## Deferred từ review skip-document-upload (2026-07-12)
- `itineraryJson` chỉ nằm in-memory trong AppContext, không rehydrate sau reload — lịch trình đã tạo hiển thị lại "AI tạo" khi reload trang (lỗi có sẵn trước story này).
- Cân nhắc unique constraint `(application_id, doc_type)` cho bảng `documents` (cần migration) để chặn row trùng ở tầng DB.
- Row `skipped` cũ vẫn còn trong `GET /documents` sau khi khách upload lại cùng doc_type (FE dedupe last-wins nên không ảnh hưởng UI; chỉ ảnh hưởng staff-view tương lai — cân nhắc dọn row skipped khi upload).
- Race 2 tab giữa `review_document` và `skip_document` (check-then-act không atomic) — cần transaction/lock nếu app lên production.

## Deferred từ review checklist-review-fixes (2026-07-13)
- `tests/e2e/checklist_skip.spec.ts` — vòng lặp `waitForTimeout(100)` khi skip hàng loạt là nguồn flake (nên thay bằng locator auto-wait / `expect.toPass()`); kèm race: skip POST bị revert sau khi loop kết thúc có thể unmount CTA submit giữa test (pre-existing).
- `ChecklistScreen.jsx` — message lỗi định dạng upload "Chỉ chấp nhận ảnh (JPG, PNG) hoặc PDF" thiếu WebP dù `allowed`/`accept` nhận webp (copy pre-existing).
- E2e chưa cover nhánh lỗi API của confirm sheet (submit fail → sheet giữ mở + error trong sheet) — cần mock backend failure (route interception) mới test được.

## Deferred từ review chat-grounding (2026-07-13)
- Chưa có bộ eval tự động cho chatbot (địa chỉ → từ chối; tự nộp → quy định ủy thác; không CJK trong output) — mỗi lần sửa prompt có thể regress lặng lẽ.
- FACTS chưa có hotline/kênh liên hệ thật của Sông Hàn Tourist — khi có số chính thức thì thêm vào để referral mạnh hơn (hiện trỏ về chat in-app + gửi hồ sơ).
- ~~Persona bot cho chat visa-flow chưa chốt~~ → ĐÃ CHỐT 13/07: dùng Thu Diễm (port đợt 1).

## Deferred từ port Diễm đợt 1 (2026-07-13)
- Router keyword trong `api/routers/chat.py:28` — substring "gợi ý"/"plan" hijack cả câu hỏi thường ("gợi ý cách chứng minh tài chính") sang nhánh itinerary, bypass mọi guardrail; kèm `except: pass` nuốt lỗi. Cần intent check chặt hơn.
- Pronoun theo gender: `profile` có thể chứa gender (từ OCR CCCD) — bot đang hard-code "anh/chị"; đợt 2 truyền gender vào context như Diễm bot làm. Headline "Hồ sơ của bạn trông tốt ✓" màn eligibility cũng còn "bạn".
- Đợt 2 còn lại: case rules theo nghề/nhóm đi từ jp_module.md; bộ eval từ tests/personas.json; phí + thời gian xử lý chờ chị Yến xác nhận.

## Deferred từ review chat-checklist-context (2026-07-13)
- IDOR: /chat (và hầu hết endpoint) nhận applicationId không kiểm tra ownership theo session_id — khách có thể đọc checklist/ngày đi của application khác qua bot. Cần story auth/ownership trước khi lên production thật.
- checklist_json cache 1 lần không invalidate khi user đổi travel_dates/employment_type — bot + UI có thể nói ngày cũ.
- Row checklist_json cũ từ thời còn generate bằng LLM (trước khi chuyển deterministic) chưa được purge/đánh version — giờ được inject với nhãn "đã kiểm duyệt".
- Logging: /chat có 2 chỗ nuốt exception im lặng — không biết bot đang trả lời "mù" hay "có checklist".
- Prompt caching cho system prompt chat (giờ ~2-3K token/message với checklist).
