from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class VisaCase(Base):
    __tablename__ = "visa_cases"

    id = Column(Integer, primary_key=True, index=True)

    # Applicant profile
    applicant_name       = Column(String(255), nullable=False)
    nationality          = Column(String(100))
    occupation           = Column(String(100))
    employer             = Column(String(255))
    monthly_income_vnd   = Column(String(50))
    prior_japan_visits   = Column(Integer, default=0)
    prior_refusals       = Column(Integer, default=0)
    declared_budget_vnd  = Column(String(50))
    trip_duration_days   = Column(Integer)

    # Documents (text descriptions)
    passport_info           = Column(Text)
    bank_statement_info     = Column(Text)
    employment_letter_info  = Column(Text)
    itinerary_info          = Column(Text)
    photo_info              = Column(Text)

    # Pipeline outcome
    status       = Column(String(50), index=True)   # disqualified | not_ready | auto_approve | human_review | approved | rejected
    case_type    = Column(String(20))                # standard | elevated | complex
    risk_level   = Column(String(20))                # low | medium | high

    # Agent outputs
    gatekeeper_result = Column(JSON)
    inspector_result  = Column(JSON)
    detective_result  = Column(JSON)
    navigator_result  = Column(JSON)
    analyst_result    = Column(JSON)

    # Analyst narrative
    summary        = Column(Text)
    recommendation = Column(Text)
    email_to_user  = Column(Text)
    email_sent     = Column(Boolean, default=False)

    # Human review
    reviewer_decision = Column(String(20))   # approved | rejected
    reviewer_notes    = Column(Text)
    reviewed_at       = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id         = Column(Integer, primary_key=True, index=True)
    category   = Column(String(50))   # financial | eligibility | documents | processing | general
    rule_text  = Column(Text, nullable=False)
    source     = Column(String(255))
    active     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PolicyDraft(Base):
    __tablename__ = "policy_drafts"

    id                = Column(Integer, primary_key=True, index=True)
    source_text       = Column(Text, nullable=False)
    librarian_output  = Column(JSON)
    status            = Column(String(20), default="pending")   # pending | approved | rejected
    approved_by       = Column(String(100))
    approved_at       = Column(DateTime)
    created_at        = Column(DateTime, default=datetime.utcnow)


# ── New visa consulting flow models ──────────────────────────────

class Application(Base):
    __tablename__ = "applications"

    id                 = Column(Integer, primary_key=True, index=True)
    session_id         = Column(String(36), index=True, nullable=False)
    destination        = Column(String(10))          # "japan" | "china"
    profile_json       = Column(JSON)
    eligibility_result = Column(String(20))          # "eligible" | "not_eligible" | "edge_case"
    eligibility_data   = Column(JSON)                # full Haiku response for eligibility
    travel_dates       = Column(JSON)                # {"departure": "YYYY-MM-DD", "return": "YYYY-MM-DD"}
    feasibility_ok     = Column(Boolean, default=False)
    payment_status     = Column(String(30), default="pending")      # "pending" | "demo_completed"
    checklist_json     = Column(JSON)                # cached checklist from Haiku
    submission_status  = Column(String(30), default="pending")      # "pending" | "submitted" | "agency_submitted" | "processing" | "approved" | "rejected" | "quota_rejected"
    submitted_at       = Column(DateTime)
    itinerary_json     = Column(JSON)                # user-confirmed AI-generated itinerary
    extracted_info_json = Column(JSON)               # OCR-extracted personal info from passport/CCCD
    created_at         = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id             = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    doc_type       = Column(String(100), nullable=False)
    file_path      = Column(String(500))
    review_status  = Column(String(30), default="pending")   # "pending" | "pass" | "fail" | "needs_clarification"
    review_notes   = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)
