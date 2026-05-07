"""Coaching schemas aligned to the Coach prompt."""

from pydantic import Field

from backend.app.schemas.common import SchemaModel


class CoachingImprovement(SchemaModel):
    issue: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)
    suggestion: str = Field(..., min_length=1)
    example_answer_guidance: str = Field(..., min_length=1)


class Coaching(SchemaModel):
    summary: str = Field(..., min_length=1)
    top_improvements: list[CoachingImprovement] = Field(default_factory=list)
    practice_plan: list[str] = Field(default_factory=list)
    next_round_focus: list[str] = Field(default_factory=list)


class CoachPrompt(SchemaModel):
    task: str
    prompt: str
