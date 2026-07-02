import json
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from anthropic import Anthropic
from core.config import ANTHROPIC_API_KEY, SONNET

router = APIRouter()
client = Anthropic(api_key=ANTHROPIC_API_KEY)

_CHECKLIST_DIR = Path(__file__).parent.parent.parent / "static" / "checklists"

SOURCE_URLS = {
    "japan": [
        "https://www.vn.emb-japan.go.jp/itpr_vi/necessary_documents.html",
        "https://www.vn.emb-japan.go.jp/itpr_vi/visa.html",
    ],
    "china": [
        "https://www.visaforchina.cn/HAN3_EN/",
    ],
}


def _fetch_page(url: str) -> str:
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; VisaFlowBot/1.0)"})
        resp.raise_for_status()
        return resp.text[:12000]
    except Exception as e:
        return f"[Không thể tải trang: {e}]"


@router.post("/admin/verify-checklist/{destination}")
def verify_checklist(destination: str):
    if destination not in ("japan", "china"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ japan hoặc china")

    checklist_path = _CHECKLIST_DIR / f"{destination}.json"
    if not checklist_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy file checklist")

    with open(checklist_path, "r", encoding="utf-8") as f:
        current = json.load(f)

    pages = {}
    for url in SOURCE_URLS.get(destination, []):
        pages[url] = _fetch_page(url)

    current_items_summary = []
    for emp, items in current.get("by_employment", {}).items():
        for item in items:
            current_items_summary.append(f"[{emp}] {item['name']}: {item['description']}")
    for item in current.get("universal", []):
        current_items_summary.append(f"[universal] {item['name']}: {item['description']}")

    page_content = "\n\n".join(
        f"=== {url} ===\n{content}" for url, content in pages.items()
    )

    prompt = f"""Bạn là chuyên gia tư vấn visa. Hãy so sánh danh sách tài liệu hiện tại trong hệ thống với thông tin từ trang web chính thức của lãnh sự quán.

DANH SÁCH HIỆN TẠI TRONG HỆ THỐNG:
{chr(10).join(current_items_summary)}

NỘI DUNG TRANG WEB CHÍNH THỨC:
{page_content}

Hãy phân tích và trả về JSON với format sau:
{{
  "status": "ok" | "needs_review" | "fetch_failed",
  "last_checked": "{destination}",
  "issues": [
    {{
      "type": "missing" | "outdated" | "extra" | "changed",
      "item": "tên tài liệu",
      "detail": "mô tả vấn đề cụ thể"
    }}
  ],
  "summary": "tóm tắt ngắn bằng tiếng Việt",
  "recommendation": "khuyến nghị cụ thể cần làm gì"
}}

Nếu không đọc được trang web (fetch failed), đặt status = "fetch_failed" và giải thích trong summary.
Chỉ trả về JSON, không có text khác."""

    response = client.messages.create(
        model=SONNET,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"status": "error", "raw": raw}

    result["source_urls"] = SOURCE_URLS.get(destination, [])
    result["checklist_last_verified"] = current.get("meta", {}).get("last_verified")

    return result
