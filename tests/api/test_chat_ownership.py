"""Chat chỉ được dùng context hồ sơ khi sessionId khớp app.session_id (chặn IDOR đọc PII qua bot)."""
import api.routers.chat as chat_module


def _capture_chat(monkeypatch):
    calls = {}
    def fake_chat(messages, context, checklist=None, progress=None):
        calls["checklist"] = checklist
        calls["progress"] = progress
        return "ok"
    monkeypatch.setattr(chat_module, "chat_with_haiku", fake_chat)
    return calls


def _start_app(client):
    res = client.post("/api/application/start")
    data = res.json()
    return data["application_id"], data["session_id"]


def test_sai_session_khong_co_context(client, monkeypatch):
    app_id, _real_session = _start_app(client)
    calls = _capture_chat(monkeypatch)
    res = client.post("/api/chat", json={
        "message": "hồ sơ tôi tới đâu rồi",
        "history": [],
        "context": {"applicationId": app_id, "sessionId": "session-cua-nguoi-khac"},
    })
    assert res.status_code == 200
    assert calls["checklist"] is None
    assert calls["progress"] is None


def test_dung_session_co_progress(client, monkeypatch):
    app_id, session = _start_app(client)
    calls = _capture_chat(monkeypatch)
    res = client.post("/api/chat", json={
        "message": "hồ sơ tôi tới đâu rồi",
        "history": [],
        "context": {"applicationId": app_id, "sessionId": session},
    })
    assert res.status_code == 200
    assert isinstance(calls["progress"], dict)


def test_khong_gui_session_khong_co_context(client, monkeypatch):
    app_id, _ = _start_app(client)
    calls = _capture_chat(monkeypatch)
    client.post("/api/chat", json={
        "message": "hi",
        "history": [],
        "context": {"applicationId": app_id},
    })
    assert calls["progress"] is None and calls["checklist"] is None
