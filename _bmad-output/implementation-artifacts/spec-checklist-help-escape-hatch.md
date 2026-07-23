---
title: 'Đỡ user bị kẹt ở màn checklist — chat CTA, bỏ qua tất cả, ô lỗi rõ hơn'
type: 'feature'
created: '2026-07-23'
status: 'done'
route: 'one-shot'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** User bị kẹt ở màn "Chuẩn bị hồ sơ" theo 3 hướng: không biết cách lấy 1 tài liệu (không có lối dẫn rõ tới chat), muốn dừng tự làm giữa chừng nhưng phải skip từng món một, và không thấy rõ lý do tài liệu bị AI đánh fail.

**Approach:** Cả 3 đều tái dùng hạ tầng có sẵn, không đổi backend/schema: (1) CTA text-link trong bottom sheet chi tiết tài liệu, mở chat kèm câu hỏi dựng sẵn theo đúng tên tài liệu (tái dùng `window.__openChatWithMessage`); (2) nút "Bỏ qua tất cả" gọi lặp `handleSkip` có sẵn cho các món chưa upload/chưa skip (trừ hộ chiếu), nối thẳng vào luồng xác nhận submit đã có; (3) ô báo lỗi fail/needs_clarification tách màu theo đúng bảng màu StatusChip thay vì đồng nhất đỏ. Review adversarial phát hiện thêm: thiếu chặn skip hộ chiếu, thiếu `type="button"`/tap-target ở 2 nút mới, thiếu guard chống double-tap cho bulk-skip — đã patch cả 3.

</frozen-after-approval>

## Suggested Review Order

**Bỏ qua tất cả — escape hatch chính**

- Điểm vào: `handleSkipAll` — lặp qua các món chưa upload/chưa skip, loại trừ hộ chiếu, có guard `bulkSkipping` chống double-tap.
  [`ChecklistScreen.jsx:225-236`](../../visa-client/src/screens/ChecklistScreen.jsx#L225)

- Nút render — chỉ hiện khi còn món chưa xử lý (`remainingCount > 0`), tap-target đủ lớn, disable khi đang chạy.
  [`ChecklistScreen.jsx:386-406`](../../visa-client/src/screens/ChecklistScreen.jsx#L386)

**Chat CTA — dẫn tới hỗ trợ khi không biết lấy tài liệu**

- CTA trong bottom sheet chi tiết, mở chat với câu hỏi dựng sẵn theo tên tài liệu đang xem.
  [`ChecklistScreen.jsx:471-488`](../../visa-client/src/screens/ChecklistScreen.jsx#L471)

**Ô báo lỗi — tách màu theo trạng thái thật**

- `fail` (đỏ, "⚠️ Lý do:") vs `needs_clarification` (vàng hổ phách, "Cần làm rõ:") — khớp đúng bảng màu StatusChip, tránh nhìn báo động y hệt cho state không chặn gửi hồ sơ.
  [`DocumentItem.jsx:10-16`](../../visa-client/src/components/DocumentItem.jsx#L10)
  [`DocumentItem.jsx:56-67`](../../visa-client/src/components/DocumentItem.jsx#L56)

**Peripherals**

- `dist/` build output regenerate theo source mới.
  [`dist/index.html`](../../visa-client/dist/index.html)

