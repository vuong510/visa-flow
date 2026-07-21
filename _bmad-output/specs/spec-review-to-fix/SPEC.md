---
id: SPEC-review-to-fix
companions: ["../spec-feedback-capture/SPEC.md", "../../../project-context.md"]
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability only — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Review-to-fix bán tự động

## Why

Hiện tại mọi feedback (từ chị Yến qua group chat) được dev tự đọc, tự điều tra, tự sửa, và ghi vào `deferred-work.md`. Việc tốn thời gian nhất không phải là viết fix, mà là đọc/điều tra để hiểu vấn đề — và dù feedback được ưu tiên tốt cỡ nào, khối lượng đọc trực tiếp vẫn bị giới hạn bởi capacity của một người. Khi kênh feedback mở rộng ra real user (spec `spec-feedback-capture`), khối lượng feedback sẽ tăng vượt quá khả năng tự đọc từng cái của dev. Cần một lớp bán tự động đứng giữa việc feedback được thu thập và việc dev quyết định sửa gì, để giảm cái dev phải tự đọc — không phải sắp xếp lại thứ tự đọc.

## Capabilities

- **CAP-1**
  - **intent:** Hệ thống nhóm các feedback có cùng root cause/vị trí code (xác định sau khi điều tra từng feedback riêng lẻ) thành một batch duy nhất, thay vì để dev xử lý từng feedback rời rạc.
  - **success:** Khi có nhiều feedback khác câu chữ nhưng cùng root cause/vị trí code, dev chỉ thấy một batch để xem xét, không phải N bản ghi rời rạc.

- **CAP-2**
  - **intent:** Với mỗi feedback, agent điều tra bằng cả đọc code tĩnh lẫn chạy reproduce/test thực tế, rồi giao nộp một gói chẩn đoán theo batch gồm: xác nhận đây có phải lỗi thật không, root cause, đề xuất hành động fix cho cả batch, và đánh giá ảnh hưởng (blast-radius) tới phần khác của hệ thống.
  - **success:** Mỗi batch có đủ bốn mục trên trước khi tới tay dev, hoặc được đánh dấu rõ "không đủ context để xác định" thay vì bỏ trống.

- **CAP-3**
  - **intent:** Gói chẩn đoán thể hiện rõ mức độ tin cậy của agent, không trình bày một root cause chỉ là suy đoán như một sự thật chắc chắn.
  - **success:** Dev phân biệt được ngay trong gói đâu là kết luận đã xác nhận (ví dụ tái hiện được lỗi) và đâu là suy đoán tốt nhất chưa kiểm chứng.

- **CAP-4**
  - **intent:** Mọi batch feedback đều đến được tay dev để ra quyết định, xuất hiện ở nơi dev đã quen theo dõi công việc — không phải một dashboard/silo mới phải nhớ ghé riêng.
  - **success:** Không có batch nào bị bỏ quên vô thời hạn; batch mới xuất hiện trong quy trình theo dõi công việc hiện có của dev (ví dụ `deferred-work.md` hoặc sprint tracking).

- **CAP-5**
  - **intent:** Dev ra quyết định (approve/dismiss) cho một batch chỉ dựa vào gói chẩn đoán, không cần đọc qua feedback gốc; batch được approve trở thành input cho `bmad-quick-dev` để dev tự tay implement fix.
  - **success:** Một batch được approve trở thành spec/input sẵn sàng cho `bmad-quick-dev`, mang theo root cause + đề xuất fix + impact assessment có sẵn — dev không cần điều tra lại từ đầu.

## Constraints

- Agent không được tự viết hoặc ship code fix — chỉ chuẩn bị gói chẩn đoán/đề xuất để dev quyết định. Người sửa code vẫn luôn là dev.
- Mọi batch bắt buộc qua gate xác nhận của con người trước khi coi là lỗi thật — hệ thống không tự dismiss hay tự approve fix mà không có quyết định của dev, vì feedback có thể chỉ là user hiểu sai.
- Gói chẩn đoán phải gộp theo batch (nhiều feedback tương tự = một gói), không phải một feedback = một gói riêng — mục tiêu cốt lõi là giảm số lượng phải đọc trực tiếp, không chỉ sắp xếp lại ưu tiên.
- Việc gộp batch xảy ra SAU khi điều tra từng feedback riêng lẻ, dựa trên root cause/vị trí code trùng nhau — không so khớp raw text trước khi điều tra, vì mô tả user mơ hồ và đa dạng cách diễn đạt cho cùng một lỗi khiến so raw text dễ gộp nhầm hoặc bỏ sót.
- Gói chẩn đoán phải luôn có chỉ báo mức độ tin cậy — không trình bày suy đoán như sự thật chắc chắn khi agent không đủ context để xác nhận. Nhãn tin cậy bám theo phương pháp điều tra: tái hiện được lỗi qua test/reproduce = đã xác nhận; chỉ đọc code tĩnh suy luận = suy đoán tốt nhất — chưa kiểm chứng.
- Batch/gói phải xuất hiện ở nơi dev đã quen kiểm tra công việc hiện có (ví dụ `deferred-work.md`, sprint tracking) — không tạo dashboard/silo mới mà dev phải nhớ ghé thăm riêng.

## Non-goals

- Agent không tự viết hoặc ship code fix — đó là `bmad-quick-dev`, quy trình sẵn có của dự án, dev vẫn là người thực hiện.
- Không bao gồm UI/mechanism thu thập feedback từ user — đã có spec riêng (`spec-feedback-capture`, done).
- Không bao gồm việc thông báo lại cho user đã report sau khi fix được ship — xảy ra sau ranh giới của spec này. Rủi ro "không khép kín vòng lặp" đã được nhận diện nhưng cần một spec/cơ chế riêng để giải quyết, có thể tái dùng notification pattern đã có (story 4-2-result-notification).
- Không tự động dismiss hoặc tự động approve fix mà không có quyết định của dev — con người luôn là gate cuối trước khi có bất kỳ hành động engineering nào.

## Success signal

Nhiều feedback tương tự đổ về từ real user → hệ thống gộp thành một batch → dev mở gói chẩn đoán và thấy ngay: có phải lỗi thật không, root cause, đề xuất fix, và ảnh hưởng tới đâu — dev ra quyết định (approve/dismiss) mà không cần đọc qua từng feedback gốc, và batch đó xuất hiện đúng nơi dev vẫn quen theo dõi công việc.

## Assumptions

- Hình thức hiển thị gói chẩn đoán chưa chốt cụ thể — giả định tái dùng định dạng markdown nhất quán với `deferred-work.md` hiện có, đơn giản nhất để tích hợp vào quy trình sẵn có.
- Chỉ báo tin cậy ở dạng nhãn đơn giản hai mức ("đã xác nhận qua tái hiện lỗi" / "suy đoán tốt nhất — chưa kiểm chứng") thay vì confidence score phức tạp.
- Cơ chế thông báo lại cho user sau khi fix ship bị defer có chủ đích (không mở spec riêng ngay) — app hiện chưa có định danh user bền vững ngoài session_id/localStorage nên khó với tới user đã rời tab; sẽ quay lại nếu thấy thực sự cần khi luồng chính đã chạy ổn.
