---
title: 'Chat — bơm checklist của khách vào prompt (hết mù nội dung sản phẩm)'
type: 'bugfix'
created: '2026-07-13'
status: 'done'
route: 'one-shot'
---

# Chat — bơm checklist của khách vào prompt (hết mù nội dung sản phẩm)

## Intent

**Problem:** Sau khi ground theo FACTS, chat quá "câm": khách hỏi "lấy giấy tạm trú kiểu gì" bị đẩy về hotline dù mỗi checklist item đã có `how_to_get`/`format`/`why` kiểm duyệt sẵn hiển thị trong UI — bot không được nhìn thấy nội dung của chính sản phẩm (feedback user kèm screenshot, 13/07).

**Approach:** Theo pattern `{{CHECKLIST}}` của japan-visa-bot: route `/chat` load `app.checklist_json` (cache = đúng nội dung khách thấy trong UI) và truyền vào `chat_with_haiku`; prompt thêm section "CHECKLIST HỒ SƠ CỦA KHÁCH" được miễn trừ khỏi luật FACTS-only, COMPLIANCE nới rõ: giấy tờ cần gì/cách lấy trả lời thẳng theo checklist, vẫn cấm đánh giá hồ sơ và khuyên tài chính cá nhân. Text checklist được sanitize (1 dòng, cap 300 ký tự/field, 20 item) vì `travel_dates` của user nội suy vào description — chặn tiêm chỉ thị vào system prompt.

## Suggested Review Order

**Luồng dữ liệu**

- Route /chat: fetch Application một lần cho mọi message, lấy checklist_json đã cache
  [`chat.py:54`](../../api/routers/chat.py#L54)

- Sanitizer: ép 1 dòng + cap độ dài — chốt chặn injection qua travel_dates nội suy vào checklist
  [`ai.py:104`](../../api/ai.py#L104)

- Formatter: render name/yêu cầu/định dạng/cách lấy/tại sao, bỏ item hỏng, cap 20 item
  [`ai.py:110`](../../api/ai.py#L110)

**Hoà giải guardrail (3 chỗ mâu thuẫn mà review bắt được)**

- Header FACTS: checklist là nguồn được phép thứ hai
  [`ai.py:165`](../../api/ai.py#L165)

- Block CHECKLIST chỉ render khi có body; kèm confidence_note
  [`ai.py:143`](../../api/ai.py#L143)

- COMPLIANCE: trả lời thẳng giấy tờ/cách lấy theo checklist — vẫn cấm đánh giá hồ sơ, khuyên tài chính
  [`ai.py:179`](../../api/ai.py#L179)

**Tests**

- Unit test formatter: item hỏng không crash, ép 1 dòng, cắt độ dài, cap số item, rỗng khi toàn item hỏng
  [`test_chat_format.py:1`](../../tests/api/test_chat_format.py#L1)

## Verification

- `python3 -m py_compile api/ai.py api/routers/chat.py` — pass
- `python3 -m pytest tests/api/test_chat_format.py -q` — 5 passed
- Smoke live: "Tôi cần chuẩn bị những giấy tờ gì?" → liệt kê đúng 10 item của case employee; "Lấy giấy tạm trú kiểu gì" → hướng dẫn CT07/CT08 + công an phường + điều kiện Bắc/Nam từ how_to_get
