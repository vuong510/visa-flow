from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from db.session import get_db
from db.models import VisaCase, PolicyRule, PolicyDraft
from agents.pipeline import VisaPipeline
from agents.librarian import LibrarianAgent

router = APIRouter()


# ── Mock OCR ─────────────────────────────────────────────────────

def mock_ocr(filename: str, doc_type: str, ctx: dict) -> str:
    name     = ctx.get("applicant_name", "Applicant")
    employer = ctx.get("employer", "Company Ltd")
    income   = ctx.get("monthly_income_vnd", "25,000,000")
    budget   = ctx.get("declared_budget_vnd", "35,000,000")

    if doc_type == "passport":
        parts = name.split()
        surname = parts[-1].upper() if parts else "NGUYEN"
        given   = " ".join(parts[:-1]).upper() if len(parts) > 1 else "VAN A"
        return f"""SOCIALIST REPUBLIC OF VIETNAM — PASSPORT
Surname: {surname}
Given names: {given}
Nationality: Vietnamese
Date of birth: 15 MAY 1990
Place of birth: Ha Noi, Vietnam
Date of issue: 10 JAN 2020
Date of expiry: 10 JAN 2030
Passport No: B7654321
Authority: Department of Immigration — Vietnam
[Source: {filename}]"""

    if doc_type == "bank":
        return f"""VIETCOMBANK — ACCOUNT STATEMENT
Account holder: {name}
Account number: 0071002345678
Statement period: 01 JAN 2025 – 31 MAR 2025

TRANSACTIONS:
05 Jan 2025 | CREDIT | {income} VND | Salary — {employer}    | Balance: 46,800,000
18 Jan 2025 | DEBIT  | 2,100,000 VND | Rent & utilities       | Balance: 44,700,000
05 Feb 2025 | CREDIT | {income} VND | Salary — {employer}    | Balance: 47,200,000
14 Feb 2025 | DEBIT  | 1,800,000 VND | Daily expenses         | Balance: 45,400,000
05 Mar 2025 | CREDIT | {income} VND | Salary — {employer}    | Balance: 48,900,000
22 Mar 2025 | DEBIT  | 3,500,000 VND | Travel savings deposit | Balance: 45,400,000

Average monthly balance: 46,100,000 VND
Largest single debit: 3,500,000 VND (travel savings — not suspicious)
Salary deposits consistent every 5th of month from {employer}.
No large unexplained cash withdrawals detected.
[Source: {filename}]"""

    if doc_type == "employment":
        return f"""EMPLOYMENT VERIFICATION LETTER

Date: 10 January 2025
Re: Visa Support Letter for {name}

To Whom It May Concern,

This is to confirm that {name} is a full-time employee of {employer},
having joined us on 01 March 2020 (4+ years tenure).

Position: Software Engineer (Senior)
Employment type: Permanent, full-time
Gross monthly salary: {income} VND
Current status: Active — in good standing

The employee has been approved for annual leave from 01 June 2025 to
15 June 2025 and is expected to resume duties on 16 June 2025.

We fully support this visa application.

Signed: HR Director, {employer}
Official company stamp attached.
[Source: {filename}]"""

    if doc_type == "itinerary":
        return f"""JAPAN TOURIST ITINERARY — 10 DAYS
Traveller: {name}
Declared budget: {budget} VND

Day 1  (01 Jun): Arrive Tokyo Narita 14:20. Transfer to Shinjuku.
                 Hotel: Shinjuku Washington Hotel (Conf# SWH-2025-4421)
Day 2  (02 Jun): Senso-ji Temple & Nakamise-dori, Asakusa (morning).
                 Akihabara electronics district (afternoon).
Day 3  (03 Jun): Tokyo DisneySea (pre-booked ticket #TDS-88821).
Day 4  (04 Jun): Day trip to Nikko — Tosho-gu Shrine (UNESCO).
Day 5  (05 Jun): Shinkansen Nozomi Tokyo→Kyoto (dep 09:00, arr 11:14).
                 Hotel: Dormy Inn Premium Kyoto Ekimae (Conf# DI-KY-77102)
Day 6  (06 Jun): Fushimi Inari Taisha (05:30 sunrise visit).
                 Arashiyama Bamboo Grove & Tenryu-ji Garden.
Day 7  (07 Jun): Nara day trip — Todai-ji Temple, Kasuga Taisha, deer park.
Day 8  (08 Jun): Shinkansen to Osaka. Hotel: APA Hotel Namba (Conf# APA-OS-3312).
                 Dotonbori food tour evening.
Day 9  (09 Jun): Universal Studios Japan (pre-booked Express Pass).
Day 10 (10 Jun): Morning: Shinsaibashi shopping. Depart Kansai Airport 16:30.

Estimated total cost: 41,500,000 VND (accommodation + transport + activities + food)
[Source: {filename}]"""

    if doc_type == "photo":
        return f"""PERSONAL PHOTO VERIFICATION
Subject: {name}
Dimensions: 4 cm × 6 cm
Background: Plain white
Face: Front-facing, neutral expression, fully visible
Lighting: Uniform, no shadows on face
Date taken: November 2024 (within 6 months)
Glasses: None
Compliance: Meets ICAO biometric photo standards for Japan visa
[Source: {filename}]"""

    return f"Document extracted from {filename}"


