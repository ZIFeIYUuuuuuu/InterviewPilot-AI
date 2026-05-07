"""Evaluation schemas aligned to the Evaluator prompt."""

from pydantic import Field

from backend.app.schemas.common import SchemaModel


class RubricScore(SchemaModel):
    score: int = Field(..., ge=0, le=100)
    reason: str = Field(..., min_length=1)


class EvaluationDimensionScores(SchemaModel):
    technical_accuracy: RubricScore
    depth: RubricScore
    structure: RubricScore
    communication: RubricScore
    role_fit: RubricScore
    evidence_quality: RubricScore


class Evaluation(SchemaModel):
    overall_score: int = Field(..., ge=0, le=100)
    dimension_scores: EvaluationDimensionScores
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    summary: str = Field(..., min_length=1)


class EvaluatorPrompt(SchemaModel):
    task: str
    prompt: str
