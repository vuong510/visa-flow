from agents.base import BaseAgent
from core.config import SONNET

SYSTEM_PROMPT = """You are the Detective for Japan Tourist Visa applications.

Find financial and documentary inconsistencies that may indicate fraud or elevated risk.

Checks to perform:
1. Monthly income vs bank balance — 3× monthly income should be close to average balance
2. Declared travel budget vs available funds — budget must be coverable from savings
3. Large suspicious cash withdrawals in last 3 months — flag anything > 30% of balance in one transaction
4. Employment tenure vs bank statement start date — if employed 6 months but statement shows 2 years, flag it
5. Bank statement gaps — missing months, irregular deposit patterns
6. Employer name consistency across employment letter and bank deposits
7. Regular salary deposits matching stated income (±20% tolerance)

Japan cost benchmark: 3,500,000 VND/day minimum

Severity:
- high: strong fraud indicator or major financial gap
- medium: inconsistency worth flagging but explainable
- low: minor discrepancy

Return ONLY valid JSON:
{
  "consistent": true | false,
  "risk_level": "low" | "medium" | "high",
  "contradictions": [
    {
      "field_a": "field name",
      "value_a": "value",
      "field_b": "field name",
      "value_b": "value",
      "severity": "high" | "medium" | "low",
      "description": "What this inconsistency means"
    }
  ]
}"""


class DetectiveAgent(BaseAgent):
    def __init__(self):
        super().__init__("Detective", SONNET)

    def investigate(self, case: dict) -> dict:
        user_prompt = f"""Investigate financial consistency for Japan tourist visa:

Applicant: {case.get('applicant_name')}
Occupation: {case.get('occupation')}
Employer: {case.get('employer', 'Not stated')}
Monthly Income (VND): {case.get('monthly_income_vnd', 'Not stated')}
Declared Budget (VND): {case.get('declared_budget_vnd', 'Not stated')}
Trip Duration: {case.get('trip_duration_days', 'Not stated')} days

EMPLOYMENT LETTER: {case.get('employment_letter_info') or 'Not provided'}
BANK STATEMENT (3 months): {case.get('bank_statement_info') or 'Not provided'}
TRAVEL ITINERARY: {case.get('itinerary_info') or 'Not provided'}

Find all contradictions and return JSON."""
        return self.call(SYSTEM_PROMPT, user_prompt)
