import concurrent.futures
from agents.gatekeeper import GatekeeperAgent
from agents.inspector import InspectorAgent
from agents.detective import DetectiveAgent
from agents.navigator import NavigatorAgent
from agents.analyst import AnalystAgent


class VisaPipeline:
    def __init__(self):
        self.gatekeeper = GatekeeperAgent()
        self.inspector = InspectorAgent()
        self.detective = DetectiveAgent()
        self.navigator = NavigatorAgent()
        self.analyst = AnalystAgent()

    def run(self, case: dict) -> dict:
        stages = {}

        # ── Stage 1: Gatekeeper ──────────────────────────────────
        gk = self.gatekeeper.assess(case)
        stages["gatekeeper"] = gk
        if not gk.get("eligible", True):
            return {"status": "disqualified", "case_type": None, "risk_level": None, "stages": stages}

        case_type = gk.get("case_type", "standard")

        # ── Stage 2: Inspector ───────────────────────────────────
        insp = self.inspector.review(case)
        stages["inspector"] = insp
        if insp.get("overall") == "fail" and insp.get("blocking_issues"):
            return {"status": "not_ready", "case_type": case_type, "risk_level": None, "stages": stages}

        # ── Stage 3: Detective + Navigator (parallel) ────────────
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            det_future = pool.submit(self.detective.investigate, case)
            nav_future = pool.submit(self.navigator.validate, case)
            det = det_future.result()
            nav = nav_future.result()

        stages["detective"] = det
        stages["navigator"] = nav

        # ── Stage 4: Analyst ─────────────────────────────────────
        analyst = self.analyst.analyze(case, gk, insp, det, nav)
        stages["analyst"] = analyst

        # ── Pipeline decision rule ───────────────────────────────
        risk_level = det.get("risk_level", "high")
        if risk_level == "low" and case_type != "complex":
            status = "auto_approve"
        else:
            status = "human_review"

        return {
            "status": status,
            "case_type": case_type,
            "risk_level": risk_level,
            "summary": analyst.get("summary", ""),
            "recommendation": analyst.get("recommendation", ""),
            "email_to_user": analyst.get("email_to_user", ""),
            "stages": stages,
        }
