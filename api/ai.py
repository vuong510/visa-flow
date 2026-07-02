import json
import re
import base64
from pathlib import Path
from anthropic import Anthropic
from core.config import ANTHROPIC_API_KEY, HAIKU, SONNET

_CHECKLIST_DIR = Path(__file__).parent.parent / "static" / "checklists"

def _load_checklist(destination: str) -> dict:
    path = _CHECKLIST_DIR / f"{destination}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def _parse_json(text: str):
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE).strip()
    # Try to extract JSON array first, then object
    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
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
    departure = (travel_dates or {}).get("departure", "")
    return_date = (travel_dates or {}).get("return", "")

    data = _load_checklist(destination)

    by_emp = data.get("by_employment", {})
    emp_items = by_emp.get(employment_type, by_emp.get("employee", []))

    # Inject travel dates into description fields that reference them
    universal_raw = data.get("universal", [])
    universal_items = []
    for item in universal_raw:
        item = dict(item)
        if "{departure}" in item.get("description", "") or "{return_date}" in item.get("description", ""):
            item["description"] = item["description"].replace("{departure}", departure).replace("{return_date}", return_date)
        universal_items.append(item)

    items = emp_items + universal_items
    confidence_note = data.get("confidence_notes", {}).get(employment_type)

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

    system = f"""Bạn là trợ lý tư vấn xin visa cho người dùng Việt Nam. Trả lời bằng tiếng Việt, ngắn gọn, thực tế.

Context người dùng: {dest_line} {emp_line} {screen_line}

Nguyên tắc:
- Trả lời thẳng vào câu hỏi, không cần chào hỏi hay giới thiệu bản thân
- Dùng văn xuôi thuần túy — KHÔNG dùng markdown (không dùng **, *, #, -)
- TUYỆT ĐỐI KHÔNG đề cập ngưỡng số dư tài khoản hay thu nhập cụ thể
- Nếu không chắc, khuyên liên hệ đại sứ quán hoặc đại lý visa
- Tối đa 150 từ mỗi câu trả lời
- Không dùng emoji"""

    response = client.messages.create(
        model=HAIKU,
        max_tokens=512,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def generate_itinerary(destination: str, departure: str, return_date: str,
                       hotel_name: str = "", hotel_phone: str = "") -> list:
    """Generate a day-by-day itinerary in English for MOFA schedule form."""
    from datetime import datetime as _dt
    try:
        days = max(1, (_dt.strptime(return_date, "%Y-%m-%d") - _dt.strptime(departure, "%Y-%m-%d")).days + 1)
    except Exception:
        days = 7

    dest_name = "Japan" if destination == "japan" else "China"
    city = "Tokyo" if destination == "japan" else "Beijing"
    airport = "Narita International Airport" if destination == "japan" else "Beijing Capital International Airport"
    hotel = hotel_name or f"Hotel in {city}"

    system = f"""Generate a {days}-day tourist itinerary for {dest_name} for a Vietnamese traveller.
Departure: {departure}, Return: {return_date}.
Primary city: {city}. Hotel: {hotel}.

Rules:
- ALL text MUST be in English (no Vietnamese, no Japanese/Chinese characters)
- Activities must be real, specific tourist attractions and activities
- Keep each activity description under 55 characters
- Day 1 = arrival day (airport → hotel check-in)
- Last day = departure day (check-out → airport)
- Vary activities across days (temples, parks, shopping, food, museums, day trips)

Return ONLY a JSON array, no markdown, no extra text:
[
  {{
    "activities": ["activity description (max 55 chars)"],
    "accommodation": {{"name": "hotel name", "phone": "{hotel_phone or ''}"}}
  }},
  ...
]
One object per day, exactly {days} objects."""

    response = client.messages.create(
        model=HAIKU,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": f"Generate the {days}-day itinerary now."}],
    )
    try:
        result = _parse_json(response.content[0].text)
        if isinstance(result, list):
            return result
    except Exception:
        pass
    return []


def extract_id_info(image_bytes: bytes, media_type: str, doc_type: str) -> dict:
    """Extract personal info fields from a CCCD or passport image using Sonnet vision."""
    system = """Extract personal information from the identity document image.
Return ONLY valid JSON, no markdown, no extra text.

For CCCD (Vietnamese citizen ID card), extract:
{
  "family_name": "HO (uppercase Latin, surname only)",
  "given_name": "TEN DEM VA TEN (uppercase Latin, all names except surname)",
  "date_of_birth": "YYYY-MM-DD",
  "gender": "male" or "female",
  "id_number": "12-digit CCCD number",
  "place_of_birth": "province/city in English or transliterated",
  "home_address": "full address in Latin script"
}

For passport, extract:
{
  "family_name": "surname as printed in MRZ/data page (uppercase)",
  "given_name": "given names as printed (uppercase)",
  "date_of_birth": "YYYY-MM-DD",
  "gender": "male" or "female",
  "passport_number": "passport number",
  "passport_issue_date": "YYYY-MM-DD",
  "passport_expiry_date": "YYYY-MM-DD",
  "place_of_birth": "as printed on passport"
}

Rules:
- Return only fields you can clearly read; omit fields that are unclear or absent
- Dates must be YYYY-MM-DD format
- Names must be uppercase Latin characters only (no Vietnamese diacritics)
- gender: "male" if Nam/M, "female" if Nữ/F
- If image is unreadable or not an ID document, return {"error": "cannot_read"}"""

    user_content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
            }
        },
        {"type": "text", "text": f"Document type: {doc_type}. Extract all readable personal information fields."}
    ]

    response = client.messages.create(
        model=SONNET,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user_content}]
    )
    return _parse_json(response.content[0].text)


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
