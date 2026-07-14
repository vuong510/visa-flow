# Kiến trúc Frontend — visa-client

Tài liệu cho session sau (thiết kế eval plan). Mọi path tính từ `visa-client/` trừ khi ghi khác.

## Tech stack

| Thành phần | Chi tiết | Nguồn |
|---|---|---|
| React | ^19.2.7 (StrictMode bật ở `src/main.jsx:7`) | `package.json:13` |
| Vite | ^8.1.0, plugin-react ^6.0.2 | `package.json:19-21` |
| Router | **Không có** — switch/case theo state `screen` | `src/App.jsx:16-31` |
| Lint | oxlint | `package.json:9` |
| CSS | Inline style + design tokens CSS variables | `src/tokens.css` |
| API base | `VITE_API_BASE` ?? `http://localhost:8000` | `src/context/AppContext.jsx:5` |

- Fallback route: screen key lạ → render "Màn hình ... chưa được xây dựng" (`src/App.jsx:26-30`).
- `ChatWidget` mount 1 lần cạnh `<Router/>` trong `App` (`src/App.jsx:37-38`) → hiện trên MỌI screen.

## AppContext state shape (`src/context/AppContext.jsx:7-18`)

| State | Kiểu / giá trị | Init | Persist? |
|---|---|---|---|
| `applicationId` | string (UUID từ server) | `localStorage['visa_application_id']` | ✅ localStorage (dòng 27) |
| `sessionId` | string | `localStorage['visa_session_id']` | ✅ localStorage (dòng 26) |
| `destination` | `'japan' \| 'china' \| null` | null | ❌ |
| `profile` | object: `employment_type, has_prior_stamps, travel_dates{departure,return}, prior_denial, denial_date, denial_country, passport_expiry, income_range` | `{}` | ❌ |
| `eligibilityResult` | `'eligible' \| 'edge_case' \| 'not_eligible' \| null` | null | ❌ |
| `resultStatus` | `'approved' \| 'rejected' \| 'quota_rejected' \| null` | null | ❌ |
| `checklist` | array items từ API checklist | `[]` | ❌ |
| `itineraryJson` | array (lịch trình AI tạo) hoặc null | null | ❌ |
| `extractedInfo` | object (OCR hộ chiếu) | `{}` | ❌ |
| `tripFormData` | object: `accommodation_address, contact_person, contact_phone, visit_purpose` | `{}` | ❌ |
| `screen` | string key cho Router | `'landing'` | ❌ |

Helpers trong context: `navigate(to)` (dòng 41), `startApplication()` → POST `/api/application/start` (dòng 20-29), `updateDestination(appId, dest)` → PATCH `/api/application/{id}/destination` (dòng 31-39), `API_BASE`.

## USER FLOW end-to-end

Lưu ý đếm bước: ProgressBar trong profile-questions dùng **total=10** (`ProfileQuestionsScreen.jsx:9`), các screen sau dùng **total=11** (Eligibility 7/11, Price 8/11, Form 9/11, Checklist 10/11) — **không có screen nào hiển thị "Bước 11/11"** (StatusTimeline/Result không có ProgressBar). "TripForm" (ngày đi/về) KHÔNG phải screen riêng — là Q3 bên trong profile-questions.

