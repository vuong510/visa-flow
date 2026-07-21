---
title: 'Công cụ triage feedback bán tự động — review-to-fix'
type: 'feature'
created: '2026-07-21'
status: 'done'
context: ['{project-root}/_bmad-output/specs/spec-review-to-fix/SPEC.md', '{project-root}/_bmad-output/specs/spec-feedback-capture/SPEC.md', '{project-root}/project-context.md']
baseline_commit: '46ae69c2d213df3cd107703b5ac738e9ab3aa2aa'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Feedback từ real user (bảng `Feedback`) sẽ tăng vượt khả năng dev tự đọc từng cái. Cần giảm cái phải đọc trực tiếp, không phải sắp xếp lại thứ tự đọc.

**Approach:** CLI `tools/feedback_triage.py` hỗ trợ quy trình: Claude Code (agent) tự điều tra từng feedback (đọc code + chạy test) → gộp theo root cause thành batch, ghi vào `feedback-triage.md` kèm confidence label → dev `set-status approved/dismissed` → batch approved sinh ra `spec-<slug>.md` (draft) sẵn sàng cho `bmad-quick-dev`. Script KHÔNG tự điều tra — chỉ ghi lại kết quả điều tra đã làm và quản lý state.

## Boundaries & Constraints

**Always:**
- Agent (Claude Code) điều tra trước (đọc code + chạy reproduce/test); script chỉ ghi nhận kết quả qua `assign-batch`, không tự động chẩn đoán
- Mọi batch bắt buộc có confidence label (`confirmed` hoặc `unverified`) khi `assign-batch`
- `generate-spec` chỉ chạy khi batch có `status: approved`; batch khác trạng thái → từ chối, không tạo file
- Batch/gói nằm trong `_bmad-output/implementation-artifacts/feedback-triage.md` — cùng thư mục spec khác, không phải dashboard/hệ thống riêng

**Ask First:**
- Không có mục nào ở scope này (đã thống nhất kiến trúc với người dùng trước khi viết spec)

**Never:**
- Không tự động approve/dismiss batch — chỉ qua `set-status` do dev gọi
- Không tự động chạy `generate-spec` ngay sau `assign-batch` — cần bước approved riêng, tách biệt
- Không ghi đè `spec-<slug>.md` đã tồn tại — từ chối nếu trùng slug
- Không sửa `deferred-work.md` — file riêng, không trộn hai loại backlog

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| list-pending rỗng | Không có feedback nào `triage_batch IS NULL` | In "Không có feedback nào đang chờ triage" | N/A |
| assign-batch id sai | `--ids` chứa id không tồn tại trong bảng `Feedback` | Từ chối, không set gì, không ghi file | Exit non-zero, thông báo id nào sai |
| generate-spec chưa approved | Batch có `status: pending` hoặc `dismissed` | Từ chối tạo file | Exit non-zero, thông báo trạng thái hiện tại |
| generate-spec trùng slug | `spec-<slug>.md` đã tồn tại | Không ghi đè | Exit non-zero, gợi ý đổi slug |

</frozen-after-approval>

## Code Map

- `db/models.py` -- `Feedback` thêm cột `triage_batch`, `triage_status`
- `db/session.py` -- thêm 2 dòng safe-migration ALTER TABLE cho cột mới (theo pattern có sẵn)
- `tools/feedback_triage.py` -- CLI mới: `list-pending`, `assign-batch`, `set-status`, `generate-spec`
- `_bmad-output/implementation-artifacts/feedback-triage.md` -- file mới, ghi batch bởi `assign-batch`/`set-status`
- `_bmad-output/implementation-artifacts/intent-<slug>.md` -- file mới do `generate-spec` sinh ra khi batch approved (brief thuần, không phải spec-template.md)
- `tests/test_feedback_triage.py` -- test mới

## Tasks & Acceptance

