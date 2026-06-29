"""
Fill official MOFA PDF forms using pymupdf AcroForm widget filling.

Visa form:   static/visa_form_blank.pdf  (XFA-based, 41+34 widgets)
Schedule:    static/schedule_blank.pdf   (simple AcroForm, 16 rows × 4 cols)

Multi-member:
  fill_visa_forms_for_group(members, shared_info)
    → list of (filename: str, bytes: bytes)
    → one visa form per member, numbered (1), (2), ...
    → for groups ≥3: also yields ("so_do_quan_he.pdf", relationship_bytes)
"""
import io
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

import pymupdf

logger = logging.getLogger(__name__)


def _parse_int(value, default: int = 0) -> int:
    """Extract the first integer from any value.

    Handles strings like "5-6 days", "khoảng 7 ngày", "10", or plain ints.
    Returns `default` when no digits are found.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    m = re.search(r"\d+", str(value))
    return int(m.group(0)) if m else default

VISA_BLANK     = Path(__file__).parent.parent / "static" / "visa_form_blank.pdf"
SCHEDULE_BLANK = Path(__file__).parent.parent / "static" / "schedule_blank.pdf"

# ── Nationality → ISO 3166-1 alpha-3 lookup ────────────────────────────────────
# Keys are lowercase; covers English names, Vietnamese names, adjective forms.
_NATIONALITY_ISO: dict[str, str] = {
    # Vietnam
    "vietnam": "VNM", "viet nam": "VNM", "việt nam": "VNM", "viet-nam": "VNM",
    "vietnamese": "VNM", "người việt": "VNM", "nguoi viet": "VNM",
    # Japan (JPN not in form choices — applicants for Japan visas won't be Japanese)
    "japan": "JPN", "nhật bản": "JPN", "nhat ban": "JPN",
    "japanese": "JPN", "người nhật": "JPN",
    # (fallback: overlay will display "JPN" since JPN is absent from form choices)
    # USA
    "usa": "USA", "united states": "USA", "united states of america": "USA",
    "us": "USA", "american": "USA", "mỹ": "USA", "my": "USA",
    "hoa kỳ": "USA", "hoa ky": "USA",
    # South Korea
    "korea": "KOR", "south korea": "KOR", "republic of korea": "KOR",
    "korean": "KOR", "hàn quốc": "KOR", "han quoc": "KOR",
    # China
    "china": "CHN", "people's republic of china": "CHN", "prc": "CHN",
    "chinese": "CHN", "trung quốc": "CHN", "trung quoc": "CHN",
    # Thailand
    "thailand": "THA", "thai": "THA", "thai lan": "THA", "thái lan": "THA",
    "thai land": "THA",
    # Singapore
    "singapore": "SGP", "singaporean": "SGP", "singapore an": "SGP",
    # Malaysia
    "malaysia": "MYS", "malaysian": "MYS", "mã lai": "MYS", "ma lai": "MYS",
    # France
    "france": "FRA", "french": "FRA", "pháp": "FRA", "phap": "FRA",
    # United Kingdom
    "uk": "GBR", "united kingdom": "GBR", "great britain": "GBR",
    "britain": "GBR", "british": "GBR", "england": "GBR", "english": "GBR",
    "anh": "GBR", "anh quốc": "GBR",
    # Australia
    "australia": "AUS", "australian": "AUS", "úc": "AUS", "uc": "AUS",
    # Cambodia
    "cambodia": "KHM", "cambodian": "KHM", "campuchia": "KHM",
    "khmer": "KHM",
    # Taiwan
    "taiwan": "TWN", "taiwanese": "TWN", "đài loan": "TWN", "dai loan": "TWN",
    # Additional common countries
    "germany": "DEU", "german": "DEU", "đức": "DEU", "duc": "DEU",
    "canada": "CAN", "canadian": "CAN", "canada an": "CAN",
    "india": "IND", "indian": "IND", "ấn độ": "IND", "an do": "IND",
    "indonesia": "IDN", "indonesian": "IDN", "indonesia n": "IDN",
    "philippines": "PHL", "philippine": "PHL", "filipino": "PHL",
    "filipina": "PHL", "philippino": "PHL",
    "russia": "RUS", "russian": "RUS", "nga": "RUS",
    "italy": "ITA", "italian": "ITA", "ý": "ITA",
    "spain": "ESP", "spanish": "ESP", "tây ban nha": "ESP",
    "netherlands": "NLD", "dutch": "NLD", "hà lan": "NLD",
    "sweden": "SWE", "swedish": "SWE", "thụy điển": "SWE",
    "switzerland": "CHE", "swiss": "CHE", "thụy sĩ": "CHE",
    "new zealand": "NZL", "new zealander": "NZL",
    "myanmar": "MMR", "burmese": "MMR", "burma": "MMR",
    "laos": "LAO", "lao": "LAO", "lào": "LAO",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def _set_widget(widget, value: str):
    """Set a text or combobox widget value and update it."""
    if widget.field_type_string == "ComboBox":
        # Translate nationality plain-text → ISO 3166-1 alpha-3 before matching
        iso = _NATIONALITY_ISO.get(value.strip().lower())
        if iso:
            value = iso

        # choice_values is a list of (export_code, display_name) tuples
        raw_choices = widget.choice_values or []
        # Build list of export codes (c[0]) for matching
        str_choices = [c[0] if isinstance(c, (list, tuple)) else str(c) for c in raw_choices]
        match = next((c for c in str_choices if c == value), None)
        if match is None:
            match = next((c for c in str_choices if c.lower() == value.lower()), None)
        if match is None:
            return
        widget.field_value = match
    else:
        widget.field_value = value
    widget.update()


def _fill_nationality_overlay(page: pymupdf.Page, value: str):
    """
    T50[0] is an XFA ComboBox that rejects widget.update() entirely.
    Instead: translate user input → ISO code → display name from choices,
    then white-out the widget rect and draw the text as a static overlay.
    """
    target_widget = None
    for w in page.widgets():
        if w.field_name.endswith("T50[0]"):
            target_widget = w
            break
    if target_widget is None or not value:
        return

    # Translate plain-text input → ISO code
    iso = _NATIONALITY_ISO.get(value.strip().lower(), value.strip().upper())

    # Find display name from form's own choice list
    display = iso  # fallback: show the ISO code itself
    for c in (target_widget.choice_values or []):
        if isinstance(c, (list, tuple)) and len(c) >= 2 and c[0] == iso:
            display = c[1].strip()
            break

    rect = target_widget.rect
    # White out the ComboBox widget area
    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
    # Insert display name text aligned to the baseline
    page.insert_text(
        (rect.x0 + 2, rect.y1 - 2),
        display,
        fontsize=9,
        color=(0, 0, 0),
    )


def _select_radio(page, field_name: str, target_export: str):
    """
    Select the radio button whose export value matches target_export.
    Falls back to selecting the first button if no match found.
    """
    for w in page.widgets():
        if w.field_name != field_name or w.field_type_string != "RadioButton":
            continue
        states = w.button_states()  # e.g. {'normal': ['Yes', 'Off'], 'down': [...]}
        on_values = [s for s in (states.get("normal") or []) if s != "Off"]
        if target_export in on_values:
            w.field_value = target_export
            w.update()
            return
    # If export value unknown, try setting directly and hope for the best
    for w in page.widgets():
        if w.field_name == field_name and w.field_type_string == "RadioButton":
            states = w.button_states()
            on_values = [s for s in (states.get("normal") or []) if s != "Off"]
            if on_values:
                w.field_value = on_values[0]
                w.update()
                return


def _radio_export_values(page, field_name: str) -> list[str]:
    """Return the list of non-Off export values for a radio group."""
    for w in page.widgets():
        if w.field_name == field_name and w.field_type_string == "RadioButton":
            states = w.button_states() or {}
            return [s for s in (states.get("normal") or []) if s != "Off"]
    return []


def _parse_date(date_str: str) -> datetime | None:
    """Try common date formats; return datetime or None."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def _to_bytes(doc: pymupdf.Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    return buf.getvalue()


