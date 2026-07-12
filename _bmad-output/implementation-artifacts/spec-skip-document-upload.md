---
title: 'Skip upload tài liệu — Bổ sung sau'
type: 'feature'
created: '2026-07-12'
status: 'done'
baseline_commit: '795b18876ece1afd15cce23b73850a313778f67a'
context: ['{project-root}/project-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Màn hình "Chuẩn bị hồ sơ" yêu cầu upload đủ toàn bộ tài liệu (pass/needs_clarification) mới hiện nút gửi hồ sơ — khách thiếu 1 file là kẹt, không thể đi tiếp (feedback tester).

**Approach:** Thêm option "Bổ sung sau" (skip) cho từng tài liệu trong checklist (kể cả lịch trình). Tài liệu skip được lưu backend với `review_status="skipped"`, khách vẫn gửi hồ sơ được; tài liệu skip hiển thị rõ để nhân viên visa thu trực tiếp sau.

## Boundaries & Constraints

**Always:**
- Text UI tiếng Việt, theo tone hiện có; label skip = "Bổ sung sau", chip skipped = "Bổ sung sau".
- Skip phải persist qua reload (lưu backend, không chỉ state frontend).
- Khách đổi ý được: item đã skip vẫn upload lại bình thường (upload ghi đè trạng thái skip trên UI).
- Trước khi gửi, nếu có tài liệu skip → hiển thị ghi chú số tài liệu sẽ bổ sung sau cho nhân viên visa.

**Ask First:**
- Nếu cần migration DB (thêm cột) — hiện tại `review_status` String(30) chứa được "skipped", không cần.

**Never:**
- Không đổi logic AI review, upload multipart, hay PDF form.
- Không chặn submit khi khách skip toàn bộ (tester yêu cầu flexible hoàn toàn).
- Không đụng 2 file đang sửa dở: `api/ai.py`, `api/routers/extract.py`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Skip 1 tài liệu | Item `pending`, bấm "Bổ sung sau" | POST skip → Document row `review_status="skipped"`; chip "Bổ sung sau"; nút "Tải lên" vẫn hiện | Lỗi mạng → giữ trạng thái cũ, toast/inline lỗi |
| Skip rồi upload lại | Item `skipped`, bấm "Tải lên" | Upload bình thường → row mới, UI chuyển pending→reviewing; skip cũ bị ghi đè trên UI | Như upload hiện tại |
| Skip sau khi AI fail | Item `fail`/`needs_clarification` | Cho phép "Bổ sung sau" → chuyển skipped | N/A |
| Submit với skip | Mọi item = pass/needs_clarification/skipped | Nút gửi hiện; banner ghi "N tài liệu sẽ bổ sung sau trực tiếp cho nhân viên visa" | N/A |
| Skip lịch trình | Itinerary chưa tạo, bấm "Bổ sung sau" | doc_type="itinerary" skipped; itineraryDone = true | N/A |
| Reload trang | Có docs skipped trong DB | `GET /documents` trả row skipped → UI khôi phục chip "Bổ sung sau" | N/A |
| Skip idempotent | Bấm skip 2 lần / doc_type đã skip | Không tạo row trùng (upsert theo doc_type) | N/A |

</frozen-after-approval>

## Code Map

- `api/routers/application.py` -- endpoint mới `POST /application/{app_id}/documents/skip`; sửa `list_documents` (order_by), `review_document` (guard skipped), `save_itinerary` (dọn row skipped)
- `db/models.py` -- `Document.review_status` String(30), `file_path` nullable — chứa "skipped" không cần migration (chỉ cập nhật comment)
- `visa-client/src/components/StatusChip.jsx` -- thêm variant `skipped`
- `visa-client/src/components/DocumentItem.jsx` -- nút/link "Bổ sung sau" cho trạng thái pending/fail/needs_clarification; render trạng thái skipped
- `visa-client/src/screens/ChecklistScreen.jsx` -- `handleSkip()` có guard race, nới `canSubmit`, itinerary skip, banner "N tài liệu bổ sung sau", ReadinessBanner đếm skip

## Tasks & Acceptance

**Execution:**
- [x] `api/routers/application.py` -- thêm `POST /application/{app_id}/documents/skip` (body Pydantic `{doc_type}`), 404 nếu app không tồn tại. Logic guarded upsert: lấy row MỚI NHẤT theo `(application_id, doc_type)` (`order_by(Document.id.desc()).first()`); (a) nếu row tồn tại và `review_status ∈ {"pass","pending"}` → KHÔNG sửa, trả `{document_id, doc_type, status: <status hiện tại>}` (chặn race ghi đè tài liệu đã upload/đang review); (b) nếu row tồn tại (fail/needs_clarification/skipped) → update row đó: `review_status="skipped"`, `file_path=None` (KHÔNG xóa file vật lý trên đĩa), `review_notes="Khách bổ sung trực tiếp cho nhân viên visa"`; (c) chưa có row → tạo mới với `file_path=None`. Trả `{document_id, doc_type, status:"skipped"}` -- persist skip, chống clobber
- [x] `api/routers/application.py` -- `list_documents`: thêm `.order_by(Document.id)` để row mới nhất luôn đứng cuối (FE docsMap last-wins đúng trên mọi DB, không chỉ SQLite) -- deterministic reload
- [x] `api/routers/application.py` -- `review_document`: guard đầu hàm — nếu `doc.review_status == "skipped"` hoặc `doc.file_path` rỗng → HTTP 400 "Tài liệu đã được đánh dấu bổ sung sau, không có file để kiểm tra." (chỉ guard, không đổi logic AI review) -- chặn skipped→pass
- [x] `api/routers/application.py` -- `save_itinerary`: sau khi lưu `itinerary_json`, xóa mọi Document row `doc_type="itinerary"` có `review_status="skipped"` của application đó -- lịch trình đã tạo thì không còn "bổ sung sau"
- [x] `db/models.py` -- cập nhật comment `review_status` thêm giá trị `"skipped"` -- tài liệu hóa
- [x] `visa-client/src/components/StatusChip.jsx` -- variant `skipped: { label: 'Bổ sung sau', bg: '#f3f4f6', color: '#374151' }` -- hiển thị trạng thái
- [x] `visa-client/src/components/DocumentItem.jsx` -- thêm prop `onSkip`; text-button "Bổ sung sau" (fontSize 12, màu muted, underline, không bg/border, stopPropagation) xếp cột dọc dưới nút "Tải lên" khi pending và dưới "Tải lại" khi fail/needs_clarification; khi `skipped`: chip + nút "Tải lên" outline -- cho phép skip & đổi ý
- [x] `visa-client/src/screens/ChecklistScreen.jsx` -- (1) `handleSkip(docId)`: clear `skipError` ngay đầu mỗi lần gọi; no-op nếu item đang `uploading`/`reviewing` hoặc đã có skip request đang bay (track `skippingIds`); POST skip; khi response về (check bên trong functional `setDocs` updater để tránh stale closure): (a) nếu state local đang `uploading`/`reviewing` HOẶC status local là `'pass'` → bỏ qua response (response trễ không được ghi đè upload mới hơn hoặc kết quả pass); (b) nếu `data.status==='skipped'` → áp dụng `{id: data.document_id, status:'skipped'}`; (c) nếu server trả status khác (`pending`/`pass` — skip bị từ chối do đã có file) → đồng bộ state local theo server: `{id: data.document_id, status: data.status}` VÀ set thông báo inline `skipError` = "Tài liệu này đã có file tải lên nên không thể đánh dấu bổ sung sau." (không im lặng); lỗi mạng → giữ state cũ + inline error `skipError` "Không thể lưu. Vui lòng thử lại."; (2) clear `skipError` khi skip thành công hoặc khi bắt đầu upload mới; (3) `canSubmit`: mọi non-itinerary item có status ∈ {pass, needs_clarification, skipped} (item đang uploading/reviewing không đạt — upload replace cả object docState nên status bị xóa, GIỮ hành vi replace này) và itinerary done hoặc skipped; (4) itinerary row: text-button "Bổ sung sau" cạnh "AI tạo" khi chưa tạo/chưa skip; khi skipped hiện chip xám "Bổ sung sau" (idiom giống span "✓ Đã tạo") và vẫn cho "AI tạo"; (5) khi `canSubmit && skippedCount>0`: banner info (idiom box #f0f9ff) trong BottomActionArea: "Bạn sẽ bổ sung N tài liệu sau trực tiếp cho nhân viên visa."; skippedCount = item non-itinerary skipped + itinerary skipped (chỉ khi chưa created, tránh đếm đôi); (6) ReadinessBanner: nhận prop `skipped`, label thêm "· N bổ sung sau" khi >0; item skipped không tính vào `uploaded`; `allPass` giữ nguyên (có skip ⇒ false); (7) truyền `onSkip={handleSkip}` vào DocumentItem -- luồng chính, chống race
- [x] Manual test theo I/O matrix -- xác nhận hành vi (API-level qua curl: skip persist + idempotent, review 400 trên row skipped, save_itinerary dọn row, guard itinerary created; FE: trace code + build pass — nên walkthrough UI thêm khi test chức năng)

**Acceptance Criteria:**
- Given checklist 9 tài liệu chưa upload gì, when khách bấm "Bổ sung sau" cho cả 9 + skip lịch trình, then nút "Gửi hồ sơ cho tư vấn viên" hiện và submit thành công.
- Given 1 tài liệu đã skip, when reload trang, then chip "Bổ sung sau" vẫn hiển thị đúng item đó.
- Given 1 tài liệu đã skip, when khách upload file cho item đó, then luồng upload + AI review chạy bình thường và trạng thái skip biến mất.
- Given hồ sơ có tài liệu skip đã submit, when nhân viên gọi `GET /documents`, then row skipped xuất hiện với `review_status="skipped"`.

## Spec Change Log

### 2026-07-12 — Vòng review 1 (bad_spec loopback #1)

**Findings kích hoạt:** (1) upsert skip không có guard trạng thái — race double-tap (skip + upload gần đồng thời, cả 2 chiều client/server) có thể ghi đè tài liệu đã upload/pass thành skipped; (2) nhánh update không set `file_path=None` — lệch spec; (3) skip lịch trình rồi "AI tạo" thành công → row skipped không được dọn, staff vẫn thấy "bổ sung sau"; (4) `list_documents` không ORDER BY — last-wins của FE không đảm bảo ngoài SQLite; (5) `review_document` chạy được trên row skipped không file → auto "pass" + xóa note skip.

**Đã sửa (non-frozen):** Tasks viết lại — endpoint skip thành guarded upsert (không sửa row pass/pending, trả status thực tế); `file_path=None` ở cả 2 nhánh (không xóa file vật lý); `save_itinerary` dọn row itinerary skipped; `list_documents` order_by id; `review_document` guard 400 cho row skipped/không file; `handleSkip` FE có guard in-flight + guard response trễ.

**Known-bad tránh được:** hồ sơ đã upload/pass bị hạ thành "skipped" kèm note "khách bổ sung trực tiếp" trong khi file thật vẫn nằm đó — dữ liệu staff sai; tài liệu skip tự thành "pass" không qua file nào.

**KEEP (giữ nguyên khi viết lại):** layout DocumentItem — skipButton text muted underline xếp cột dọc dưới nút chính, stopPropagation; StatusChip variant skipped đúng màu đã chọn; ChecklistScreen — cách tính `skippedCount` tránh đếm đôi itinerary, chip xám itinerary theo idiom "✓ Đã tạo", banner trong BottomActionArea idiom #f0f9ff, ReadinessBanner prop `skipped` + hậu tố "· N bổ sung sau", inline `skipError` banner đỏ trên list, hành vi upload replace-cả-object docState (tự loại item đang upload khỏi canSubmit).

### 2026-07-12 — Vòng review 2 (bad_spec loopback #2)

**Findings kích hoạt:** (1) spec quy định "server trả status khác → giữ nguyên state local" — tạo silent no-op: row server kẹt `pending` (review đứt giữa chừng + reload) thì nút "Bổ sung sau" bấm mãi không có phản hồi; (2) guard response trễ chỉ check `uploading`/`reviewing` — skip response về trễ sau khi upload mới đã `pass` vẫn ghi đè chip "Đạt" thành "Bổ sung sau".

**Đã sửa (non-frozen):** Task ChecklistScreen mục (1) viết lại — response không phải skipped thì ĐỒNG BỘ state local theo server (`{id, status}`) + hiện thông báo inline giải thích, không im lặng; guard response trễ thêm điều kiện status local `'pass'`.

**Known-bad tránh được:** người dùng kẹt với nút skip chết không phản hồi; tài liệu đã pass hiển thị sai thành "bổ sung sau" đến khi reload.

**KEEP (giữ nguyên khi viết lại):** TOÀN BỘ implementation vòng 2 đã được acceptance auditor xác nhận đạt 100% spec — giữ nguyên mọi thứ, chỉ thay đổi phần xử lý response trong `handleSkip` theo task mục (1) mới. Tham chiếu diff vòng 2 (nếu còn): scratchpad `skip-upload-v2.diff`. Cụ thể giữ: guarded upsert backend + `file_path=None` 2 nhánh + guard 400 review + dọn itinerary trong save_itinerary + order_by; StatusChip variant; DocumentItem layout cột dọc + skipButtonStyle; skippingIds finally-cleanup; canSubmit/skippedCount/banner/ReadinessBanner như vòng 2.

### 2026-07-12 — Vòng review 3 (patch, không loopback)

**Findings kích hoạt (đều là guard corner-case, sửa điểm):** (1) sync response có thể hạ cấp local `needs_clarification` → `pending` khi server row kẹt pending — mất quyền submit + mất notes; (2) guard response trễ thiếu so sánh `document_id` — response mang row cũ vẫn ghi đè kết quả review mới hơn; (3) skip itinerary race với `save_itinerary` → row skipped ma khi `itinerary_json` đã có; (4) `docsRef` sync bằng passive effect trễ 1 nhịp so với microtask của response; (5) `triggerUpload` không chặn khi skip request cùng doc đang bay.

**Patch đã áp:** `skipResponseStale(docState, data)` thêm điều kiện `!data.document_id` và `data.document_id < docState.id`; updater giữ nguyên state khi server trả `pending` đè `needs_clarification` (vẫn hiện thông báo từ chối); endpoint skip trả `{document_id: null, status: "created"}` khi `doc_type="itinerary"` và `itinerary_json` đã có (client im lặng — context sẽ tự cập nhật); `useLayoutEffect` cho docsRef; `triggerUpload` no-op khi `skippingIds` chứa docId.

**Defer:** row skipped cũ còn lại sau khi upload lại cùng doc_type (chỉ ảnh hưởng consumer staff-view tương lai); race 2 tab giữa review/skip (cần transaction). **Reject:** thông báo lỗi không phân biệt HTTP status (idiom toàn codebase), spinner nút skip (polish).

### 2026-07-12 — Tích hợp với bản skip trên origin/main

**Bối cảnh:** Khi push, phát hiện `origin/main` đã có bản skip riêng (commit "Song Han user feedback") — UX "Tôi chưa có tài liệu này" / "Bỏ qua" / "Hoàn tác", nhãn "Không bắt buộc", passport không cho skip, confirm khi gửi thiếu tài liệu bắt buộc — nhưng **chỉ state client, không persist**. Human chọn phương án ghép: giữ UX remote + port backend persistence của spec này.

**Kết quả tích hợp (thay thế phần UI của các task cũ):**
- Backend giữ nguyên từ spec: endpoint skip guarded upsert (không đè pass/pending), guard 400 review trên row skipped, `list_documents` order_by id. Thêm mới: endpoint `POST /documents/unskip` (xóa row skipped theo doc_type) phục vụ nút "Hoàn tác" của UX remote.
- Bỏ (do UX remote thay thế): StatusChip variant skipped, DocumentItem onSkip, itinerary skip + dọn row trong save_itinerary (itinerary giờ là "Tự động tạo", không skip được), skipResponseStale/docsRef (mô hình optimistic + two-map của remote tự lành: row skipped tách khỏi docsMap, upload thắng skip).
- FE wiring: `loadExistingDocs` tách row skipped vào map `skipped` (persist qua reload); `handleSkip` optimistic + revert khi server từ chối (đã có file); `handleUnskip` optimistic + xóa row backend; upload dọn row skipped cũ.
- Bản implementation cũ đầy đủ lưu ở branch `backup-local-skip` (commit 40f6074).

## Suggested Review Order (bản tích hợp — thay bảng cũ)

**Persist skip ở backend**

- Entry point: endpoint skip — guarded upsert, không đè pass/pending
  [`application.py:168`](../../api/routers/application.py#L168)

- Endpoint unskip cho nút "Hoàn tác" — xóa row skipped theo doc_type
  [`application.py:203`](../../api/routers/application.py#L203)

- Guard 400: row skipped không vào luồng AI review
  [`application.py:245`](../../api/routers/application.py#L245)

- order_by(id) cho last-wins deterministic
  [`application.py:222`](../../api/routers/application.py#L222)

**Nối UX remote với backend**

- loadExistingDocs tách row skipped → map `skipped` (khôi phục sau reload)
  [`ChecklistScreen.jsx:104`](../../visa-client/src/screens/ChecklistScreen.jsx#L104)

- handleSkip optimistic + revert khi server từ chối vì đã có file
  [`ChecklistScreen.jsx:119`](../../visa-client/src/screens/ChecklistScreen.jsx#L119)

- handleUnskip + dọn row skipped cũ khi upload
  [`ChecklistScreen.jsx:138`](../../visa-client/src/screens/ChecklistScreen.jsx#L138)

- Nút "Tôi chưa có tài liệu này" / "Hoàn tác" gọi backend thay vì chỉ setState
  [`ChecklistScreen.jsx:339`](../../visa-client/src/screens/ChecklistScreen.jsx#L339)

## Design Notes

- Upsert theo `(application_id, doc_type)` chỉ áp dụng cho skip và chỉ khi row mới nhất KHÔNG ở trạng thái `pass`/`pending` — bảo vệ tài liệu đã upload khỏi bị clobber bởi request skip trễ. Upload giữ nguyên hành vi tạo row mới (docsMap phía FE key theo doc_type, row sau ghi đè row trước — cần `list_documents` order_by id).
- Set `file_path=None` khi skip nhưng KHÔNG xóa file vật lý trên đĩa (không phá dữ liệu người dùng đã gửi).
- Không thêm confirm dialog khi skip — 1 tap là đủ (tester muốn flexible, ít friction); đổi ý = bấm "Tải lên".
- Không thêm unique constraint `(application_id, doc_type)` (cần migration — Ask First); chống double-tap bằng guard client `skippingIds` là đủ cho demo.

## Verification

**Commands:**
- `cd visa-client && npm run build` -- expected: build pass, không lỗi ESLint/JSX
- `curl -X POST localhost:8000/api/application/{id}/documents/skip -H 'Content-Type: application/json' -d '{"doc_type":"bank_statement"}'` -- expected: `{"document_id":..., "status":"skipped"}`; gọi lần 2 trả cùng `document_id`

**Manual checks (if no CLI):**
- Chạy app local, đi đến bước Chuẩn bị hồ sơ: skip vài item → reload → trạng thái giữ nguyên; skip hết → nút gửi hiện kèm banner "N tài liệu sẽ bổ sung sau".

## Suggested Review Order

**Persist skip ở backend (guarded upsert)**

- Entry point: endpoint skip — guard pass/pending chống clobber, upsert row mới nhất, file_path=None
  [`application.py:159`](../../api/routers/application.py#L159)

- Guard race với "AI tạo": itinerary đã có thì trả `created`, không tạo row ma
  [`application.py:166`](../../api/routers/application.py#L166)

- Guard 400: row skipped/không file không được vào luồng AI review (chặn skipped→pass)
  [`application.py:227`](../../api/routers/application.py#L227)

- save_itinerary dọn row itinerary skipped — hết trạng thái "vừa có vừa bổ sung sau"
  [`application.py:292`](../../api/routers/application.py#L292)

- order_by(id) để FE last-wins đúng trên mọi DB, không chỉ SQLite
  [`application.py:203`](../../api/routers/application.py#L203)

**Luồng skip phía client (chống response trễ)**

- Predicate staleness: response trễ không ghi đè upload đang chạy / pass / row mới hơn
  [`ChecklistScreen.jsx:157`](../../visa-client/src/screens/ChecklistScreen.jsx#L157)

- handleSkip: clear lỗi đầu call, guard in-flight, sync theo server khi bị từ chối (không im lặng)
  [`ChecklistScreen.jsx:162`](../../visa-client/src/screens/ChecklistScreen.jsx#L162)

- docsRef sync bằng layout effect — đóng cửa sổ microtask giữa commit và response
  [`ChecklistScreen.jsx:64`](../../visa-client/src/screens/ChecklistScreen.jsx#L64)

- triggerUpload no-op khi skip cùng doc đang bay — bịt lỗ hổng in-flight 2 chiều
  [`ChecklistScreen.jsx:104`](../../visa-client/src/screens/ChecklistScreen.jsx#L104)

**Nới điều kiện gửi hồ sơ**

- canSubmit: pass/needs_clarification/skipped + itinerary done-hoặc-skip — tester yêu cầu flexible
  [`ChecklistScreen.jsx:209`](../../visa-client/src/screens/ChecklistScreen.jsx#L209)

- skippedCount không đếm đôi itinerary; banner "Bạn sẽ bổ sung N tài liệu sau..." trên CTA
  [`ChecklistScreen.jsx:213`](../../visa-client/src/screens/ChecklistScreen.jsx#L213)

**UI phụ trợ**

- DocumentItem: nút "Bổ sung sau" cho pending/fail, chip + "Tải lên" khi skipped
  [`DocumentItem.jsx:14`](../../visa-client/src/components/DocumentItem.jsx#L14)

- Chip variant skipped
  [`StatusChip.jsx:6`](../../visa-client/src/components/StatusChip.jsx#L6)

- Comment giá trị review_status mới
  [`models.py:111`](../../db/models.py#L111)
