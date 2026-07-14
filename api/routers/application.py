import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import Application, Document

router = APIRouter()

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
PDF_TYPE = "application/pdf"
ALLOWED_UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}


class DestinationUpdate(BaseModel):
    destination: str


class ProfileUpdate(BaseModel):
    profile_json: dict
    travel_dates: Optional[dict] = None


class ItineraryUpdate(BaseModel):
    itinerary: list


class DocumentSkip(BaseModel):
    doc_type: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/application/start")
def start_application(db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    app = Application(session_id=session_id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"application_id": app.id, "session_id": session_id}


@router.patch("/application/{app_id}/destination")
def set_destination(app_id: int, body: DestinationUpdate, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.destination = body.destination
    db.commit()
    return {"ok": True}


@router.put("/application/{app_id}/profile")
def update_profile(app_id: int, body: ProfileUpdate, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.profile_json = body.profile_json
    if body.travel_dates:
        app.travel_dates = body.travel_dates
    db.commit()
    return {"ok": True}


@router.post("/application/{app_id}/eligibility")
def run_eligibility(app_id: int, db: Session = Depends(get_db)):
    import json
    from api.working_days import vn_today
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    profile = app.profile_json or {}
    travel_dates = app.travel_dates or {}
    # Legacy rows may store travel_dates as a JSON string (same guard as forms.py)
    if isinstance(travel_dates, str):
        try:
            travel_dates = json.loads(travel_dates)
        except Exception:
            travel_dates = {}
    if not isinstance(travel_dates, dict):
        travel_dates = {}
    destination = app.destination or "japan"
    today = vn_today()

    # Deterministic Python pre-checks — no LLM call when either rule fails
    result = _deterministic_eligibility(profile, travel_dates, destination, today)

    if result is None:
        from api.ai import assess_eligibility
        try:
            result = assess_eligibility(
                profile=profile,
                travel_dates=travel_dates,
                destination=destination,
            )
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    app.eligibility_result = result.get("result")
    app.eligibility_data = result
    db.commit()
    return result


def _deterministic_eligibility(profile, travel_dates, destination, today):
    """Python-first eligibility rules. Returns a FE-shaped result dict when a
    hard rule fails, or None when both checks pass (→ caller invokes the LLM)."""
    from datetime import date, timedelta
    from api.working_days import check_departure_rule, check_prior_denial_rule

    dest_name = "Nhật Bản" if destination == "japan" else destination

    # Rule 1 — 180 ngày sau lần từ chối cùng điểm đến
    if not check_prior_denial_rule(profile, destination, today):
        retry_note = ""
        try:
            denial_date = date.fromisoformat(str(profile.get("denial_date")))
            retry_from = (denial_date + timedelta(days=180)).strftime("%d/%m/%Y")
            retry_note = f" Bạn có thể nộp lại từ ngày {retry_from}."
        except (TypeError, ValueError):
            pass
        return {
            "result": "not_eligible",
            "headline": "Bạn cần chờ đủ 180 ngày sau lần từ chối trước",
            "bullets": [
                f"Hồ sơ của bạn từng bị từ chối visa {dest_name} trong vòng 180 ngày gần đây",
                "Theo quy định, hồ sơ nộp lại trước thời hạn này sẽ không được xét duyệt",
            ],
            "reason": f"Bạn cần chờ đủ 180 ngày kể từ ngày bị từ chối visa {dest_name} trước khi nộp hồ sơ mới.{retry_note}",
            "confidence_label": "Độ tin cậy AI: Cao",
        }

    # Rule 2 — khởi hành phải SAU mốc 10 ngày làm việc kể từ hôm nay
    departure_raw = (travel_dates or {}).get("departure", "")
    try:
        departure = date.fromisoformat(str(departure_raw))
    except (TypeError, ValueError):
        departure = None  # không parse được → để LLM xử như cũ
    if departure is not None:
        ok, moc = check_departure_rule(today, departure)
        if not ok:
            moc_fmt = moc.strftime("%d/%m/%Y")
            return {
                "result": "not_eligible",
                "headline": "Ngày khởi hành quá gần",
                "bullets": [
                    "Hồ sơ visa cần tối thiểu 10 ngày làm việc để xử lý (không tính Thứ 7, Chủ nhật và ngày lễ)",
                    f"Bạn hãy chọn ngày khởi hành sau ngày {moc_fmt}",
                ],
                "reason": f"Chuyến đi cần khởi hành sau ngày {moc_fmt} (10 ngày làm việc kể từ hôm nay, không tính Thứ 7, Chủ nhật và ngày lễ).",
                "confidence_label": "Độ tin cậy AI: Cao",
            }

    return None


@router.post("/application/{app_id}/payment/demo")
def demo_payment(app_id: int, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.payment_status = "demo_completed"
    app.feasibility_ok = True
    db.commit()
    return {"ok": True}


@router.post("/application/{app_id}/checklist")
def get_checklist(app_id: int, db: Session = Depends(get_db)):
    from api.ai import generate_checklist
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.checklist_json:
        return app.checklist_json
    try:
        result = generate_checklist(
            profile=app.profile_json or {},
            travel_dates=app.travel_dates or {},
            destination=app.destination or "japan",
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    app.checklist_json = result
    db.commit()
    return result


@router.post("/application/{app_id}/documents")
async def upload_document(
    app_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    db: Session = Depends(get_db),
):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Chỉ chấp nhận ảnh (JPG, PNG, WebP) hoặc PDF. Vui lòng chọn lại tệp."
        )

    app_dir = UPLOADS_DIR / str(app_id)
    app_dir.mkdir(exist_ok=True)

    safe_name = f"{doc_type}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = app_dir / safe_name

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        application_id=app_id,
        doc_type=doc_type,
        file_path=str(file_path),
        review_status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"document_id": doc.id, "doc_type": doc_type, "status": "pending"}


@router.post("/application/{app_id}/documents/skip")
def skip_document(app_id: int, body: DocumentSkip, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    doc = (
        db.query(Document)
        .filter(Document.application_id == app_id, Document.doc_type == body.doc_type)
        .order_by(Document.id.desc())
        .first()
    )

    # Không ghi đè tài liệu đã upload/đang review — trả trạng thái thực tế
    if doc and doc.review_status in ("pass", "pending"):
        return {"document_id": doc.id, "doc_type": body.doc_type, "status": doc.review_status}

    if doc:
        doc.review_status = "skipped"
        doc.file_path = None  # chỉ gỡ tham chiếu, không xóa file vật lý trên đĩa
        doc.review_notes = "Khách bổ sung trực tiếp cho nhân viên visa"
    else:
        doc = Document(
            application_id=app_id,
            doc_type=body.doc_type,
            file_path=None,
            review_status="skipped",
            review_notes="Khách bổ sung trực tiếp cho nhân viên visa",
        )
        db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"document_id": doc.id, "doc_type": body.doc_type, "status": "skipped"}


@router.post("/application/{app_id}/documents/unskip")
def unskip_document(app_id: int, body: DocumentSkip, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.query(Document).filter(
        Document.application_id == app_id,
        Document.doc_type == body.doc_type,
        Document.review_status == "skipped",
    ).delete()
    db.commit()
    return {"ok": True}


@router.get("/application/{app_id}/documents")
def list_documents(app_id: int, db: Session = Depends(get_db)):
    docs = (
        db.query(Document)
        .filter(Document.application_id == app_id)
        .order_by(Document.id)
        .all()
    )
    return [
        {
            "id": d.id,
            "doc_type": d.doc_type,
            "review_status": d.review_status,
            "review_notes": d.review_notes,
        }
        for d in docs
    ]


@router.post("/application/{app_id}/documents/{doc_id}/review")
def review_document(app_id: int, doc_id: int, db: Session = Depends(get_db)):
    from api.ai import review_document_image
    doc = db.get(Document, doc_id)
    if not doc or doc.application_id != app_id:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.review_status == "skipped":
        raise HTTPException(
            status_code=400,
            detail="Tài liệu đã được đánh dấu bổ sung sau, không có file để kiểm tra.",
        )

    app = db.get(Application, app_id)
    file_path = Path(doc.file_path) if doc.file_path else None

    if file_path and file_path.exists():
        content_type = _guess_media_type(file_path.name)
        profile_ctx = {**(app.profile_json or {}), "destination": app.destination}

        if content_type in IMAGE_TYPES:
            try:
                result = review_document_image(
                    images=[(file_path.read_bytes(), content_type)],
                    doc_type=doc.doc_type,
                    profile=profile_ctx,
                )
                doc.review_status = result.get("status", "pass")
                doc.review_notes = result.get("reason")
            except Exception:
                doc.review_status = "needs_clarification"
                doc.review_notes = "Không thể tự động kiểm tra. Đội tư vấn sẽ xem xét."

        elif content_type == PDF_TYPE:
            try:
                import fitz  # PyMuPDF
                pdf_doc = fitz.open(str(file_path))
                # Render TẤT CẢ các trang (dpi 150) — gửi hết trong MỘT call Sonnet
                page_images = [
                    (page.get_pixmap(dpi=150).tobytes("png"), "image/png")
                    for page in pdf_doc
                ]
                pdf_doc.close()
                if not page_images:
                    # Zero-page PDF → fall into the needs_clarification catch below
                    raise ValueError("PDF has no renderable pages")
                result = review_document_image(
                    images=page_images,
                    doc_type=doc.doc_type,
                    profile=profile_ctx,
                )
                doc.review_status = result.get("status", "pass")
                doc.review_notes = result.get("reason")
            except Exception:
                doc.review_status = "needs_clarification"
                doc.review_notes = "Không thể tự động kiểm tra file PDF. Đội tư vấn sẽ xem xét."

        else:
            doc.review_status = "fail"
            doc.review_notes = "Định dạng file không được hỗ trợ. Vui lòng tải lên ảnh hoặc PDF."
    else:
        doc.review_status = "needs_clarification"
        doc.review_notes = "Không tìm thấy file. Vui lòng thử tải lên lại."

    # For passport images: also extract personal info for form pre-fill
    if doc.doc_type == "passport" and file_path and file_path.exists():
        ct = _guess_media_type(file_path.name)
        if ct in IMAGE_TYPES:
            try:
                from api.ai import extract_id_info
                extracted = extract_id_info(file_path.read_bytes(), ct, "passport")
                if extracted and not extracted.get("error"):
                    existing = app.extracted_info_json or {}
                    app.extracted_info_json = {**existing, **{k: v for k, v in extracted.items() if v}}
            except Exception:
                pass

    db.commit()
    return {"status": doc.review_status, "reason": doc.review_notes}


@router.get("/application/{app_id}/extracted-info")
def get_extracted_info(app_id: int, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app.extracted_info_json or {}


@router.patch("/application/{app_id}/itinerary")
def save_itinerary(app_id: int, body: ItineraryUpdate, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.itinerary_json = body.itinerary
    db.commit()
    return {"ok": True}


@router.post("/application/{app_id}/submit")
def submit_application(app_id: int, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.submission_status = "submitted"
    app.submitted_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.get("/application/{app_id}/status")
def get_status(app_id: int, db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    status = app.submission_status or "pending"
    submitted_at = app.submitted_at.isoformat() if app.submitted_at else None

    node_states = _build_timeline(status, submitted_at)
    return {
        "submission_status": status,
        "nodes": node_states,
        "is_terminal": status in {"approved", "rejected", "quota_rejected"},
    }


def _build_timeline(status: str, submitted_at):
    completed = {"agency_submitted", "processing", "approved", "rejected", "quota_rejected"}
    nodes = [
        {"id": "received", "label": "Tài liệu đã nhận", "sub": "Chúng tôi đã nhận hồ sơ của bạn"},
        {"id": "embassy_submitted", "label": "Đã nộp lên Đại sứ quán", "sub": "Hồ sơ được chuyển đến ĐSQ"},
        {"id": "processing", "label": "Đang xử lý", "sub": "ĐSQ đang xem xét hồ sơ"},
        {"id": "result", "label": "Có kết quả", "sub": "Kết quả sẽ được thông báo ngay"},
    ]
    order = ["received", "embassy_submitted", "processing", "result"]
    status_to_active = {
        "submitted": "received",
        "agency_submitted": "embassy_submitted",
        "processing": "processing",
        "approved": "result",
        "rejected": "result",
        "quota_rejected": "result",
    }
    active_id = status_to_active.get(status, "received")
    active_idx = order.index(active_id)

    result = []
    for i, node in enumerate(nodes):
        if i < active_idx:
            state = "completed"
        elif i == active_idx:
            state = "active"
        else:
            state = "pending"
        result.append({**node, "state": state})
    return result


def _guess_media_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".jpg") or name.endswith(".jpeg"):
        return "image/jpeg"
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".webp"):
        return "image/webp"
    if name.endswith(".gif"):
        return "image/gif"
    if name.endswith(".pdf"):
        return "application/pdf"
    return "application/octet-stream"
