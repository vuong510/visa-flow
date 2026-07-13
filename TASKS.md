# TASKS

## Session 2026-07-13

- [x] UX + editorial review màn "Chuẩn bị hồ sơ" theo `docs/vi-ux-style-guide.md` → spec `_bmad-output/implementation-artifacts/spec-checklist-review-fixes.md` (done, 1 loopback bad_spec)
  - Copy fixes (7), banner vàng all-skipped (đếm non-passport), confirm BottomSheet thay window.confirm, Hoàn tác thành text link, contrast, bỏ image/gif, e2e cập nhật + test mới
  - Chưa chốt (Ask First trong spec): đổi label CTA "Gửi hồ sơ cho tư vấn viên" → có brand; "Hỏi Diễm" thay "AI chat"; deferred mới trong `deferred-work.md`
  - E2e playwright CHƯA chạy (cần app đang chạy) — chỉ mới lint/build/grep + 3 review agents
- [x] Ground chatbot theo feedback tester (chị) → spec `_bmad-output/implementation-artifacts/spec-chat-grounding-facts.md` (one-shot, done)
  - FACTS: nộp qua ủy thác (không nộp trực tiếp LSQ), ảnh 4.5×3.5cm/6 tháng/nền trắng; cấm địa chỉ + xác nhận/phủ nhận; cấm CJK (cả nhánh itinerary); chống injection context/history; không xưng "tôi"
  - Smoke test live pass cả 3 kịch bản lỗi tester báo
  - CẦN CHỊ XÁC NHẬN: kích thước ảnh 4.5×3.5 (reviewer nghi spec MOFA là 4.5×4.5); hotline chính thức để thêm vào FACTS

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
