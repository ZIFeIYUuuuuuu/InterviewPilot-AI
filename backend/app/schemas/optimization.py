"""Resume optimization schemas aligned to the Resume Optimization prompt."""

from pydantic import Field

from backend.app.schemas.common import SchemaModel
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.resume import ResumeAnalysis


class BulletImprovementSuggestion(SchemaModel):
    original_issue: str = Field(..., min_length=1)
    why_it_is_weak: str = Field(..., min_length=1)
    suggested_direction: str = Field(..., min_length=1)
    example_rewrite: str = Field(..., min_length=1)
    evidence_boundary: str = Field(
        default="只能基于用户材料中已有事实；缺少真实指标时使用条件表达，不补造数字或结果。"
    )


class ResumeOptimization(SchemaModel):
    optimization_summary: str = Field(..., min_length=1)
    rewrite_targets: list[str] = Field(default_factory=list)
    bullet_improvement_suggestions: list[BulletImprovementSuggestion] = Field(default_factory=list)
    skill_positioning_suggestions: list[str] = Field(default_factory=list)
    risk_warnings: list[str] = Field(default_factory=list)


class ResumeOptimizationRequest(SchemaModel):
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis


class ResumeOptimizationPrompt(SchemaModel):
    task: str
    prompt: str


class ResumeOptimizationResponse(SchemaModel):
    resume_optimization: ResumeOptimization
    analyzer_prompt: ResumeOptimizationPrompt
