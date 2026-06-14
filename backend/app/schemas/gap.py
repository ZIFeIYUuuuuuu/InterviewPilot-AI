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


class FreeDiagnosisPreviewRequest(SchemaModel):
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis


class FreeDiagnosisPreview(SchemaModel):
    overall_preview_score: int = Field(..., ge=0, le=100)
    top_issues: list[str] = Field(default_factory=list)
    weak_evidence: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    report_summary: str = Field(..., min_length=1)
    privacy_or_boundary_note: str = Field(..., min_length=1)


class FreeDiagnosisPreviewResponse(SchemaModel):
    preview: FreeDiagnosisPreview
