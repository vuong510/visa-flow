from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.ai import extract_id_info

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/extract-id")
async def extract_id(
    file: UploadFile = File(...),
    doc_type: str = Form("cccd"),  # "cccd" or "passport"
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận ảnh JPG, PNG, WEBP, HEIC")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File quá lớn (tối đa 10MB)")

    media_type = file.content_type
    # HEIC → treat as jpeg for Anthropic API
    if media_type in ("image/heic", "image/heif"):
        media_type = "image/jpeg"

    try:
        result = extract_id_info(image_bytes, media_type, doc_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể đọc tài liệu: {e}")

    if result.get("error") == "not_id_document":
        raise HTTPException(status_code=422, detail="Ảnh này không phải hộ chiếu hoặc CCCD. Vui lòng chọn đúng ảnh giấy tờ tùy thân.")
    if result.get("error"):
        raise HTTPException(status_code=422, detail="Không thể đọc thông tin từ ảnh. Vui lòng chụp lại rõ hơn (đủ sáng, không bị mờ).")

    return result
