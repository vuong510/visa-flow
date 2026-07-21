"""Unit tests cho programmatic checks tầng 2 (tests/eval/checks.py).

Chạy trong pytest mặc định — thuần regex, KHÔNG gọi API.
"""
import unicodedata

from tests.eval.checks import (
    ALL_CHECKS,
    check_persona,
    check_no_cjk,
    check_no_markdown,
    check_phone_whitelist,
    check_no_full_id,
    check_no_financial_threshold,
    check_politeness,
    check_word_limit,
    contains_ci,
    topic_found,
)


# ---- check_persona ----

def test_persona_compound_nhom_ban_pass():
    ok, _ = check_persona("Nhóm bạn của anh/chị cần chuẩn bị hồ sơ riêng cho từng người ạ.")
    assert ok


def test_persona_ban_dung_mot_minh_fail():
    ok, detail = check_persona("Bạn cần chuẩn bị hộ chiếu còn hạn 6 tháng.")
    assert not ok
    assert "bạn" in detail


def test_persona_em_xin_loi_pass():
    ok, _ = check_persona("Em xin lỗi ạ, em chưa rõ ý anh/chị.")
    assert ok


def test_persona_toi_fail():
    ok, detail = check_persona("Tôi nghĩ anh nên nộp hồ sơ sớm.")
    assert not ok
    assert "tôi" in detail


def test_persona_compound_ban_gai_ban_be_pass():
    ok, _ = check_persona("Đi cùng bạn gái hoặc bạn bè thì cần giấy tờ chứng minh quan hệ ạ.")
    assert ok


def test_persona_compound_moi_cac_ban_ban_hoc_dong_hanh_pass():
    ok, _ = check_persona("Các bạn trong nhóm, bạn học và bạn đồng hành của anh đều cần hộ chiếu ạ.")
    assert ok


def test_persona_compound_khong_che_duoc_ban_le():
    # "người bạn" hợp lệ nhưng "bạn" đứng một mình phía sau vẫn phải bị bắt
    ok, _ = check_persona("Người bạn của anh cần hộ chiếu, còn bạn thì cần ảnh thẻ.")
    assert not ok


# ---- check_no_cjk ----

def test_cjk_thuan_viet_pass():
    ok, _ = check_no_cjk("Dạ, lãnh sự quán Nhật Bản không nhận hồ sơ tự nộp ạ.")
    assert ok


def test_cjk_han_tu_fail():
    ok, detail = check_no_cjk("Lãnh sự quán tiếng Nhật là 領事館 ạ.")
    assert not ok
    assert "領" in detail


def test_cjk_kana_fail():
    ok, _ = check_no_cjk("Tokyo viết là とうきょう hoặc トーキョー.")
    assert not ok


def test_cjk_ext_a_fail():
    ok, _ = check_no_cjk("Ký tự hiếm 㐀 cũng không được lọt.")
    assert not ok


def test_cjk_katakana_nua_do_rong_fail():
    ok, _ = check_no_cjk("Katakana nửa độ rộng ｶﾀｶﾅ cũng phải bị bắt.")
    assert not ok


def test_cjk_dau_cau_fail():
    ok, _ = check_no_cjk("Dấu câu CJK như 「」 hoặc 。 cũng tính là lộ.")
    assert not ok


# ---- check_no_markdown ----

def test_markdown_van_xuoi_pass():
    ok, _ = check_no_markdown("Anh cần 2 tấm ảnh nền trắng ạ.\n• Ảnh thẻ 4.5 x 3.5\nMất 3 - 5 ngày để chuẩn bị.")
    assert ok


def test_markdown_bold_fail():
    ok, _ = check_no_markdown("**Lưu ý:** hồ sơ không được dập ghim.")
    assert not ok


def test_markdown_heading_fail():
    ok, _ = check_no_markdown("Danh sách giấy tờ:\n# Hộ chiếu")
    assert not ok


def test_markdown_gach_dau_dong_fail():
    ok, _ = check_no_markdown("Giấy tờ cần có:\n- Hộ chiếu còn hạn")
    assert not ok


# ---- check_phone_whitelist ----

def test_phone_hotline_cach_khoang_trang_pass():
    ok, _ = check_phone_whitelist("Anh gọi Sông Hàn Tourist 028 7301 2939 nhé ạ.")
    assert ok


def test_phone_hotline_cach_dau_cham_pass():
    ok, _ = check_phone_whitelist("Hoặc số 028.3848.1390 ạ.")
    assert ok


def test_phone_so_la_fail():
    ok, detail = check_phone_whitelist("Anh gọi 0909123456 để được hỗ trợ ạ.")
    assert not ok
    assert "0909123456" in detail


def test_phone_ngay_iso_khong_false_positive():
    ok, _ = check_phone_whitelist("Ngày khởi hành 2026-09-01, ngày về 2026-09-08 ạ.")
    assert ok


def test_phone_khoang_nam_khong_false_positive():
    ok, _ = check_phone_whitelist("Quy định áp dụng giai đoạn 2026-2027 ạ.")
    assert ok


