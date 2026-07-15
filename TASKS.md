# TASKS

## Session 2026-07-15

- [x] Eval plan → `docs/eval-plan.md`: 5 tầng đo (deterministic → programmatic → kịch bản → LLM-judge → adversarial), ưu tiên theo rủi ro (chat + eligibility = P0), cadence + chi phí, kiến trúc harness `tests/eval/`
  - Việc kế tiếp theo plan: (1) build harness khung + regression_seeds; (4) nhờ chị Yến gắn nhãn golden set doc review/OCR
- Cập nhật index docs: thêm eval-plan.md

## Session 2026-07-14

- [x] Bộ docs AI-context toàn sản phẩm (deep scan, bmad-document-project) → `docs/index.md` là điểm vào
  - 12 file: overview, source tree, integration, architecture×2, api-contracts (31 endpoints/8 LLM), data-models (5 tables), component inventory, dev/deploy guide
  - Phát hiện mới: 8 AI surfaces (thêm admin verify + agents pipeline 6 con chạy MOCK OCR); bug forms.py:130 (itinerary luôn 7 ngày); PDF tự tick "No" 6 câu tiền án; railway.toml không volume; e2e checklist_skip helper lỗi thời
  - Mục đích: input cho eval plan design (kèm docs/chatbot-behavior-spec.md cho phần chat)
- [x] 4 fixes từ deep scan → spec `_bmad-output/implementation-artifacts/spec-4-fixes-pdf-review-eligibility.md` (done, 92 test pass)
  - (1) itinerary parse fix — PDF ra đúng số ngày chuyến đi; (2) review PDF mọi trang 1 call Sonnet; (3) bỏ auto-"No" 6 câu tiền án — bước "Khai báo" mới (5 bước form-filling), câu hỏi trích nguyên văn từ PDF MOFA; (4) eligibility Python-first: working_days.py + vn_holidays.json (múi giờ VN, nghỉ bù), rule 10 ngày làm việc + 180 ngày deterministic, LLM chỉ còn xét freelancer
  - pytest đã vào venv (requirements-dev.txt); review 3-agent: auditor ACCEPT, 8 patch robustness đã áp
  - CHỜ CHỊ YẾN: đối chiếu vn_holidays.json (ngày âm + nghỉ bù) với công bố chính thức
- [x] Chat biết tiến độ thật → spec `_bmad-output/implementation-artifacts/spec-chat-progress-context.md` (one-shot, done, 103 test)
  - Bơm eligibility + status từng tài liệu + OCR (mask số HC/CCCD, bỏ địa chỉ) vào prompt
  - QUAN TRỌNG: chat giờ có ownership check (sessionId phải khớp) — IDOR không còn đọc được PII qua bot; các endpoint khác VẪN CHƯA có ownership
  - Reply được strip markdown tất định; fix rules-of-hooks có sẵn trong ChatWidget; behavior spec đã cập nhật (nguồn context thứ ba + 3 regression seed mới)

## Session 2026-07-13

- [x] UX + editorial review màn "Chuẩn bị hồ sơ" theo `docs/vi-ux-style-guide.md` → spec `_bmad-output/implementation-artifacts/spec-checklist-review-fixes.md` (done, 1 loopback bad_spec)
  - Copy fixes (7), banner vàng all-skipped (đếm non-passport), confirm BottomSheet thay window.confirm, Hoàn tác thành text link, contrast, bỏ image/gif, e2e cập nhật + test mới
  - Chưa chốt (Ask First trong spec): đổi label CTA "Gửi hồ sơ cho tư vấn viên" → có brand; "Hỏi Diễm" thay "AI chat"; deferred mới trong `deferred-work.md`
  - E2e playwright CHƯA chạy (cần app đang chạy) — chỉ mới lint/build/grep + 3 review agents
- [x] Ground chatbot theo feedback tester (chị) → spec `_bmad-output/implementation-artifacts/spec-chat-grounding-facts.md` (one-shot, done)
  - FACTS: nộp qua ủy thác (không nộp trực tiếp LSQ), ảnh 4.5×3.5cm/6 tháng/nền trắng; cấm địa chỉ + xác nhận/phủ nhận; cấm CJK (cả nhánh itinerary); chống injection context/history; không xưng "tôi"
  - Smoke test live pass cả 3 kịch bản lỗi tester báo
  - Kích thước ảnh: CHỐT 4.5×3.5cm theo chị Yến (domain authority — không đổi theo kiến thức model); được xác nhận lần 2 bởi visa_checklist.json của japan-visa-bot (45×35mm)
