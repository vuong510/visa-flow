"""
Tests for the forms/download itinerary bug fix (forms.py):
travel_dates is a dict (JSON column) — the old code called json.loads on it,
swallowed the TypeError and always fed empty dates into generate_itinerary
(→ 7-day fallback). Now dict passes through; a JSON string still parses.
"""
import io
import json
import zipfile

import pymupdf
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Application

TRAVEL_DATES = {"departure": "2026-09-01", "return": "2026-09-04"}  # 4 days

PERSONAL_INFO = {
    "family_name": "NGUYEN",
    "given_name": "VAN A",
    "date_of_birth": "1990-01-01",
    "passport_number": "B1234567",
    "gender": "male",
    "marital_status": "single",
    "accommodation": "APA Hotel Shinjuku",
    "accommodation_phone": "+81-3-1234-5678",
    "conviction_any_crime": False,
    "sentenced_1yr_plus": False,
    "deported_or_removed": False,
    "drug_offense": False,
    "prostitution_related": False,
    "human_trafficking": False,
}


@pytest.fixture
def itinerary_calls(monkeypatch):
    """Capture generate_itinerary args and return a deterministic 4-day plan."""
    calls = []

    def fake_generate_itinerary(destination, departure, return_date, hotel_name="", hotel_phone=""):
        calls.append({
            "destination": destination,
            "departure": departure,
            "return_date": return_date,
            "hotel_name": hotel_name,
            "hotel_phone": hotel_phone,
        })
        return [
            {"activities": [f"Day {i + 1} sightseeing in Tokyo"],
             "accommodation": {"name": hotel_name or "Hotel", "phone": hotel_phone or ""}}
            for i in range(4)
        ]

    monkeypatch.setattr("api.routers.forms.generate_itinerary", fake_generate_itinerary)
    return calls


def _download(client, app_id):
    return client.post(
        f"/api/application/{app_id}/forms/download",
        json={"personal_info": PERSONAL_INFO},
    )


def _schedule_widgets(zip_bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        assert set(zf.namelist()) == {"don_xin_visa.pdf", "lich_trinh.pdf"}
        schedule = zf.read("lich_trinh.pdf")
    doc = pymupdf.open(stream=schedule, filetype="pdf")
    return {w.field_name: (w.field_value or "") for w in doc[0].widgets()}


class TestItineraryDates:
    def test_dict_travel_dates_reach_generate_itinerary(self, client, new_application, itinerary_calls):
        """travel_dates dict (đường đi thực tế) → generate_itinerary nhận đúng ngày."""
        client.put(f"/api/application/{new_application}/profile", json={
            "profile_json": {"employment_type": "employee"},
            "travel_dates": TRAVEL_DATES,
        })

        res = _download(client, new_application)
        assert res.status_code == 200

        assert len(itinerary_calls) == 1
        assert itinerary_calls[0]["departure"] == "2026-09-01"
        assert itinerary_calls[0]["return_date"] == "2026-09-04"
        assert itinerary_calls[0]["hotel_name"] == "APA Hotel Shinjuku"

    def test_schedule_pdf_has_exactly_4_days(self, client, new_application, itinerary_calls):
        client.put(f"/api/application/{new_application}/profile", json={
            "profile_json": {"employment_type": "employee"},
            "travel_dates": TRAVEL_DATES,
        })

        res = _download(client, new_application)
        assert res.status_code == 200

        widgets = _schedule_widgets(res.content)
        for i in range(1, 5):
            assert widgets.get(f"DateRow{i}"), f"DateRow{i} should be filled"
            assert f"Day {i} sightseeing" in widgets.get(f"Activity PlanRow{i}", "")
        # Không tràn sang ngày thứ 5 (fallback 7 ngày cũ sẽ fail ở đây)
        assert not widgets.get("DateRow5"), "Schedule must stop after day 4"

    def test_string_travel_dates_still_parse(self, client, new_application, itinerary_calls):
        """travel_dates lưu dạng chuỗi JSON (legacy) → vẫn parse đúng qua guard isinstance."""
        client.put(f"/api/application/{new_application}/profile", json={
            "profile_json": {"employment_type": "employee"},
        })
        # Ghi thẳng chuỗi JSON vào cột travel_dates (không đi qua API)
        engine = create_engine("sqlite:///./test_visa_flow.db",
                               connect_args={"check_same_thread": False})
        session = sessionmaker(bind=engine)()
        try:
            application = session.get(Application, new_application)
            application.travel_dates = json.dumps(TRAVEL_DATES)
            session.commit()
        finally:
            session.close()

        res = _download(client, new_application)
        assert res.status_code == 200

        assert len(itinerary_calls) == 1
        assert itinerary_calls[0]["departure"] == "2026-09-01"
        assert itinerary_calls[0]["return_date"] == "2026-09-04"


class TestFormsValidation:
    def test_missing_declaration_returns_422(self, client, new_application, itinerary_calls):
        client.put(f"/api/application/{new_application}/profile", json={
            "profile_json": {"employment_type": "employee"},
            "travel_dates": TRAVEL_DATES,
        })
        incomplete = {k: v for k, v in PERSONAL_INFO.items() if k != "drug_offense"}
        res = client.post(
            f"/api/application/{new_application}/forms/download",
            json={"personal_info": incomplete},
        )
        assert res.status_code == 422
