import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.json_store import clear_store_for_tests


JD_ANALYSIS = {
    "role_title": "Backend Engineer",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
    "preferred_skills": ["Testing"],
    "responsibilities": ["Build reliable APIs and optimize data access."],
    "interview_focus": ["API design", "Database trade-offs"],
    "uncertainty_notes": [],
    "raw_jd_text": "Backend Engineer requirements...",
}

RESUME_ANALYSIS = {
    "candidate_skills": ["Python", "FastAPI", "PostgreSQL"],
    "projects": [
        {
            "name": "Backend API",
            "tech_stack": ["Python", "FastAPI"],
            "highlights": ["Built FastAPI routes and discussed API boundaries."],
            "evidence_quality": "medium",
        }
    ],
    "strengths": ["Has backend API project evidence."],
    "weaknesses": ["Redis is not evidenced."],
    "weak_evidence_skills": ["PostgreSQL"],
    "resume_summary": "Backend project evidence with thin database depth.",
    "uncertainty_notes": [],
    "raw_resume_text": "Backend resume...",
}

GAP_ANALYSIS = {
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["Redis"],
    "weak_evidence_skills": ["PostgreSQL"],
    "high_risk_topics": ["Missing required JD evidence: Redis"],
    "recommended_focus": ["Redis", "PostgreSQL", "API design"],
    "summary": "Redis is missing and PostgreSQL evidence is weak.",
}


class SessionPersistenceAPITests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["INTERVIEWPILOT_STORE_PATH"] = os.path.join(self.tempdir.name, "store.json")
        clear_store_for_tests()
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("INTERVIEWPILOT_STORE_PATH", None)
        self.tempdir.cleanup()

    def _create_product_session(self):
        response = self.client.post(
            "/api/v1/sessions",
            json={
                "input": {
                    "target_role": "Backend Engineer",
                    "jd": {"text": "Backend Engineer JD", "source_type": "text"},
                    "resume": {"text": "Backend resume", "source_type": "text"},
                    "interview_type": "targeted_mock",
                    "difficulty": "medium",
                    "duration_minutes": 20,
                }
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()["session"]

    def _plan(self):
        response = self.client.post(
            "/api/v1/interview/plan",
            json={
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": GAP_ANALYSIS,
                "interview_type": "targeted_mock",
                "difficulty": "medium",
                "duration_minutes": 20,
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()["interview_plan"]

    def _completed_interview_session(self, session_id):
        plan = self._plan()
        return {
            "session_id": session_id,
            "status": "completed",
            "interview_plan": plan,
            "jd_analysis": JD_ANALYSIS,
            "resume_analysis": RESUME_ANALYSIS,
            "gap_analysis": GAP_ANALYSIS,
            "messages": [
                {
                    "role": "interviewer",
                    "content": "How does your Backend API project map to FastAPI?",
                    "section": plan["sections"][0]["name"],
                },
                {
                    "role": "candidate",
                    "content": (
                        "In the Backend API project, I designed FastAPI route boundaries because "
                        "validation and maintainability mattered. I implemented schemas, tested "
                        "PostgreSQL behavior, measured latency, and chose not to add Redis because "
                        "the data volume was small."
                    ),
                    "section": plan["sections"][0]["name"],
                },
            ],
            "current_section_index": 0,
            "current_question_count": 1,
            "latest_question": {
                "question_type": "new_question",
                "current_section": plan["sections"][0]["name"],
                "question": "How does your Backend API project map to FastAPI?",
                "why_this_question": "It checks role fit.",
                "expected_signal": "Concrete implementation evidence.",
            },
            "last_action": "end",
        }

    def test_session_lifecycle_report_read_and_history(self):
        session = self._create_product_session()
        session_id = session["session_id"]
        self.assertEqual("draft", session["status"])

        update = self.client.patch(
            f"/api/v1/sessions/{session_id}",
            json={
                "status": "interview_ready",
                "current_step": "interview_planning",
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": GAP_ANALYSIS,
                "interview_plan": self._plan(),
            },
        )
        self.assertEqual(200, update.status_code)
        self.assertEqual("interview_ready", update.json()["session"]["status"])

        report_response = self.client.post(
            "/api/v1/reports/generate",
            json={
                "interview_session": self._completed_interview_session(session_id),
                "resume_optimization": None,
            },
        )
        self.assertEqual(200, report_response.status_code)
        stored_report = report_response.json()["stored_report"]
        report_id = stored_report["report_id"]

        report_read = self.client.get(f"/api/v1/reports/{report_id}")
        self.assertEqual(200, report_read.status_code)
        self.assertEqual(report_id, report_read.json()["report_id"])

        latest_read = self.client.get(f"/api/v1/reports/sessions/{session_id}/latest")
        self.assertEqual(200, latest_read.status_code)
        self.assertEqual(report_id, latest_read.json()["report_id"])

        finish = self.client.post(
            f"/api/v1/sessions/{session_id}/finish",
            json={"report_id": report_id},
        )
        self.assertEqual(200, finish.status_code)
        finished = finish.json()["session"]
        self.assertEqual("report_ready", finished["status"])
        self.assertEqual("report", finished["current_step"])
        self.assertEqual(report_id, finished["report"]["report_id"])

        history = self.client.get("/api/v1/sessions").json()["items"]
        self.assertEqual(1, len(history))
        self.assertEqual(session_id, history[0]["session_id"])
        self.assertEqual(report_id, history[0]["latest_report_id"])
        self.assertIsInstance(history[0]["overall_score"], int)
        self.assertTrue(history[0]["weak_area_summary"])

    def test_session_routes_return_basic_errors(self):
        missing = self.client.get("/api/v1/sessions/session_missing")
        self.assertEqual(404, missing.status_code)

        finish_missing_report = self.client.post(
            f"/api/v1/sessions/{self._create_product_session()['session_id']}/finish",
            json={"report_id": "report_missing"},
        )
        self.assertEqual(404, finish_missing_report.status_code)


if __name__ == "__main__":
    unittest.main()
