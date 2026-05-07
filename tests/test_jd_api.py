import base64
import unittest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.jd import JDInputRequest, JDInputType
from backend.app.services.jd_analyzer import analyze_jd_input


class JDAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_text_jd_analyze_returns_structured_analysis_and_prompt(self):
        response = self.client.post(
            "/api/v1/jd/analyze",
            json={
                "input_type": "text",
                "text": (
                    "Backend Engineer\n"
                    "Requirements: Python, FastAPI, PostgreSQL, Redis, Docker.\n"
                    "Responsibilities: build reliable APIs and optimize database performance.\n"
                    "Preferred: AWS and CI/CD experience."
                ),
            },
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("extracted", body["extraction"]["status"])
        self.assertEqual("Backend Engineer", body["analysis"]["role_title"])
        self.assertIn("Python", body["analysis"]["required_skills"])
        self.assertIn("AWS", body["analysis"]["preferred_skills"])
        self.assertIn("Analyze the provided job description", body["analyzer_prompt"]["prompt"])

    def test_low_quality_text_does_not_interrupt_flow(self):
        result = analyze_jd_input(JDInputRequest(input_type=JDInputType.text, text="Python role"))

        self.assertTrue(result.needs_manual_correction)
        self.assertEqual("目标岗位", result.analysis.role_title)
        self.assertTrue(result.analysis.uncertainty_notes)

    def test_image_without_ocr_degrades_to_manual_correction(self):
        response = self.client.post(
            "/api/v1/jd/analyze",
            json={"input_type": "image", "content_base64": base64.b64encode(b"fake image").decode()},
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("manual_required", body["extraction"]["status"])
        self.assertTrue(body["needs_manual_correction"])
        self.assertEqual([], body["analysis"]["required_skills"])

    def test_pdf_with_text_fallback_is_accepted_as_partial_extraction(self):
        response = self.client.post(
            "/api/v1/jd/analyze",
            json={
                "input_type": "pdf",
                "filename": "jd.pdf",
                "text": "Full Stack Developer\nRequirements: TypeScript, React, Node.js.",
            },
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("partial", body["extraction"]["status"])
        self.assertIn("TypeScript", body["analysis"]["required_skills"])
        self.assertIn("降级内容", " ".join(body["extraction"]["warnings"]))

    def test_preview_and_manual_correction_entrypoint(self):
        created = self.client.post(
            "/api/v1/jd/analyze",
            json={"input_type": "text", "text": "Backend Engineer\nRequirements: Python."},
        ).json()
        analysis_id = created["analysis_id"]

        preview = self.client.get(f"/api/v1/jd/analyses/{analysis_id}/preview")
        self.assertEqual(200, preview.status_code)
        self.assertIn("role_title", preview.json()["editable_fields"])

        corrected = self.client.patch(
            f"/api/v1/jd/analyses/{analysis_id}/correction",
            json={
                "role_title": "Backend Engineer",
                "required_skills": ["Python", "FastAPI"],
                "preferred_skills": [],
                "responsibilities": ["Build APIs"],
                "interview_focus": ["API design"],
                "uncertainty_notes": ["Manually corrected by user."],
                "raw_jd_text": "Backend Engineer\nRequirements: Python.",
            },
        )

        self.assertEqual(200, corrected.status_code)
        self.assertTrue(corrected.json()["manually_corrected"])
        self.assertEqual(["Python", "FastAPI"], corrected.json()["analysis"]["required_skills"])


if __name__ == "__main__":
    unittest.main()