# ── Visa form ──────────────────────────────────────────────────────────────────

# Mapping: personal_info key → short field suffix (we match by suffix against full XFA name)
# Values are (page_index, suffix_or_exact_name)
VISA_TEXT_MAP = {
    # Page 1
    "family_name":           (0, "T2[0]"),
    "given_name":            (0, "T7[0]"),
    "date_of_birth":         (0, "T14[0]"),
    "place_of_birth":        (0, "T16[0]"),
    "nationality":           (0, "T50[0]"),
    "id_number":             (0, "T37[0]"),       # CCCD
    "passport_number":       (0, "T49[0]"),
    # T57[0] = issuing authority (hardcoded below), T57[1] = place of issue
    "passport_issue_date":   (0, "T53[0]"),
    "passport_expiry_date":  (0, "T59[0]"),
    "purpose":               (0, "T68[2]"),
    "entry_date":            (0, "T66[0]"),
    "travel_days":           (0, "T68[3]"),
    "port_of_entry":         (0, "T68[0]"),       # e.g. Narita, Haneda
    "airline":               (0, "T68[1]"),       # e.g. Vietnam Airlines
    "accommodation":         (0, "emp_name[1]"),
    "accommodation_address": (0, "emp_adr[1]"),
    "accommodation_phone":   (0, "emp_tel[1]"),
    "visa_history":          (0, "T64[0]"),
    "home_address":          (0, "T0[1]"),
    "phone":                 (0, "T97[0]"),
    "mobile":                (0, "T3[0]"),
    "email":                 (0, "T3[1]"),
    "occupation":            (0, "T5[0]"),
    "company_name":          (0, "emp_name[0]"),
    "company_phone":         (0, "emp_tel[0]"),
    "company_address":       (0, "emp_adr[0]"),
}

