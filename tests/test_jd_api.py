import base64
from io import BytesIO
import unittest

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend.app.main import app
from backend.app.schemas.jd import JDInputRequest, JDInputType
from backend.app.services.jd_analyzer import analyze_jd_input
from backend.app.services.ocr import pymupdf_ocr_available


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

    def test_image_jd_attempts_ocr_or_returns_structured_fallback(self):
        response = self.client.post(
            "/api/v1/jd/analyze",
            json={"input_type": "image", "filename": "jd.png", "content_base64": _make_jd_image_base64()},
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        if pymupdf_ocr_available() and body["extraction"]["raw_text"]:
            self.assertEqual("partial", body["extraction"]["status"])
            self.assertIn("Python", body["extraction"]["raw_text"])
            self.assertIn("OCR", " ".join(body["extraction"]["warnings"]))
        else:
            self.assertEqual("manual_required", body["extraction"]["status"])
            self.assertTrue(body["needs_manual_correction"])
            self.assertIn("OCR", " ".join(body["extraction"]["warnings"]))

    def test_scanned_pdf_jd_attempts_ocr_or_returns_structured_fallback(self):
        response = self.client.post(
            "/api/v1/jd/analyze",
            json={"input_type": "pdf", "filename": "jd.pdf", "content_base64": _make_image_only_pdf_base64()},
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        if pymupdf_ocr_available() and body["extraction"]["raw_text"]:
            self.assertEqual("partial", body["extraction"]["status"])
            self.assertIn("Python", body["extraction"]["raw_text"])
            self.assertIn("OCR", " ".join(body["extraction"]["warnings"]))
        else:
            self.assertEqual("manual_required", body["extraction"]["status"])
            self.assertTrue(body["needs_manual_correction"])
            self.assertRegex(" ".join(body["extraction"]["warnings"]), r"扫描版|图片型|OCR")

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


def _make_jd_image_base64() -> str:
    image_buffer = BytesIO()
    image = Image.new("RGB", (960, 320), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 50), "Backend Engineer JD", fill="black")
    draw.text((40, 120), "Requirements: Python FastAPI Redis PostgreSQL", fill="black")
    draw.text((40, 190), "Responsibilities: Build APIs and diagnose logs", fill="black")
    image.save(image_buffer, format="PNG")
    return base64.b64encode(image_buffer.getvalue()).decode("ascii")


def _make_image_only_pdf_base64() -> str:
    import fitz  # type: ignore

    image_data = base64.b64decode(_make_jd_image_base64())
    document = fitz.open()
    page = document.new_page(width=960, height=320)
    page.insert_image(page.rect, stream=image_data)
    pdf_bytes = document.tobytes()
    document.close()
    return base64.b64encode(pdf_bytes).decode("ascii")


if __name__ == "__main__":
    unittest.main()
