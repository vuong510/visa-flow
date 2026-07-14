"""
Tests for api/working_days.py and the Python-first eligibility pre-checks.

Working-day rule: count working days starting from TOMORROW (today excluded),
skipping Sat/Sun + holidays; mốc = 10th working day; departure valid only if
strictly AFTER the mốc. Holidays are injected — no dependence on the real
holiday calendar.
"""
import inspect
from datetime import date, timedelta

import pytest

from api.working_days import (
    check_departure_rule,
    check_prior_denial_rule,
    load_vn_holidays,
    nth_working_day_after,
)

# Mon 13/07/2026 — spec reference example (no holidays in range)
MONDAY = date(2026, 7, 13)


class TestNthWorkingDayAfter:
    def test_no_holidays_spec_example(self):
        """Hôm nay T2 13/07 → ngày làm việc thứ 10 là T2 27/07."""
        assert nth_working_day_after(MONDAY, 10, holidays=set()) == date(2026, 7, 27)

    def test_today_is_never_counted(self):
        """Counting starts from tomorrow: 1st working day after Mon = Tue."""
        assert nth_working_day_after(MONDAY, 1, holidays=set()) == date(2026, 7, 14)

    def test_weekend_start_counts_from_monday(self):
        """Start Sat 18/07 → 1st working day = Mon 20/07."""
        assert nth_working_day_after(date(2026, 7, 18), 1, holidays=set()) == date(2026, 7, 20)

    def test_holiday_mid_range_pushes_moc_back(self):
        """Một ngày lễ giữa khoảng đếm → mốc lùi đúng 1 ngày làm việc."""
        holidays = {date(2026, 7, 15)}  # Wed within the counting window
        assert nth_working_day_after(MONDAY, 10, holidays=holidays) == date(2026, 7, 28)

    def test_multi_day_holiday_block(self):
        """Kỳ nghỉ nhiều ngày (kiểu Tết) → mốc lùi đúng số ngày lễ rơi vào ngày làm việc."""
        holidays = {date(2026, 7, 20), date(2026, 7, 21), date(2026, 7, 22)}  # Mon-Wed
        assert nth_working_day_after(MONDAY, 10, holidays=holidays) == date(2026, 7, 30)

    def test_weekend_holiday_observed_on_next_working_day(self):
        """Nghỉ bù: Giỗ Tổ 2026-04-26 rơi vào CN → T2 27/04 nghỉ bù (không làm việc)."""
        holidays = {date(2026, 4, 26)}  # Sunday
        # Fri 24/04 → Mon 27/04 is the substitute day → 1st working day = Tue 28/04
        assert nth_working_day_after(date(2026, 4, 24), 1, holidays=holidays) == date(2026, 4, 28)

    def test_weekend_holiday_shifts_moc_via_substitute(self):
        """Lễ rơi CN → nghỉ bù T2 → mốc lùi 1 ngày làm việc."""
        holidays = {date(2026, 7, 19)}  # Sunday → substitute Mon 20/07
        assert nth_working_day_after(MONDAY, 10, holidays=holidays) == date(2026, 7, 28)

    def test_back_to_back_weekend_holidays_chain_substitutes(self):
        """T7 + CN đều là lễ → nghỉ bù dây chuyền sang T2 và T3."""
        holidays = {date(2026, 7, 18), date(2026, 7, 19)}  # Sat + Sun
        # Fri 17/07 → substitutes Mon 20/07 + Tue 21/07 → 1st working day = Wed 22/07
        assert nth_working_day_after(date(2026, 7, 17), 1, holidays=holidays) == date(2026, 7, 22)
        # From MONDAY 13/07 the 10th working day shifts 27/07 → 29/07
        assert nth_working_day_after(MONDAY, 10, holidays=holidays) == date(2026, 7, 29)

    def test_year_outside_holiday_file_degrades_to_weekends_only(self):
        """Năm ngoài phạm vi file lễ → chỉ bỏ T7/CN (default holidays load)."""
        # Mon 05/01/2099 — far beyond any plausible file content, so this stays
        # pure weekend-skipping arithmetic even after future file updates.
        assert nth_working_day_after(date(2099, 1, 5), 10) == date(2099, 1, 19)

    def test_n_must_be_positive(self):
        with pytest.raises(ValueError):
            nth_working_day_after(MONDAY, 0, holidays=set())


