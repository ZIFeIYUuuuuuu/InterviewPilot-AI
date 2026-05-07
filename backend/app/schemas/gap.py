"""Gap analysis schemas aligned to the Gap Analysis prompt."""

from pydantic import Field

from backend.app.schemas.common import SchemaModel
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.resume import ResumeAnalysis


class GapAnalysis(SchemaModel):
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_evidence_skills: list[str] = Field(default_factory=list)
    high_risk_topics: list[str] = Field(default_factory=list)
    recommended_focus: list[str] = Field(default_factory=list)
    summary: str = Field(..., min_length=1)


class GapAnalysisRequest(SchemaModel):
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis


class GapAnalyzerPrompt(SchemaModel):
    task: str
    prompt: str


class GapAnalysisResponse(SchemaModel):
    gap_analysis: GapAnalysis
    analyzer_prompt: GapAnalyzerPrompt
