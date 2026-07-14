"""Deterministic working-day and prior-denial rules for eligibility pre-checks.

Working-day rule (quy tắc 10 ngày làm việc):
- Đếm ngày làm việc BẮT ĐẦU TỪ NGÀY MAI (hôm nay không tính), bỏ Thứ 7/Chủ nhật
  và ngày lễ VN (static/vn_holidays.json).
- Nghỉ bù: ngày lễ rơi vào T7/CN được nghỉ bù vào ngày làm việc kế tiếp
  (chưa phải cuối tuần và chưa là ngày lễ/nghỉ bù khác).
- Mốc = ngày làm việc thứ N (mặc định 10). Ngày khởi hành hợp lệ phải SAU mốc
  (strictly >, không phải đúng ngày mốc).
- Năm ngoài phạm vi file lễ (2028+): degrade — chỉ bỏ Thứ 7/Chủ nhật.
"""
import functools
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_HOLIDAYS_FILE = Path(__file__).parent.parent / "static" / "vn_holidays.json"
_VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def vn_today() -> date:
    """Today in Asia/Ho_Chi_Minh — the server may run in UTC, where 00:00-07:00
    VN time would otherwise still count as 'yesterday'."""
    return datetime.now(_VN_TZ).date()


@functools.lru_cache(maxsize=1)
def load_vn_holidays() -> frozenset:
    """Load VN statutory holidays from static/vn_holidays.json as a frozenset of dates.

    Years absent from the file (e.g. 2028+) simply contribute no entries, so
    counting through those years degrades to skipping only Sat/Sun.
    Any failure (missing file, malformed JSON, wrong structure) logs a warning
    and returns an empty set — never raises.

    Cached for the process lifetime (lru_cache) so the file is not re-read on
    every request — restart the server to pick up file changes.
    """
    holidays = set()
    try:
        with open(_HOLIDAYS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for days in (data.get("years") or {}).values():
            for d in days or []:
                try:
                    holidays.add(date.fromisoformat(str(d)))
                except (TypeError, ValueError):
                    continue
    except Exception as e:
        logger.warning("Could not load VN holidays from %s: %s", _HOLIDAYS_FILE, e)
        return frozenset()
    return frozenset(holidays)


def _expand_substitute_days(holidays) -> set:
    """Apply the VN nghỉ bù rule: a public holiday falling on Sat/Sun is observed
    on the next day that is neither a weekend nor already a holiday/substitute.

    Holidays are processed in date order so back-to-back weekend holidays chain
    correctly (Sat + Sun → Mon + Tue). Must be applied exactly once to a raw
    holiday set (it is not idempotent).
    """
    expanded = set(holidays)
    for holiday in sorted(holidays):
        if holiday.weekday() < 5:
            continue
        substitute = holiday + timedelta(days=1)
        while substitute.weekday() >= 5 or substitute in expanded:
            substitute += timedelta(days=1)
        expanded.add(substitute)
    return expanded


def nth_working_day_after(start_date: date, n: int, holidays: set | None = None) -> date:
    """Return the n-th working day counting from the day AFTER start_date.

    start_date itself is never counted. Saturdays, Sundays, dates in `holidays`
    and their nghỉ bù substitute days are skipped. `holidays=None` loads
    static/vn_holidays.json; pass an explicit set (e.g. set()) in tests to
    avoid real calendar data.

    Example:
        >>> nth_working_day_after(date(2026, 7, 13), 10, holidays=set())
        datetime.date(2026, 7, 27)   # Mon 13/07 → 10th working day = Mon 27/07
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    non_working = _expand_substitute_days(load_vn_holidays() if holidays is None else holidays)
    current = start_date
    counted = 0
    while counted < n:
        current += timedelta(days=1)
        if current.weekday() >= 5 or current in non_working:
            continue
        counted += 1
    return current


def check_departure_rule(today: date, departure: date, n: int = 10,
                         holidays: set | None = None) -> tuple[bool, date]:
    """Check that departure is strictly AFTER the n-th working day from today.

    Returns (ok, moc) where moc is the n-th working day. Departure exactly on
    the moc is NOT ok.

    Example:
        >>> check_departure_rule(date(2026, 7, 13), date(2026, 7, 27), holidays=set())
        (False, datetime.date(2026, 7, 27))   # đúng mốc → chưa hợp lệ
        >>> check_departure_rule(date(2026, 7, 13), date(2026, 7, 28), holidays=set())
        (True, datetime.date(2026, 7, 27))    # sau mốc → hợp lệ
    """
    moc = nth_working_day_after(today, n, holidays=holidays)
    return departure > moc, moc


def check_prior_denial_rule(profile: dict, destination: str, today: date) -> bool:
    """Check the 180-day prior-denial rule. Returns True when the profile PASSES.

    Blocked (returns False) only when ALL hold:
    - profile["prior_denial"] is truthy
    - profile["denial_country"] == destination (case/whitespace-insensitive)
    - 0 <= (today - denial_date).days < 180

    Missing/unparseable denial_date → True (để LLM xử như cũ). A FUTURE
    denial_date is a data error and is treated the same way (pass to LLM).

    Example:
        >>> check_prior_denial_rule(
        ...     {"prior_denial": True, "denial_country": "japan",
        ...      "denial_date": "2026-04-05"},
        ...     "japan", date(2026, 7, 14))
        False   # bị từ chối 100 ngày trước, cùng nước → chặn
    """
    profile = profile or {}
    if not profile.get("prior_denial"):
        return True
    denial_country = str(profile.get("denial_country") or "").strip().lower()
    if denial_country != str(destination or "").strip().lower():
        return True
    try:
        denial_date = date.fromisoformat(str(profile.get("denial_date")))
    except (TypeError, ValueError):
        return True
    days_since = (today - denial_date).days
    if days_since < 0:  # denial in the future = data error → pass to LLM path
        return True
    return days_since >= 180