class TestLoadVnHolidays:
    def test_loads_dates_for_2026_and_2027(self):
        holidays = load_vn_holidays()
        assert date(2026, 1, 1) in holidays
        assert date(2026, 4, 30) in holidays
        assert date(2027, 5, 1) in holidays
        assert all(isinstance(d, date) for d in holidays)


class TestCheckDepartureRule:
    def test_departure_exactly_on_moc_fails(self):
        ok, moc = check_departure_rule(MONDAY, date(2026, 7, 27), holidays=set())
        assert moc == date(2026, 7, 27)
        assert ok is False

    def test_departure_day_after_moc_passes(self):
        ok, moc = check_departure_rule(MONDAY, date(2026, 7, 28), holidays=set())
        assert moc == date(2026, 7, 27)
        assert ok is True

    def test_departure_before_moc_fails(self):
        ok, _ = check_departure_rule(MONDAY, date(2026, 7, 15), holidays=set())
        assert ok is False

    def test_moc_shifts_with_injected_holidays(self):
        holidays = {date(2026, 7, 15)}
        ok, moc = check_departure_rule(MONDAY, date(2026, 7, 28), holidays=holidays)
        assert moc == date(2026, 7, 28)
        assert ok is False


class TestCheckPriorDenialRule:
    TODAY = date(2026, 7, 14)

    def _profile(self, days_ago, country="japan"):
        return {
            "prior_denial": True,
            "denial_country": country,
            "denial_date": (self.TODAY - timedelta(days=days_ago)).isoformat(),
        }

    def test_denial_100_days_ago_same_country_blocked(self):
        assert check_prior_denial_rule(self._profile(100), "japan", self.TODAY) is False

    def test_denial_200_days_ago_passes(self):
        assert check_prior_denial_rule(self._profile(200), "japan", self.TODAY) is True

    def test_denial_exactly_179_days_ago_blocked(self):
        assert check_prior_denial_rule(self._profile(179), "japan", self.TODAY) is False

    def test_denial_exactly_180_days_ago_passes(self):
        assert check_prior_denial_rule(self._profile(180), "japan", self.TODAY) is True

    def test_different_country_passes(self):
        assert check_prior_denial_rule(self._profile(100, country="korea"), "japan", self.TODAY) is True

    def test_country_match_case_and_whitespace_insensitive(self):
        assert check_prior_denial_rule(self._profile(100, country=" Japan "), "japan", self.TODAY) is False

    def test_future_denial_date_passes_to_llm(self):
        """denial_date trong tương lai = lỗi dữ liệu → xử như không parse được."""
        assert check_prior_denial_rule(self._profile(-30), "japan", self.TODAY) is True

    def test_no_prior_denial_passes(self):
        assert check_prior_denial_rule({"prior_denial": False}, "japan", self.TODAY) is True

    def test_unparseable_denial_date_passes_to_llm(self):
        profile = {"prior_denial": True, "denial_country": "japan", "denial_date": "hôm kia"}
        assert check_prior_denial_rule(profile, "japan", self.TODAY) is True

    def test_missing_profile_passes(self):
        assert check_prior_denial_rule(None, "japan", self.TODAY) is True


# ── Eligibility endpoint: deterministic Python-first behaviour ────────────────

EXPECTED_SHAPE_KEYS = {"result", "headline", "bullets", "reason", "confidence_label"}


def _put_profile(client, app_id, profile, travel_dates):
    res = client.put(f"/api/application/{app_id}/profile", json={
        "profile_json": profile,
        "travel_dates": travel_dates,
    })
    assert res.status_code == 200


@pytest.fixture
def llm_calls(monkeypatch):
    """Record assess_eligibility calls; deterministic paths must never hit it."""
    calls = []

    def fake_assess(**kwargs):
        calls.append(kwargs)
        return {
            "result": "edge_case",
            "headline": "Hồ sơ của bạn có thể đủ điều kiện",
            "bullets": [],
            "reason": "freelancer",
            "confidence_label": "Độ tin cậy AI: Trung bình",
        }

    monkeypatch.setattr("api.ai.assess_eligibility", fake_assess)
    return calls


