import json
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
    "candidate_skills": ["Python", "FastAPI", "PostgreSQL", "Testing"],
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
            "highlights": ["Used PostgreSQL in a small project."],
            "evidence_quality": "low",
        },
    ],
    "strengths": ["Has backend API project evidence."],
    "weaknesses": ["PostgreSQL evidence is thin.", "Resume lacks scale details."],
    "weak_evidence_skills": ["PostgreSQL", "Testing"],
    "resume_summary": "Candidate has backend project evidence with some thin areas.",
    "uncertainty_notes": [],
    "raw_resume_text": "Backend resume...",
}


class GapOptimizationAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_gap_analysis_distinguishes_matched_missing_and_weak_evidence(self):
        response = self.client.post(
            "/api/v1/analysis/gap",
            json={"jd_analysis": JD_ANALYSIS, "resume_analysis": RESUME_ANALYSIS},
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        gap = body["gap_analysis"]
        self.assertIn("Python", gap["matched_skills"])
        self.assertIn("FastAPI", gap["matched_skills"])
        self.assertIn("Redis", gap["missing_skills"])
        self.assertIn("PostgreSQL", gap["weak_evidence_skills"])
        self.assertNotIn("PostgreSQL", gap["missing_skills"])
        self.assertTrue(any("证据偏弱" in topic for topic in gap["high_risk_topics"]))
        self.assertIn("Compare the JD analysis", body["analyzer_prompt"]["prompt"])

    def test_resume_optimization_is_truthful_and_specific(self):
        gap = self.client.post(
            "/api/v1/analysis/gap",
            json={"jd_analysis": JD_ANALYSIS, "resume_analysis": RESUME_ANALYSIS},
        ).json()["gap_analysis"]

        response = self.client.post(
            "/api/v1/analysis/resume-optimization",
            json={
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": gap,
            },
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        optimization = body["resume_optimization"]
        self.assertTrue(optimization["rewrite_targets"])
        self.assertTrue(optimization["bullet_improvement_suggestions"])
        self.assertTrue(any("不要虚构" in warning for warning in optimization["risk_warnings"]))
        self.assertTrue(any("可能被面试追问" in warning for warning in optimization["risk_warnings"]))
        suggestion_text = json.dumps(optimization["bullet_improvement_suggestions"], ensure_ascii=False)
        self.assertNotIn("fake", suggestion_text.casefold())
        self.assertIn("Generate role-specific resume optimization", body["analyzer_prompt"]["prompt"])

    def test_gap_analysis_does_not_treat_weak_evidence_as_missing(self):
        response = self.client.post(
            "/api/v1/analysis/gap",
            json={
                "jd_analysis": {
                    **JD_ANALYSIS,
                    "required_skills": ["Testing"],
                    "preferred_skills": [],
                },
                "resume_analysis": RESUME_ANALYSIS,
            },
        )

        self.assertEqual(200, response.status_code)
        gap = response.json()["gap_analysis"]
        self.assertEqual([], gap["missing_skills"])
        self.assertEqual(["Testing"], gap["weak_evidence_skills"])


if __name__ == "__main__":
    unittest.main()
