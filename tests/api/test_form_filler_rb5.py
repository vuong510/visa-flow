"""
Tests for the RB5[0-5] criminal-history declaration block in fill_visa_form.

The 6 radio groups on page 2 map to declaration keys (form order top→bottom is
RB5[3], RB5[0], RB5[1], RB5[5], RB5[4], RB5[2]). In each group, sorted by x:
leftmost (export '0') = Yes, rightmost (export '1') = No.
"""
import pymupdf
import pytest

from api.form_filler import fill_visa_form

RB5_KEYS = {
    0: "sentenced_1yr_plus",
    1: "deported_or_removed",
    2: "human_trafficking",
    3: "conviction_any_crime",
    4: "prostitution_related",
    5: "drug_offense",
}

BASE_INFO = {
    "family_name": "NGUYEN",
    "given_name": "VAN A",
    "gender": "male",
    "marital_status": "single",
    "nationality": "vietnam",
}


def _rb5_states(pdf_bytes):
    """Return {idx: (left_value, right_value)} for the 6 RB5 groups."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    groups = {}
    for w in doc[1].widgets():
        name = w.field_name.split(".")[-1]
        if name.startswith("RB5[") and w.field_type_string == "RadioButton":
            groups.setdefault(name, []).append(w)
    states = {}
    for idx in range(6):
        buttons = sorted(groups[f"RB5[{idx}]"], key=lambda w: w.rect.x0)
        assert len(buttons) == 2
        states[idx] = (buttons[0].field_value, buttons[1].field_value)
    return states


def _assert_ticks(pdf_bytes, declarations):
    states = _rb5_states(pdf_bytes)
    for idx in range(6):
        left, right = states[idx]
        key = RB5_KEYS[idx]
        if declarations[key]:
            assert left == "0", f"RB5[{idx}] ({key}=True) must tick Yes (left)"
            assert right == "Off", f"RB5[{idx}] ({key}=True) must not tick No"
        else:
            assert right == "1", f"RB5[{idx}] ({key}=False) must tick No (right)"
            assert left == "Off", f"RB5[{idx}] ({key}=False) must not tick Yes"


class TestRB5Declarations:
    def test_all_no(self):
        declarations = {key: False for key in RB5_KEYS.values()}
        pdf = fill_visa_form({**BASE_INFO, **declarations})
        _assert_ticks(pdf, declarations)

    def test_all_yes(self):
        declarations = {key: True for key in RB5_KEYS.values()}
        pdf = fill_visa_form({**BASE_INFO, **declarations})
        _assert_ticks(pdf, declarations)

    def test_mixed_yes_no(self):
        declarations = {
            "conviction_any_crime": True,
            "sentenced_1yr_plus": False,
            "deported_or_removed": True,
            "drug_offense": False,
            "prostitution_related": False,
            "human_trafficking": True,
        }
        pdf = fill_visa_form({**BASE_INFO, **declarations})
        _assert_ticks(pdf, declarations)

    @pytest.mark.parametrize("single_yes", list(RB5_KEYS.values()))
    def test_single_yes_only_ticks_its_own_group(self, single_yes):
        declarations = {key: key == single_yes for key in RB5_KEYS.values()}
        pdf = fill_visa_form({**BASE_INFO, **declarations})
        _assert_ticks(pdf, declarations)


class TestRB5MissingKey:
    @pytest.mark.parametrize("missing", list(RB5_KEYS.values()))
    def test_missing_declaration_raises_value_error(self, missing):
        declarations = {key: False for key in RB5_KEYS.values() if key != missing}
        with pytest.raises(ValueError, match=missing):
            fill_visa_form({**BASE_INFO, **declarations})


class TestRB5NonBoolValues:
    @pytest.mark.parametrize("bad_value", ["false", "true", None, 0, 1, "yes", ""])
    def test_non_bool_declaration_raises_value_error(self, bad_value):
        """Chuỗi 'false' là truthy — nếu không chặn sẽ tick nhầm Yes."""
        declarations = {key: False for key in RB5_KEYS.values()}
        declarations["drug_offense"] = bad_value
        with pytest.raises(ValueError, match="drug_offense"):
            fill_visa_form({**BASE_INFO, **declarations})
