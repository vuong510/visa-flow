from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.ai import chat_with_haiku
from db.session import get_db
from db.models import Application

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

    if is_itinerary and app_id:
        try:
            app = db.get(Application, int(app_id))
            td = app.travel_dates if app and isinstance(app.travel_dates, dict) else {}
            if app and td.get("departure") and td.get("return"):
                from api.ai import suggest_itinerary_chat
                result = suggest_itinerary_chat(
                    destination=app.destination or "japan",
                    departure=td["departure"],
                    return_date=td["return"],
                )
                return {"reply": result["reply"], "itinerary": result["itinerary_data"]}
        except Exception:
            pass

    reply = chat_with_haiku(messages, req.context)
    return {"reply": reply}
