# Phiếu gắn nhãn Golden Set — dành cho chị Yến

Chị Yến ơi, phiếu này dùng để chị "chấm điểm mẫu" một lần cho các giấy tờ và ảnh hộ chiếu/CCCD.
Kết quả chấm của chị sẽ là đáp án chuẩn để tụi em kiểm tra xem AI chấm có giống chị không — chị chấm một buổi, máy được kiểm tra mãi mãi.
Chị chỉ cần điền vào 2 bảng bên dưới, không cần biết gì về kỹ thuật; chỗ nào phân vân chị cứ ghi thẳng vào cột ghi chú.

> ⚠️ **QUAN TRỌNG — bảo mật thông tin khách:**
> **KHÔNG chép số giấy tờ đầy đủ (số hộ chiếu, số CCCD) hay họ tên đầy đủ vào file này** — file sẽ được lưu trong hệ thống code.
> Chỉ ghi phần đã rút gọn theo đúng cột trong bảng (3 số cuối, 3 ký tự đầu của tên, năm sinh).

---

## Bảng 1 — Chấm tài liệu hồ sơ (~30 file)

Với mỗi file, chị xem như đang kiểm tra hồ sơ thật của khách và chọn MỘT trong ba nhãn:

- **ĐẠT** — giấy tờ rõ ràng, hợp lệ, nộp được
- **KHÔNG ĐẠT** — chắc chắn sai (hết hạn, sai tên, mờ đến mức vô dụng, giả mạo...)
- **CẦN XEM THÊM** — phân vân, cần hỏi lại khách hoặc xem bản gốc

| STT | Tên file | Loại giấy tờ | Nhãn (ĐẠT / KHÔNG ĐẠT / CẦN XEM THÊM) | Lý do (1 câu) |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| 11 | | | | |
| 12 | | | | |
| 13 | | | | |
| 14 | | | | |
| 15 | | | | |
| 16 | | | | |
| 17 | | | | |
| 18 | | | | |
| 19 | | | | |
| 20 | | | | |
| 21 | | | | |
| 22 | | | | |
| 23 | | | | |
| 24 | | | | |
| 25 | | | | |
| 26 | | | | |
| 27 | | | | |
| 28 | | | | |
| 29 | | | | |
| 30 | | | | |

Gợi ý chọn mẫu: trộn đủ loại (hộ chiếu, sao kê, xác nhận công tác, ảnh thẻ, đặt phòng...), có cả file đẹp lẫn file mờ/chụp nghiêng/thiếu trang — càng giống thực tế khách gửi càng tốt.

---

## Bảng 2 — Đáp án đọc ảnh hộ chiếu/CCCD (~15 ảnh)

Với mỗi ảnh, chị nhìn giấy tờ và ghi lại phần thông tin RÚT GỌN theo đúng 3 cột dưới đây (không ghi số đầy đủ — xem cảnh báo ở đầu phiếu):

- **Họ + 3 ký tự đầu của tên** — ví dụ tên trên giấy là NGUYEN VAN ANH thì ghi `NGUYEN + VAN`
- **3 số cuối của số hộ chiếu/CCCD** — ví dụ số là B1234567 thì chỉ ghi `567`
- **Năm sinh** — ví dụ `1995`

| Tên file | Họ + 3 ký tự đầu của tên | 3 số cuối hộ chiếu/CCCD | Năm sinh | Ghi chú |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

---

## Đặt file ở đâu?

- File tài liệu của Bảng 1 → bỏ vào thư mục: `tests/eval/golden/documents/`
- Ảnh hộ chiếu/CCCD của Bảng 2 → bỏ vào thư mục: `tests/eval/golden/ocr/`
- Tên file trong bảng phải khớp đúng tên file trong thư mục (ví dụ `ho_chieu_khach_01.jpg`).
- Phiếu này chị điền trực tiếp vào file, hoặc in ra điền tay rồi đưa lại em cũng được; điền xong gửi cho dev qua kênh riêng (Zalo/Drive nội bộ), **không** đính kèm vào code.

## Lưu ý riêng tư (quan trọng)

Ảnh và giấy tờ của khách thật là thông tin cá nhân — **KHÔNG được đưa lên git/mạng**.
Thư mục `tests/eval/golden/` đã được cài để máy tự bỏ qua toàn bộ file trong đó khi lưu code.
Chị cứ yên tâm bỏ file vào đúng thư mục, không cần làm gì thêm.

---

*Ghi chú kỹ thuật cho dev (chị Yến không cần đọc): nhãn OCR cố ý chỉ chứa định danh đã rút gọn để phiếu nhãn không thành nguồn rò PII thứ hai. Runner tầng 4 so khớp field-level dạng mask: 3 ký tự cuối của passport_number/id_number OCR được vs cột "3 số cuối"; họ đầy đủ + 3 ký tự đầu given_name vs cột tên; năm của date_of_birth vs cột "Năm sinh". So khớp đầy đủ từng ký tự chỉ làm thủ công trên máy dev có ảnh gốc — không đưa đáp án đầy đủ vào repo.*
