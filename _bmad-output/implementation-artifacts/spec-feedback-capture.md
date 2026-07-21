---
title: 'Thu thập feedback từ real user'
type: 'feature'
created: '2026-07-21'
status: 'done'
context: ['{project-root}/_bmad-output/specs/spec-feedback-capture/SPEC.md', '{project-root}/project-context.md']
baseline_commit: 'cbc7f8573c4c3105b018b25cbbb2a25546fd809f'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** visa-flow chỉ nhận feedback từ nội bộ (chị Yến qua group chat); real user thật không phàn nàn bằng lời, họ chỉ tức và bỏ luồng. Cần một kênh thu feedback trực tiếp từ real user, hoạt động ngay cả khi backend đang lỗi (đúng lúc user dễ bực nhất).

**Approach:** Component `FeedbackWidget` riêng biệt (không tái dùng `ChatWidget`), luôn hiện diện mọi màn hình dạng FAB, mở ra ô free-text. Context (screen/applicationId/sessionId) tự động đính kèm. Submit ghi optimistic ack ngay, queue vào localStorage nếu backend không phản hồi, retry sau; backend lưu vào bảng `Feedback` mới, idempotent theo `client_id`.

## Boundaries & Constraints

**Always:**
- `FeedbackWidget` là component/route riêng biệt, không tái dùng `ChatWidget.jsx` hay `/chat`
- Luôn render trên mọi màn hình — không có logic ẩn theo `screen` (khác `ChatWidget` hiện ẩn ở màn `price`)
- Chỉ một ô free-text, không thêm field bắt buộc nào khác
- Context (`screen`, `applicationId`, `sessionId`) lấy tự động từ `AppContext`, không hỏi user
- Ack hiển thị ngay lập tức (optimistic) — không chờ kết quả network call
- Mỗi submit kèm `client_id` (`crypto.randomUUID()`) để idempotent khi retry

**Ask First:**
- Nếu cần cơ chế retry phức tạp hơn "flush khi mount + flush khi submit tiếp theo" (vd background sync/service worker) — hỏi trước vì tăng phạm vi

**Never:**
- Không tự động chụp screenshot
- Không lưu feedback vào bảng `Document`/`Application` hiện có — bảng `Feedback` mới, one-to-many với `Application`
- Không tự động phát hiện exit-intent/frustration để tự trigger
- Không có admin UI đọc/triage feedback (ngoài phạm vi — spec `review-to-fix` khác)

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Happy path | User bấm FAB, gõ text, bấm Gửi, backend OK | Row tạo trong `Feedback` với đủ context; UI hiện xác nhận | N/A |
| Backend down | Submit khi fetch fail (network error/5xx) | Entry lưu vào localStorage queue; UI vẫn hiện xác nhận ngay | Retry khi widget mount lại hoặc lần submit tiếp theo |
| Retry trùng | Server thực ra đã nhận trước đó nhưng client tưởng fail, gửi lại cùng `client_id` | Server trả về record đã có, không tạo dòng mới | Idempotent theo unique `client_id` |
| Message rỗng | User bấm Gửi mà chưa gõ gì | Nút Gửi disabled | N/A |

</frozen-after-approval>

## Code Map

- `db/models.py` -- thêm model `Feedback` (mới)
- `api/routers/feedback.py` -- router mới, POST /feedback
- `api/main.py` -- đăng ký router mới
- `visa-client/src/components/FeedbackWidget.jsx` -- component mới
- `visa-client/src/App.jsx` -- mount widget cạnh `ChatWidget`
- `visa-client/src/context/AppContext.jsx` -- đọc, không sửa (đã có screen/applicationId/sessionId)
- `tests/test_feedback.py` -- test mới

## Tasks & Acceptance

**Execution:**
- [x] `db/models.py` -- thêm `Feedback(id, application_id FK->applications, session_id, screen, message, client_id unique, created_at)` -- lưu context tự động (CAP-3) + khoá idempotency (CAP-4)
- [x] `api/routers/feedback.py` -- `POST /feedback`: nếu `client_id` đã tồn tại trả về record cũ (200, không tạo mới); ngược lại insert row mới (201) -- CAP-2/CAP-3/CAP-4
- [x] `api/main.py` -- import + `include_router(feedback_router, prefix="/api")` -- wire endpoint
- [x] `visa-client/src/components/FeedbackWidget.jsx` -- FAB bottom-left (🚩, không đè lên FAB `ChatWidget` bottom-right); panel một ô textarea + nút Gửi; submit sinh `client_id`, đọc `screen/applicationId/sessionId` từ `useApp()`, hiện ack ngay, `fetch` POST; fail → push vào `localStorage['visa_feedback_queue']`; flush queue khi mount và sau mỗi submit mới -- CAP-1/2/3/4/5
- [x] `visa-client/src/App.jsx` -- render `<FeedbackWidget />` không điều kiện, ngoài `Router`, cạnh `<ChatWidget />` -- CAP-1
- [x] `tests/test_feedback.py` -- test: submit tạo row đúng context; submit 2 lần cùng `client_id` không tạo dòng trùng; thiếu `message` trả 422 -- cover edge-case matrix

