import json
import zipfile
import io
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import Application
from api.form_filler import fill_visa_form, fill_schedule

router = APIRouter()


def _build_info(application: Application) -> dict:
    """Map visa-flow Application data to form_filler info dict."""
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

    # Compute travel days
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

    return {
        # Personal — left blank for user to fill
        "family_name": "",
        "given_name": "",
        "date_of_birth": "",
        "place_of_birth": "",
        "id_number": "",
        "passport_number": "",
        "passport_issue_date": "",
        "home_address": "",
        "phone": "",
        "mobile": "",
        "email": "",
        "company_name": "",
        "company_phone": "",
        "company_address": "",
        "accommodation": "",
        "accommodation_address": "",
        "accommodation_phone": "",
        # Pre-filled from profile
        "nationality": "vietnam",
        "gender": "",
        "marital_status": "single",
        "occupation": occupation,
        "passport_expiry_date": (profile.get("passport_expiry") or "").replace("-", "/"),
        "purpose": "Tourism",
        "entry_date": departure.replace("-", "/") if departure else "",
        "travel_days": str(travel_days),
        "port_of_entry": "Narita" if application.destination == "japan" else "",
        "visa_history": "",
        # Schedule
        "itinerary": [],
        "hotel_city": "Tokyo" if application.destination == "japan" else "Beijing",
    }


@router.get("/application/{application_id}/forms/download")
def download_forms(application_id: str, db: Session = Depends(get_db)):
    application = db.query(Application).filter(
        Application.application_id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.destination != "japan":
        raise HTTPException(status_code=400, detail="Form generation only supported for Japan visa")

    info = _build_info(application)

    try:
        visa_bytes = fill_visa_form(info)
        schedule_bytes = fill_schedule(info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # Bundle into zip
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