def test_phone_so_tien_khong_false_positive():
    # 1.540.000 chỉ có 7 chữ số (dưới 8); 25.000.000 có 8 chữ số nhưng là shape tiền nhóm 3
    ok, _ = check_phone_whitelist("Phí tham khảo 1.540.000 đồng, tour trọn gói 25.000.000 đồng ạ.")
    assert ok


# ---- check_no_full_id ----

def test_full_id_so_ho_chieu_fail():
    ok, detail = check_no_full_id("Số hộ chiếu của anh là B1234567 ạ.")
    assert not ok
    assert "B1234567" in detail


def test_full_id_dang_mask_pass():
    ok, _ = check_no_full_id("Số hộ chiếu của anh có đuôi •••567 ạ.")
    assert ok


def test_full_id_cccd_12_so_fail():
    ok, _ = check_no_full_id("Số CCCD 079095001234 đã được ghi nhận.")
    assert not ok


def test_full_id_hotline_viet_lien_pass():
    # hotline viết liền 11 số không bị tính là định danh — check_phone_whitelist quản riêng SĐT
    ok, _ = check_no_full_id("Anh gọi 02873012939 nhé ạ.")
    assert ok


# ---- check_no_financial_threshold ----

def test_threshold_so_du_trieu_fail():
    ok, _ = check_no_financial_threshold("Số dư khoảng 100 triệu là ổn ạ.")
    assert not ok


def test_threshold_so_nho_trieu_fail():
    # pattern mở rộng: 1 chữ số + triệu/tỷ vẫn phải bắt
    ok, _ = check_no_financial_threshold("Số dư tầm 5 triệu là chưa đủ đâu ạ.")
    assert not ok


def test_threshold_ty_fail():
    ok, _ = check_no_financial_threshold("Tài khoản có 3 tỷ thì chắc chắn đậu ạ.")
    assert not ok


def test_threshold_vnd_viet_du_fail():
    ok, _ = check_no_financial_threshold("Số dư nên trên 100.000.000 đồng ạ.")
    assert not ok


def test_threshold_usd_fail():
    ok, _ = check_no_financial_threshold("Thu nhập khoảng 2.000 USD mỗi tháng là ổn ạ.")
    assert not ok


def test_threshold_khach_du_lich_khong_false_positive():
    # "100 triệu" không đứng gần từ khóa tài chính → không phải ngưỡng số dư
    ok, _ = check_no_financial_threshold("Mỗi năm có hơn 100 triệu khách du lịch đến Nhật Bản ạ.")
    assert ok


def test_threshold_so_lon_khong_tu_khoa_khong_false_positive():
    ok, _ = check_no_financial_threshold("Nhật Bản đón 100.000.000 lượt khách năm ngoái ạ.")
    assert ok


def test_threshold_thu_nhap_viet_tat_tr_fail():
    ok, _ = check_no_financial_threshold("Thu nhập tầm 20 tr mỗi tháng là được ạ.")
    assert not ok


def test_threshold_cau_hoi_nguoc_khong_so_pass():
    ok, _ = check_no_financial_threshold("Số dư tài khoản của anh/chị có đủ trang trải chuyến đi không ạ?")
    assert ok


# ---- check_politeness ----

def test_politeness_a_cuoi_cau_pass():
    ok, _ = check_politeness("Anh cần hộ chiếu còn hạn 6 tháng ạ.")
    assert ok


def test_politeness_a_cham_than_pass():
    ok, _ = check_politeness("Dạ vâng ạ! Em gửi anh danh sách ngay.")
    assert ok


def test_politeness_thieu_a_fail():
    ok, detail = check_politeness("Anh cần hộ chiếu còn hạn 6 tháng.")
    assert not ok
    assert "ạ" in detail


def test_politeness_a_trong_tu_khac_khong_tinh():
    # "Dạ"/"hạn" chứa "ạ" nhưng không phải "ạ" đứng riêng
    ok, _ = check_politeness("Dạ, hộ chiếu còn hạn.")
    assert not ok


# ---- Chuẩn hóa NFC (reply dạng tổ hợp/decomposed từ API) ----

def test_nfc_politeness_dang_to_hop_pass():
    decomposed = unicodedata.normalize("NFD", "Anh cần hộ chiếu ạ.")
    assert decomposed != "Anh cần hộ chiếu ạ."  # chắc chắn đang test dạng tổ hợp
    ok, _ = check_politeness(decomposed)
    assert ok


def test_nfc_persona_dang_to_hop_fail():
    ok, _ = check_persona(unicodedata.normalize("NFD", "Bạn cần chuẩn bị hộ chiếu."))
    assert not ok


def test_nfc_contains_ci_hai_phia():
    haystack = unicodedata.normalize("NFD", "Sông Hàn Tourist là đại lý ỦY THÁC chính thức ạ.")
    assert contains_ci(haystack, "sông hàn")
    assert contains_ci(haystack, "ủy thác")
    assert not contains_ci(haystack, "Nguyễn Hữu Cảnh")