# ── Pydantic schemas (non-file endpoints) ─────────────────────────

class ReviewRequest(BaseModel):
    decision: str
    notes: str

class AnnouncementRequest(BaseModel):
    announcement_text: str

class ApproveRequest(BaseModel):
    approved_by: str


# ── Cases ────────────────────────────────────────────────────────

@router.post("/cases")
async def submit_case(
    applicant_name:      str           = Form(...),
    nationality:         str           = Form(...),
    occupation:          str           = Form(...),
    employer:            Optional[str] = Form(None),
    monthly_income_vnd:  Optional[str] = Form(None),
    prior_japan_visits:  int           = Form(0),
    prior_refusals:      int           = Form(0),
    declared_budget_vnd: Optional[str] = Form(None),
    trip_duration_days:  Optional[int] = Form(None),
    passport_file:            Optional[UploadFile] = File(None),
    bank_statement_file:      Optional[UploadFile] = File(None),
    employment_letter_file:   Optional[UploadFile] = File(None),
    itinerary_file:           Optional[UploadFile] = File(None),
    photo_file:               Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    ctx = dict(
        applicant_name=applicant_name,
        nationality=nationality,
        occupation=occupation,
        employer=employer,
        monthly_income_vnd=monthly_income_vnd,
        prior_japan_visits=prior_japan_visits,
        prior_refusals=prior_refusals,
        declared_budget_vnd=declared_budget_vnd,
        trip_duration_days=trip_duration_days,
    )

    # Mock OCR for each uploaded file
    file_map = {
        "passport":           (passport_file,          "passport"),
        "bank_statement":     (bank_statement_file,     "bank"),
        "employment_letter":  (employment_letter_file,  "employment"),
        "itinerary":          (itinerary_file,          "itinerary"),
        "photo":              (photo_file,              "photo"),
    }
    for field_key, (upload, doc_type) in file_map.items():
        if upload and upload.filename:
            ctx[f"{field_key}_info"] = mock_ocr(upload.filename, doc_type, ctx)
        else:
            ctx[f"{field_key}_info"] = None

    data = ctx

    db_case = VisaCase(**{k: v for k, v in data.items() if hasattr(VisaCase, k)})
    db_case.status = "processing"
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    try:
        result = VisaPipeline().run(data)
    except Exception as e:
        db_case.status = "error"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Pipeline error: {e}")

    db_case.status          = result.get("status")
    db_case.case_type       = result.get("case_type")
    db_case.risk_level      = result.get("risk_level")
    db_case.summary         = result.get("summary")
    db_case.recommendation  = result.get("recommendation")
    db_case.email_to_user   = result.get("email_to_user")
    db_case.updated_at      = datetime.utcnow()

    stages = result.get("stages", {})
    db_case.gatekeeper_result = stages.get("gatekeeper")
    db_case.inspector_result  = stages.get("inspector")
    db_case.detective_result  = stages.get("detective")
    db_case.navigator_result  = stages.get("navigator")
    db_case.analyst_result    = stages.get("analyst")

    db.commit()
    db.refresh(db_case)

    return {
        "case_id":        db_case.id,
        "status":         db_case.status,
        "case_type":      db_case.case_type,
        "risk_level":     db_case.risk_level,
        "summary":        db_case.summary,
        "recommendation": db_case.recommendation,
        "email_to_user":  db_case.email_to_user,
        "stages":         stages,
    }


@router.get("/cases")
def list_cases(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(VisaCase)
    if status:
        q = q.filter(VisaCase.status == status)
    rows = q.order_by(VisaCase.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id":               r.id,
            "applicant_name":   r.applicant_name,
            "nationality":      r.nationality,
            "occupation":       r.occupation,
            "status":           r.status,
            "case_type":        r.case_type,
            "risk_level":       r.risk_level,
            "recommendation":   r.recommendation,
            "reviewer_decision":r.reviewer_decision,
            "created_at":       r.created_at,
        }
        for r in rows
    ]


@router.get("/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    c = db.query(VisaCase).filter(VisaCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    return {
        "id": c.id, "applicant_name": c.applicant_name, "nationality": c.nationality,
        "occupation": c.occupation, "employer": c.employer,
        "monthly_income_vnd": c.monthly_income_vnd, "prior_japan_visits": c.prior_japan_visits,
        "prior_refusals": c.prior_refusals, "declared_budget_vnd": c.declared_budget_vnd,
        "trip_duration_days": c.trip_duration_days,
        "status": c.status, "case_type": c.case_type, "risk_level": c.risk_level,
        "summary": c.summary, "recommendation": c.recommendation, "email_to_user": c.email_to_user,
        "stages": {
            "gatekeeper": c.gatekeeper_result,
            "inspector":  c.inspector_result,
            "detective":  c.detective_result,
            "navigator":  c.navigator_result,
            "analyst":    c.analyst_result,
        },
        "reviewer_decision": c.reviewer_decision,
        "reviewer_notes":    c.reviewer_notes,
        "reviewed_at":       c.reviewed_at,
        "created_at":        c.created_at,
    }


@router.patch("/cases/{case_id}/review")
def review_case(case_id: int, req: ReviewRequest, db: Session = Depends(get_db)):
    c = db.query(VisaCase).filter(VisaCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    if c.status != "human_review":
        raise HTTPException(status_code=400, detail="Case is not pending human review")
    if req.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be approved or rejected")
    c.reviewer_decision = req.decision
    c.reviewer_notes    = req.notes
    c.reviewed_at       = datetime.utcnow()
    c.status            = req.decision
    c.updated_at        = datetime.utcnow()
    db.commit()
    return {"case_id": case_id, "decision": req.decision}


# ── Policy / Librarian ───────────────────────────────────────────

@router.post("/policies/analyze")
def analyze_announcement(req: AnnouncementRequest, db: Session = Depends(get_db)):
    try:
        result = LibrarianAgent().analyze_announcement(req.announcement_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Librarian error: {e}")

    draft = PolicyDraft(source_text=req.announcement_text, librarian_output=result, status="pending")
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return {"draft_id": draft.id, "result": result}


@router.get("/policies/drafts")
def list_drafts(db: Session = Depends(get_db)):
    drafts = db.query(PolicyDraft).order_by(PolicyDraft.created_at.desc()).all()
    return [
        {
            "id": d.id, "status": d.status, "approved_by": d.approved_by,
            "summary": (d.librarian_output or {}).get("summary", ""),
            "changes_count": len((d.librarian_output or {}).get("changes", [])),
            "librarian_output": d.librarian_output,
            "created_at": d.created_at,
        }
        for d in drafts
    ]


@router.patch("/policies/drafts/{draft_id}/approve")
def approve_draft(draft_id: int, req: ApproveRequest, db: Session = Depends(get_db)):
    draft = db.query(PolicyDraft).filter(PolicyDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != "pending":
        raise HTTPException(status_code=400, detail="Draft already processed")

    changes = (draft.librarian_output or {}).get("changes", [])
    for ch in changes:
        if ch["type"] in ("add", "modify"):
            db.add(PolicyRule(
                category=ch.get("category", "general"),
                rule_text=ch.get("new_rule", ""),
                source=f"Draft #{draft_id}",
                active=True,
            ))
        elif ch["type"] == "remove":
            snippet = ch.get("old_rule", "")[:60]
            for r in db.query(PolicyRule).filter(PolicyRule.active == True).all():
                if snippet and snippet.lower() in r.rule_text.lower():
                    r.active = False

    draft.status      = "approved"
    draft.approved_by = req.approved_by
    draft.approved_at = datetime.utcnow()
    db.commit()
    return {"draft_id": draft_id, "status": "approved", "changes_applied": len(changes)}


@router.patch("/policies/drafts/{draft_id}/reject")
def reject_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(PolicyDraft).filter(PolicyDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    draft.status = "rejected"
    db.commit()
    return {"draft_id": draft_id, "status": "rejected"}


@router.get("/policies/rules")
def list_rules(active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(PolicyRule)
    if active_only:
        q = q.filter(PolicyRule.active == True)
    rules = q.order_by(PolicyRule.category, PolicyRule.created_at).all()
    return [
        {"id": r.id, "category": r.category, "rule_text": r.rule_text,
         "source": r.source, "active": r.active, "created_at": r.created_at}
        for r in rules
    ]