class TestEligibilityDeterministic:
    def test_departure_too_soon_is_deterministic_not_eligible(self, client, new_application, llm_calls):
        """Departure tomorrow is always <= mốc 10 ngày làm việc → no LLM call."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        far_return = (date.today() + timedelta(days=8)).isoformat()
        _put_profile(client, new_application, {"employment_type": "employee"},
                     {"departure": tomorrow, "return": far_return})

        res = client.post(f"/api/application/{new_application}/eligibility")
        assert res.status_code == 200
        data = res.json()
        assert data["result"] == "not_eligible"
        assert set(data.keys()) == EXPECTED_SHAPE_KEYS
        assert data["confidence_label"] == "Độ tin cậy AI: Cao"
        assert "10 ngày làm việc" in data["reason"]
        assert llm_calls == []

    def test_legacy_string_travel_dates_no_500(self, client, new_application, llm_calls):
        """travel_dates lưu dạng chuỗi JSON (legacy) → precheck vẫn chạy, không 500."""
        import json as _json
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from db.models import Application

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        _put_profile(client, new_application, {"employment_type": "employee"}, None)
        engine = create_engine("sqlite:///./test_visa_flow.db",
                               connect_args={"check_same_thread": False})
        session = sessionmaker(bind=engine)()
        try:
            application = session.get(Application, new_application)
            application.travel_dates = _json.dumps({"departure": tomorrow, "return": tomorrow})
            session.commit()
        finally:
            session.close()

        res = client.post(f"/api/application/{new_application}/eligibility")
        assert res.status_code == 200
        assert res.json()["result"] == "not_eligible"
        assert llm_calls == []

    def test_prior_denial_100_days_same_country_deterministic(self, client, new_application, llm_calls):
        denial_date = (date.today() - timedelta(days=100)).isoformat()
        far = (date.today() + timedelta(days=60)).isoformat()
        _put_profile(client, new_application,
                     {"employment_type": "employee", "prior_denial": True,
                      "denial_country": "japan", "denial_date": denial_date},
                     {"departure": far, "return": far})

        res = client.post(f"/api/application/{new_application}/eligibility")
        assert res.status_code == 200
        data = res.json()
        assert data["result"] == "not_eligible"
        assert "180" in data["reason"]
        assert data["confidence_label"] == "Độ tin cậy AI: Cao"
        assert llm_calls == []

    def test_prior_denial_200_days_passes_python_check(self, client, new_application, llm_calls):
        denial_date = (date.today() - timedelta(days=200)).isoformat()
        far = (date.today() + timedelta(days=60)).isoformat()
        _put_profile(client, new_application,
                     {"employment_type": "freelancer", "prior_denial": True,
                      "denial_country": "japan", "denial_date": denial_date},
                     {"departure": far, "return": far})

        res = client.post(f"/api/application/{new_application}/eligibility")
        assert res.status_code == 200
        assert res.json()["result"] == "edge_case"
        assert len(llm_calls) == 1

    def test_both_checks_pass_calls_llm_exactly_once(self, client, new_application, llm_calls):
        far_departure = (date.today() + timedelta(days=60)).isoformat()
        far_return = (date.today() + timedelta(days=67)).isoformat()
        _put_profile(client, new_application, {"employment_type": "freelancer"},
                     {"departure": far_departure, "return": far_return})

        res = client.post(f"/api/application/{new_application}/eligibility")
        assert res.status_code == 200
        assert res.json()["result"] == "edge_case"
        assert len(llm_calls) == 1

    def test_llm_prompt_no_longer_contains_date_rules(self):
        """Luật 180 ngày và 10 ngày làm việc đã chuyển sang Python."""
        import api.ai
        src = inspect.getsource(api.ai.assess_eligibility)
        assert "180" not in src
        assert "10 ngày làm việc" not in src
        assert "CHẶN CỨNG" not in src
        # freelancer edge_case rule stays with the LLM
        assert "freelancer" in src
