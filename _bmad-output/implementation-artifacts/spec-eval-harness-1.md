---
title: 'Eval harness đợt 1 — checks tầng 2 + regression seeds + runner + baseline'
type: 'feature'
created: '2026-07-16'
status: 'done'
route: 'one-shot'
---

# Eval harness đợt 1 — checks tầng 2 + regression seeds + runner + baseline

## Intent

**Problem:** Eval plan (`docs/eval-plan.md`) đã có nhưng chưa có gì chạy được — mỗi lần đổi prompt chatbot không có cách nào biết 9 lỗi cũ có tái phát không, ngoài test tay.

**Approach:** Build bước 1 của plan: `tests/eval/` gồm `checks.py` (8 programmatic check tầng 2: persona/CJK/markdown/phone whitelist/PII/ngưỡng tài chính/"ạ"/độ dài — thuần regex, NFC-normalized, không API), `scenarios/regression_seeds.json` (13 seed từ §5 behavior spec, expected_topics hỗ trợ any-of variants), `run_eval.py` (runner gọi `chat_with_haiku` thật, đa lượt, 2 gate đúng plan: per-check ≥95% + per-seed ≥2/3, `--dry-run/--repeat/--only/--out`, không nằm trong pytest mặc định). IDOR seed đo ở tầng 1 (`test_chat_ownership.py`) vì ownership nằm ở router — ghi chú coverage trong seeds meta. Kèm 48 unit test cho checks + baseline live.

## Suggested Review Order

**Checks (đọc trước — đây là "luật đo")**

- 8 check thuần regex, whitelist compound "bạn", date/money shape không false-positive thành SĐT
  [`checks.py:1`](../../tests/eval/checks.py#L1)

**Seeds**

- 13 kịch bản = 9 lỗi thật chị Yến/review + injection ảnh OCR + injection context + hỏi số hộ chiếu + vé máy bay; meta ghi IDOR cover ở tầng 1
  [`regression_seeds.json:1`](../../tests/eval/scenarios/regression_seeds.json#L1)

**Runner**

- Multi-turn qua chat_with_haiku thật, fixture checklist/progress đúng shape router, 2 gate, JSON + bảng console
  [`run_eval.py:1`](../../tests/eval/run_eval.py#L1)

**Kết quả**

- Baseline 16/07: 39/39 run pass (100%), 8/8 check 100%, 2 gate ĐẠT
  [`eval-baseline-20260716.json:1`](../../../docs/eval-baseline-20260716.json#L1)

- Unit tests cho checks (48 test, không API)
  [`test_eval_checks.py:1`](../../tests/api/test_eval_checks.py#L1)

## Verification

- `pytest tests/api -q` — 151 passed (103 cũ + 48 checks)
- `python3 -m tests.eval.run_eval --dry-run` — exit 0 (schema 13 seed + import + fixture OK)
- Live baseline ×2: lần 1 bắt được seed_10 over-spec (bot từ chối đưa cả mask — an toàn hơn kỳ vọng, sửa seed); lần 2 sau 15 patch review: **39/39 pass, gate tầng 2 + 3 ĐẠT** → `docs/eval-baseline-20260716.json`
- Adversarial review: 15 patch đã áp (seed_12 vacuous, thiếu check "ạ", gate semantics, NFC normalize, mở rộng CJK/threshold regex, runner robustness); reject có lý do: no_markdown đo surface sau sanitizer (đúng chủ đích), word_limit đếm âm tiết (proxy chấp nhận); defer: nhánh itinerary surface (đợt 2)