# RB2[0] marital status: sorted by x position (left → right)
# [0] x=331 export='0' = Single
# [1] x=390 export='1' = Married
# [2] x=458 export='3' = Widowed
# [3] x=524 export='2' = Divorced
_MARITAL_INDEX = {
    "single": 0, "độc thân": 0, "doc than": 0, "chưa kết hôn": 0,
    "married": 1, "đã kết hôn": 1, "da ket hon": 1, "kết hôn": 1, "ket hon": 1,
    "widowed": 2, "góa": 2, "goa": 2,
    "divorced": 3, "ly hôn": 3, "ly hon": 3,
}


def _field_matches(full_name: str, suffix: str) -> bool:
    """True if the XFA full field name ends with the given suffix."""
    return full_name == suffix or full_name.endswith("." + suffix) or full_name.endswith("]." + suffix.split("[")[0] + "[" + suffix.split("[")[1] if "[" in suffix else suffix)


def _find_widget(page: pymupdf.Page, suffix: str):
    """Find the first widget on page whose name ends with the given suffix."""
    for w in page.widgets():
        name = w.field_name
        # Match: exact, or ends with .suffix, or ends with ]suffix
        if name == suffix or name.endswith(f".{suffix}") or name.endswith(f"]{suffix}"):
            return w
        # Also match by the last segment after any bracket group
        last = name.split(".")[-1] if "." in name else name
        if last == suffix:
            return w
    return None


