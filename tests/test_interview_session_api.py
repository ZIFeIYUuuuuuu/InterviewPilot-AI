import unittest
import os
import tempfile

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.json_store import clear_store_for_tests


JD_ANALYSIS = {
    "role_title": "Backend Engineer",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
    "preferred_skills": ["AWS", "Testing"],
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
            "highlights": ["Built a FastAPI service and explained API boundaries."],
            "evidence_quality": "medium",
        }
    ],
    "strengths": ["Has backend API project evidence."],
    "weaknesses": ["PostgreSQL evidence is thin."],
    "weak_evidence_skills": ["PostgreSQL"],
    "resume_summary": "Candidate has backend project evidence with thin database evidence.",
    "uncertainty_notes": [],
    "raw_resume_text": "Backend resume...",
}

GAP_ANALYSIS = {
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["Redis"],
    "weak_evidence_skills": ["PostgreSQL"],
    "high_risk_topics": [
        "Missing required JD evidence: Redis",
        "Weak resume evidence for JD skill: PostgreSQL",
    ],
    "recommended_focus": ["Redis", "PostgreSQL", "API design"],
    "summary": "Matched 2 skills; Redis missing; PostgreSQL weak.",
}


class InterviewSessionAPITests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["INTERVIEWPILOT_STORE_PATH"] = os.path.join(self.tempdir.name, "store.json")
        clear_store_for_tests()
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("INTERVIEWPILOT_STORE_PATH", None)
        self.tempdir.cleanup()

    def _plan(self, duration=20, difficulty="medium"):
        response = self.client.post(
            "/api/v1/interview/plan",
            json={
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": GAP_ANALYSIS,
                "interview_type": "targeted_mock",
                "difficulty": difficulty,
                "duration_minutes": duration,
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()["interview_plan"]

    def _start(self, duration=20):
        response = self.client.post(
            "/api/v1/interview/sessions",
            json={
                "interview_plan": self._plan(duration=duration),
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": GAP_ANALYSIS,
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def test_start_session_returns_role_and_resume_anchored_question(self):
        body = self._start()
        output = body["interviewer_output"]
        session = body["session"]

        self.assertEqual("in_progress", session["status"])
        self.assertEqual(1, session["current_question_count"])
        self.assertEqual("new_question", output["question_type"])
        self.assertIn("Backend Engineer", output["question"])
        self.assertIn("Backend API", output["question"])
        self.assertIn("Generate the next best interview question", body["interviewer_prompt"]["prompt"])

    def test_short_answer_gets_contextual_follow_up_without_live_score(self):
        body = self._start()
        session_id = body["session"]["session_id"]
        response = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "answer", "answer": "I used it a bit."},
        )
        self.assertEqual(200, response.status_code)
        turn = response.json()
        output = turn["interviewer_output"]

        self.assertEqual("follow_up", output["question_type"])
        self.assertIn("I used it a bit", output["question"])
        self.assertIn("职责", output["question"])
        live_text = " ".join(
            [
                output["question"],
                output["why_this_question"],
                output["expected_signal"],
            ]
        ).casefold()
        self.assertNotIn("score", live_text)

    def test_detailed_answer_moves_to_new_question_and_keeps_state_stable(self):
        body = self._start()
        session_id = body["session"]["session_id"]
        detailed_answer = (
            "In the FastAPI project, I owned the API route boundaries because the service needed "
            "clear validation and test coverage. I designed request schemas, added database access "
            "checks, measured latency around cache reads, and chose a simpler PostgreSQL query path "
            "instead of Redis because the data size was small."
        )
        response = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "answer", "answer": detailed_answer},
        )
        self.assertEqual(200, response.status_code)
        body = response.json()

        self.assertEqual("new_question", body["interviewer_output"]["question_type"])
        self.assertEqual(2, body["session"]["current_question_count"])
        self.assertEqual(3, len(body["session"]["messages"]))

    def test_controls_skip_next_regenerate_and_end(self):
        body = self._start()
        session_id = body["session"]["session_id"]
        first_question = body["interviewer_output"]["question"]

        regenerated = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "regenerate"},
        ).json()
        self.assertEqual(1, regenerated["session"]["current_question_count"])
        self.assertNotEqual(first_question, regenerated["interviewer_output"]["question"])

        skipped = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "skip"},
        ).json()
        self.assertEqual(2, skipped["session"]["current_question_count"])

        moved = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "next"},
        ).json()
        self.assertEqual(3, moved["session"]["current_question_count"])

        ended = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "end"},
        ).json()
        self.assertEqual("completed", ended["session"]["status"])
        self.assertIsNone(ended["interviewer_output"])

    def test_three_to_five_rounds_do_not_corrupt_state(self):
        body = self._start(duration=20)
        session_id = body["session"]["session_id"]
        for index in range(4):
            response = self.client.post(
                f"/api/v1/interview/sessions/{session_id}/turn",
                json={
                    "action": "answer",
                    "answer": (
                        f"Round {index}: I designed an API because FastAPI schemas helped validation, "
                        "tested database behavior, measured latency, and explained the trade-off."
                    ),
                },
            )
            self.assertEqual(200, response.status_code)
            body = response.json()
            self.assertGreaterEqual(body["session"]["current_section_index"], 0)
            self.assertLess(
                body["session"]["current_section_index"],
                len(body["session"]["interview_plan"]["sections"]),
            )

        session = self.client.get(f"/api/v1/interview/sessions/{session_id}").json()
        self.assertEqual(body["session"]["current_question_count"], session["current_question_count"])
        self.assertGreaterEqual(len(session["messages"]), 5)


if __name__ == "__main__":
    unittest.main()
