import unittest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.resume import ResumeInputRequest, ResumeInputType
from backend.app.services.resume_analyzer import analyze_resume_input


class ResumeAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_text_resume_analyze_returns_structured_evidence(self):
        response = self.client.post(
            "/api/v1/resume/analyze",
            json={
                "input_type": "text",
                "text": (
                    "Backend API Project: Built a FastAPI service with PostgreSQL and Redis caching.\n"
                    "Implemented REST APIs, Docker deployment, and reduced lookup latency by 35%.\n"
                    "Skills: Python, FastAPI, PostgreSQL, Redis, Docker, REST API, Testing."
                ),
            },
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("extracted", body["extraction"]["status"])
        self.assertIn("Python", body["analysis"]["candidate_skills"])
        self.assertGreaterEqual(len(body["analysis"]["projects"]), 1)
        self.assertIn("Analyze the candidate resume", body["analyzer_prompt"]["prompt"])

    def test_resume_analysis_is_conservative_for_thin_evidence(self):
        result = analyze_resume_input(
            ResumeInputRequest(input_type=ResumeInputType.text, text="Skills: Python, Redis.")
        )

        self.assertTrue(result.needs_manual_correction)
        self.assertIn("Python", result.analysis.candidate_skills)
        self.assertEqual([], result.analysis.projects)
        self.assertTrue(result.analysis.weaknesses)
        self.assertIn("Gap Analysis", " ".join(result.analysis.uncertainty_notes))

    def test_empty_resume_does_not_interrupt_flow(self):
        response = self.client.post("/api/v1/resume/analyze", json={"input_type": "text", "text": ""})

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("manual_required", body["extraction"]["status"])
        self.assertTrue(body["needs_manual_correction"])
        self.assertEqual([], body["analysis"]["candidate_skills"])
        self.assertIn("没有可用的简历文本", body["analysis"]["resume_summary"])

    def test_pdf_resume_input_accepts_text_fallback(self):
        response = self.client.post(
            "/api/v1/resume/analyze",
            json={
                "input_type": "pdf",
                "filename": "resume.pdf",
                "text": "Project: Built a Python API.\nSkills: Python, FastAPI.",
            },
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("partial", body["extraction"]["status"])
        self.assertIn("Python", body["analysis"]["candidate_skills"])
        self.assertIn("降级内容", " ".join(body["extraction"]["warnings"]))

    def test_image_resume_input_requires_text_fallback_without_ocr(self):
        response = self.client.post(
            "/api/v1/resume/analyze",
            json={"input_type": "image", "filename": "resume.png", "content_base64": "ZmFrZQ=="},
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("manual_required", body["extraction"]["status"])
        self.assertTrue(body["needs_manual_correction"])
        self.assertIn("图片 OCR", " ".join(body["extraction"]["warnings"]))

    def test_image_resume_input_accepts_manual_text_fallback(self):
        response = self.client.post(
            "/api/v1/resume/analyze",
            json={
                "input_type": "image",
                "filename": "resume.png",
                "text": "项目：使用 Python 和 FastAPI 构建后端 API。\n技能：Python、FastAPI。",
            },
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("partial", body["extraction"]["status"])
        self.assertIn("Python", body["analysis"]["candidate_skills"])

    def test_pdf_without_text_requires_manual_resume_text(self):
        response = self.client.post(
            "/api/v1/resume/analyze",
            json={"input_type": "pdf", "filename": "resume.pdf", "content_base64": "ZmFrZQ=="},
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("manual_required", body["extraction"]["status"])
        self.assertTrue(body["needs_manual_correction"])

    def test_preview_and_manual_correction_entrypoint(self):
        created = self.client.post(
            "/api/v1/resume/analyze",
            json={"input_type": "text", "text": "Project: Built a Python API.\nSkills: Python."},
        ).json()
        analysis_id = created["analysis_id"]

        preview = self.client.get(f"/api/v1/resume/analyses/{analysis_id}/preview")
        self.assertEqual(200, preview.status_code)
        self.assertIn("candidate_skills", preview.json()["editable_fields"])

        corrected = self.client.patch(
            f"/api/v1/resume/analyses/{analysis_id}/correction",
            json={
                "candidate_skills": ["Python", "FastAPI"],
                "projects": [
                    {
                        "name": "Backend API",
                        "tech_stack": ["Python", "FastAPI"],
                        "highlights": ["Built a small API service."],
                        "evidence_quality": "medium",
                    }
                ],
                "strengths": ["Has backend project evidence."],
                "weaknesses": ["Limited scale evidence."],
                "weak_evidence_skills": ["FastAPI"],
                "resume_summary": "Candidate has one backend API project.",
                "uncertainty_notes": ["Manually corrected by user."],
                "raw_resume_text": "Project: Built a Python API.\nSkills: Python.",
            },
        )

        self.assertEqual(200, corrected.status_code)
        self.assertTrue(corrected.json()["manually_corrected"])
        self.assertEqual(["Python", "FastAPI"], corrected.json()["analysis"]["candidate_skills"])


if __name__ == "__main__":
    unittest.main()
