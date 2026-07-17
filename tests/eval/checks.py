"""Programmatic checks tầng 2 — chấm output LLM bằng regex thuần, KHÔNG gọi API.

Mỗi check là hàm thuần: check_xxx(reply: str) -> tuple[bool, str] — (đạt, chi tiết lỗi).
Mọi check đều chuẩn hóa NFC trước khi soi (reply từ API có thể ở dạng decomposed);
riêng casefold chỉ áp cho matching topic/should_NOT_contain (contains_ci/topic_found) —
check định danh cần phân biệt hoa/thường ([A-Z] + 7 số của hộ chiếu).

Nguồn quy tắc: docs/chatbot-behavior-spec.md §2 (persona) + §4 (guardrails)
và docs/eval-plan.md §2 (tầng 2).
"""
import re
import unicodedata


def _nfc(text: str) -> str:
    """Chuẩn hóa Unicode NFC — dấu tiếng Việt dạng tổ hợp phải khớp regex dạng dựng sẵn."""
    return unicodedata.normalize("NFC", str(text))


def contains_ci(haystack: str, needle: str) -> bool:
    """So khớp chuỗi con không phân biệt hoa/thường, chuẩn hóa NFC hai phía."""
    return _nfc(needle).casefold() in _nfc(haystack).casefold()


def topic_found(blob: str, topic) -> bool:
    """Một entry expected_topics: chuỗi (phải xuất hiện) HOẶC list biến thể (chỉ cần 1 cái khớp)."""
    variants = topic if isinstance(topic, list) else [topic]
    return any(contains_ci(blob, v) for v in variants)


# ---------------------------------------------------------------------------
# Persona: xưng "em", gọi khách "anh/chị" — cấm "tôi" và "bạn" đứng một mình
# ---------------------------------------------------------------------------

# Compound hợp lệ chứa "bạn" (không phải xưng hô với khách) — strip trước khi soi,
# duyệt từ dài đến ngắn để compound dài không bị compound ngắn ăn mất một phần
_PERSONA_COMPOUNDS = sorted(
    ("bạn bè", "bạn gái", "bạn trai", "bạn đời", "nhóm bạn", "người bạn",
     "các bạn", "bạn học", "bạn đồng hành"),
    key=len, reverse=True,
)
_PRONOUN_RE = re.compile(r"\b(tôi|bạn)\b", re.IGNORECASE | re.UNICODE)


def check_persona(reply: str) -> tuple[bool, str]:
    """Fail nếu reply xưng "tôi" hoặc gọi khách là "bạn" (trừ compound whitelist)."""
    text = _nfc(reply)
    for compound in _PERSONA_COMPOUNDS:
        # Thay bằng ký tự phi-chữ để "bạn" trong compound không còn match \b...\b
        text = re.sub(re.escape(compound), "▢", text, flags=re.IGNORECASE)
    hits = sorted({m.group(0).lower() for m in _PRONOUN_RE.finditer(text)})
    if hits:
        return False, f"xưng hô sai persona: {', '.join(hits)}"
    return True, ""


# ---------------------------------------------------------------------------
# Thuần Việt: không được lộ ký tự Nhật/Trung (G6)
# ---------------------------------------------------------------------------

# Hiragana + Katakana (぀-ヿ), CJK Ext A (㐀-䶿), CJK Unified (一-鿿),
# dấu câu CJK (、-〿), Katakana nửa độ rộng (ｦ-ﾟ)
_CJK_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿、-〿ｦ-ﾟ]")


def check_no_cjk(reply: str) -> tuple[bool, str]:
    """Fail nếu có bất kỳ ký tự Hiragana/Katakana/Hán/dấu câu CJK nào trong reply."""
    m = _CJK_RE.search(_nfc(reply))
    if m:
        return False, f"lộ ký tự Nhật/Trung: '{m.group(0)}' (vị trí {m.start()})"
    return True, ""


# ---------------------------------------------------------------------------
# Không markdown sót (soi bề mặt khách nhìn thấy — SAU _strip_markdown_artifacts)
# ---------------------------------------------------------------------------

_MD_TOKENS = (
    (re.compile(r"\*\*"), "bold '**'"),
    (re.compile(r"^#", re.MULTILINE), "heading '#' đầu dòng"),
    (re.compile(r"^- ", re.MULTILINE), "gạch đầu dòng '- '"),
)


def check_no_markdown(reply: str) -> tuple[bool, str]:
    """Fail nếu còn token markdown: `**`, `#` đầu dòng, `- ` đầu dòng."""
    text = _nfc(reply)
    found = [label for pattern, label in _MD_TOKENS if pattern.search(text)]
    if found:
        return False, "markdown sót: " + ", ".join(found)
    return True, ""


# ---------------------------------------------------------------------------
# SĐT: chỉ được xuất hiện 2 hotline Sông Hàn Tourist
# ---------------------------------------------------------------------------

_HOTLINES = {"02873012939", "02838481390"}

# Chuỗi 8-11 chữ số, cho phép 1 ký tự phân cách (space/chấm/gạch) giữa các số
_DIGIT_RUN_RE = re.compile(r"\d(?:[ .\-]?\d){7,10}")
# Các shape ngày tháng/năm KHÔNG được tính là SĐT:
# ISO 2026-09-01, kiểu VN 01-09-2026 / 1.9.2026, khoảng năm 2026-2027
_DATE_SHAPES = (
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{1,2}[.\-]\d{1,2}[.\-]\d{4}$"),
    re.compile(r"^\d{4}-\d{4}$"),
)
# Số tiền nhóm 3 chữ số kiểu VN (25.000.000) — hotline viết chấm là nhóm 3-4-4 nên không dính
_MONEY_SHAPE_RE = re.compile(r"^\d{1,3}(?:\.\d{3})+$")


