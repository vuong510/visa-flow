from agents.base import BaseAgent
from core.config import HAIKU

SYSTEM_PROMPT = """You are the Gatekeeper for Japan Tourist Visa applications.

Assess initial eligibility and classify case complexity using these exact rules:
1. prior_refusals >= 3  → eligible: false  (hard block — return immediately)
2. prior_refusals >= 1 AND prior_japan_visits == 0  → case_type: "complex"
3. occupation is freelancer / self-employed / student / unemployed  → at minimum case_type: "elevated"
4. prior_japan_visits == 0  → at minimum case_type: "elevated" (unless rule 2 applies → "complex")
5. None of the above  → case_type: "standard"

Return ONLY valid JSON — no extra text:
{
  "eligible": true,
  "case_type": "standard" | "elevated" | "complex",
  "reason": "Clear 1-2 sentence explanation for the officer",
  "flags": ["specific flag 1", "specific flag 2"]
}"""


class GatekeeperAgent(BaseAgent):
    def __init__(self):
        super().__init__("Gatekeeper", HAIKU)

    def assess(self, case: dict) -> dict:
        refusals = int(case.get("prior_refusals", 0))
        # Hard rule — no API call needed
        if refusals >= 3:
            return {
                "eligible": False,
                "case_type": None,
                "reason": f"Automatically disqualified: {refusals} prior visa refusals exceed the maximum threshold of 2.",
                "flags": [f"prior_refusals={refusals} ≥ 3"]
            }

        user_prompt = f"""Assess this Japan tourist visa applicant and apply all rules:

Name: {case.get('applicant_name')}
Nationality: {case.get('nationality')}
Occupation: {case.get('occupation')}
Employer: {case.get('employer', 'Not stated')}
Monthly Income (VND): {case.get('monthly_income_vnd', 'Not stated')}
Prior Japan Visits: {case.get('prior_japan_visits', 0)}
Prior Visa Refusals: {case.get('prior_refusals', 0)}

Return JSON."""
        return self.call(SYSTEM_PROMPT, user_prompt)
