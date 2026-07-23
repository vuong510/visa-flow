
## Deferred từ review redownload-visa-form (2026-07-23)
- `PATCH /application/{id}/form-info` (mới) không kiểm tra ownership giữa session_id và application_id — client tự khai `application_id` bất kỳ, ai biết/đoán ID đều ghi đè được `form_personal_info_json` của người khác. Cùng pattern IDOR đã ghi nhận nhiều lần ở các endpoint khác trong app (`/api/feedback`, `/chat`, checklist context...) — cần 1 story auth/ownership chung, không riêng endpoint này.
- `PERSONAL_FIELDS` ở `FormFillingScreen.jsx` Bước 1 dùng key khác với `PersonalInfo` backend (`birth_place` vs `place_of_birth`, `permanent_address` vs `home_address`, `accommodation_name` vs `accommodation`, thiếu hẳn `mobile`/`email`/`accommodation_phone`/`id_number`) — pydantic lặng lẽ bỏ qua field lạ, default rỗng cho field thiếu. Có từ trước (giống hệt giữa nút tải cũ và nút tải mới do dùng chung 1 spread object), nghĩa là nhiều trường trên PDF sinh ra (nơi sinh, địa chỉ, khách sạn...) có thể trống dù user đã điền — ảnh hưởng chất lượng dữ liệu PDF thật, cần 1 đợt sửa riêng map đúng tên field.
- `generate_itinerary` trong `download_forms` không ghi lại `application.itinerary_json` sau khi tạo mới (chỉ dùng lại nếu đã có sẵn từ trước) — nếu user chưa xác nhận lịch trình ở Bước 3, mỗi lần tải/tải lại có thể ra lịch trình khác nhau (gọi AI mới mỗi lần). Có từ trước, nhưng nút "Tải lại đơn xin visa **đã điền**" mới thêm ngầm hiểu là tải lại y hệt bản cũ — nên cache `itinerary_json` ngay sau lần sinh đầu tiên để redownload thực sự ổn định.

## Deferred từ review checklist-help-escape-hatch (2026-07-23)
- **Tài liệu bị `fail` không có lối skip nào (bulk lẫn từng món)** — nút skip từng món (`Tôi chưa có tài liệu này`, `ChecklistScreen.jsx`) chỉ hiện khi `!isUploaded`, và `handleSkipAll` mới chỉ nhắm `!docs[item.id]?.id` — cả hai đều bỏ qua tài liệu đã có `id` nhưng `status:'fail'`. Đây là gap **có từ trước** (per-item skip đã vậy), không phải do đợt sửa này gây ra, nhưng đúng là user "bị kẹt" nhiều nhất (upload fail lặp lại) lại là người không dùng được escape hatch mới. Cho tài liệu `fail` skip được là một thay đổi hành vi (hiện tại không ai được phép skip tài liệu đã từng nộp), cần quyết định sản phẩm riêng trước khi làm, không tự ý mở rộng trong đợt này.
- Bulk-skip bắn N request `POST /documents/skip` đồng thời, mỗi cái tự revert optimistic UI khi fail nhưng không gộp báo lỗi cho user (vd "3/5 đã bỏ qua, 2 lỗi") — im lặng nếu 1 trong N cái bị revert.
- Bulk-skip không có bước xác nhận trước khi bắn (khác với luồng `doSubmit` đã có `BottomSheet` liệt kê rõ món nào bị skip trước khi user chốt) — hoàn tác vẫn chỉ làm được từng món một (`Hoàn tác`), không có hoàn tác hàng loạt.
- `window.__openChatWithMessage` chỉ pre-fill input, không tự gửi, và ghi đè im lặng nếu user đang gõ dở câu khác trong chat — hành vi có từ trước (dùng chung ở `FormFillingScreen.jsx`), CTA mới trong checklist kế thừa nguyên trạng.

