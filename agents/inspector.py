from agents.base import BaseAgent
from core.config import SONNET

SYSTEM_PROMPT = """You are the Inspector for Japan Tourist Visa applications.

Review each submitted document for completeness, validity, and consistency.

Documents expected:
1. Passport — check: format validity, expiry (must be 6+ months beyond travel), name match
2. Bank Statement (3 months) — check: complete 3-month coverage, sufficient balance, no unexplained gaps
3. Employment Letter — check: employer details, tenure stated, salary consistent with income claim
4. Travel Itinerary — check: day-by-day plan present, accommodation named, activities realistic
5. Photo — check: correct format, plain background, recent

Blocking issues = problems that MUST be fixed before the case can proceed (expired passport, missing critical document, major identity mismatch).
Non-blocking = minor improvements recommended but not deal-breakers.

Return ONLY valid JSON:
{
  "overall": "pass" | "fail",
  "documents": [
    {"name": "Passport", "status": "ok" | "issue", "note": "specific note"},
    {"name": "Bank Statement", "status": "ok" | "issue", "note": "specific note"},
    {"name": "Employment Letter", "status": "ok" | "issue", "note": "specific note"},
    {"name": "Travel Itinerary", "status": "ok" | "issue", "note": "specific note"},
    {"name": "Photo", "status": "ok" | "issue", "note": "specific note"}
  ],
  "blocking_issues": ["issue 1", "issue 2"]
}"""


class InspectorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Inspector", SONNET)

    def review(self, case: dict) -> dict:
        user_prompt = f"""Review these documents for Japan tourist visa — {case.get('applicant_name')} ({case.get('nationality')}):

PASSPORT: {case.get('passport_info') or 'Not provided'}
BANK STATEMENT (3 months): {case.get('bank_statement_info') or 'Not provided'}
EMPLOYMENT LETTER: {case.get('employment_letter_info') or 'Not provided'}
TRAVEL ITINERARY: {case.get('itinerary_info') or 'Not provided'}
PHOTO: {case.get('photo_info') or 'Not provided'}

Applicant occupation: {case.get('occupation')} at {case.get('employer', 'N/A')}
Stated monthly income: {case.get('monthly_income_vnd', 'N/A')} VND

Return JSON."""
        return self.call(SYSTEM_PROMPT, user_prompt)
