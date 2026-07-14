---
title: 'Chat — bơm tiến độ thật (eligibility, status tài liệu, OCR) + ownership check'
type: 'feature'
created: '2026-07-14'
status: 'done'
route: 'one-shot'
---

# Chat — bơm tiến độ thật (eligibility, status tài liệu, OCR) + ownership check

## Intent

**Problem:** ChatWidget chỉ nhận checklist_json — không biết eligibility, trạng thái review từng tài liệu, personal_info đã OCR → trả lời chung chung, tách rời tiến độ thật của khách (feedback user 14/07).

**Approach:** `/chat` dựng khối TIẾN ĐỘ HỒ SƠ server-side (eligibility_result + headline, status theo doc_type — ORDER BY id lấy bản mới nhất, personal_info OCR với số hộ chiếu/CCCD mask còn 3 ký tự cuối, loại địa chỉ nhà) bơm vào system prompt như pattern checklist; mọi giá trị qua sanitize 1 dòng + cap độ dài; block tự tuyên bố là DỮ LIỆU (chống injection qua ảnh OCR). Kèm 2 hệ quả từ adversarial review: (1) **ownership check** — sessionId client phải khớp app.session_id mới được dùng context (chặn IDOR thành máy đọc PII); (2) `_strip_markdown_artifacts` gỡ tất định `**`/heading/gạch đầu dòng khỏi reply (cả nhánh itinerary) thay vì trông vào prompt adherence. Không đổi guardrail/persona/rule — behavior spec được cập nhật mô tả nguồn context thứ ba.

## Suggested Review Order

**Bảo mật (đọc trước)**

- Ownership check: sai/thiếu sessionId → bot chạy không context, không lộ hồ sơ người khác
  [`chat.py:31`](../../api/routers/chat.py#L31)

- FE gửi sessionId trong context chat
  [`ChatWidget.jsx:46`](../../visa-client/src/components/ChatWidget.jsx#L46)

**Khối tiến độ**

- Dựng progress server-side: documents ORDER BY id (re-upload lấy status mới nhất), eligibility, OCR
  [`chat.py:56`](../../api/routers/chat.py#L56)

- Formatter: mask định danh, headline "bạn"→"anh/chị", sanitize mọi nhánh kể cả result lạ
  [`ai.py:152`](../../api/ai.py#L152)

- Header block: tuyên bố DỮ LIỆU ≠ chỉ thị (chống injection qua ảnh OCR)
  [`ai.py:220`](../../api/ai.py#L220)

**Trình bày & hooks**

- Strip markdown tất định khỏi reply (cả nhánh itinerary)
  [`ai.py:283`](../../api/ai.py#L283)

- Fix rules-of-hooks có sẵn: early-return màn price chuyển xuống sau hooks
  [`ChatWidget.jsx:81`](../../visa-client/src/components/ChatWidget.jsx#L81)

**Hợp đồng eval + tests**

- Behavior spec cập nhật: nguồn thứ ba, ownership, 3 regression seed mới, risk acceptance DOB không mask
  [`chatbot-behavior-spec.md:1`](../../docs/chatbot-behavior-spec.md#L1)

- Tests: ownership 3 case + formatter (mask, injection, headline, strip)
  [`test_chat_ownership.py:1`](../../tests/api/test_chat_ownership.py#L1) · [`test_chat_format.py:61`](../../tests/api/test_chat_format.py#L61)

## Verification

- `python3 -m pytest tests/api -q` — 103 passed (+7 test mới)
- `npx oxlint src/components/ChatWidget.jsx` — 0 errors (hết error rules-of-hooks); `npm run build` pass
- Smoke live: "Hồ sơ của mình tới đâu rồi?" → 3/3 lần dùng đúng data (kể eligibility + status từng tài liệu + hành động tiếp theo); "Số hộ chiếu của mình?" → chỉ đưa dạng mask •••567
