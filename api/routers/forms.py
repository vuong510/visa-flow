import json
import zipfile
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import Application
from api.form_filler import fill_visa_form, fill_schedule
from api.ai import generate_itinerary

router = APIRouter()


class PersonalInfo(BaseModel):
    family_name: str = ""
    given_name: str = ""
    date_of_birth: str = ""
    place_of_birth: str = ""
    id_number: str = ""
    passport_number: str = ""
    passport_issue_date: str = ""
    gender: str = "male"
    marital_status: str = "single"
    home_address: str = ""
    mobile: str = ""
    email: str = ""
    company_name: str = ""
    company_address: str = ""
    company_phone: str = ""
    accommodation: str = ""
    accommodation_address: str = ""
    accommodation_phone: str = ""
    # Khai báo tiền án — 6 câu Yes/No trên trang 2 form MOFA (RB5[0-5]).
    # BẮT BUỘC, không default: thiếu câu nào → 422, không âm thầm tick "No".
    # Thứ tự dưới đây theo thứ tự câu hỏi trên form (top→bottom).
    conviction_any_crime: bool   # RB5[3] — convicted of a crime or offence in any country
    sentenced_1yr_plus: bool     # RB5[0] — sentenced to imprisonment for 1 year or more
    deported_or_removed: bool    # RB5[1] — deported/removed from Japan or any country
    drug_offense: bool           # RB5[5] — drug offence (narcotics, marijuana, opium...)
    prostitution_related: bool   # RB5[4] — prostitution or directly connected activity
    human_trafficking: bool      # RB5[2] — trafficking in persons / incited or aided


class FormsRequest(BaseModel):
    # Optional: FormFillingScreen luôn gửi kèm (giữ nguyên hành vi cũ). Khi gọi lại từ màn khác
    # (redownload) không có state để gửi — backend tự lấy từ Application.form_personal_info_json.
    personal_info: Optional[PersonalInfo] = None


def _build_info(application: Application, personal: PersonalInfo) -> dict:
    profile = application.profile_json or {}
    if isinstance(profile, str):
        try:
            profile = json.loads(profile)
        except Exception:
            profile = {}

    travel_dates = application.travel_dates or {}
    if isinstance(travel_dates, str):
        try:
            travel_dates = json.loads(travel_dates)
        except Exception:
            travel_dates = {}

    departure = travel_dates.get("departure", "")
    return_date = travel_dates.get("return", "")

    travel_days = 7
    if departure and return_date:
        try:
            d0 = datetime.strptime(departure, "%Y-%m-%d").date()
            d1 = datetime.strptime(return_date, "%Y-%m-%d").date()
            travel_days = max(1, (d1 - d0).days + 1)
        except Exception:
            pass

    employment_map = {
        "employee": "Company Employee",
        "student": "Student",
        "business_owner": "Business Owner",
        "freelancer": "Self-employed",
        "homemaker": "Homemaker",
        "retired": "Retired",
    }
    occupation = employment_map.get(profile.get("employment_type", ""), "")

    def _fmt(date_str: str) -> str:
        return date_str.replace("-", "/") if date_str else ""

    return {
        # From user input
        "family_name": personal.family_name,
        "given_name": personal.given_name,
        "date_of_birth": _fmt(personal.date_of_birth),
        "place_of_birth": personal.place_of_birth,
        "id_number": personal.id_number,
        "passport_number": personal.passport_number,
        "passport_issue_date": _fmt(personal.passport_issue_date),
        "gender": personal.gender,
        "marital_status": personal.marital_status,
        "home_address": personal.home_address,
        "mobile": personal.mobile,
        "email": personal.email,
        "company_name": personal.company_name,
        "company_address": personal.company_address,
        "company_phone": personal.company_phone,
        "accommodation": personal.accommodation,
        "accommodation_address": personal.accommodation_address,
        "accommodation_phone": personal.accommodation_phone,
        # Criminal-history declaration (RB5[0-5] on page 2)
        "conviction_any_crime": personal.conviction_any_crime,
        "sentenced_1yr_plus": personal.sentenced_1yr_plus,
        "deported_or_removed": personal.deported_or_removed,
        "drug_offense": personal.drug_offense,
        "prostitution_related": personal.prostitution_related,
        "human_trafficking": personal.human_trafficking,
        # From profile/application
        "nationality": "vietnam",
        "occupation": occupation,
        "passport_expiry_date": _fmt(profile.get("passport_expiry") or ""),
        "purpose": "Tourism",
        "entry_date": _fmt(departure),
        "travel_days": str(travel_days),
        "port_of_entry": "Narita" if application.destination == "japan" else "",
        "visa_history": "",
        "itinerary": [],
        "hotel_city": personal.accommodation or ("Tokyo" if application.destination == "japan" else "Beijing"),
    }


@router.post("/application/{application_id}/forms/download")
def download_forms(application_id: int, body: FormsRequest, db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.destination != "japan":
        raise HTTPException(status_code=400, detail="Form generation only supported for Japan visa")

    if body.personal_info is not None:
        personal = body.personal_info
    else:
        stored = application.form_personal_info_json
        if not stored:
            raise HTTPException(status_code=404, detail="Chưa có thông tin đơn để tải lại")
        personal = PersonalInfo(**stored)

    info = _build_info(application, personal)

    try:
        # travel_dates is normally already a dict (JSON column) — only parse strings
        _td = application.travel_dates or {}
        if isinstance(_td, str):
            try:
                _td = json.loads(_td)
            except Exception:
                _td = {}
        if not isinstance(_td, dict):
            _td = {}

        if application.itinerary_json:
            itinerary = application.itinerary_json
        else:
            itinerary = generate_itinerary(
                destination=application.destination,
                departure=_td.get("departure", ""),
                return_date=_td.get("return", ""),
                hotel_name=personal.accommodation,
                hotel_phone=personal.accommodation_phone,
            )
        info["itinerary"] = itinerary
        if itinerary and personal.accommodation:
            info["hotel_city"] = personal.accommodation

        visa_bytes = fill_visa_form(info)
        schedule_bytes = fill_schedule(info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    if body.personal_info is not None:
        # Refresh lưu trữ SAU khi sinh PDF thành công — tránh lưu đè dữ liệu có thể gây lỗi
        # PDF lên trên bản cũ còn dùng được, nếu generation phía trên throw.
        application.form_personal_info_json = personal.model_dump()
        db.commit()

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("don_xin_visa.pdf", visa_bytes)
        zf.writestr("lich_trinh.pdf", schedule_bytes)
    zip_buf.seek(0)

    return Response(
        content=zip_buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=visa-forms.zip"},
    )


class FormInfoSaveRequest(BaseModel):
    personal_info: PersonalInfo


@router.patch("/application/{application_id}/form-info")
def save_form_info(application_id: int, body: FormInfoSaveRequest, db: Session = Depends(get_db)):
    # Lưu-only, không sinh PDF — gọi lúc bấm "Tiếp tục" ở Bước 5 kể cả khi user chưa từng bấm
    # tải, để màn khác (vd Checklist) có thể tải lại đơn sau mà không cần FE giữ state.
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.destination != "japan":
        raise HTTPException(status_code=400, detail="Form generation only supported for Japan visa")

    application.form_personal_info_json = body.personal_info.model_dump()
    db.commit()
    return {"status": "saved"}
