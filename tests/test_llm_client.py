import os
import unittest
from unittest.mock import patch

from backend.app.core.config import get_settings
from backend.app.schemas.jd import JDAnalysis
from backend.app.services import llm_client


class LLMClientTests(unittest.TestCase):
    def tearDown(self):
        get_settings.cache_clear()

    def test_llm_disabled_without_api_key(self):
        with patch.dict(
            os.environ,
            {
                "INTERVIEWPILOT_LLM_API_KEY": "",
                "DASHSCOPE_API_KEY": "",
                "BAILIAN_API_KEY": "",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            self.assertFalse(llm_client.is_llm_enabled())
            self.assertIsNone(llm_client.generate_structured_output("{}", JDAnalysis))

    def test_extracts_json_from_markdown_wrapped_content(self):
        content = """```json
        {
          "role_title": "Backend Engineer",
          "required_skills": ["Python"],
          "preferred_skills": [],
          "responsibilities": ["Build APIs"],
          "interview_focus": ["API design"],
          "uncertainty_notes": [],
          "raw_jd_text": "Need Python"
        }
        ```"""

        parsed = llm_client._extract_json_object(content)

        self.assertEqual("Backend Engineer", parsed["role_title"])
        self.assertEqual(["Python"], parsed["required_skills"])

    def test_validates_structured_output_when_provider_returns_json(self):
        with patch.dict(
            os.environ,
            {
                "INTERVIEWPILOT_LLM_API_KEY": "test-key",
                "INTERVIEWPILOT_LLM_ENABLED": "true",
                "INTERVIEWPILOT_LLM_MODEL": "glm-5",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            payload = (
                '{"role_title":"Backend Engineer","required_skills":["Python"],'
                '"preferred_skills":[],"responsibilities":["Build APIs"],'
                '"interview_focus":["API design"],"uncertainty_notes":[],'
                '"raw_jd_text":"Need Python"}'
            )
            with patch.object(llm_client, "_chat_completion", return_value=payload):
                result = llm_client.generate_structured_output("prompt", JDAnalysis)

        self.assertIsNotNone(result)
        self.assertEqual("Backend Engineer", result.role_title)
        self.assertEqual("Need Python", result.raw_jd_text)


if __name__ == "__main__":
    unittest.main()
