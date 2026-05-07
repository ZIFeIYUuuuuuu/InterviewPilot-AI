import unittest
import os
import tempfile

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

RESUME_OPTIMIZATION = {
    "optimization_summary": "Make backend API evidence more concrete without adding unsupported claims.",
    "rewrite_targets": ["Backend API project"],
    "bullet_improvement_suggestions": [
        {
            "original_issue": "API project impact is vague.",
            "why_it_is_weak": "The bullet does not show ownership or constraints.",
            "suggested_direction": "Clarify owned API boundaries and validation choices if true.",
            "example_rewrite": "If true, describe the FastAPI route boundaries and validation decisions.",
        }
    ],
    "skill_positioning_suggestions": ["Position FastAPI near API design evidence."],
    "risk_warnings": ["If Redis is listed later, prepare truthful evidence or say it is a ramp-up area."],
}


class ReportAPITests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["INTERVIEWPILOT_STORE_PATH"] = os.path.join(self.tempdir.name, "store.json")
        clear_store_for_tests()
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("INTERVIEWPILOT_STORE_PATH", None)
        self.tempdir.cleanup()

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

    def _completed_session_id(self):
        start = self.client.post(
            "/api/v1/interview/sessions",
            json={
                "interview_plan": self._plan(),
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": GAP_ANALYSIS,
            },
        )
        self.assertEqual(200, start.status_code)
        session_id = start.json()["session"]["session_id"]
        answer = (
            "In the Backend API project, I designed FastAPI route boundaries because validation "
            "and maintainability mattered. I implemented schemas, tested database behavior with "
            "PostgreSQL, measured latency, and chose not to add Redis because the data volume was "
            "small. The result was a simpler API that I could explain and test clearly."
        )
        turn = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "answer", "answer": answer},
        )
        self.assertEqual(200, turn.status_code)
        end = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "end"},
        )
        self.assertEqual(200, end.status_code)
        return session_id

    def test_generate_report_from_completed_session(self):
        session_id = self._completed_session_id()
        response = self.client.post(
            f"/api/v1/reports/sessions/{session_id}",
            json={"resume_optimization": RESUME_OPTIMIZATION},
        )
        self.assertEqual(200, response.status_code)
        body = response.json()
        report = body["report"]
        evaluation = report["evaluation"]
        coaching = report["coaching"]

        self.assertEqual(session_id, report["session_id"])
        self.assertGreaterEqual(evaluation["overall_score"], 0)
        self.assertLessEqual(evaluation["overall_score"], 100)
        self.assertIn("不代表招聘", report["disclaimer"])
        self.assertIn("Evaluate the completed mock interview", body["evaluator_prompt"]["prompt"])
        self.assertIn("Turn the interview evaluation", body["coach_prompt"]["prompt"])

        dimensions = evaluation["dimension_scores"]
        self.assertEqual(
            {
                "technical_accuracy",
                "depth",
                "structure",
                "communication",
                "role_fit",
                "evidence_quality",
            },
            set(dimensions.keys()),
        )
        for dimension in dimensions.values():
            self.assertIsInstance(dimension["score"], int)
            self.assertTrue(dimension["reason"])

        self.assertTrue(coaching["top_improvements"])
        self.assertTrue(coaching["practice_plan"])
        self.assertIn("Redis", " ".join(evaluation["risk_flags"] + coaching["next_round_focus"]))

    def test_report_rejects_in_progress_session(self):
        start = self.client.post(
            "/api/v1/interview/sessions",
            json={
                "interview_plan": self._plan(),
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": GAP_ANALYSIS,
            },
        )
        session_id = start.json()["session"]["session_id"]
        response = self.client.post(f"/api/v1/reports/sessions/{session_id}", json={})

        self.assertEqual(409, response.status_code)
        self.assertIn("完成模拟面试", response.json()["detail"])

    def test_generate_report_from_supplied_session_state(self):
        session_id = self._completed_session_id()
        session = self.client.get(f"/api/v1/interview/sessions/{session_id}").json()
        response = self.client.post(
            "/api/v1/reports/generate",
            json={"interview_session": session, "resume_optimization": None},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(session_id, response.json()["report"]["session_id"])

    def test_generated_report_avoids_recruiter_style_verdict_terms(self):
        session_id = self._completed_session_id()
        body = self.client.post(f"/api/v1/reports/sessions/{session_id}", json={}).json()
        user_visible_report = body["report"]
        text = str(user_visible_report).casefold()

        self.assertNotIn("pass/fail", text)
        self.assertNotIn("reject", text)
        self.assertNotIn("offer decision", text)


if __name__ == "__main__":
    unittest.main()
