"""Application configuration for the backend skeleton."""

from __future__ import annotations

from functools import lru_cache
import os

from pydantic import BaseModel, Field

from backend.app.core.env import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str = "InterviewPilot AI"
    app_version: str = "0.1.0"
    environment: str = Field(default="local")
    api_v1_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    cors_allowed_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    llm_enabled: bool = False
    llm_api_key: str | None = None
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "glm-5"
    llm_timeout_seconds: int = 30


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("INTERVIEWPILOT_APP_NAME", "InterviewPilot AI"),
        app_version=os.getenv("INTERVIEWPILOT_APP_VERSION", "0.1.0"),
        environment=os.getenv("INTERVIEWPILOT_ENV", "local"),
        api_v1_prefix=os.getenv("INTERVIEWPILOT_API_V1_PREFIX", "/api/v1"),
        host=os.getenv("INTERVIEWPILOT_HOST", "127.0.0.1"),
        port=int(os.getenv("INTERVIEWPILOT_PORT", "8000")),
        reload=_as_bool(os.getenv("INTERVIEWPILOT_RELOAD", "false")),
        cors_allowed_origins=_split_csv(
            os.getenv(
                "INTERVIEWPILOT_CORS_ORIGINS",
                "http://127.0.0.1:5173,http://localhost:5173",
            )
        ),
        llm_enabled=_as_bool(os.getenv("INTERVIEWPILOT_LLM_ENABLED", "true"))
        and bool(_llm_api_key()),
        llm_api_key=_llm_api_key(),
        llm_base_url=os.getenv(
            "INTERVIEWPILOT_LLM_BASE_URL",
            os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        ).rstrip("/"),
        llm_model=os.getenv("INTERVIEWPILOT_LLM_MODEL", os.getenv("DASHSCOPE_MODEL", "glm-5")),
        llm_timeout_seconds=int(os.getenv("INTERVIEWPILOT_LLM_TIMEOUT_SECONDS", "30")),
    )


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _as_bool(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _llm_api_key() -> str | None:
    for name in ("INTERVIEWPILOT_LLM_API_KEY", "DASHSCOPE_API_KEY", "BAILIAN_API_KEY"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return None
