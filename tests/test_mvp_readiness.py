import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.json_store import clear_store_for_tests


FORBIDDEN_REPORT_TERMS = ("pass/fail", "hire/no-hire", "offer decision", "reject")


class MVPReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["INTERVIEWPILOT_STORE_PATH"] = os.path.join(self.tempdir.name, "store.json")
        clear_store_for_tests()
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("INTERVIEWPILOT_STORE_PATH", None)
        self.tempdir.cleanup()

    def test_complete_text_flow_generates_demo_safe_report(self):
        jd = self.client.post(
            "/api/v1/jd/analyze",
            json={
                "input_type": "text",
                "text": (
                    "Backend Engineer\n"
                    "Required: Python, FastAPI, PostgreSQL, Redis.\n"
                    "Responsibilities: build reliable APIs and reason about caching."
                ),
            },
        ).json()["analysis"]
        resume = self.client.post(
            "/api/v1/resume/analyze",
            json={
                "input_type": "text",
                "text": (
                    "Backend API Project\n"
                    "Built a FastAPI service with Python and PostgreSQL. "
                    "Designed request schemas and tested API behavior."
                ),
            },
        ).json()["analysis"]
        gap = self.client.post(
            "/api/v1/analysis/gap",
            json={"jd_analysis": jd, "resume_analysis": resume},
        ).json()["gap_analysis"]
        plan = self.client.post(
            "/api/v1/interview/plan",
            json={
                "jd_analysis": jd,
                "resume_analysis": resume,
                "gap_analysis": gap,
                "duration_minutes": 20,
                "difficulty": "medium",
                "interview_type": "targeted_mock",
            },
        ).json()["interview_plan"]
        live = self.client.post(
            "/api/v1/interview/sessions",
            json={
                "interview_plan": plan,
                "jd_analysis": jd,
                "resume_analysis": resume,
                "gap_analysis": gap,
            },
        ).json()["session"]
        session_id = live["session_id"]
        self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={
                "action": "answer",
                "answer": (
                    "In my FastAPI project, I designed API route boundaries because validation "
                    "and maintainability mattered. I implemented schemas, tested PostgreSQL access, "
                    "and described Redis as a ramp-up topic rather than overstating experience."
                ),
            },
        )
        self.client.post(f"/api/v1/interview/sessions/{session_id}/turn", json={"action": "end"})
        report = self.client.post(f"/api/v1/reports/sessions/{session_id}", json={}).json()["report"]

        self.assertIn("不代表招聘", report["disclaimer"])
        report_text = str(report).casefold()
        for term in FORBIDDEN_REPORT_TERMS:
            self.assertNotIn(term, report_text)
        self.assertTrue(report["coaching"]["practice_plan"])
        self.assertEqual(
            {
                "technical_accuracy",
                "depth",
                "structure",
                "communication",
                "role_fit",
                "evidence_quality",
            },
            set(report["evaluation"]["dimension_scores"]),
        )

    def test_incomplete_jd_input_degrades_without_blocking_manual_correction(self):
        response = self.client.post(
            "/api/v1/jd/analyze",
            json={"input_type": "image", "filename": "unreadable-jd.png"},
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertTrue(body["needs_manual_correction"])
        self.assertEqual("manual_required", body["extraction"]["status"])
        self.assertTrue(body["analysis"]["uncertainty_notes"])


if __name__ == "__main__":
    unittest.main()