**Execution:**
- [x] `db/models.py` -- thêm `Feedback.triage_batch` (String, nullable, index), `Feedback.triage_status` (String, nullable — "pending"|"approved"|"dismissed") -- nền tảng cho CAP-1/CAP-4/CAP-5
- [x] `db/session.py` -- thêm `"ALTER TABLE feedbacks ADD COLUMN triage_batch VARCHAR(64)"` và `"ALTER TABLE feedbacks ADD COLUMN triage_status VARCHAR(20)"` vào list safe-migration hiện có
- [x] `tools/feedback_triage.py::list_pending` -- in ra mọi `Feedback` có `triage_batch IS NULL` (id, screen, application_id, session_id, message) -- CAP-1 input cho agent điều tra
- [x] `tools/feedback_triage.py::assign_batch(ids, batch_slug, root_cause, confidence, proposed_fix, impact)` -- validate mọi id tồn tại trước khi set; set `triage_batch=batch_slug`, `triage_status="pending"` cho các row; append section batch vào `feedback-triage.md` (id list, root cause, confidence, proposed fix, impact, status: pending) -- CAP-1/CAP-2/CAP-3/CAP-4
- [x] `tools/feedback_triage.py::set_status(batch_slug, status)` -- cập nhật `triage_status` cho mọi row cùng batch + cập nhật dòng status trong section tương ứng ở `feedback-triage.md` -- CAP-5
- [x] `tools/feedback_triage.py::assign_batch(...)` -- REJECT nếu `batch_slug` đã có section trong `feedback-triage.md` (chống duplicate section); REJECT nếu bất kỳ id nào đã có `triage_batch` khác (chống re-tag âm thầm); validate `batch_slug` khớp `^[a-z0-9-]+$` và root_cause/proposed_fix/impact không chứa newline hay dòng bắt đầu bằng `## `/`- ` (chống injection phá parser); ghi markdown TRƯỚC, commit DB SAU, rollback nếu ghi file lỗi; dedupe ids trước khi render -- CAP-1/CAP-2/CAP-3/CAP-4
- [x] `tools/feedback_triage.py::set_status(...)` -- cùng thứ tự ghi file trước/commit sau như `assign_batch` -- CAP-5
- [x] `tools/feedback_triage.py::generate_spec(batch_slug)` -- guard status approved + slug chưa tồn tại (dùng exclusive-create, vd `open(path, "x")`, không phải exists()-rồi-write, để tránh race); KHÔNG sinh file theo khuôn `spec-template.md` với placeholder token (`INVARIANT_RULES`...) -- thay vào đó ghi một file intent thuần: `_bmad-output/implementation-artifacts/intent-<batch_slug>.md`, KHÔNG có YAML frontmatter, KHÔNG có `<frozen-after-approval>`, chỉ có `## Problem` (root cause) và `## Approach` (proposed fix + impact) dạng văn xuôi -- CAP-5
- [x] CLI: bọc parse `--ids` (CSV) bằng try/except báo lỗi rõ token nào sai; toàn bộ message CLI dùng tiếng Anh nhất quán (tool nội bộ dev, không phải copy tiếng Việt cho end-user)
- [x] `tests/test_feedback_triage.py` -- sửa `test_empty_when_no_unassigned_feedback` để không sweep các row pending có sẵn vào batch rác (test isolation); thêm test: duplicate-slug bị reject, id đã thuộc batch khác bị reject, slug/field không hợp lệ bị reject, đúng message rỗng in ra ở `_print_pending`, và shape file `intent-<slug>.md` mới -- cover toàn bộ edge-case matrix + finding từ review

**Acceptance Criteria:**
- Given nhiều feedback cùng root cause đã được điều tra thủ công, when chạy `assign-batch` với id của chúng, then cả nhóm được gắn cùng `triage_batch` và xuất hiện thành một section duy nhất trong `feedback-triage.md`, không phải N dòng rời rạc — kể cả khi gọi `assign-batch` nhiều lần với cùng slug (lần sau bị reject rõ ràng, không tạo section thứ hai).
- Given một batch chưa `approved`, when chạy `generate-spec`, then không có file nào được tạo và lệnh báo lỗi rõ ràng.
- Given một batch đã `approved`, when chạy `generate-spec`, then `intent-<slug>.md` được tạo — một brief thuần văn xuôi (không frontmatter, không frozen block) mang root cause + đề xuất fix + impact, để khi chạy `bmad-quick-dev` trên file này, step-01 nhận diện đây là intent thô (không có `status` frontmatter) và đi vào planning đầy đủ từ đầu — không phải resume một draft nửa vời với placeholder giả.

## Spec Change Log

