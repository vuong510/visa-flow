"""
Tests for the feedback capture endpoint (POST /api/feedback).
Covers: happy path with context, idempotent retry by client_id, missing message → 422,
race-condition-safe duplicate handling, and length validation on capped columns.
"""
import uuid
from unittest.mock import patch

from fastapi import Response

from db.models import Feedback
from conftest import TestingSessionLocal
from api.routers.feedback import create_feedback, FeedbackCreate


class TestFeedbackCreate:
    def test_submit_creates_row_with_context(self, client, new_application):
        client_id = str(uuid.uuid4())
        res = client.post("/api/feedback", json={
            "client_id": client_id,
            "message": "Nút gửi bị đơ ở màn hình checklist",
            "application_id": new_application,
            "session_id": "sess-abc",
            "screen": "checklist",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["message"] == "Nút gửi bị đơ ở màn hình checklist"
        assert data["application_id"] == new_application
        assert data["session_id"] == "sess-abc"
        assert data["screen"] == "checklist"
        assert data["client_id"] == client_id
        assert data["id"] is not None

    def test_submit_without_application_id(self, client):
        """Feedback from a screen with no application yet (e.g. landing) must still work."""
        client_id = str(uuid.uuid4())
        res = client.post("/api/feedback", json={
            "client_id": client_id,
            "message": "Trang chủ load chậm",
            "screen": "landing",
        })
        assert res.status_code == 201
        assert res.json()["application_id"] is None

    def test_duplicate_client_id_does_not_create_new_row(self, client, new_application):
        client_id = str(uuid.uuid4())
        payload = {
            "client_id": client_id,
            "message": "Lỗi khi upload passport",
            "application_id": new_application,
            "session_id": "sess-xyz",
            "screen": "documents",
        }
        first = client.post("/api/feedback", json=payload)
        assert first.status_code == 201
        first_id = first.json()["id"]

        # Simulate client retrying after thinking the first submit failed
        second = client.post("/api/feedback", json=payload)
        assert second.status_code == 200
        assert second.json()["id"] == first_id

    def test_missing_message_returns_422(self, client):
        res = client.post("/api/feedback", json={
            "client_id": str(uuid.uuid4()),
            "screen": "landing",
        })
        assert res.status_code == 422

    def test_whitespace_only_message_returns_422(self, client):
        res = client.post("/api/feedback", json={
            "client_id": str(uuid.uuid4()),
            "message": "   ",
            "screen": "landing",
        })
        assert res.status_code == 422

    def test_oversized_screen_returns_422(self, client):
        res = client.post("/api/feedback", json={
            "client_id": str(uuid.uuid4()),
            "message": "Test feedback",
            "screen": "x" * 51,  # column is String(50)
        })
        assert res.status_code == 422

    def test_oversized_session_id_returns_422(self, client):
        res = client.post("/api/feedback", json={
            "client_id": str(uuid.uuid4()),
            "message": "Test feedback",
            "session_id": "x" * 37,  # column is String(36)
        })
        assert res.status_code == 422

    def test_race_duplicate_client_id_hits_conflict_path_returns_200_not_500(self):
        """
        Simulates two near-simultaneous requests with the same client_id (e.g. React
        StrictMode's double-invoked mount effect, or a post-submit flush racing a
        mount-triggered flush): both pass the initial "not found" check, then one
        loses the race on INSERT. The endpoint must catch the resulting IntegrityError,
        roll back, and return the already-committed row with a 200 — not a 500.
        """
        client_id = str(uuid.uuid4())

        # Row "already committed by the winning concurrent request" before this
        # request's INSERT runs.
        setup_db = TestingSessionLocal()
        try:
            winner = Feedback(client_id=client_id, message="Winner request")
            setup_db.add(winner)
            setup_db.commit()
            setup_db.refresh(winner)
            winner_id = winner.id
        finally:
            setup_db.close()

        request_db = TestingSessionLocal()
        try:
            real_query = request_db.query
            call_count = {"n": 0}

            def fake_query(*args, **kwargs):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    # Force the pre-check to miss the row, simulating the race
                    # window where this request's SELECT ran before the other
                    # request's INSERT had committed.
                    class _FakeFilter:
                        def first(self):
                            return None
                    class _FakeQuery:
                        def filter(self, *a, **k):
                            return _FakeFilter()
                    return _FakeQuery()
                # The except-block's requery must see the real, now-committed row.
                return real_query(*args, **kwargs)

            with patch.object(request_db, "query", side_effect=fake_query):
                body = FeedbackCreate(client_id=client_id, message="Losing request (racing)")
                response = Response()
                result = create_feedback(body, response, request_db)

            assert response.status_code == 200
            assert result["id"] == winner_id
            assert result["client_id"] == client_id
        finally:
            request_db.close()

        # No duplicate row should have been created for this client_id.
        verify_db = TestingSessionLocal()
        try:
            count = verify_db.query(Feedback).filter(Feedback.client_id == client_id).count()
            assert count == 1
        finally:
            verify_db.close()
