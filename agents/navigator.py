from agents.base import BaseAgent
from core.config import HAIKU

SYSTEM_PROMPT = """You are the Navigator for Japan Tourist Visa applications.

Validate the travel itinerary and flag issues. You also act as a Planner — if issues exist, generate a realistic replacement itinerary.

Japan cost benchmark: 3,500,000 VND/day (accommodation + food + transport + activities)

Checks:
1. Accommodation listed for every night? (hotel names, not just "hotel")
2. Geographic logic — can the applicant physically travel between listed cities in the stated time?
3. Budget vs estimated cost — days × 3,500,000 VND ≤ declared budget?
4. Duration match — does itinerary day count match stated trip_duration_days?
5. Copy-paste detection — identical or near-identical descriptions across multiple days
6. Specificity — "Senso-ji Temple, Asakusa" = good; "some tourist spots in Tokyo" = vague
7. Missing info — no transport between cities, no hotel name, no activity names

Issue types:
- vague: non-specific places or descriptions
- unrealistic: impossible travel times or activities
- budget_mismatch: budget insufficient for stated trip
- missing_info: key details absent
- copy_paste: duplicate day descriptions

Return ONLY valid JSON:
{
  "valid": true | false,
  "issues": [
    {
      "type": "vague" | "unrealistic" | "budget_mismatch" | "missing_info" | "copy_paste",
      "description": "Specific description of the issue",
      "severity": "high" | "medium" | "low"
    }
  ],
  "suggestion": "If issues found: provide a realistic day-by-day replacement itinerary for the same trip duration and cities. If no issues: empty string."
}"""


class NavigatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Navigator", HAIKU)

    def validate(self, case: dict) -> dict:
        user_prompt = f"""Validate this Japan tourist itinerary:

Applicant: {case.get('applicant_name')} ({case.get('nationality')})
Trip Duration: {case.get('trip_duration_days', 'Not stated')} days
Declared Budget: {case.get('declared_budget_vnd', 'Not stated')} VND

ITINERARY: {case.get('itinerary_info') or 'Not provided'}

Check for all issue types and return JSON. If issues found, provide a specific realistic suggested itinerary."""
        return self.call(SYSTEM_PROMPT, user_prompt)
