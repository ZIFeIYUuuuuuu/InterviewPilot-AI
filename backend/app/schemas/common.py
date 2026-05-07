"""Shared schema primitives for InterviewPilot AI."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class SchemaModel(BaseModel):
    """Base schema with strict keys to keep agent outputs predictable."""

    model_config = ConfigDict(extra="forbid")


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class EvidenceQuality(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class InterviewMessageRole(str, Enum):
    system = "system"
    interviewer = "interviewer"
    candidate = "candidate"
    assistant = "assistant"


class InterviewQuestionType(str, Enum):
    new_question = "new_question"
    follow_up = "follow_up"
    transition = "transition"


class SessionStatus(str, Enum):
    draft = "draft"
    analysis_ready = "analysis_ready"
    interview_ready = "interview_ready"
    in_progress = "in_progress"
    report_ready = "report_ready"
    archived = "archived"


class WorkflowStep(str, Enum):
    jd_analysis = "jd_analysis"
    resume_analysis = "resume_analysis"
    gap_analysis = "gap_analysis"
    resume_optimization = "resume_optimization"
    interview_planning = "interview_planning"
    interview = "interview"
    evaluation = "evaluation"
    coaching = "coaching"
    report = "report"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


NonEmptyStringList = list[str]


class SourceText(SchemaModel):
    text: str = Field(..., min_length=1)
    source_type: str = Field(default="text", description="Input source, such as text, image, or pdf.")
    filename: str | None = None