| # | Screen key / file | Người dùng làm gì | API gọi | AI surface | Điều kiện chuyển tiếp |
|---|---|---|---|---|---|
| 1 | `landing` — `src/screens/LandingScreen.jsx` | Đọc value props, bấm "Bắt đầu →" | GET `/api/health` (warm-up, :13); POST `/api/application/start` (:20 → context) | — | Start OK → `destination` (:21) |
| 2 | `destination` — `src/screens/DestinationScreen.jsx` | Chọn 🇯🇵 Nhật / 🇨🇳 Trung Quốc | PATCH `/api/application/{id}/destination` (:16) | — | Lưu OK → `profile-questions` (:17) |
| 3 | `profile-questions` Q1-Q2 — `src/screens/ProfileQuestionsScreen.jsx:221-263` | Q1 nghề nghiệp (6 option, auto-advance :138), Q2 từng đến Nhật/TQ (auto-advance :144) | — | — | Chọn option → Q tiếp |
| 4 | `profile-questions` Q3 (TripForm) — `:265-299` | Nhập ngày khởi hành + ngày về | — | — | Validate ngày tương lai, return ≥ departure (:150-157) → Q4 |
| 5 | `profile-questions` Q4-Q5 — `:301-383` | Q4 từng bị từ chối visa (nếu "Có": ngày + quốc gia), Q5 hạn hộ chiếu | — | — | Validate: denial ở quá khứ (:170-176); hộ chiếu còn ≥6 tháng từ ngày đi (:179-194) |
| 6 | `profile-questions` Q6 — `:385-412` | Chọn khoảng thu nhập → auto-submit | PUT `/api/application/{id}/profile` (body: `profile_json` + destination, `travel_dates`) (:203) | — | PUT OK → `eligibility-loading` (:212) |
| 7 | `eligibility-loading` — `src/screens/EligibilityScreen.jsx` | Chờ (skeleton sau 3s :90), xem card kết quả 3 màu | POST `/api/application/{id}/eligibility` (:99) | **AI đánh giá eligibility** (headline, reason, bullets, confidence_label) | `result !== 'not_eligible'` → hiện CTA "Xem chi phí dịch vụ" → `price` (:158). `not_eligible` → dead-end + mailto tư vấn (:139-151), KHÔNG có nút back |
| 8 | `price` — `src/screens/PriceScreen.jsx` | Xem giá cứng 1.540.000₫ (:8-12), bấm "Thanh toán (Demo)" | POST `/api/application/{id}/payment/demo` (:23) | — | Overlay loading 1.5s → success 1s → `form-filling` (:30-33). ChatWidget bị ẩn ở screen này |
| 9 | `form-filling` — `src/screens/FormFillingScreen.jsx` (4 sub-step, state cục bộ `step` :513) | S1: upload hộ chiếu (OCR) hoặc điền tay 17 field (:38-58, required: family_name, given_name, date_of_birth, passport_number); S2: chi tiết chuyến đi (đều optional); S3: lịch trình — mở chat AI qua `window.__openChatWithMessage` (:373,393) hoặc Bỏ qua; S4: review + tải ZIP | S1: POST `/api/extract-id` (:123), POST `.../documents` (:139), POST `.../documents/{docId}/review` (:145), GET `.../extracted-info` (:150). S4: POST `.../forms/download` → blob ZIP (:428) | **OCR hộ chiếu** + **AI review passport** + (qua chat) **AI tạo itinerary** | S4 "Tiếp tục" → `checklist` (:566). Back ở S1 → `price` (:519) |
| 10 | `checklist` — `src/screens/ChecklistScreen.jsx` | Xem danh sách tài liệu AI tạo; upload từng file (JPG/PNG/WebP/PDF :160); skip "Tôi chưa có" (lưu backend :125); xem chi tiết BottomSheet; bấm "Gửi hồ sơ cho tư vấn viên" | POST `.../checklist` (:88, cache vào ctx :93); GET `.../documents` (:103); POST `.../documents` + `/review` mỗi file (:180,195); POST `.../documents/skip|unskip` (:125,143); POST `.../submit` (:250) | **AI sinh checklist** (+confidence_note) + **AI review từng tài liệu** (pass/fail/needs_clarification) | `canSubmit` (:217): mọi item non-itinerary đều pass/needs_clarification/skipped. Skip item bắt buộc → BottomSheet xác nhận "Vẫn gửi hồ sơ" (:396). Submit OK → `status-timeline` (:252) |
| 11 | `status-timeline` — `src/screens/StatusTimelineScreen.jsx` → `result` — `src/screens/ResultScreen.jsx` | Xem timeline node; poll 5 phút/lần (:5,64) + nút ↻; khi terminal tự chuyển Result (approved 🎉 / rejected ❌ / quota_rejected 📋); "Bắt đầu hồ sơ mới" xóa localStorage → `landing` (ResultScreen:39-44) | GET `.../status` (:70) | — | `data.is_terminal` → set `resultStatus` = `submission_status` → `result` (:75-79) |