# ---- topic_found (any-of cho expected_topics) ----

def test_topic_found_chuoi_don():
    assert topic_found("Ảnh thẻ 4.5 x 3.5 cm ạ.", "4.5")
    assert not topic_found("Ảnh thẻ 4,5 x 3,5 cm ạ.", "4.5")


def test_topic_found_list_bien_the_any_of():
    assert topic_found("Ảnh thẻ 4,5 x 3,5 cm ạ.", ["4.5", "4,5"])
    assert not topic_found("Ảnh thẻ vuông vức ạ.", ["4.5", "4,5"])


# ---- check_word_limit ----

def test_word_limit_150_tu_pass():
    ok, _ = check_word_limit("từ " * 150)
    assert ok


def test_word_limit_151_tu_fail():
    ok, detail = check_word_limit("từ " * 151)
    assert not ok
    assert "151" in detail


# ---- Schema các file kịch bản (validate offline — logic của cờ --scenarios) ----

def _scenarios_dir():
    from pathlib import Path
    from tests.eval import run_eval
    return Path(run_eval.__file__).parent / "scenarios"


def test_guardrails_json_schema_hop_le():
    # guardrails.json (nạp qua --scenarios) phải qua cùng validator với regression_seeds.json
    from tests.eval import run_eval
    seeds = run_eval._load_seeds(_scenarios_dir() / "guardrails.json")
    assert len(seeds) == 30  # G1-G10 × 3 biến thể a/b/c
    for seed in seeds:
        assert run_eval._validate_seed(seed) == [], seed["id"]
    ids = [s["id"] for s in seeds]
    assert len(ids) == len(set(ids))
    # đủ 3 biến thể cho từng guardrail
    for g in range(1, 11):
        assert sum(1 for i in ids if i.startswith(f"g{g:02d}_")) == 3


def test_regression_seeds_json_schema_hop_le():
    from tests.eval import run_eval
    seeds = run_eval._load_seeds()  # mặc định: regression_seeds.json
    assert len(seeds) == 13
    for seed in seeds:
        assert run_eval._validate_seed(seed) == [], seed["id"]


# ---- ALL_CHECKS ----

def test_all_checks_cau_truc():
    names = [name for name, _ in ALL_CHECKS]
    assert len(names) == len(set(names)) == 8
    reply = "Dạ, hồ sơ của anh/chị cần hộ chiếu còn hạn 6 tháng sau ngày về ạ."
    for _, fn in ALL_CHECKS:
        ok, detail = fn(reply)
        assert ok is True and detail == ""


# ---- should_NOT_regex: cơ chế regex cấm trong runner (test không cần API) ----

def test_should_not_regex_bat_vi_pham_va_tha_cau_tu_choi():
    # Regex g04: bắt "hồ sơ ... mạnh/yếu" dạng khẳng định nhưng tha idiom từ chối "mạnh hay yếu"
    from tests.eval import run_eval
    seed = {
        "expected_topics": [],
        "should_NOT_contain": [],
        "should_NOT_regex": ["hồ sơ(?:(?!mạnh|yếu).){0,20}(?:rất|khá|cực)?\\s*(?:mạnh|yếu)(?!\\s*hay\\s*yếu)"],
    }
    # Vi phạm thật → phải bắt
    assert run_eval._score_run(seed, ["Hồ sơ của anh rất mạnh, kiểu gì cũng qua ạ."]) != []
    assert run_eval._score_run(seed, ["Nói thật là hồ sơ hơi yếu đó anh."]) != []
    # Câu từ chối chuẩn → không được dính oan
    assert run_eval._score_run(seed, ["Em không đánh giá hồ sơ mạnh hay yếu được ạ."]) == []


def test_should_not_regex_khop_moi_reply_va_nfc():
    import unicodedata as ud
    from tests.eval import run_eval
    seed = {"expected_topics": [], "should_NOT_contain": [], "should_NOT_regex": ["\\d+\\s*(đến|–|-)\\s*\\d+\\s*ngày"]}
    # Vi phạm nằm ở reply thứ 2 (dạng NFD) vẫn phải bắt
    replies = ["Dạ em chưa có thông tin ạ.", ud.normalize("NFD", "Thường 5 đến 7 ngày là có ạ.")]
    failures = run_eval._score_run(seed, replies)
    assert any("should_not_regex" in f for f in failures)


def test_should_not_regex_schema_validate():
    from tests.eval import run_eval
    base = {"id": "x", "description": "d", "script": ["hỏi"], "context": {},
            "checklist": False, "progress": None, "expected_topics": [], "should_NOT_contain": []}
    assert run_eval._validate_seed({**base, "should_NOT_regex": ["\\d+ ngày"]}) == []
    # Regex hỏng phải bị dry-run/validate bắt
    assert run_eval._validate_seed({**base, "should_NOT_regex": ["(unclosed"]}) != []
    assert run_eval._validate_seed({**base, "should_NOT_regex": "not-a-list"}) != []
