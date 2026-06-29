from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from api.ai import chat_with_haiku

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list
    context: dict


@router.post("/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        return {"reply": ""}

    messages = req.history + [{"role": "user", "content": req.message}]
    reply = chat_with_haiku(messages, req.context)
    return {"reply": reply}