**Acceptance Criteria:**
- Given user đang ở bất kỳ màn hình nào, when họ mở `FeedbackWidget`, then họ gửi được text tự do mà không cần điền field nào khác.
- Given backend không phản hồi, when user submit feedback, then UI vẫn hiện xác nhận ngay và entry được giữ lại để đồng bộ sau.
- Given một entry đã queue cục bộ, when app reload và backend đã sống lại, then entry được đồng bộ đúng một lần (không trùng), dựa trên `client_id`.

## Spec Change Log

## Design Notes

Local queue shape trong `localStorage['visa_feedback_queue']`:
```js
[{ client_id, application_id, session_id, screen, message, created_at }]
```
Flush: gọi khi `FeedbackWidget` mount, và ngay sau mỗi submit mới (để dọn cả backlog cũ lẫn item vừa gửi).

## Verification

**Commands:**
- `python3 -m pytest tests/test_feedback.py -v` -- expected: tất cả pass
- `cd visa-client && npm run lint` -- expected: không lỗi
- `cd visa-client && npm run build` -- expected: build thành công

## Suggested Review Order

**Persistence & idempotency (backend)**

- Entry point — bảng `Feedback` mới, `client_id` unique là idempotency key, `application_id` nullable vì feedback có thể xảy ra trước khi có application (vd màn landing)
  [`models.py:116`](../../db/models.py#L116)

- `POST /feedback`: check-then-insert, nhưng insert được bọc `try/except IntegrityError` — thua race thì rollback + re-query trả về row đã thắng thay vì 500
  [`feedback.py:41`](../../api/routers/feedback.py#L41)

- Validation khớp độ rộng cột DB (`max_length`) + chặn message rỗng/toàn khoảng trắng bằng `field_validator`
  [`feedback.py:13`](../../api/routers/feedback.py#L13)

- Router mới được đăng ký cạnh các router khác, cùng prefix `/api`
  [`main.py:43`](../../api/main.py#L43)

**Resilience & retry queue (frontend)**

- `sendEntry` gắn `isClientError` cho response 4xx — phân biệt "đừng retry" (lỗi client, sai vĩnh viễn) với "network/5xx, nên retry"
  [`FeedbackWidget.jsx:50`](../../visa-client/src/components/FeedbackWidget.jsx#L50)

- `flushQueue` dùng `flushPromise` module-level làm khoá in-flight — chặn 2 lần flush (mount + sau submit) chạy chồng lên nhau, race trên localStorage
  [`FeedbackWidget.jsx:68`](../../visa-client/src/components/FeedbackWidget.jsx#L68)

- `writeQueue` cắt queue còn tối đa `MAX_QUEUE_SIZE` (50) entry mới nhất — tránh localStorage phình vô hạn rồi ghi thất bại toàn bộ
  [`FeedbackWidget.jsx:18`](../../visa-client/src/components/FeedbackWidget.jsx#L18)

- `makeClientId` có fallback khi `crypto.randomUUID` không tồn tại (browser cũ/insecure context) — không throw làm mất luôn feedback
  [`FeedbackWidget.jsx:36`](../../visa-client/src/components/FeedbackWidget.jsx#L36)

**UI: ack, submit guard, mount** (không có logic ẩn theo `screen` — khác `ChatWidget`)

- `submit()`: ack chỉ hiện khi ghi cục bộ/network thực sự thành công (không còn optimistic mù), có `isSubmitting` chặn double-submit
  [`FeedbackWidget.jsx:113`](../../visa-client/src/components/FeedbackWidget.jsx#L113)

- Nút Gửi disable khi rỗng hoặc đang submit
  [`FeedbackWidget.jsx:226`](../../visa-client/src/components/FeedbackWidget.jsx#L226)

- Mount cạnh `ChatWidget`, ngoài `Router` — không remount khi đổi màn hình
  [`App.jsx:39`](../../visa-client/src/App.jsx#L39)

**Tests**

- Race condition được test trực tiếp: monkeypatch query để giả lập thua race, xác nhận rơi vào nhánh `except IntegrityError` và trả 200 thay vì 500
  [`test_feedback.py:95`](../../tests/test_feedback.py#L95)

- Edge case còn lại: message rỗng/khoảng trắng, field quá dài, thiếu application_id, duplicate client_id
  [`test_feedback.py:64`](../../tests/test_feedback.py#L64)
