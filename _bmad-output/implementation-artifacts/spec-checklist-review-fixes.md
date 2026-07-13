---
title: 'Checklist — fix copy & UX theo editorial review'
type: 'bugfix'
created: '2026-07-13'
status: 'done'
baseline_commit: 'a55bc4d7364bec000c689301a7e4cdc0fbf4f82b'
context: ['{project-root}/project-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Editorial + UX review (13/07/2026, theo `docs/vi-ux-style-guide.md`) tìm ra: (1) 7 lỗi copy tiếng Việt trên ChecklistScreen (thiếu tên thương hiệu, sai trật tự từ khi interpolate số, "Bỏ qua" đọc như nút hành động, lẫn "nộp"/"gửi"); (2) trạng thái all-skipped hiển thị banner xanh "✓ Sẵn sàng gửi" + progress 100% dù chưa tải lên tài liệu nào; (3) guard duy nhất khi skip tài liệu bắt buộc là `window.confirm` native — lệch pattern BottomSheet của app, nút OK/Cancel theo ngôn ngữ browser; (4) hàng skipped có 2 nút viền ngang hàng gây nhiễu; (5) chữ xám `#9ca3af`/`#d1d5db` dưới chuẩn tương phản; (6) validate cho phép `image/gif` nhưng `accept` của input không nhận gif.

**Approach:** Sửa string-level copy theo bảng review; đảo thứ tự nhánh ReadinessBanner để all-skipped ra cảnh báo vàng thay vì xanh; thay `window.confirm` bằng BottomSheet liệt kê tài liệu bắt buộc đã bỏ qua; hạ "Hoàn tác" thành text link; nâng màu tương phản; bỏ gif khỏi allowed types; cập nhật e2e test tương ứng.

## Boundaries & Constraints

**Always:**
- Copy mới phải theo `docs/vi-ux-style-guide.md`: xưng "bạn", tên đầy đủ "Sông Hàn Tourist" ở lần nhắc đầu mỗi màn, không "ạ" trong label UI.
- "Hoàn tác" vẫn là `<button>` (e2e query theo role button).
- BottomSheet render theo pattern dự án: conditional render + `open={true}` cùng nhau.
- Backend API không đổi.

**Ask First:**
- Đổi label CTA "Gửi hồ sơ cho tư vấn viên" (đang là query trong review — chưa chốt).

**Never:**
- Không đụng `DocumentItem.jsx`, `BottomSheet.jsx`, `StatusChip.jsx`, backend, checklist JSON.
- Không đổi logic `canSubmit` (skip vẫn cho phép submit) — chỉ đổi cách *hiển thị* trạng thái.
- Ngoài phạm vi: toast khi skip request fail, pill "Đã tạo" cho itinerary, thống nhất ✅/✓, route skip tài liệu bắt buộc qua sheet "Cách lấy".

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| All-skipped | uploaded=0, mọi item non-passport skipped, passport pass → canSubmit=true | Banner vàng "Đã bỏ qua N/T — chưa tải lên tài liệu nào", bar màu vàng; CTA submit vẫn hiện | N/A |
| Submit có skip bắt buộc | ≥1 item required skipped, bấm CTA | BottomSheet mở, liệt kê tên các tài liệu bắt buộc đã bỏ qua, nút "Vẫn gửi hồ sơ" + nút "Đóng" (của BottomSheet) để hủy | Hủy → sheet đóng, không gọi API |
| Submit không skip bắt buộc | chỉ skip optional hoặc không skip | Submit thẳng, không mở sheet | Lỗi API → giữ nguyên message hiện tại |
| Upload file .gif | chọn file image/gif | Bị từ chối với message lỗi định dạng hiện có | N/A |
| Banner đếm partial | uploaded=3, skipped=2, còn 4 | "AI đã kiểm tra 3 · bỏ qua 2 · còn lại 4" | N/A |

</frozen-after-approval>

## Code Map

- `visa-client/src/screens/ChecklistScreen.jsx` — toàn bộ thay đổi UI/copy/logic nằm ở đây (ReadinessBanner :23-57, copy :36,42,200,259,273,284,307, skipped row :300-321, confirm :219-224, allowed types :157)
- `visa-client/src/components/BottomSheet.jsx` — dùng lại, không sửa; có sẵn nút "Đóng" làm hành động hủy
- `tests/e2e/checklist_skip.spec.ts` — test :95-112 assert native dialog, phải chuyển sang assert BottomSheet
- `docs/vi-ux-style-guide.md` — thẩm quyền cuối về copy

## Tasks & Acceptance

**Execution:**
- [x] `visa-client/src/screens/ChecklistScreen.jsx` — Copy: (a) `:42` → `` `AI đã kiểm tra ${uploaded} · bỏ qua ${skipped} · còn lại ${total - processed}` ``; (b) `:36` → "Đã bỏ qua ${skipped}/${total} — chưa tải lên tài liệu nào"; (c) `:200` → "Không thể tự động kiểm tra tài liệu này. Đội tư vấn Sông Hàn Tourist sẽ xem xét trực tiếp."; (d) `:273` → "Một số tài liệu cần xem xét thêm. Bạn vẫn có thể gửi hồ sơ — đội tư vấn Sông Hàn Tourist sẽ kiểm tra trực tiếp."; (e) `:259` "nộp đại sứ quán" → "nộp cho đại sứ quán"; (f) `:284` → "Đã tạo — sẽ tự điền khi bạn tải form visa"; (g) `:307` "Bỏ qua" → "Đã bỏ qua" — sửa lỗi theo review, không sáng tác thêm
- [x] `visa-client/src/screens/ChecklistScreen.jsx` — ReadinessBanner: tính `nonPassportUploaded = uploadedItems.filter(i => i.id !== 'passport').length` ở parent, truyền xuống banner; nhánh vàng khi `nonPassportUploaded === 0 && skipped > 0`, đặt TRƯỚC nhánh `readyToSubmit`, style vàng (`#92400e`/`#fef3c7`/bar `#f59e0b`), label như matrix. LƯU Ý: KHÔNG dùng `uploaded === 0` — hộ chiếu đã upload từ bước eligibility nên `uploadedCount` luôn ≥ 1 ở trạng thái all-skipped thực tế (nhánh sẽ chết)
- [x] `visa-client/src/screens/ChecklistScreen.jsx` — Thay `window.confirm` (`:219-224`) bằng state `confirmSheetOpen` + BottomSheet: title "Tài liệu bắt buộc còn thiếu", body liệt kê `item.name` của các item required-skipped, CTA "Vẫn gửi hồ sơ" gọi submit thật; tách `handleSubmit` thành check + `doSubmit`. Guards bắt buộc: (i) `doSubmit` chặn re-entry — `if (submitting) return` ở đầu; (ii) `onClose` của sheet không làm gì khi `submitting === true`; (iii) lỗi API → GIỮ sheet mở, render `submitError` trong sheet ngay trên CTA (message giữ nguyên; message ở BottomActionArea vẫn giữ cho đường submit thẳng); (iv) `useEffect` tự đóng sheet nếu `skippedRequiredItems.length === 0` khi sheet đang mở (skip có thể bị revert nền); (v) copy trong sheet KHÔNG hứa chủ động liên hệ — dùng: "Bạn chưa tải lên các tài liệu bắt buộc sau. Bạn vẫn có thể gửi hồ sơ — đội tư vấn Sông Hàn Tourist sẽ hướng dẫn bạn bổ sung khi xử lý hồ sơ."
- [x] `visa-client/src/screens/ChecklistScreen.jsx` — Hàng skipped: bỏ viền nút "Hoàn tác" (background none, border none, text `#6b7280`, giữ `<button>`); status "Đã bỏ qua" + tên item xám `#6b7280` thay `#9ca3af`; label "Không bắt buộc" trong hàng skipped `#9ca3af` thay `#d1d5db`; nút skip "Tôi chưa có tài liệu này" `#6b7280` thay `#9ca3af`
- [x] `visa-client/src/screens/ChecklistScreen.jsx` — Bỏ `'image/gif'` khỏi mảng `allowed` (`:157`) cho khớp `accept`
- [x] `tests/e2e/checklist_skip.spec.ts` — Test "submitting with skipped required items": bỏ `waitForEvent("dialog")`; assert selector chặt: `getByRole('heading', { name: /tài liệu bắt buộc còn thiếu/i })` visible + nút /vẫn gửi/i visible; bấm "Đóng" → assert heading `not.toBeVisible()` VÀ vẫn thấy /chuẩn bị hồ sơ/i (header luôn visible sau overlay nên một mình nó không đủ)
- [x] `tests/e2e/checklist_skip.spec.ts` — Thêm test "confirm sheet — Vẫn gửi hồ sơ submits": skip hết item, bấm CTA gửi, bấm nút /vẫn gửi/i trong sheet → assert điều hướng sang màn status timeline (đọc `visa-client/src/screens/StatusTimelineScreen.jsx` để chọn một chuỗi text ổn định của màn đó làm assertion)

**Acceptance Criteria:**
- Given mọi item non-passport đã skip và passport pass, when nhìn banner, then banner nền vàng với "Đã bỏ qua", không có "✓ Sẵn sàng gửi", không bar xanh 100%
- Given có item bắt buộc bị skip, when bấm "Gửi hồ sơ cho tư vấn viên", then BottomSheet mở và KHÔNG có request POST /submit cho tới khi bấm "Vẫn gửi hồ sơ"
- Given chỉ item optional bị skip (item bắt buộc đều pass), when bấm CTA, then submit thẳng không qua sheet
- Given màn checklist bất kỳ trạng thái, then không còn chuỗi "Đội tư vấn sẽ" thiếu "Sông Hàn Tourist" và không còn `window.confirm` trong file

## Spec Change Log

### 2026-07-13 — Loopback #1 (bad_spec, specLoopIteration 1→2)

- **Trigger (Auditor F1):** nhánh vàng theo điều kiện literal `uploaded === 0 && skipped > 0` là dead branch — hộ chiếu upload từ bước eligibility nên `uploadedCount ≥ 1`, banner xanh "✓ Sẵn sàng gửi" vẫn hiện ở đúng trạng thái Intent muốn diệt. **Amended:** task banner đổi sang `nonPassportUploaded === 0 && skipped > 0`. **Known-bad tránh:** đếm cả passport vào điều kiện cảnh báo.
- **Trigger (Auditor F2):** lệnh grep Verification đòi `#9ca3af` = 0 trong khi task contrast bắt dùng đúng màu đó cho label "Không bắt buộc". **Amended:** grep bỏ `#9ca3af`, ghi chú ngoại lệ 1 lần.
- **Trigger (Edge/Blind, patch-class gộp vào task để re-derive nhất quán):** race đóng sheet khi đang submit; double-tap "Vẫn gửi" gây double POST; lỗi API đóng sheet khiến error có thể không render (nằm trong gate `canSubmit &&`); sheet hiện list rỗng nếu skip bị revert nền; e2e selector lỏng (text match không scoped, header luôn visible sau overlay → pass giả); thiếu e2e nhánh xác nhận gửi; copy sheet hứa "sẽ liên hệ" không có backend nào thực hiện. **Known-bad tránh:** test pass khi sheet không mở/không đóng; hứa hẹn dịch vụ không được trigger.
- **KEEP (phải sống sót qua re-derive):** 7 chuỗi copy (a)–(g) đã audit pass — giữ nguyên từng chữ; cancel dùng nút "Đóng" có sẵn của BottomSheet (không thêm nút cancel riêng); tách `handleSubmit` (check) / `doSubmit` (gửi thật); giá trị màu `#6b7280`/`#9ca3af` như task contrast; pattern conditional render + `open={true}`; "Hoàn tác" vẫn là `<button>` dạng text link.

## Verification

**Commands:**
- `cd visa-client && npx oxlint src/screens/ChecklistScreen.jsx` — expected: 0 errors
- `cd visa-client && npm run build` — expected: build thành công
- `grep -c "window.confirm\|image/gif" visa-client/src/screens/ChecklistScreen.jsx` — expected: 0 (riêng `#9ca3af` được PHÉP xuất hiện đúng 1 lần — label "Không bắt buộc" trong hàng skipped, theo task contrast)

**Manual checks (if no CLI):**
- Chạy app, skip toàn bộ item → banner vàng "Đã bỏ qua 8/8..."; bấm CTA → BottomSheet liệt kê đúng các item bắt buộc; "Đóng" hủy, "Vẫn gửi hồ sơ" chuyển sang status-timeline

## Suggested Review Order

**Luồng xác nhận gửi (thay window.confirm)**

- Điểm vào: check tài liệu bắt buộc bị skip → mở sheet thay vì confirm native
  [`ChecklistScreen.jsx:233`](../../visa-client/src/screens/ChecklistScreen.jsx#L233)

- Gửi thật với 2 guard: chặn re-entry + chặn khi checklist hết submit-ready (skip revert nền)
  [`ChecklistScreen.jsx:243`](../../visa-client/src/screens/ChecklistScreen.jsx#L243)

- Sheet xác nhận: list item bắt buộc, error render trong sheet, onClose khoá khi đang gửi
  [`ChecklistScreen.jsx:396`](../../visa-client/src/screens/ChecklistScreen.jsx#L396)

- Tự đóng sheet khi list required-skipped rỗng — trừ lúc đang gửi
  [`ChecklistScreen.jsx:229`](../../visa-client/src/screens/ChecklistScreen.jsx#L229)

**Banner trạng thái all-skipped**

- Đếm upload không tính hộ chiếu — lý do nhánh cũ `uploaded === 0` là dead branch
  [`ChecklistScreen.jsx:211`](../../visa-client/src/screens/ChecklistScreen.jsx#L211)

- Nhánh cảnh báo vàng đặt trước `readyToSubmit` — hết tín hiệu thành công giả
  [`ChecklistScreen.jsx:31`](../../visa-client/src/screens/ChecklistScreen.jsx#L31)

**Copy & tương phản (theo style guide)**

- Thương hiệu Sông Hàn Tourist vào message review-fail
  [`ChecklistScreen.jsx:203`](../../visa-client/src/screens/ChecklistScreen.jsx#L203)

- "Đã bỏ qua" (status, hết đọc nhầm thành nút) + hàng skipped nâng contrast, Hoàn tác thành text link
  [`ChecklistScreen.jsx:330`](../../visa-client/src/screens/ChecklistScreen.jsx#L330)

- Bỏ image/gif khỏi allowed cho khớp `accept`
  [`ChecklistScreen.jsx:160`](../../visa-client/src/screens/ChecklistScreen.jsx#L160)

**Tests**

- Test cancel: selector heading chặt + assert sheet đóng thật (header không đủ)
  [`checklist_skip.spec.ts:95`](../../tests/e2e/checklist_skip.spec.ts#L95)

- Test mới nhánh xác nhận gửi → điều hướng status timeline
  [`checklist_skip.spec.ts:122`](../../tests/e2e/checklist_skip.spec.ts#L122)