def fill_visa_form(info: dict) -> bytes:
    """Fill the official MOFA visa application form with personal_info data."""
    doc = pymupdf.open(str(VISA_BLANK))
    page1 = doc[0]

    # ── Text fields (nationality handled separately below) ───────────────────
    for key, (page_idx, suffix) in VISA_TEXT_MAP.items():
        if key == "nationality":
            continue   # handled by overlay below
        value = str(info.get(key) or "")
        if not value:
            continue
        page = doc[page_idx]
        w = _find_widget(page, suffix)
        if w:
            _set_widget(w, value)
        else:
            logger.warning("Widget not found: suffix=%s", suffix)

    # ── Nationality — text overlay (XFA ComboBox rejects widget.update()) ────
    _fill_nationality_overlay(page1, str(info.get("nationality") or ""))

    # ── Hardcoded issuing authority fields ───────────────────────────────────
    # T57[0] = issuing authority, T57[1] = place of issue
    # Both hardcoded for Vietnamese passports
    for suffix, value in (("T57[0]", "Cục Quản lý Xuất nhập cảnh"),
                          ("T57[1]", "Cục Quản lý Xuất nhập cảnh")):
        w = _find_widget(page1, suffix)
        if w:
            _set_widget(w, value)

    # ── Marital status radio (RB2[0]) ─────────────────────────────────────────
    # Left→right: Single(0) Married(1) Widowed(2) Divorced(3)
    marital_raw = str(info.get("marital_status") or "single").strip().lower()
    marital_idx = _MARITAL_INDEX.get(marital_raw, 0)
    rb2_buttons = [w for w in page1.widgets()
                   if w.field_name.endswith("RB2[0]")
                   and w.field_type_string == "RadioButton"]
    rb2_buttons.sort(key=lambda w: w.rect.x0)
    if marital_idx < len(rb2_buttons):
        target = rb2_buttons[marital_idx]
        states = target.button_states() or {}
        on_vals = [s for s in (states.get("normal") or []) if s != "Off"]
        if on_vals:
            target.field_value = on_vals[0]
            target.update()

    # ── Sex radio (RB1[0]) ────────────────────────────────────────────────────
    # Radio export value is '0' for ALL buttons in this XFA form.
    # The two buttons differ only by position: x≈113 = Male, x≈171 = Female.
    # pymupdf selects a radio by setting ALL buttons with the same name to
    # the same export value — it picks the first one that matches. So we must
    # set the correct button by directly accessing its widget object.
    gender = str(info.get("gender") or "").lower()
    is_female = "female" in gender or "nữ" in gender or gender == "f"
    sex_buttons = [w for w in page1.widgets()
                   if w.field_name == "topmostSubform[0].Page1[0].#area[5].#area[6].#area[7].RB1[0]"
                   and w.field_type_string == "RadioButton"]
    # sort by x position: lower x = Male, higher x = Female
    sex_buttons.sort(key=lambda w: w.rect.x0)
    target_btn = sex_buttons[1] if (is_female and len(sex_buttons) > 1) else sex_buttons[0] if sex_buttons else None
    if target_btn:
        states = target_btn.button_states() or {}
        on_vals = [s for s in (states.get("normal") or []) if s != "Off"]
        if on_vals:
            target_btn.field_value = on_vals[0]
            target_btn.update()

    # ── Passport type radio (RB3[0]) — always Ordinary for tourist visa ──────
    # 4 buttons in x order: Diplomatic(186), Official(244), Ordinary(310), Other(365)
    rb3_buttons = [w for w in page1.widgets()
                   if w.field_name == "topmostSubform[0].Page1[0].#area[1].#area[2].RB3[0]"
                   and w.field_type_string == "RadioButton"]
    rb3_buttons.sort(key=lambda w: w.rect.x0)
    ordinary_btn = rb3_buttons[2] if len(rb3_buttons) >= 3 else rb3_buttons[0] if rb3_buttons else None
    if ordinary_btn:
        states = ordinary_btn.button_states() or {}
        on_vals = [s for s in (states.get("normal") or []) if s != "Off"]
        if on_vals:
            ordinary_btn.field_value = on_vals[0]
            ordinary_btn.update()

    # ── Page 2 ────────────────────────────────────────────────────────────────
    _fill_visa_page2(doc[1], info)

    return _to_bytes(doc)


def _fill_visa_page2(page2, info: dict):
    """Fill page 2: partner profession, guarantor, inviter, date, Yes/No questions."""

    wmap = {w.field_name.split(".")[-1]: w for w in page2.widgets()}

    def _set(suffix, value):
        w = wmap.get(suffix)
        if w and value:
            _set_widget(w, str(value))

    # ── Partner's profession (top note) — skip for solo travellers ───────────
    group_type = str(info.get("group_type") or "").lower()
    if group_type not in ("solo", "một mình", "mot minh", "1"):
        _set("T16[2]", info.get("partner_occupation") or info.get("partner_profession") or "")

    # ── Guarantor (reference in Japan) ────────────────────────────────────────
    _set("guarantor_name[0]", info.get("guarantor_name") or "")
    _set("guarantor_tel[0]",  info.get("guarantor_phone") or "")
    _set("guarantor_adr[0]",  info.get("guarantor_address") or "")
    _set("T25[0]",            info.get("guarantor_relationship") or "")
    _set("T5[0]",             info.get("guarantor_occupation") or "")
    _set("T5[1]",             info.get("guarantor_nationality") or "")

    # ── Inviter in Japan ──────────────────────────────────────────────────────
    inviter_name = info.get("inviter_name") or ""
    # If no separate inviter, default to "same as above" when guarantor exists
    if not inviter_name and info.get("guarantor_name"):
        inviter_name = "Same as above"
    _set("T19[0]", inviter_name)
    _set("T10[0]", info.get("inviter_phone") or "")
    _set("T23[0]", info.get("inviter_address") or "")
    _set("T25[1]", info.get("inviter_relationship") or "")
    _set("T5[2]",  info.get("inviter_occupation") or "")
    _set("T5[3]",  info.get("inviter_nationality") or "")

    # ── Date of application (auto = today) ────────────────────────────────────
    _set("T150[0]", datetime.today().strftime("%d/%m/%Y"))

    # ── Yes/No criminal history questions — all defaulted to No ─────────────
    # 6 radio groups RB5[0]–RB5[5]
    # Each group sorted by x: left(≈502) = Yes, right(≈539) = No
    # We always tick No; a warning is shown to the user in the chat UI.
    rb5_groups = {}
    for w in page2.widgets():
        name = w.field_name.split(".")[-1]
        if name.startswith("RB5[") and w.field_type_string == "RadioButton":
            rb5_groups.setdefault(name, []).append(w)

    for idx in range(6):
        group_name = f"RB5[{idx}]"
        buttons = rb5_groups.get(group_name, [])
        if not buttons:
            continue
        buttons.sort(key=lambda w: w.rect.x0)
        no_btn = buttons[-1]  # rightmost = No
        states = no_btn.button_states() or {}
        on_vals = [s for s in (states.get("normal") or []) if s != "Off"]
        if on_vals:
            no_btn.field_value = on_vals[0]
            no_btn.update()


