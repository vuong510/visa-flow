# Inventory Components & Screens — visa-client

Path tính từ `visa-client/src/`.

## Screens (9 file — mount qua switch/case tại `App.jsx:16-31`)

| Screen | Key trong switch | Chức năng 1 dòng | File |
|---|---|---|---|
| LandingScreen | `landing` | Hero + value props, "Bắt đầu →" tạo application (POST start) | `screens/LandingScreen.jsx` |
| DestinationScreen | `destination` | Chọn Nhật Bản / Trung Quốc (PATCH destination) | `screens/DestinationScreen.jsx` |
| ProfileQuestionsScreen | `profile-questions` | 6 câu hỏi tuần tự (nghề, đã đến chưa, ngày đi/về, từ chối visa, hạn hộ chiếu, thu nhập) → PUT profile | `screens/ProfileQuestionsScreen.jsx` |
| EligibilityScreen | `eligibility-loading` | Gọi AI eligibility, card 3 màu eligible/edge_case/not_eligible; not_eligible = dead-end | `screens/EligibilityScreen.jsx` |
| PriceScreen | `price` | Bảng giá cứng 1.540.000₫ + thanh toán demo (overlay giả lập) | `screens/PriceScreen.jsx` |
| FormFillingScreen | `form-filling` | Wizard 4 sub-step: OCR hộ chiếu/điền tay → chi tiết chuyến đi → lịch trình AI → tải ZIP đơn visa | `screens/FormFillingScreen.jsx` |
| ChecklistScreen | `checklist` | Checklist AI sinh, upload + AI review từng tài liệu, skip, gửi hồ sơ | `screens/ChecklistScreen.jsx` |
| StatusTimelineScreen | `status-timeline` | Timeline trạng thái, poll 5 phút, terminal → result | `screens/StatusTimelineScreen.jsx` |
| ResultScreen | `result` | Kết quả cuối approved/rejected/quota_rejected + restart (xóa localStorage) | `screens/ResultScreen.jsx` |

Sub-component nội bộ screen (không export riêng): `ValueRow` (Landing:87), `SkeletonCard`/`EligibilityCard` (Eligibility:8,31), `Step1-4`/`SummaryRow` (FormFilling:84,282,360,421,73), `SkeletonList`/`ReadinessBanner` (Checklist:10,23), `TimelineNode` (StatusTimeline:7), `InlineError` (ProfileQuestions:82).

## Components (10 file trong `components/`)

| Component | Props chính | Dùng ở đâu | File |
|---|---|---|---|
| NavHeader | `title, onBack, showBack=true, rightAction` — header sticky 56px; mặc định nút "AI" mở BottomSheet disclosure (:48-61) | Mọi screen | `components/NavHeader.jsx` |
| CTAButton | `label, onClick, disabled, loading, secondary` — nút chính 52px, spinner khi loading | Mọi screen có CTA | `components/CTAButton.jsx` |
| OptionButton | `label, selected, onClick, disabled` — nút chọn 56px, `aria-pressed`, ✓ khi selected | Destination, ProfileQuestions | `components/OptionButton.jsx` |
| ProgressBar | `current, total=10` — "Bước N/total" + bar % | ProfileQuestions (/10), Eligibility 7/11, Price 8/11, FormFilling 9/11, Checklist 10/11 | `components/ProgressBar.jsx` |
| BottomActionArea | `children` — vùng CTA fixed bottom, max-width 430 | Landing, ProfileQuestions, Eligibility, Price, Checklist | `components/BottomActionArea.jsx` |
| BottomSheet | `open, onClose, title, children` — sheet đáy màn, khóa body scroll, nút "Đóng" built-in | NavHeader (AI info), Checklist (chi tiết doc + confirm skip) | `components/BottomSheet.jsx` |
| StatusChip | `status` — 7 variant: pass/fail/needs_clarification/pending/processing/uploading/reviewing (fallback pending) | DocumentItem | `components/StatusChip.jsx` |
| DocumentItem | `item, docState, onUpload, onDetail` — row tài liệu: tên + mô tả + StatusChip + nút Tải lên/Tải lại + note lỗi đỏ | ChecklistScreen | `components/DocumentItem.jsx` |
| ChatWidget | không props — đọc context; FAB 💬 + panel chat; ẩn ở screen `price` (:6); expose `window.__openChatWithMessage` (:16) | Mount global `App.jsx:38` | `components/ChatWidget.jsx` |
| PersonalInfoModal | `onSubmit, onClose, loading, initialValues` — modal form 15+ field, OCR CCCD/hộ chiếu qua `/api/extract-id` | **⚠️ DEAD CODE — không được import ở đâu** (grep toàn `src/` không có usage) | `components/PersonalInfoModal.jsx` |

## Design tokens chính (`tokens.css`)

| Token | Giá trị | Dòng |
|---|---|---|
| Font | `'Be Vietnam Pro'` (Google Fonts import, weights 400-700) | :1, :59 |
| `--color-primary` | `#1A2E4A` (navy — nền NavHeader, hero Landing) | :5 |
| `--color-cta` | `#2563EB` (xanh dương — mọi CTA, chat, progress) | :6 |
| `--color-cta-hover/pressed` | `#1D4ED8` / `#1E40AF` | :7-8 |
| `--color-background` / `--color-surface` | `#F5F7FA` / `#FFFFFF` | :9-10 |
| `--color-success/warning/error` | `#16A34A` / `#D97706` / `#DC2626` (+bản `-light`) | :11-16 |
| `--color-text-primary/secondary/muted` | `#1A1A2E` / `#374151` / `#6B7280` | :17-19 |
| `--radius-card/button/input/chip` | 16 / 12 / 10 / 20 px | :24-27 |
| `--shadow-card`, `--shadow-modal` | shadow 2 lớp nhẹ / modal đậm | :46-48 |
| Motion | `--duration-fast/base/slow` 150/250/400ms; `--ease-spring` cho BottomSheet | :51-56 |
| Reduced motion | `prefers-reduced-motion` tắt animation | :62-67 |

Lưu ý: nhiều màu semantic (`#d1fae5`, `#fee2e2`, `#fef3c7`, `#065f46`, `#991b1b`, `#92400e`...) bị hardcode inline trong screens thay vì dùng token (vd `EligibilityScreen.jsx:37-41`, `StatusChip.jsx:2-8`) — token success/warning/error-light gần như không được tham chiếu.

## Điểm đáng chú ý cho eval

- `PersonalInfoModal.jsx` dead code (chức năng đã được thay bằng Step1 của FormFillingScreen).
- `ChatWidget.jsx:6` early-return trước hooks → vi phạm Rules of Hooks khi vào/ra screen `price`.
- ProgressBar total 10 (ProfileQuestions:9) vs 11 (các screen sau) — không màn nào hiện "Bước 11/11".
- Comment sai tại `ChecklistScreen.jsx:32,210`: nói hộ chiếu upload "từ bước eligibility" nhưng thực tế upload ở form-filling Step1.
