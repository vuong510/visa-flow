---
title: 'Chatbot — ground theo FACTS kiểm chứng, thu hẹp bề mặt thông tin'
type: 'bugfix'
created: '2026-07-13'
status: 'done'
route: 'one-shot'
---

# Chatbot — ground theo FACTS kiểm chứng, thu hẹp bề mặt thông tin

## Intent

**Problem:** Tester (13/07) bắt được chatbot tự bịa từ kiến thức nền của Haiku: tư vấn khách lên nộp trực tiếp tại lãnh sự quán (quy định mới chỉ nhận qua công ty ủy thác), bịa sai địa chỉ lãnh sự quán, lộ ký tự tiếng Nhật, thiếu quy tắc ảnh chụp trong 6 tháng. Dòng cũ "khuyên liên hệ đại sứ quán" trong prompt chủ động gây ra lỗi này.

**Approach:** Thu hẹp bề mặt thông tin của bot theo hướng stakeholder: khối FACTS kiểm chứng (nộp qua ủy thác, ảnh 4.5×3.5cm/6 tháng/nền trắng) là nguồn thủ tục duy nhất; cấm cung cấp/xác nhận/phủ nhận địa chỉ-liên hệ của mọi cơ quan; mọi phí/thời hạn/quy định ngoài FACTS → referral về đội tư vấn Sông Hàn Tourist với kênh in-app cụ thể; cấm ký tự Nhật/Trung (cả nhánh itinerary); chống prompt-injection qua context và history; không tự xưng "tôi".

## Suggested Review Order

**Grounding & lệnh cấm (system prompt chính)**

- Khối FACTS — nguồn thủ tục duy nhất; sửa cả gốc lỗi "khuyên liên hệ đại sứ quán"
  [`ai.py:120`](../../api/ai.py#L120)

- Cấm cung cấp lẫn xác nhận/phủ nhận địa chỉ, quận/đường, SĐT, email của mọi cơ quan
  [`ai.py:129`](../../api/ai.py#L129)

- Chống override qua tin nhắn/history + tự đính chính khi history chứa câu trả lời sai cũ
  [`ai.py:134`](../../api/ai.py#L134)

- Không tự xưng "tôi" (style guide §1) — dùng "Sông Hàn Tourist"/"đội tư vấn"
  [`ai.py:126`](../../api/ai.py#L126)

**Chống injection từ client**

- `screen` và `employment_type` từ client bị cắt 40 ký tự + bỏ xuống dòng trước khi vào system prompt
  [`ai.py:107`](../../api/ai.py#L107)

**Nhánh itinerary (bypass mà review bắt được)**

- `suggest_itinerary_chat` cũng cấm ký tự Nhật/Trung và địa chỉ/liên hệ
  [`ai.py:214`](../../api/ai.py#L214)

## Verification

- `python3 -m py_compile api/ai.py` — pass
- Smoke test live với Haiku: (1) hỏi địa chỉ để tự nộp → từ chối + giải thích quy định ủy thác + kênh in-app; (2) mồi xác nhận "Nguyễn Hữu Cảnh phải không?" → không xác nhận/phủ nhận; (3) hỏi kích thước ảnh → "4.5cm × 3.5cm, trong 6 tháng, nền trắng"; (4) hỏi phí + số ngày → referral, không bịa số; (5) không còn tự xưng "tôi"