# ── Schedule form ──────────────────────────────────────────────────────────────

def fill_schedule(info: dict) -> bytes:
    """Fill the MOFA schedule-of-stay form with day-by-day travel data."""
    doc = pymupdf.open(str(SCHEDULE_BLANK))
    page = doc[0]

    # ── Header date (Year / Month / Day of application) ───────────────────────
    today = datetime.today()
    for w in page.widgets():
        if w.field_name == "Year":
            _set_widget(w, str(today.year))
        elif w.field_name == "Month":
            _set_widget(w, f"{today.month:02d}")
        elif w.field_name == "Day":
            _set_widget(w, f"{today.day:02d}")

    # ── Daily rows ────────────────────────────────────────────────────────────
    days       = _parse_int(info.get("travel_days"), default=7) or 7
    entry_str  = str(info.get("entry_date") or "")
    accomm     = str(info.get("accommodation") or "")
    accomm_tel = str(info.get("accommodation_phone") or "")
    itinerary  = info.get("itinerary") or []
    airport    = str(info.get("port_of_entry") or "").strip()
    hotel_city = str(info.get("hotel_city") or "").strip()

    base_date = _parse_date(entry_str)

    # Default per-day activities when user hasn't provided a specific itinerary.
    # MUST be English — MOFA form font cannot render Vietnamese diacritics
    # (text becomes invisible until field is clicked).
    def _default_activity(day_idx: int, total: int) -> str:
        city = hotel_city or "Tokyo"
        if day_idx == 1:
            where = f" at {airport}" if airport else ""
            return f"Arrival{where}, transfer to {city}, hotel check-in"
        if day_idx == total:
            return "Hotel check-out, transfer to airport, departure"
        # Mid-trip: rotate through generic sightseeing themes
        themes = [
            f"City center sightseeing in {city}",
            f"Historic sites and temples in {city}",
            f"Shopping and local cuisine in {city}",
            f"Parks and scenic spots in {city}",
            f"Museums and cultural sites in {city}",
        ]
        return themes[(day_idx - 2) % len(themes)]

    # Build a widget lookup: name → widget
    widget_map = {w.field_name: w for w in page.widgets()}

    for i in range(1, min(days + 1, 17)):  # rows 1–16
        # Date
        if base_date:
            day_date = base_date + timedelta(days=i - 1)
            date_str = day_date.strftime("%Y/%m/%d")
        else:
            date_str = f"Day {i}"

        date_w    = widget_map.get(f"DateRow{i}")
        activity_w = widget_map.get(f"Activity PlanRow{i}")
        contact_w = widget_map.get(f"ContactRow{i}")
        accomm_w  = widget_map.get(f"AccommodationRow{i}")

        if date_w:
            _set_widget(date_w, date_str)

        # Activity: use itinerary data if available, else per-day default
        if activity_w:
            activity_text = _default_activity(i, days)
            if i <= len(itinerary):
                day_data = itinerary[i - 1]
                activities = day_data.get("activities", [])
                if activities:
                    activity_text = ", ".join(activities)
            _set_widget(activity_w, activity_text[:60])

        # Contact: use hotel phone, fall back to per-day accommodation phone
        if contact_w:
            day_tel = accomm_tel
            if i <= len(itinerary):
                day_accomm = itinerary[i - 1].get("accommodation", {})
                if isinstance(day_accomm, dict):
                    day_tel = day_accomm.get("phone") or day_tel
            if day_tel:
                # Shrink font for long phone numbers (+81-xx-xxxx-xxxx = 16 chars)
                # to prevent truncation in narrow Contact column
                try:
                    contact_w.text_fontsize = 7
                except Exception:
                    pass
                _set_widget(contact_w, day_tel)

        # Accommodation: use per-day accommodation name if available
        if accomm_w:
            day_accomm_name = accomm
            if i <= len(itinerary):
                day_accomm = itinerary[i - 1].get("accommodation", {})
                if isinstance(day_accomm, dict):
                    day_accomm_name = day_accomm.get("name") or day_accomm_name
            if day_accomm_name:
                _set_widget(accomm_w, day_accomm_name[:40])

    return _to_bytes(doc)