- **2026-07-21 — bad_spec loopback (round 1 review).** Trigger: acceptance auditor lần theo `bmad-quick-dev/step-02-plan.md` và xác nhận cơ chế "draft resume" giữ nguyên verbatim toàn bộ `<frozen-after-approval>` khi resume một spec `status: draft` — nghĩa là placeholder token (`INVARIANT_RULES`, `NON_GOALS_AND_FORBIDDEN_APPROACHES`...) mà `generate_spec` từng ghi vào Boundaries & Constraints sẽ bị mang nguyên xi vào bản spec đã duyệt sau này nếu người dùng không để ý sửa. Root cause nằm ngoài frozen block (task mô tả cho `generate_spec` chưa đủ rõ phải làm gì với các section không có dữ liệu thật). Amend: `generate_spec` đổi từ "sinh spec-template.md giả với placeholder" sang "sinh file intent thuần, không frontmatter/frozen block" — để `bmad-quick-dev` đi vào planning thật từ đầu thay vì resume rác. KEEP: toàn bộ logic `list_pending`/`assign_batch`/`set_status` giữ nguyên hướng thiết kế (chỉ thêm guard chống duplicate-section/re-tag/injection theo finding review, không đổi kiến trúc); thứ tự "agent điều tra trước, script chỉ ghi nhận" giữ nguyên.
- **2026-07-21 — patch bundle (round 1 review).** Cùng đợt review phát hiện: duplicate batch section khi gọi lại `assign-batch` cùng slug (vi phạm AC1, đã tái hiện được), reassign id sang batch khác không cảnh báo, DB/markdown ghi không cùng thứ tự nên có thể lệch trạng thái khi ghi file lỗi, TOCTOU race ở `generate-spec`, thiếu validate slug/field gây injection phá parser hoặc path traversal, test tự gây bẩn state dùng chung. Tất cả patch mechanic, không đổi kiến trúc — gộp cùng đợt implement lại với bad_spec ở trên.

## Design Notes

Quy trình chạy tay (không tự động hoá lịch): dev/Claude Code gọi `list-pending` → tự điều tra từng feedback (đọc code, chạy test liên quan) → gộp những feedback cùng root cause → `assign-batch` ghi lại kết quả → dev xem `feedback-triage.md`, gọi `set-status --batch X --status approved` (hoặc `dismissed`) → nếu approved, `generate-spec --batch X` sinh spec draft, tiếp tục bằng `bmad-quick-dev` như bình thường.

`feedback-triage.md` section mẫu:
```md
## Batch: <slug>
- Feedback IDs: 12, 13, 15
- Root cause: ...
- Confidence: confirmed | unverified
- Proposed fix: ...
- Impact: ...
- Status: pending | approved | dismissed
```

## Verification

**Commands:**
- `python3 -m pytest tests/test_feedback_triage.py -v` -- expected: tất cả pass
- `python3 -m pytest tests/ -q` -- expected: không regress (toàn bộ suite pass)

## Suggested Review Order

**Vì sao đổi kiến trúc generate-spec (bad_spec loopback)**

- Entry point — lý do `generate_spec` không còn sinh spec-template.md giả mà sinh brief thuần, viết ngay trong docstring
  [`feedback_triage.py:317`](../../tools/feedback_triage.py#L317)

- Output thật: exclusive-create tránh TOCTOU, guard status approved trước khi đọc field
  [`feedback_triage.py:335`](../../tools/feedback_triage.py#L335)

**Guard chống duplicate/re-tag (AC1 fix)**

- `assign_batch`: check duplicate-slug trước khi ghi section mới
  [`feedback_triage.py:216`](../../tools/feedback_triage.py#L216)

- Check id đã thuộc batch khác — không cho re-tag âm thầm
  [`feedback_triage.py:198`](../../tools/feedback_triage.py#L198)

- Validate slug + chống injection phá parser markdown
  [`feedback_triage.py:71`](../../tools/feedback_triage.py#L71)

**Write-before-commit (chống lệch DB/markdown khi ghi file lỗi)**

- Ghi file trước, chỉ commit DB sau khi ghi thành công; rollback nếu file lỗi
  [`feedback_triage.py:226`](../../tools/feedback_triage.py#L226)

**Tests**

- Test isolation fix + toàn bộ guard mới
  [`test_feedback_triage.py:60`](../../tests/test_feedback_triage.py#L60)

- Shape file `intent-<slug>.md` mới, không frontmatter/frozen
  [`test_feedback_triage.py:292`](../../tests/test_feedback_triage.py#L292)
