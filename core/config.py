from dotenv import load_dotenv
import os
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visa_flow.db")
SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"
