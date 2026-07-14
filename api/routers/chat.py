from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.ai import chat_with_haiku
from db.session import get_db
from db.models import Application, Document

router = APIRouter()

_ITINERARY_KEYWORDS = ["lịch trình", "đi đâu", "gợi ý", "kế hoạch đi", "plan", "itinerary"]


class ChatRequest(BaseModel):
    message: str
    history: list
    context: dict


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message.strip():
        return {"reply": ""}

    messages = req.history + [{"role": "user", "content": req.message}]
    msg_lower = req.message.lower()

    is_itinerary = any(kw in msg_lower for kw in _ITINERARY_KEYWORDS)
    app_id = req.context.get("applicationId")

    app = None
    if app_id:
        try:
            app = db.get(Application, int(app_id))
            # Ownership check: applicationId là số tự tăng đoán được (IDOR) — từ khi chat mang
            # PII/tiến độ thật, chỉ chấp nhận app khi sessionId của client khớp
            session_id = req.context.get("sessionId")
            if app and app.session_id and session_id != app.session_id:
                app = None
        except Exception:
            app = None

    if is_itinerary and app:
        try:
            td = app.travel_dates if isinstance(app.travel_dates, dict) else {}
            if td.get("departure") and td.get("return"):
                from api.ai import suggest_itinerary_chat
                result = suggest_itinerary_chat(
                    destination=app.destination or "japan",
                    departure=td["departure"],
                    return_date=td["return"],
                )
                return {"reply": result["reply"], "itinerary": result["itinerary_data"]}
        except Exception:
            pass

    # Checklist đã cache trên application = đúng nội dung khách đang thấy trong UI —
    # bơm vào prompt để bot tư vấn được "giấy tờ nào cần / cách lấy" từ nội dung kiểm duyệt
    checklist = app.checklist_json if app and isinstance(app.checklist_json, dict) else None

    # Tiến độ thật của khách (server-side, chỉ status — không nội dung file) để bot
    # trả lời bám vào hồ sơ thay vì chung chung
    progress = None
    if app:
        try:
            # ORDER BY id: re-upload tạo row mới cùng doc_type — dict last-wins lấy trạng thái mới nhất
            doc_rows = (db.query(Document)
                        .filter(Document.application_id == app.id)
                        .order_by(Document.id).all())
            documents = {d.doc_type: (d.review_status or "pending") for d in doc_rows}
            elig_data = app.eligibility_data if isinstance(app.eligibility_data, dict) else {}
            extracted = app.extracted_info_json if isinstance(app.extracted_info_json, dict) else None
            progress = {
                "eligibility_result": app.eligibility_result,
                "eligibility_headline": elig_data.get("headline"),
                "documents": documents,
                "personal": extracted,
            }
        except Exception:
            import logging
            logging.getLogger(__name__).warning("Không dựng được progress context cho chat (app_id=%s)", app.id, exc_info=True)
            progress = None

    reply = chat_with_haiku(messages, req.context, checklist, progress)
    return {"reply": reply}
