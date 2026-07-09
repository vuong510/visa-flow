"""
Tests for the checklist endpoint.
Verifies that the Song Han UX feedback changes are reflected in the checklist data.
"""
import json
import pytest


EMPLOYEE_PROFILE = {
    "employment_type": "employee",
    "passport_expiry": "2028-01-01",
    "has_previous_visa": False,
    "monthly_income": 15000000,
    "bank_balance": 50000000,
}


def setup_employee_app(client, app_id):
    client.put(f"/api/application/{app_id}/profile", json={
        "profile_json": EMPLOYEE_PROFILE,
        "travel_dates": {"departure": "2026-09-01", "return": "2026-09-08"},
    })
    client.post(f"/api/application/{app_id}/eligibility")
    client.post(f"/api/application/{app_id}/payment/demo")


class TestChecklistContent:
    def test_checklist_returns_200(self, client, new_application):
        setup_employee_app(client, new_application)
        res = client.post(f"/api/application/{new_application}/checklist")
        assert res.status_code == 200

    def test_checklist_has_items(self, client, new_application):
        setup_employee_app(client, new_application)
        data = client.post(f"/api/application/{new_application}/checklist").json()
        assert "items" in data
        assert len(data["items"]) > 0

    def test_photo_size_is_4x3_5(self, client, new_application):
        """Photo should be 4.5×3.5cm per Song Han feedback, not 4.5×4.5cm."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        photo = next((i for i in items if i["id"] == "photo"), None)
        assert photo is not None, "photo item missing from checklist"
        assert "3.5" in photo["name"], f"Expected 4.5×3.5cm, got: {photo['name']}"
        assert "4.5" not in photo["name"].replace("4.5×3.5", ""), "Old 4.5×4.5 size still present"

    def test_flight_booking_renamed_to_hanh_trinh_bay(self, client, new_application):
        """flight_booking item should be renamed to 'Hành trình bay'."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        flight = next((i for i in items if i["id"] == "flight_booking"), None)
        assert flight is not None, "flight_booking item missing"
        assert "Hành trình bay" in flight["name"], f"Got: {flight['name']}"
        assert "Đặt vé" not in flight["name"], "Old name 'Đặt vé máy bay' still present"

    def test_flight_booking_description_no_ticket_required(self, client, new_application):
        """Description should say you don't need to buy ticket upfront."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        flight = next((i for i in items if i["id"] == "flight_booking"), None)
        assert flight is not None
        desc = flight.get("description", "")
        assert "Không cần mua vé" in desc or "chưa cần" in desc.lower(), \
            f"Description should mention no upfront ticket needed. Got: {desc}"

    def test_payslips_updated_to_6_months(self, client, new_application):
        """Payslips should require 6 months, not 3 months."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        payslips = next((i for i in items if i["id"] == "payslips"), None)
        assert payslips is not None, "payslips item missing"
        assert "6" in payslips["name"], f"Expected 6 months in name, got: {payslips['name']}"

    def test_bank_statements_updated_to_6_months(self, client, new_application):
        """Bank statements should require 6 months."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        bank = next((i for i in items if i["id"] == "bank_statements"), None)
        assert bank is not None, "bank_statements item missing"
        assert "6" in bank["name"] or "6" in bank.get("description", ""), \
            f"Expected 6 months, got: {bank['name']}"

    def test_leave_approval_is_optional(self, client, new_application):
        """leave_approval should be marked optional (LSQ doesn't require it currently)."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        leave = next((i for i in items if i["id"] == "leave_approval"), None)
        assert leave is not None, "leave_approval item missing"
        assert leave.get("optional") is True, \
            f"leave_approval should be optional=True, got: {leave.get('optional')}"

    def test_hotel_booking_is_optional(self, client, new_application):
        """hotel_booking should be marked optional."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        hotel = next((i for i in items if i["id"] == "hotel_booking"), None)
        assert hotel is not None, "hotel_booking item missing"
        assert hotel.get("optional") is True, \
            f"hotel_booking should be optional=True, got: {hotel.get('optional')}"

    def test_residency_proof_item_exists(self, client, new_application):
        """residency_proof item should be present for all Japan applicants."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        residency = next((i for i in items if i["id"] == "residency_proof"), None)
        assert residency is not None, "residency_proof item missing from checklist"
        assert residency.get("optional") is True, "residency_proof should be optional"
        # Should mention CCCD, CT07/CT08, or VNEID
        desc = residency.get("description", "")
        assert any(kw in desc for kw in ["CCCD", "CT07", "VNEID"]), \
            f"residency_proof description should mention CCCD/CT07/VNEID. Got: {desc}"

    def test_passport_is_not_optional(self, client, new_application):
        """Passport must never be optional."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        passport = next((i for i in items if i["id"] == "passport"), None)
        assert passport is not None
        assert not passport.get("optional"), "Passport must not be optional"

    def test_itinerary_item_exists(self, client, new_application):
        """Lịch trình should still be in checklist."""
        setup_employee_app(client, new_application)
        items = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        itinerary = next((i for i in items if i["id"] == "itinerary"), None)
        assert itinerary is not None, "itinerary item missing"


class TestChecklistCaching:
    def test_checklist_cached_after_first_call(self, client, new_application):
        """Second call returns same items (cached in application.checklist_json)."""
        setup_employee_app(client, new_application)
        first = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        second = client.post(f"/api/application/{new_application}/checklist").json()["items"]
        assert [i["id"] for i in first] == [i["id"] for i in second]


class TestChecklistNotJapan:
    def test_checklist_requires_japan_destination(self, client):
        """Checklist endpoint should return items for non-japan too (or handle gracefully)."""
        res = client.post("/api/application/start")
        app_id = res.json()["application_id"]
        client.patch(f"/api/application/{app_id}/destination", json={"destination": "china"})
        client.put(f"/api/application/{app_id}/profile", json={
            "profile_json": EMPLOYEE_PROFILE,
            "travel_dates": {"departure": "2026-09-01", "return": "2026-09-08"},
        })
        res = client.post(f"/api/application/{app_id}/checklist")
        # Should not crash — either returns items or an empty list
        assert res.status_code in (200, 400, 404)