- [x] Port đợt 1 từ Diễm bot (japan-visa-bot) vào chat → spec `_bmad-output/implementation-artifacts/spec-chat-diem-persona-port.md` (one-shot, done)
  - Persona Thu Diễm (em/anh-chị/ạ), hotline 028 7301 2939 / 028 3848 1390 (tìm thấy trong _base.md — hết treo), P0 compliance, out-of-scope + disclaimer, 7 hard rules + spec ảnh đầy đủ (CHỈ scope visa Nhật)
  - Đợt 2 (chưa làm): case rules theo nghề/nhóm, bộ eval personas.json, pronoun theo gender, fix router "gợi ý" — xem deferred-work.md
  - Phí (520k+200k, hết hạn 31/3/2026) + thời gian xử lý: CHỜ chị Yến xác nhận số mới rồi thêm vào FACTS
- [x] Chat hết "mù" checklist → spec `_bmad-output/implementation-artifacts/spec-chat-checklist-context.md` (one-shot, done)
  - /chat bơm app.checklist_json (đúng nội dung UI) vào prompt — bot trả lời được "cần giấy gì / lấy ở đâu" từ how_to_get kiểm duyệt
  - Sanitize chống injection qua travel_dates; unit test formatter 5/5
  - QUAN TRỌNG (deferred): IDOR applicationId không có ownership check — phải fix trước khi production thật

## Completed This Session

- [x] PRD finalized: `_bmad-output/planning-artifacts/prds/prd-vuongnguyen-2026-06-29/prd.md`
- [x] UX design finalized: `DESIGN.md` + `EXPERIENCE.md` in `ux-designs/ux-visa-flow-2026-06-29/`
- [x] Architecture spine finalized: `architecture/architecture-visa-flow-2026-06-29/ARCHITECTURE-SPINE.md`
- [x] Epics & stories complete: `_bmad-output/planning-artifacts/epics.md`
  - 5 epics (Epic 5 deferred post-v1)
  - 12 stories with full acceptance criteria
  - All 31 in-scope FRs covered

## All Stories Complete ✅

1. ~~**Story 1.1**~~ ✅ — Backend skeleton: FastAPI + SQLite + session_id middleware + Application + Document tables
2. ~~**Story 1.2**~~ ✅ — Design system + Landing screen: React+Vite scaffold, all tokens, NavHeader, Landing, Destination selection
3. ~~**Story 1.3**~~ ✅ — Profile question flow: 6 question screens, ProgressBar, PUT /api/application/{id}/profile
4. ~~**Story 1.4**~~ ✅ — AI eligibility gate: Haiku, EligibilityCard (3 states), Bước 7/10, "Hồ sơ của bạn trông tốt ✓"
5. ~~**Story 1.5**~~ ✅ — Price screen (Bước 8/10), full-screen payment overlay, demo payment → checklist
6. ~~**Story 2.1**~~ ✅ — Checklist generation: deterministic per employment_type, skeleton loading, Bước 9/10
7. ~~**Story 2.2**~~ ✅ — Checklist item detail bottom sheet (YÊU CẦU/ĐỊNH DẠNG/TẠI SAO CẦN), upload trigger
8. ~~**Story 3.1**~~ ✅ — Document upload: multipart POST, saves to uploads/{app_id}/, Document DB record
9. ~~**Story 3.2**~~ ✅ — AI document review: Sonnet vision for images, StatusChip (pass/fail/needs_clarification)
10. ~~**Story 3.3**~~ ✅ — Readiness banner, Submit CTA when all pass, POST /submit → status-timeline
11. ~~**Story 4.1**~~ ✅ — Status timeline: 4 nodes, active pulse dot, 5-min polling, refresh button
12. ~~**Story 4.2**~~ ✅ — Result screen: 3 states (approved/rejected/quota_rejected)

## Key Files

- Backend: `api/routers/application.py`, `api/ai.py`
- Frontend screens: `visa-client/src/screens/`
- Components: `StatusChip.jsx`, `DocumentItem.jsx`, `ProgressBar.jsx`
- DB: `visa_flow.db`, models in `db/models.py`
- Uploads: `uploads/{app_id}/`

## Deferred / Post-v1

- FR8: Group/family compound assessment
- FR15: Checklist auto-update from embassy monitoring (depends on Epic 5)
- Epic 5 (FR25–FR27): Automated embassy requirement monitoring
- PostgreSQL migration, Cloudflare R2, MoMo payment SDK, admin dashboard
- Real payment gateway integration (replace demo_completed)
- Document upload: add PDF support via Anthropic document API

## Feedback tester (2026-07-12)

- ✅ **Skip upload tài liệu** — ghép 2 bản: UX "Bỏ qua/Hoàn tác" từ origin/main (Song Han feedback) + backend persistence (`review_status="skipped"`, endpoint skip/unskip, guard race + guard AI review). Spec: `_bmad-output/implementation-artifacts/spec-skip-document-upload.md`. Bản cũ đầy đủ: branch `backup-local-skip`.
- ⏳ **Cập nhật bảng giá visa mới** — CHỜ giá final. Vị trí: `visa-client/src/screens/PriceScreen.jsx` (990.000/550.000/1.540.000 ₫). Xem `deferred-work.md`.
