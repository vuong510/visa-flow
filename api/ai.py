import json
import re
import base64
from anthropic import Anthropic
from core.config import ANTHROPIC_API_KEY, HAIKU, SONNET

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE).strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def assess_eligibility(profile: dict, travel_dates: dict, destination: str) -> dict:
    from datetime import date
    today = date.today().isoformat()
    departure = (travel_dates or {}).get("departure", "")
    dest_name = "Nhật Bản" if destination == "japan" else "Trung Quốc"

    system = f"""Bạn là chuyên gia đánh giá hồ sơ visa {dest_name} cho công dân Việt Nam.

LUẬT ÁP DỤNG (theo thứ tự, dừng ở luật đầu tiên phù hợp):
1. CHẶN CỨNG: Nếu prior_denial=true VÀ denial_country="{destination}" VÀ denial_date trong vòng 180 ngày trước ngày hôm nay → result="not_eligible"
2. CHẶN CỨNG: Nếu ngày khởi hành ít hơn 10 ngày làm việc (bỏ qua thứ 7, CN) kể từ hôm nay → result="not_eligible"
3. TRƯỜNG HỢP ĐẶC BIỆT: Nếu employment_type="freelancer" → result="edge_case"
4. MẶC ĐỊNH: result="eligible"

TÍN HIỆU TÍCH CỰC (thêm vào bullets cho eligible/edge_case):
- Nếu has_prior_stamps=true: thêm "Có dấu nhập cảnh trước đây — tín hiệu tích cực"

Trả về JSON chính xác sau (KHÔNG có markdown, KHÔNG có text thừa):
{{
  "result": "eligible" | "not_eligible" | "edge_case",
  "headline": "chuỗi tiếng Việt",
  "bullets": ["điểm 1", "điểm 2"],
  "reason": "một câu tiếng Việt nếu not_eligible hoặc edge_case, null nếu eligible",
  "confidence_label": "Độ tin cậy AI: Cao" | "Độ tin cậy AI: Trung bình"
}}

Quy tắc headline:
- eligible: PHẢI là CHÍNH XÁC "Hồ sơ của bạn trông tốt ✓"
- not_eligible: tiêu đề ngắn gọn nêu lý do từ chối
- edge_case: "Hồ sơ của bạn có thể đủ điều kiện"

Quy tắc confidence_label (bắt buộc):
- eligible → "Độ tin cậy AI: Cao"
- edge_case → "Độ tin cậy AI: Trung bình"
- not_eligible → "Độ tin cậy AI: Cao"

TUYỆT ĐỐI KHÔNG đề cập đến ngưỡng số dư tài khoản hay thu nhập tối thiểu cụ thể."""

    user = f"Ngày hôm nay: {today}\nNgày khởi hành: {departure}\nHồ sơ: {json.dumps(profile, ensure_ascii=False)}"

    response = client.messages.create(
        model=HAIKU,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return _parse_json(response.content[0].text)


def generate_checklist(profile: dict, travel_dates: dict, destination: str) -> dict:
    employment_type = (profile or {}).get("employment_type", "employee")
    dest_name = "Nhật Bản" if destination == "japan" else "Trung Quốc"
    departure = (travel_dates or {}).get("departure", "")
    return_date = (travel_dates or {}).get("return", "")

    employment_map = {
        "employee": "nhân viên công ty",
        "student": "sinh viên",
        "business_owner": "chủ doanh nghiệp",
        "freelancer": "freelancer/tự do",
        "homemaker": "nội trợ",
        "retired": "đã nghỉ hưu",
    }
    emp_label = employment_map.get(employment_type, employment_type)

    doc_rules = {
        "employee": [
            {"id": "passport", "name": "Hộ chiếu", "description": "Còn hạn ít nhất 6 tháng sau ngày về", "format": "Bản gốc", "why": "Tài liệu định danh chính thức bắt buộc"},
            {"id": "employment_certificate", "name": "Xác nhận công tác", "description": "Do công ty cấp, có đóng dấu và chữ ký giám đốc", "format": "Bản gốc", "why": "Xác nhận bạn đang có việc làm ổn định"},
            {"id": "leave_approval", "name": "Đơn xin nghỉ phép được duyệt", "description": f"Phép nghỉ phải khớp đúng với ngày đi {departure} và ngày về {return_date}", "format": "Bản gốc có chữ ký trưởng bộ phận", "why": "Đảm bảo ngày đi/về nhất quán với hồ sơ"},
            {"id": "payslips", "name": "Bảng lương 3 tháng gần nhất", "description": "Lương tháng gần đây nhất, có dấu công ty", "format": "Bản gốc hoặc bản sao công chứng", "why": "Chứng minh thu nhập ổn định"},
            {"id": "bank_statements", "name": "Sao kê ngân hàng 3 tháng", "description": "Tài khoản thanh toán chính, sao kê từ ngân hàng", "format": "Bản có dấu ngân hàng", "why": "Chứng minh khả năng tài chính cho chuyến đi"},
        ],
        "student": [
            {"id": "passport", "name": "Hộ chiếu", "description": "Còn hạn ít nhất 6 tháng sau ngày về", "format": "Bản gốc", "why": "Tài liệu định danh chính thức bắt buộc"},
            {"id": "student_id", "name": "Thẻ sinh viên / Xác nhận đang học", "description": "Còn hiệu lực, do trường cấp", "format": "Bản gốc", "why": "Chứng minh tình trạng học tập"},
            {"id": "parent_guarantee", "name": "Thư bảo lãnh của phụ huynh", "description": "Phụ huynh cam kết bảo lãnh chi phí và đón về", "format": "Bản gốc có công chứng", "why": "Bảo lãnh tài chính cho sinh viên"},
            {"id": "parent_employment", "name": "Xác nhận công tác của phụ huynh", "description": "Do công ty phụ huynh cấp", "format": "Bản gốc", "why": "Chứng minh nguồn thu nhập của người bảo lãnh"},
            {"id": "parent_bank_statements", "name": "Sao kê ngân hàng phụ huynh 3 tháng", "description": "Tài khoản của người bảo lãnh", "format": "Bản có dấu ngân hàng", "why": "Chứng minh khả năng tài chính của người bảo lãnh"},
        ],
        "business_owner": [
            {"id": "passport", "name": "Hộ chiếu", "description": "Còn hạn ít nhất 6 tháng sau ngày về", "format": "Bản gốc", "why": "Tài liệu định danh chính thức bắt buộc"},
            {"id": "business_license", "name": "Giấy phép kinh doanh", "description": "Còn hiệu lực, có tên bạn là chủ sở hữu", "format": "Bản sao công chứng", "why": "Chứng minh hoạt động kinh doanh hợp pháp"},
            {"id": "company_financials", "name": "Báo cáo tài chính doanh nghiệp", "description": "Kỳ gần nhất, có chữ ký kế toán", "format": "Bản gốc hoặc sao y", "why": "Chứng minh hoạt động kinh doanh có doanh thu"},
            {"id": "bank_statements", "name": "Sao kê ngân hàng cá nhân 3 tháng", "description": "Tài khoản cá nhân của chủ doanh nghiệp", "format": "Bản có dấu ngân hàng", "why": "Chứng minh tài chính cá nhân"},
        ],
        "freelancer": [
            {"id": "passport", "name": "Hộ chiếu", "description": "Còn hạn ít nhất 6 tháng sau ngày về", "format": "Bản gốc", "why": "Tài liệu định danh chính thức bắt buộc"},
            {"id": "freelance_contracts", "name": "Hợp đồng dịch vụ / Bằng chứng thu nhập", "description": "Hợp đồng với khách hàng, hóa đơn, hoặc biên lai thanh toán gần nhất", "format": "Bản gốc hoặc bản sao", "why": "Chứng minh nguồn thu nhập từ công việc tự do"},
            {"id": "bank_statements", "name": "Sao kê ngân hàng 3 tháng", "description": "Thể hiện các khoản tiền vào từ công việc freelance", "format": "Bản có dấu ngân hàng", "why": "Chứng minh dòng tiền ổn định"},
            {"id": "tax_declaration", "name": "Tờ khai thuế TNCN", "description": "Nếu có đăng ký mã số thuế cá nhân", "format": "Bản sao có xác nhận cơ quan thuế", "why": "Bổ sung chứng minh hoạt động thu nhập hợp pháp"},
        ],
        "homemaker": [
            {"id": "passport", "name": "Hộ chiếu", "description": "Còn hạn ít nhất 6 tháng sau ngày về", "format": "Bản gốc", "why": "Tài liệu định danh chính thức bắt buộc"},
            {"id": "spouse_employment", "name": "Xác nhận công tác của vợ/chồng", "description": "Do công ty vợ/chồng cấp, có đóng dấu", "format": "Bản gốc", "why": "Chứng minh nguồn thu nhập của gia đình"},
            {"id": "marriage_certificate", "name": "Giấy đăng ký kết hôn", "description": "Bản có dấu đỏ của UBND", "format": "Bản sao công chứng", "why": "Chứng minh mối quan hệ hôn nhân với người bảo lãnh"},
            {"id": "household_registration", "name": "Sổ hộ khẩu / Giấy xác nhận thường trú", "description": "Bản mới nhất", "format": "Bản sao công chứng", "why": "Xác nhận địa chỉ cư trú hợp pháp"},
            {"id": "bank_statements", "name": "Sao kê ngân hàng gia đình 3 tháng", "description": "Tài khoản chung hoặc của vợ/chồng", "format": "Bản có dấu ngân hàng", "why": "Chứng minh khả năng tài chính"},
        ],
        "retired": [
            {"id": "passport", "name": "Hộ chiếu", "description": "Còn hạn ít nhất 6 tháng sau ngày về", "format": "Bản gốc", "why": "Tài liệu định danh chính thức bắt buộc"},
            {"id": "retirement_certificate", "name": "Quyết định nghỉ hưu", "description": "Do cơ quan/tổ chức nơi công tác cấp", "format": "Bản sao công chứng", "why": "Xác nhận tình trạng đã nghỉ hưu"},
            {"id": "pension_statement", "name": "Quyết định hưởng lương hưu", "description": "Do BHXH cấp, thể hiện mức lương hưu hàng tháng", "format": "Bản gốc hoặc sao y", "why": "Chứng minh nguồn thu nhập ổn định"},
            {"id": "bank_statements", "name": "Sao kê ngân hàng 3 tháng", "description": "Thể hiện tiền lương hưu chuyển vào hàng tháng", "format": "Bản có dấu ngân hàng", "why": "Chứng minh tài chính thực tế"},
        ],
    }

    items = doc_rules.get(employment_type, doc_rules["employee"])
    confidence_note = None
    if employment_type == "freelancer":
        confidence_note = "Hồ sơ freelancer có độ biến động cao. Nhân viên tư vấn sẽ kiểm tra lại toàn bộ tài liệu trước khi nộp."

    return {"items": items, "confidence_note": confidence_note}


def chat_with_haiku(messages: list, context: dict) -> str:
    destination = context.get("destination")
    screen = context.get("screen", "")
    profile = context.get("profile") or {}

    dest_name = {"japan": "Nhật Bản", "china": "Trung Quốc"}.get(destination, "")
    dest_line = f"Điểm đến: {dest_name}." if dest_name else "Điểm đến: chưa chọn."
    emp = profile.get("employment_type", "")
    emp_line = f"Loại việc làm: {emp}." if emp else ""
    screen_line = f"Màn hình hiện tại: {screen}." if screen else ""

    system = f"""Bạn là trợ lý tư vấn xin visa cho người dùng Việt Nam. Hãy trả lời bằng tiếng Việt, ngắn gọn và thực tế.

Context người dùng: {dest_line} {emp_line} {screen_line}

Nguyên tắc:
- Trả lời dựa trên thông tin context nếu có liên quan
- TUYỆT ĐỐI KHÔNG đề cập ngưỡng số dư tài khoản hay thu nhập cụ thể
- Nếu không chắc, khuyên người dùng liên hệ đại sứ quán hoặc đại lý visa
- Giữ câu trả lời dưới 200 từ"""

    response = client.messages.create(
        model=HAIKU,
        max_tokens=512,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def review_document_image(image_bytes: bytes, media_type: str, doc_type: str, profile: dict) -> dict:
    employment_type = (profile or {}).get("employment_type", "")
    destination = (profile or {}).get("destination", "")

    system = """Bạn đang kiểm tra ảnh tài liệu visa. Hãy kiểm tra xem tài liệu có rõ ràng và hợp lệ không.

Trả về JSON (KHÔNG có markdown):
{
  "status": "pass" | "fail" | "needs_clarification",
  "reason": "lý do tiếng Việt nếu fail hoặc needs_clarification, null nếu pass"
}

Nguyên tắc:
- pass: tài liệu rõ ràng, đọc được, không có vấn đề rõ ràng
- needs_clarification: tài liệu mờ, thiếu thông tin, hoặc cần xác nhận thêm
- fail: tài liệu rõ ràng sai (hết hạn, tên không khớp, bị giả mạo)
- Khi không chắc → "needs_clarification" thay vì "fail"
- Lý do phải bằng tiếng Việt, cụ thể và hữu ích"""

    user_content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
            }
        },
        {
            "type": "text",
            "text": f"Loại tài liệu: {doc_type}\nLoại việc làm: {employment_type}\nĐiểm đến: {destination}\n\nKiểm tra tài liệu này."
        }
    ]

    response = client.messages.create(
        model=SONNET,
        max_tokens=256,
        system=system,
        messages=[{"role": "user", "content": user_content}]
    )
    return _parse_json(response.content[0].text)
