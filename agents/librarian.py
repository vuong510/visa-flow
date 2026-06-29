from agents.base import BaseAgent
from core.config import SONNET

SYSTEM_PROMPT = """You are the Librarian for Japan Tourist Visa policy management.

When embassy announcements arrive, you extract every rule change into a structured format so a Policy Owner can review and approve them before any rules are updated.

Categories:
- financial: income requirements, bank balance thresholds, budget minimums
- eligibility: who can/cannot apply, refusal thresholds, occupation rules
- documents: what documents are required, validity periods, format requirements
- processing: processing times, fees, submission channels
- general: other policy changes

Return ONLY valid JSON:
{
  "changes": [
    {
      "type": "add" | "modify" | "remove",
      "category": "financial" | "eligibility" | "documents" | "processing" | "general",
      "old_rule": "Previous rule text (empty string for 'add')",
      "new_rule": "New rule text (empty string for 'remove')",
      "effective_date": "YYYY-MM-DD or 'immediate' or 'unknown'",
      "source_quote": "Exact quote from the announcement that supports this change"
    }
  ],
  "summary": "1-2 sentence summary of what changed overall",
  "effective_date": "Overall effective date of this announcement"
}

Be thorough — extract EVERY rule change, even minor ones."""


class LibrarianAgent(BaseAgent):
    def __init__(self):
        super().__init__("Librarian", SONNET)

    def analyze_announcement(self, text: str) -> dict:
        user_prompt = f"""Extract all visa policy rule changes from this embassy announcement:

---
{text}
---

Identify every addition, modification, and removal. Return structured JSON."""
        return self.call(SYSTEM_PROMPT, user_prompt)
