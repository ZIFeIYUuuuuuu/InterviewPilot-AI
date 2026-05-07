import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


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
        },
        {
            "name": "Database Cache",
            "tech_stack": ["PostgreSQL"],
            "highlights": ["Used PostgreSQL in a small cache experiment."],
            "evidence_quality": "low",
        },
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


class InterviewPlannerAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

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
        return response.json()

    def test_plan_has_structured_sections_and_gap_driven_focus(self):
        body = self._plan(duration=20, difficulty="medium")
        plan = body["interview_plan"]

        self.assertEqual("targeted_mock", plan["interview_type"])
        self.assertEqual(20, sum(section["duration_minutes"] for section in plan["sections"]))
        self.assertEqual(4, len(plan["sections"]))
        self.assertTrue(all(section["goal"] for section in plan["sections"]))
        self.assertTrue(all(section["focus_topics"] for section in plan["sections"]))
        flattened_focus = " ".join(topic for section in plan["sections"] for topic in section["focus_topics"])
        self.assertIn("Redis", flattened_focus)
        self.assertIn("PostgreSQL", flattened_focus)
        self.assertIn("Backend API", flattened_focus)
        self.assertIn("Create a structured mock interview plan", body["planner_prompt"]["prompt"])

    def test_duration_mapping_changes_section_count(self):
        short_plan = self._plan(duration=15)["interview_plan"]
        long_plan = self._plan(duration=40)["interview_plan"]

        self.assertEqual(3, len(short_plan["sections"]))
        self.assertEqual(5, len(long_plan["sections"]))
        self.assertEqual(15, sum(section["duration_minutes"] for section in short_plan["sections"]))
        self.assertEqual(40, sum(section["duration_minutes"] for section in long_plan["sections"]))

    def test_difficulty_changes_question_budget_and_goals(self):
        easy = self._plan(duration=20, difficulty="easy")["interview_plan"]
        hard = self._plan(duration=20, difficulty="hard")["interview_plan"]

        self.assertLess(easy["max_questions"], hard["max_questions"])
        self.assertIn("基础理解", easy["sections"][0]["goal"])
        self.assertIn("压力测试", hard["sections"][0]["goal"])


if __name__ == "__main__":
    unittest.main()
