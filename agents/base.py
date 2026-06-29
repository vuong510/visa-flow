import anthropic
import json
import re
from core.config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class BaseAgent:
    def __init__(self, name, model):
        self.name = name
        self.model = model

    def call(self, system_prompt, user_prompt):
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt + "\n\nIMPORTANT: Return only valid, complete JSON. No extra text.",
            messages=[{"role": "user", "content": user_prompt}]
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
        # Extract first JSON object if there's surrounding text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        return json.loads(text)