# ── Multi-member group helpers ──────────────────────────────────────────────────

def fill_visa_forms_for_group(
    members: list[dict],
    shared_info: dict,
) -> list[tuple[str, bytes]]:
    """
    Generate one visa form PDF per member, plus a relationship diagram for groups ≥3.

    Args:
        members:     session["members"] list — each has "personal_info", "relation", "name", etc.
        shared_info: session["personal_info"] (main applicant or shared travel data)

    Returns:
        List of (filename, pdf_bytes) tuples, in display order.
        Filenames: "(1)don_xin_visa.pdf", "(2)don_xin_visa.pdf", ...
        For groups ≥3, also appends ("so_do_quan_he.pdf", diagram_bytes).
    """
    results: list[tuple[str, bytes]] = []

    for i, member in enumerate(members, start=1):
        # Merge shared travel info into member personal_info
        merged = {**shared_info}
        merged.update({k: v for k, v in member.get("personal_info", {}).items() if v})
        # Propagate member-level employment to occupation if not already set
        if not merged.get("occupation") and member.get("employment"):
            merged["occupation"] = member["employment"]

        try:
            pdf_bytes = fill_visa_form(merged)
        except Exception as e:
            logger.warning("fill_visa_form failed for member %d: %s", i, e)
            continue

        filename = f"({i})don_xin_visa.pdf"
        results.append((filename, pdf_bytes))

    # Relationship diagram for groups ≥3
    if len(members) >= 3:
        try:
            diagram_bytes = _build_relationship_diagram(members)
            results.append(("so_do_quan_he.pdf", diagram_bytes))
        except Exception as e:
            logger.warning("relationship diagram failed: %s", e)

    return results


def _build_relationship_diagram(members: list[dict]) -> bytes:
    """
    Build a simple text-based relationship diagram PDF for groups ≥3.
    Lists each member's name, relation to main applicant, and employment.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4

    x, y = 50, 60
    page.insert_text((x, y), "SƠ ĐỒ QUAN HỆ NHÓM / GROUP RELATIONSHIP DIAGRAM",
                     fontsize=13, color=(0, 0, 0))
    y += 30
    page.draw_line((x, y), (545, y), color=(0.4, 0.4, 0.4), width=1)
    y += 20

    for i, member in enumerate(members, start=1):
        info = member.get("personal_info", {})
        name = (info.get("full_name_latin")
                or (info.get("given_name", "") + " " + info.get("family_name", "")).strip())
        if not name:
            name = member.get("name") or f"Người {i}"
        relation = member.get("relation", "companion")
        employment = member.get("employment") or info.get("occupation") or "N/A"
        dob = info.get("date_of_birth", "")

        _REL_VI = {
            "main": "Người đứng đơn chính", "spouse": "Vợ/chồng", "child": "Con",
            "parent": "Cha/mẹ", "sibling": "Anh/chị/em", "friend": "Bạn",
            "companion": "Người đi cùng",
        }
        label = "Người đứng đơn chính" if i == 1 else _REL_VI.get(relation, relation.capitalize())

        page.insert_text((x, y), f"({i})  {name}", fontsize=11,
                         color=(0, 0, 0.7))
        y += 18
        page.insert_text((x + 20, y), f"Quan hệ: {label}", fontsize=9)
        y += 14
        page.insert_text((x + 20, y), f"Nghề nghiệp: {employment}", fontsize=9)
        y += 14
        if dob:
            page.insert_text((x + 20, y), f"Ngày sinh: {dob}", fontsize=9)
            y += 14
        y += 10

    y += 10
    page.draw_line((x, y), (545, y), color=(0.7, 0.7, 0.7), width=0.5)
    y += 16
    page.insert_text((x, y),
                     "Tài liệu này đính kèm hồ sơ xin visa — mỗi thành viên nộp đơn riêng.",
                     fontsize=8, color=(0.4, 0.4, 0.4))

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    return buf.getvalue()
