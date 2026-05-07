import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.core.config import get_settings
from backend.app.core.env import load_dotenv


class EnvConfigTests(unittest.TestCase):
    def tearDown(self):
        get_settings.cache_clear()

    def test_load_dotenv_reads_values_without_overriding_existing_env(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "INTERVIEWPILOT_LLM_MODEL=glm-5",
                        "INTERVIEWPILOT_HOST=0.0.0.0",
                        "QUOTED_VALUE=\"hello world\"",
                    ]
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"INTERVIEWPILOT_HOST": "127.0.0.1"}, clear=False):
                os.environ.pop("INTERVIEWPILOT_LLM_MODEL", None)
                os.environ.pop("QUOTED_VALUE", None)

                load_dotenv(env_path)

                self.assertEqual("glm-5", os.environ["INTERVIEWPILOT_LLM_MODEL"])
                self.assertEqual("127.0.0.1", os.environ["INTERVIEWPILOT_HOST"])
                self.assertEqual("hello world", os.environ["QUOTED_VALUE"])

    def test_settings_use_llm_env_values(self):
        with patch.dict(
            os.environ,
            {
                "INTERVIEWPILOT_LLM_API_KEY": "test-key",
                "INTERVIEWPILOT_LLM_ENABLED": "true",
                "INTERVIEWPILOT_LLM_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "INTERVIEWPILOT_LLM_MODEL": "glm-5",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            settings = get_settings()

        self.assertTrue(settings.llm_enabled)
        self.assertEqual("glm-5", settings.llm_model)
        self.assertEqual("https://dashscope.aliyuncs.com/compatible-mode/v1", settings.llm_base_url)


if __name__ == "__main__":
    unittest.main()
