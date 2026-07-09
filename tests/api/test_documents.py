"""
Tests for document upload endpoint.
Note: file type validation is frontend-only; backend accepts all file types
and applies AI review only to images/PDF.
"""
import io
import pytest


EMPLOYEE_PROFILE = {
    "employment_type": "employee",
    "passport_expiry": "2028-01-01",
    "has_previous_visa": False,
    "monthly_income": 15000000,
    "bank_balance": 50000000,
}


def ready_app(client):
    res = client.post("/api/application/start")
    app_id = res.json()["application_id"]
    client.patch(f"/api/application/{app_id}/destination", json={"destination": "japan"})
    client.put(f"/api/application/{app_id}/profile", json={
        "profile_json": EMPLOYEE_PROFILE,
        "travel_dates": {"departure": "2026-09-01", "return": "2026-09-08"},
    })
    client.post(f"/api/application/{app_id}/eligibility")
    client.post(f"/api/application/{app_id}/payment/demo")
    return app_id


class TestDocumentUpload:
    def test_upload_jpeg_returns_200(self, client):
        app_id = ready_app(client)
        fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # minimal JPEG header
        res = client.post(
            f"/api/application/{app_id}/documents",
            files={"file": ("photo.jpg", fake_jpeg, "image/jpeg")},
            data={"doc_type": "photo"},
        )
        assert res.status_code == 200
        assert "document_id" in res.json()

    def test_upload_pdf_returns_200(self, client):
        app_id = ready_app(client)
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
        res = client.post(
            f"/api/application/{app_id}/documents",
            files={"file": ("payslips.pdf", fake_pdf, "application/pdf")},
            data={"doc_type": "payslips"},
        )
        assert res.status_code == 200

    def test_upload_creates_document_record(self, client):
        app_id = ready_app(client)
        fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        client.post(
            f"/api/application/{app_id}/documents",
            files={"file": ("photo.jpg", fake_jpeg, "image/jpeg")},
            data={"doc_type": "photo"},
        )
        docs = client.get(f"/api/application/{app_id}/documents").json()
        assert any(d["doc_type"] == "photo" for d in docs), "photo document not found in list"

    def test_get_documents_returns_list(self, client):
        app_id = ready_app(client)
        res = client.get(f"/api/application/{app_id}/documents")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_upload_to_nonexistent_app_returns_404(self, client):
        fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        res = client.post(
            "/api/application/999999/documents",
            files={"file": ("photo.jpg", fake_jpeg, "image/jpeg")},
            data={"doc_type": "photo"},
        )
        assert res.status_code == 404

    def test_multiple_uploads_same_doc_type(self, client):
        """Uploading a replacement for the same doc_type should succeed."""
        app_id = ready_app(client)
        for i in range(2):
            fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            res = client.post(
                f"/api/application/{app_id}/documents",
                files={"file": (f"photo_{i}.jpg", fake_jpeg, "image/jpeg")},
                data={"doc_type": "photo"},
            )
            assert res.status_code == 200


class TestApplicationFlow:
    def test_start_returns_application_id(self, client):
        res = client.post("/api/application/start")
        assert res.status_code == 200
        data = res.json()
        assert "application_id" in data
        assert "session_id" in data

    def test_health_endpoint(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_submit_application(self, client):
        app_id = ready_app(client)
        res = client.post(f"/api/application/{app_id}/submit")
        assert res.status_code == 200

    def test_status_after_submit(self, client):
        app_id = ready_app(client)
        client.post(f"/api/application/{app_id}/submit")
        res = client.get(f"/api/application/{app_id}/status")
        assert res.status_code == 200