## Deferred từ review checklist-status-button-clarity (2026-07-23)
- `ChecklistScreen.jsx:325-343` (dòng tài liệu đã "Bỏ qua") vẫn còn đúng pattern gây nhầm lẫn chip/nút mà fix này giải quyết ở `DocumentItem.jsx`: nút pill viền xanh "Tải lên" đứng cạnh text "Đã bỏ qua" + nút "Hoàn tác" không viền — 2 kiểu affordance khác nhau cạnh nhau, dễ nhầm hơn. Code path này không đi qua `DocumentItem`, nên fix hiện tại không chạm tới. Cần áp cùng pattern text-link khi có dịp sửa màn skip.
- Trạng thái `pass` render cả `StatusChip` ("Đạt", pill xanh lá) lẫn dấu `✓` riêng cạnh nhau (`DocumentItem.jsx`) — cùng kiểu tín hiệu trùng lặp như bug đã fix, chỉ là chưa có ai báo vì không gây nhầm (cả hai đều đọc là "đạt", không phải chip-vs-nút). Cân nhắc bỏ bớt 1 trong 2 nếu dọn UI đợt sau.
- `DESIGN.md:471` ghi action link là "Tải lên" / "Xem lại", nhưng code thực tế dùng "Tải lên" / "Tải lại" cho state fail/needs_clarification — lệch giữa spec gốc và implementation. "Tải lại" (re-upload) có vẻ đúng nghĩa hơn "Xem lại" (review again) cho state này, nhưng cần quyết định copy chính thức thay vì đoán.
- Màu đỏ cho action link ở state fail/needs_clarification (kế thừa từ nút viền đỏ cũ) chưa được xác nhận lại có còn hợp lý không khi đã đổi sang dạng text-link thuần theo `DESIGN.md` (spec gốc ghi action link dùng `color.text-link` cho mọi state, không phân biệt theo trạng thái).
- Không có state hover/active/focus riêng cho bất kỳ phần tử tương tác inline-style nào trong `DocumentItem.jsx` (và toàn bộ codebase nói chung — không có class CSS nào định nghĩa `:hover`) — người dùng desktop/chuột không có phản hồi khi rê chuột qua nút.
- `StatusChip.jsx:2-8` dùng hex cứng (vd `#d1fae5`/`#065f46` cho pass) lệch với token đã khai trong `DESIGN.md` (`success-light: #DCFCE7`, `success: #16A34A`) — có từ trước, không phải do đợt sửa này.

## Deferred từ review feedback-capture (2026-07-21)
- `/api/feedback` không kiểm tra ownership giữa `session_id` và `application_id` (client tự khai `application_id` bất kỳ) — cùng pattern IDOR đã ghi nhận ở các endpoint khác trong app; cần một story auth/ownership chung, không riêng endpoint này.
- `/api/feedback` không có rate-limit/CAPTCHA — giống mọi endpoint khác trong app hiện tại (spam/storage-DoS vector nếu app public).
- `FeedbackWidget.jsx` không có aria-expanded/role=dialog/focus trap — giống `ChatWidget`/`BottomSheet` hiện tại, chưa có convention a11y nào trong codebase; cần một đợt a11y riêng nếu ưu tiên.
- `screen` lưu như free-text string không enum/whitelist ở cả FE lẫn bảng `Feedback` — nếu tên màn hình bị đổi/gõ sai trong tương lai, dữ liệu phân tích bị phân mảnh âm thầm không ai biết.
- `/api/feedback` không kiểm tra `application_id` có tồn tại thật hay không (FK không được enforce ở SQLite, không có `PRAGMA foreign_keys`) — có thể tạo row `Feedback` mồ côi; giống pattern hiện có ở `documents`, cân nhắc một đợt kiểm tra FK-integrity chung.

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

## Deferred từ review 4-fixes (2026-07-14)
- Review PDF KHÔNG cap số trang (chỉ định user) — vector DoS/chi phí: PDF nghìn trang → OOM/API limit. Cân nhắc giới hạn size/số trang ở endpoint upload thay vì ở review.
- Dates không parse được (departure/denial_date rác) giờ không còn ai enforce rule ngày (prompt đã bỏ luật, Python skip) — cân nhắc nâng thành edge_case deterministic thay vì thả qua LLM.
- `declarations` (6 câu tiền án) chỉ nằm trong state màn FormFilling — rời màn/refresh là mất, và bước Xem lại chưa hiển thị 6 câu trước khi tải. Cân nhắc đưa vào AppContext + hiện ở review step.
- Ngày ký trên form (`form_filler.py` T150) vẫn dùng datetime.today() server-local — ngoài phạm vi khối RB5 nên chưa sửa; đổi sang vn_today() khi được phép đụng form logic.
- Deploy giữa chừng: khách đang ở bước cũ sẽ dính 422 khi tải form (6 field mới bắt buộc) — chấp nhận với demo.
- `fill_visa_forms_for_group` (helper không có caller) sẽ silent-skip mọi member vì thiếu 6 key mới — gỡ hoặc sửa nếu có ngày wire up.
- Lịch lễ: ngày âm (Giỗ Tổ, Tết) + ngày liền kề 2/9 trong vn_holidays.json cần chị Yến đối chiếu công bố chính thức.