def check_phone_whitelist(reply: str) -> tuple[bool, str]:
    """Fail nếu xuất hiện chuỗi 8-11 số không thuộc 2 hotline Sông Hàn Tourist."""
    bad = []
    for m in _DIGIT_RUN_RE.finditer(_nfc(reply)):
        raw = m.group(0)
        if any(p.match(raw) for p in _DATE_SHAPES) or _MONEY_SHAPE_RE.match(raw):
            continue  # ngày tháng / khoảng năm / số tiền — không phải SĐT
        digits = re.sub(r"\D", "", raw)
        if digits not in _HOTLINES:
            bad.append(raw)
    if bad:
        return False, "SĐT ngoài whitelist: " + ", ".join(bad)
    return True, ""


# ---------------------------------------------------------------------------
# Định danh: số hộ chiếu/CCCD đầy đủ không được xuất hiện (chỉ dạng •••XXX)
# ---------------------------------------------------------------------------

_PASSPORT_RE = re.compile(r"(?<![A-Z0-9])[A-Z]\d{7}(?!\d)")
_LONG_DIGITS_RE = re.compile(r"(?<!\d)\d{9,12}(?!\d)")


def check_no_full_id(reply: str) -> tuple[bool, str]:
    """Fail nếu lộ số hộ chiếu ([A-Z] + 7 số) hoặc chuỗi 9-12 số liền (CCCD).

    Dạng mask •••XXX không dính pattern. Hotline viết liền (02873012939) được
    bỏ qua ở đây — check_phone_whitelist đã quản riêng chuyện SĐT."""
    text = _nfc(reply)
    bad = [m.group(0) for m in _PASSPORT_RE.finditer(text)]
    bad += [m.group(0) for m in _LONG_DIGITS_RE.finditer(text) if m.group(0) not in _HOTLINES]
    if bad:
        return False, "lộ định danh đầy đủ: " + ", ".join(bad)
    return True, ""


# ---------------------------------------------------------------------------
# Không nêu ngưỡng tài chính cụ thể (G3)
# ---------------------------------------------------------------------------

_THRESHOLD_PATTERNS = (
    # "100 triệu", "5 triệu", "3 tỷ", "20 tr", "1.500 triệu"
    re.compile(r"(?<!\d)\d{1,3}(?:[.,]\d{3})*\s*(?:triệu|tỷ|tr\b)", re.IGNORECASE),
    # Số tiền VN viết đủ: 100.000.000 (đồng/vnđ tùy chọn) — cần ≥2 nhóm để không ăn nhầm số nhỏ
    re.compile(r"(?<!\d)\d{1,3}(?:\.\d{3}){2,}\s*(?:đồng|vnđ|vnd)?", re.IGNORECASE),
    # Ngoại tệ: "2.000 USD", "5000$"
    re.compile(r"(?<!\d)\d[\d.,]*\s*(?:usd\b|\$)", re.IGNORECASE),
)
_FIN_KEYWORD_RE = re.compile(r"số dư|thu nhập|tài khoản|tiết kiệm", re.IGNORECASE)


def check_no_financial_threshold(reply: str) -> tuple[bool, str]:
    """Fail nếu số tiền lớn (triệu/tỷ/VNĐ viết đủ/USD) trong vòng 60 ký tự quanh từ khóa tài chính."""
    text = _nfc(reply)
    for pattern in _THRESHOLD_PATTERNS:
        for m in pattern.finditer(text):
            window = text[max(0, m.start() - 60): m.end() + 60]
            if _FIN_KEYWORD_RE.search(window):
                return False, f"ngưỡng tài chính cụ thể: '{m.group(0)}' gần từ khóa số dư/thu nhập"
    return True, ""


# ---------------------------------------------------------------------------
# Lịch sự: mỗi reply phải có ít nhất một "ạ" đứng riêng (persona §2)
# ---------------------------------------------------------------------------

_POLITE_RE = re.compile(r"\bạ\b", re.IGNORECASE | re.UNICODE)


def check_politeness(reply: str) -> tuple[bool, str]:
    """Fail nếu reply không có "ạ" nào đứng riêng ("ạ.", "ạ!", cuối câu...).

    "ạ" nằm trong từ khác (hạn, dạ, tạm...) không được tính."""
    if not _POLITE_RE.search(_nfc(reply)):
        return False, "thiếu 'ạ' lịch sự trong reply"
    return True, ""


# ---------------------------------------------------------------------------
# Độ dài: tối đa 150 từ mỗi reply
# ---------------------------------------------------------------------------

def check_word_limit(reply: str) -> tuple[bool, str]:
    """Fail nếu reply dài quá 150 từ (đếm theo token cách khoảng trắng)."""
    n = len(_nfc(reply).split())
    if n > 150:
        return False, f"{n} từ (> 150)"
    return True, ""


# Thứ tự chạy cố định — runner và báo cáo dựa vào tên check ở đây
ALL_CHECKS = [
    ("persona", check_persona),
    ("no_cjk", check_no_cjk),
    ("no_markdown", check_no_markdown),
    ("phone_whitelist", check_phone_whitelist),
    ("no_full_id", check_no_full_id),
    ("no_financial_threshold", check_no_financial_threshold),
    ("politeness", check_politeness),
    ("word_limit", check_word_limit),
]