Ghi chú flow: hộ chiếu được upload lần đầu ở **form-filling Step1** (không phải eligibility như comment cũ tại `ChecklistScreen.jsx:32,210` ghi nhầm); vì cùng `doc_type='passport'`, item passport trong checklist thường đã "pass" sẵn và không có nút skip (`ChecklistScreen.jsx:360`).

## ChatWidget (`src/components/ChatWidget.jsx`)

- Mount: 1 lần trong `App` (`src/App.jsx:38`) — FAB 💬 fixed bottom-right, hiển thị trên mọi screen **trừ `price`** (early-return `if (screen === 'price') return null` tại dòng 6 — ⚠️ return TRƯỚC các hook `useState` → vi phạm Rules of Hooks, nguy cơ crash khi chuyển vào/ra `price`).
- API: POST `/api/chat` (dòng 40) với body `{ message, history, context: { destination, screen, profile, applicationId, visit_purpose: tripFormData?.visit_purpose } }` (dòng 43-47).
- Itinerary: response có `data.itinerary` → hiện card "Dùng lịch trình này" (:180-190) → PATCH `/api/application/{id}/itinerary` (:65) + `setItineraryJson`.
- Global hook: `window.__openChatWithMessage(msg)` (:16-21) — FormFillingScreen Step3 dùng để mở chat với prompt "Gợi ý lịch trình..." (prompt chỉ được điền vào input, user vẫn phải bấm Gửi).
- 3 câu hỏi gợi ý khi history rỗng (:133): mang thai / sao kê / nghề tự do.

## Pattern UI

- **BottomSheet** (`src/components/BottomSheet.jsx`): overlay đáy màn, khóa scroll body, nút "Đóng" built-in. Dùng cho: AI disclosure (NavHeader:64), chi tiết tài liệu + xác nhận skip-submit (Checklist:396,423).
- **CTAButton** (`src/components/CTAButton.jsx`): nút chính 52px full-width, màu `--color-cta`, props `loading` (spinner) / `disabled` / `secondary`.
- **BottomActionArea** (`src/components/BottomActionArea.jsx`): thanh CTA fixed bottom, max-width 430px.
- **StatusChip** (`src/components/StatusChip.jsx`): 7 trạng thái pass/fail/needs_clarification/pending/processing/uploading/reviewing.
- **ProgressBar** (`src/components/ProgressBar.jsx`): text "Bước N/total" + bar; default total=10; caller truyền 10 (profile) hoặc 11 (các screen sau) — **không nhất quán**.

## localStorage & reload

- Chỉ persist `visa_application_id` + `visa_session_id` (`AppContext.jsx:26-27`); xóa ở ResultScreen restart (:40-41).
- **Reload bất kỳ lúc nào → quay về `landing`** (screen init `'landing'`, `AppContext.jsx:18`) — không có logic resume. Bấm "Bắt đầu" lại tạo application MỚI, ghi đè ID cũ → hồ sơ dở dang bị bỏ rơi phía client (server vẫn giữ).
- `destination`, `profile`, `checklist`, `itineraryJson`, `extractedInfo` mất sạch khi reload.

## E2E tests (chạy từ repo root, `playwright.config.ts`)

- Config: testDir `./tests/e2e`, baseURL `BASE_URL` ?? `http://localhost:5173`, chromium-only, retries 1, timeout 30s (`playwright.config.ts:4-15`).
- `tests/e2e/chat_widget.spec.ts` (6 test): FAB hiển thị/mở/đóng, nút ✕ header, FAB không đè nút Gửi, Enter gửi tin không đóng panel. Chạy được trên landing, không cần backend flow.
- `tests/e2e/checklist_skip.spec.ts` (12 test): skip flow, badge "Không bắt buộc", nội dung item (Hành trình bay, ảnh 4.5×3.5, bảng lương 6 tháng, residency_proof), accept attr file input, confirm sheet + submit → timeline. ⚠️ Helper `completeFlowToChecklist` (:13-46) **lỗi thời so với UI hiện tại**: mong đợi nhập ngày ngay sau destination với label "ngày đi" (:23) — UI thật vào Q1 nghề nghiệp trước và label là "Ngày khởi hành" (`ProfileQuestionsScreen.jsx:274`); flow test cũng không đi qua form-filling (nhảy price → checklist) — khả năng cao cả suite này fail từ đầu helper.
