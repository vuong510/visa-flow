from agents.base import BaseAgent
from core.config import SONNET

SYSTEM_PROMPT = """You are the Analyst for Japan Tourist Visa applications.

You synthesize ALL agent findings into one coherent assessment for the visa officer. You NEVER make the final decision — humans do.

CRITICAL RULES:
- "recommendation" field must NEVER contain the words "approve" or "reject"
- Only use: "proceed with caution", "address [specific issue] before proceeding", "refer to senior reviewer"
- overall_status is set by the pipeline rules — your job is the narrative

You also write ONE consolidated email to the applicant combining ALL issues (financial + itinerary + documents) into a single clear communication.

Return ONLY valid JSON:
{
  "overall_status": "auto_approve" | "human_review" | "not_ready",
  "risk_level": "low" | "medium" | "high",
  "summary": "3-4 sentence executive summary for the visa officer — factual, no recommendation language",
  "blocking_issues": ["critical issues that must be resolved"],
  "risk_flags": ["notable risk flags for officer attention"],
  "recommendation": "proceed with caution | address [X] before proceeding | refer to senior reviewer",
  "email_to_user": "Full email text to applicant. Must: combine ALL financial + itinerary issues in one email, list specific actions needed, be professional but clear, NOT use the word approve/reject/decision. Sign off: Japan Visa Processing Team"
}"""


class AnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__("Analyst", SONNET)

    def analyze(
        self,
        case: dict,
        gatekeeper: dict,
        inspector: dict,
        detective: dict,
        navigator: dict,
    ) -> dict:
        user_prompt = f"""Synthesize this Japan tourist visa assessment for the officer:

APPLICANT: {case.get('applicant_name')}, {case.get('nationality')}, {case.get('occupation')}
CASE TYPE: {gatekeeper.get('case_type')}
GATEKEEPER FLAGS: {gatekeeper.get('flags', [])}

INSPECTOR: overall={inspector.get('overall')}
  Issues: {[d for d in inspector.get('documents', []) if d.get('status') == 'issue']}
  Blocking: {inspector.get('blocking_issues', [])}

DETECTIVE: risk={detective.get('risk_level')}, consistent={detective.get('consistent')}
  Contradictions: {detective.get('contradictions', [])}

NAVIGATOR: valid={navigator.get('valid')}
  Issues: {navigator.get('issues', [])}
  Suggested itinerary: {'Yes — available' if navigator.get('suggestion') else 'None'}

Write a comprehensive assessment and consolidated applicant email. Return JSON."""
        return self.call(SYSTEM_PROMPT, user_prompt)
