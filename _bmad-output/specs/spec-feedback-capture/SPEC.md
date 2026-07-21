---
id: SPEC-feedback-capture
companions: ["../../../project-context.md"]
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability only — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Thu thập feedback từ real user

## Why

Hiện tại visa-flow chỉ nhận được feedback từ nội bộ (team chị Yến dùng thử, nhắn qua group chat, dev tự sửa và ghi vào `deferred-work.md`). Đây là một pain đang giới hạn khả năng phát hiện lỗi: real user thật không nhắn group chat khi gặp trục trặc — họ chỉ tức và bỏ luồng (drop-off), nghĩa là phần lớn vấn đề thật sự đang không được nhìn thấy. Cần một kênh thu feedback trực tiếp từ real user để bắt được các vấn đề này trước khi ảnh hưởng đến nhiều khách hàng hơn.

## Capabilities

- **CAP-1**
  - **intent:** User có thể mở ô nhập feedback từ bất kỳ màn hình nào trong app, tại bất kỳ thời điểm nào trong flow.
  - **success:** Audit toàn bộ danh sách màn hình của visa-client xác nhận không màn nào thiếu entry point feedback; từ màn hình bất kỳ, user mở được ô nhập trong một thao tác bấm.

- **CAP-2**
  - **intent:** User mô tả vấn đề gặp phải bằng văn bản tự do (chat-style), không phải điền form có cấu trúc nhiều field.
  - **success:** Bản ghi feedback lưu được nguyên văn text do user gõ; luồng gửi không yêu cầu chọn category, severity, hay bất kỳ field bắt buộc nào khác trước khi submit.

- **CAP-3**
  - **intent:** Hệ thống tự động đính kèm context tại thời điểm submit (màn hình hiện tại, applicationId, sessionId) mà không cần user tự khai.
  - **success:** Mọi bản ghi feedback lưu kèm screen/applicationId/sessionId được hệ thống tự capture; không có field context nào đòi hỏi user nhập tay.

- **CAP-4**
  - **intent:** Cơ chế ghi nhận feedback hoạt động độc lập với tính khả dụng của backend/API chính.
  - **success:** Mô phỏng backend không phản hồi (network fault injection) — feedback vẫn được giữ lại ở queue cục bộ tại thời điểm submit, và được đồng bộ lên server khi backend phục hồi; không mất dữ liệu ngoại trừ mất hẳn thiết bị hoặc local storage bị xoá.

- **CAP-5**
  - **intent:** User nhận được xác nhận rõ ràng ngay sau khi gửi feedback.
  - **success:** Sau khi bấm gửi, UI hiển thị thông báo xác nhận trong vòng vài giây — kể cả khi việc đồng bộ lên server vẫn đang chờ ở nền (ack không phụ thuộc kết quả network call).

## Constraints

- Entry point feedback phải là component/route riêng biệt, không tái dùng `ChatWidget.jsx` hay `/chat`: tránh AI bot cố trả lời complaint thay vì chỉ ghi nhận, tránh bug có sẵn khiến ChatWidget tự ẩn ở màn Price (vi phạm CAP-1), và tránh phụ thuộc vào backend AI (vi phạm CAP-4). UI bên trong vẫn ở dạng một ô chat đơn giản để giữ cảm giác quen thuộc, chỉ khác component/logic/route.
- Trigger phải là hành động bấm chủ động của user — không tự động phát hiện khoảnh khắc frustration/exit-intent (đã xác nhận không khả thi đáng tin cậy).
- Không yêu cầu user tự khai màn hình/bước đang gặp lỗi — phải tự động đính kèm, vì mô tả mơ hồ của user là nguyên nhân chính khiến việc điều tra sau này tốn thời gian.
- Chỉ một ô free-text, không dùng form nhiều field — feedback thường xảy ra đúng lúc user đang bực, mọi field thêm là ma sát.
- Backend/API chính không được là single point of failure của việc ghi nhận feedback — vì đây chính là lúc backend nhiều khả năng đang lỗi nhất (cùng nguyên nhân khiến user bực).
- Feedback lưu ở bảng DB mới (`Feedback`), quan hệ one-to-many với `Application` — không gắn vào `Document` (mô hình file-upload theo `doc_type`, không khớp) hay vào `Application` (một dòng/hồ sơ, không hợp nhiều feedback theo thời gian).

## Non-goals

- Không bao gồm việc AI điều tra, tổng hợp, phân cụm, hay đề xuất fix cho feedback đã thu — thuộc spec riêng "review-to-fix bán tự động".
- Không thay đổi kênh feedback nội bộ hiện tại của team (chị Yến qua group chat) — giữ nguyên như hiện trạng.
- Không bao gồm admin dashboard/UI cho staff đọc và triage feedback — spec này chỉ dừng ở thu thập và lưu trữ.
- Không tự động chụp screenshot màn hình kèm feedback — rủi ro privacy (màn hình có thể đang hiển thị passport/CCCD hoặc thông tin cá nhân) trong khi app chưa có access-control chặt cho phía staff. CAP-3 (screen + applicationId + sessionId) đủ để dev tái hiện trạng thái từ dữ liệu đã lưu.

## Success signal

Một real user (không thuộc team nội bộ) gặp trục trặc ở bất kỳ bước nào trong flow, bấm feedback, mô tả bằng lời tự nhiên, và nhận được xác nhận đã gửi — kể cả khi đúng lúc đó backend đang gặp sự cố. Bản ghi feedback đến tay người điều tra kèm đủ context (màn hình, applicationId, sessionId) để không cần hỏi lại user đang ở bước nào.

## Assumptions

- Cơ chế lưu tạm khi backend down dùng localStorage + retry queue phía client (giải pháp đơn giản nhất khả thi trên web hiện tại), trừ khi có chỉ định khác.
- Xác nhận (ack) hiển thị cho user là optimistic — hiện ngay khi ghi cục bộ thành công, không chờ server xác nhận — để CAP-5 không vô tình phụ thuộc backend giống điều CAP-4 đang tránh.
- Mỗi bản ghi feedback kèm một client-generated id để retry từ local queue (CAP-4) không tạo bản ghi trùng (idempotency).
