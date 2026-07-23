---
title: 'Tách status chip khỏi nút hành động trong DocumentItem — sửa nhầm lẫn UX'
type: 'bugfix'
created: '2026-07-23'
status: 'done'
route: 'one-shot'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Trên màn "Chuẩn bị hồ sơ", `StatusChip` ("Chưa kiểm tra") và nút hành động ("Tải lên"/"Tải lại") render sát nhau trong cùng một hàng, cùng dạng pill bo tròn, cùng font-weight — user thật báo không phân biệt được đâu là trạng thái (không bấm được) đâu là nút bấm thật.

**Approach:** Tách hai phần tử ra 2 hàng riêng theo đúng spec UX gốc (`ux-visa-flow-2026-06-29/DESIGN.md` § DocumentItem): StatusChip vẫn right-aligned trên hàng nhãn chính, hành động chuyển xuống hàng riêng bên dưới mô tả và đổi từ nút pill viền sang link chữ gạch chân thuần (giống convention link đang dùng ở `FormFillingScreen.jsx`). Review adversarial phát hiện tap-target bị thu hẹp quá mức so với ngưỡng 44×44px chính spec đề ra — đã patch tăng vùng bấm (padding/margin) và token hoá màu đỏ fail-state, giữ nguyên visual text-link.

</frozen-after-approval>

## Suggested Review Order

**Cấu trúc hàng — tách chip khỏi hành động**

- Điểm vào: hành động rời khỏi hàng flex chứa StatusChip, xuống dòng riêng bên dưới mô tả — đây là thay đổi cấu trúc chính giải quyết đúng vấn đề báo cáo.
  [`DocumentItem.jsx:20-32`](../../visa-client/src/components/DocumentItem.jsx#L20)

- StatusChip + dấu ✓ (state pass) giữ nguyên trong hàng nhãn chính, không đổi logic.
  [`DocumentItem.jsx:27-30`](../../visa-client/src/components/DocumentItem.jsx#L27)

**Style hành động — từ nút pill sang text-link**

- Bỏ border/background/padding-pill, chuyển `textDecoration: underline`; `type="button"` thêm vào tránh submit ẩn.
  [`DocumentItem.jsx:32-52`](../../visa-client/src/components/DocumentItem.jsx#L32)

- Màu fail-state đổi từ hex cứng `#dc2626` sang token `var(--color-error)` đã có sẵn trong `tokens.css`.
  [`DocumentItem.jsx:12`](../../visa-client/src/components/DocumentItem.jsx#L12)

**Tap-target — patch sau review adversarial**

- Padding/margin điều chỉnh để bù vùng bấm bị thu hẹp khi bỏ border-pill, tránh mis-tap lọt qua `onClick` của cả hàng (row có `onDetail`).
  [`DocumentItem.jsx:36-40`](../../visa-client/src/components/DocumentItem.jsx#L36)

**Peripherals**

- `dist/` build output regenerate theo source mới — commit cùng theo convention Railway deploy hiện có (xem `.gitignore` comment).
  [`dist/index.html`](../../visa-client/dist/index.html)

