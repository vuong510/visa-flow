"""
Tests for multi-page PDF document review: every page must be rendered (dpi 150)
and sent to review_document_image in ONE call — no page cap.
"""
import pymupdf
import pytest


def _make_pdf(pages):
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Bank statement — page {i + 1} of {pages}")
    return doc.tobytes()


@pytest.fixture
def review_calls(monkeypatch):
    calls = []

    def fake_review(images, doc_type, profile):
        calls.append({"images": images, "doc_type": doc_type, "profile": profile})
        return {"status": "pass", "reason": None}

    monkeypatch.setattr("api.ai.review_document_image", fake_review)
    return calls


def _upload(client, app_id, filename, content, mime, doc_type="bank_statements"):
    res = client.post(
        f"/api/application/{app_id}/documents",
        files={"file": (filename, content, mime)},
        data={"doc_type": doc_type},
    )
    assert res.status_code == 200
    return res.json()["document_id"]


class TestMultiPagePdfReview:
    def test_3_page_pdf_sends_3_images_in_one_call(self, client, new_application, review_calls):
        doc_id = _upload(client, new_application, "statement.pdf", _make_pdf(3), "application/pdf")

        res = client.post(f"/api/application/{new_application}/documents/{doc_id}/review")
        assert res.status_code == 200
        assert res.json()["status"] == "pass"

        assert len(review_calls) == 1, "All pages must go in a single review call"
        images = review_calls[0]["images"]
        assert len(images) == 3
        for image_bytes, media_type in images:
            assert media_type == "image/png"
            assert image_bytes.startswith(b"\x89PNG"), "Each page must be a rendered PNG"

    def test_single_page_pdf_sends_1_image(self, client, new_application, review_calls):
        doc_id = _upload(client, new_application, "statement.pdf", _make_pdf(1), "application/pdf")

        res = client.post(f"/api/application/{new_application}/documents/{doc_id}/review")
        assert res.status_code == 200
        assert len(review_calls) == 1
        assert len(review_calls[0]["images"]) == 1

    def test_image_upload_sends_1_element_list(self, client, new_application, review_calls):
        # Render a real PNG so the (bytes, media_type) contract is honest
        png = pymupdf.open()
        page = png.new_page(width=200, height=100)
        page.insert_text((10, 50), "receipt")
        png_bytes = page.get_pixmap().tobytes("png")

        doc_id = _upload(client, new_application, "receipt.png", png_bytes, "image/png")

        res = client.post(f"/api/application/{new_application}/documents/{doc_id}/review")
        assert res.status_code == 200
        assert len(review_calls) == 1
        images = review_calls[0]["images"]
        assert len(images) == 1
        assert images[0][1] == "image/png"
        assert images[0][0] == png_bytes

    def test_zero_page_pdf_falls_back_to_needs_clarification(self, client, new_application, review_calls):
        """PDF 0 trang → không gọi Sonnet với 0 ảnh, rơi vào catch needs_clarification."""
        zero_page_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
            b"trailer\n<< /Root 1 0 R >>\n"
            b"%%EOF"
        )
        doc_id = _upload(client, new_application, "empty.pdf", zero_page_pdf, "application/pdf")

        res = client.post(f"/api/application/{new_application}/documents/{doc_id}/review")
        assert res.status_code == 200
        assert res.json()["status"] == "needs_clarification"
        assert review_calls == []
