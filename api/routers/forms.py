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
    accommodation: str = ""
    accommodation_address: str = ""
    accommodation_phone: str = ""


class FormsRequest(BaseModel):
    personal_info: PersonalInfo


def _build_info(application: Application, personal: PersonalInfo) -> dict:
    profile = {}
    if application.profile_json:
        try:
            profile = json.loads(application.profile_json)
        except Exception:
            pass

    travel_dates = {}
    if application.travel_dates:
        try:
            travel_dates = json.loads(application.travel_dates)
        except Exception:
            pass

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
        "accommodation": personal.accommodation,
        "accommodation_address": personal.accommodation_address,
        "accommodation_phone": personal.accommodation_phone,
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
def download_forms(application_id: str, body: FormsRequest, db: Session = Depends(get_db)):
    application = db.query(Application).filter(
        Application.application_id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.destination != "japan":
        raise HTTPException(status_code=400, detail="Form generation only supported for Japan visa")

    info = _build_info(application, body.personal_info)

    try:
        _td = {}
        if application.travel_dates:
            try:
                _td = json.loads(application.travel_dates)
            except Exception:
                pass

        itinerary = generate_itinerary(
            destination=application.destination,
            departure=_td.get("departure", ""),
            return_date=_td.get("return", ""),
            hotel_name=body.personal_info.accommodation,
            hotel_phone=body.personal_info.accommodation_phone,
        )
        info["itinerary"] = itinerary
        if itinerary and body.personal_info.accommodation:
            info["hotel_city"] = body.personal_info.accommodation

        visa_bytes = fill_visa_form(info)
        schedule_bytes = fill_schedule(info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

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
