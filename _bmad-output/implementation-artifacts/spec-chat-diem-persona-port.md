---
title: 'Chat — port đợt 1 từ Diễm bot: persona, hotline, P0 compliance, hard rules'
type: 'feature'
created: '2026-07-13'
status: 'done'
route: 'one-shot'
---

# Chat — port đợt 1 từ Diễm bot: persona, hotline, P0 compliance, hard rules

## Intent

**Problem:** Chat visa-flow là "Haiku + prompt mỏng": không persona, tư vấn trực tiếp kiểu "anh nên có sổ tiết kiệm" (rủi ro compliance), không xử lý câu hỏi ngoài phạm vi, referral không có kênh liên hệ thật. Trong khi đó japan-visa-bot (Diễm) đã có sẵn persona chuẩn style guide, nguyên tắc P0 compliance, hotline chính thức và 7 hard rules đã kiểm chứng.

**Approach:** Port đợt 1 (chỉ sửa prompt trong `api/ai.py`): persona Thu Diễm (em/anh-chị/ạ, không bịa); hotline Sông Hàn Tourist 028 7301 2939 / 028 3848 1390 là số duy nhất được phép cung cấp; P0 — không bảo khách phải làm gì với hồ sơ, frame thành câu hỏi (quy định lãnh sự quán trong FACTS vẫn nêu thẳng); out-of-scope → từ chối mềm + hotline; disclaimer kèm miễn trừ trách nhiệm pháp lý; 7 hard rules + spec ảnh đầy đủ, scope rõ CHỈ visa Nhật (visa Trung Quốc chưa có facts → hotline); đồng bộ persona cho nhánh gợi ý lịch trình. Giữ nguyên mọi guardrail sẵn có.

## Suggested Review Order

**Persona & FACTS (system prompt chính)**

- Persona Thu Diễm + quy tắc xưng hô + "không bịa thì đưa hotline"
  [`ai.py:116`](../../api/ai.py#L116)

- FACTS: 7 hard rules + spec ảnh + hotline, scope "CHỈ visa Nhật"; wording "kênh được chỉ định" (nguồn ghi ủy thác HOẶC VFS — không nói quá thành "chỉ ủy thác")
  [`ai.py:125`](../../api/ai.py#L125)

- Dòng chặn China: chưa có facts kiểm chứng → hotline, không áp rule Nhật sang Trung Quốc
  [`ai.py:136`](../../api/ai.py#L136)

**Compliance & disclaimer**

- P0: không lời khuyên trực tiếp, frame câu hỏi; quy định lãnh sự quán nêu thẳng không tính là lời khuyên
  [`ai.py:138`](../../api/ai.py#L138)

- Disclaimer đầy đủ: nguồn LSQ Nhật + miễn trừ trách nhiệm pháp lý (bị rơi khi port lần đầu, review bắt được)
  [`ai.py:151`](../../api/ai.py#L151)

**Nhánh itinerary (đồng bộ persona)**

- suggest_itinerary_chat hết xưng "bạn" — em/anh-chị như prompt chính
  [`ai.py:231`](../../api/ai.py#L231)

## Verification

- `python3 -m py_compile api/ai.py` — pass
- Smoke test live: (1) hỏi ngưỡng số dư → không đưa số, frame câu hỏi + hotline; (2) visa Hàn Quốc → từ chối mềm + hotline; (3) hỏi cách liên hệ → hotline thật; (4) xin địa chỉ LSQ → vẫn chặn (regression); (5) hỏi rule 3 tháng cho visa TQ → tự đính chính "rule đó riêng visa Nhật" + hotline; (6) hỏi mua vé trước → nêu thẳng quy định, đúng persona em/anh-chị/ạ
