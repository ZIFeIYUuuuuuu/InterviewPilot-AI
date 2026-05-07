"""Resume analysis schemas aligned to the Resume Analyzer prompt."""

from enum import Enum

from pydantic import Field

from backend.app.schemas.common import EvidenceQuality, SchemaModel, new_id, utc_now


class ResumeInputType(str, Enum):
    text = "text"
    image = "image"
    pdf = "pdf"


class ResumeExtractionStatus(str, Enum):
    extracted = "extracted"
    partial = "partial"
    failed = "failed"
    manual_required = "manual_required"


class ResumeProject(SchemaModel):
    name: str = Field(..., min_length=1)
    tech_stack: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    evidence_quality: EvidenceQuality


class ResumeAnalysis(SchemaModel):
    candidate_skills: list[str] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    weak_evidence_skills: list[str] = Field(default_factory=list)
    resume_summary: str = Field(..., min_length=1)
    uncertainty_notes: list[str] = Field(default_factory=list)
    raw_resume_text: str | None = None


class ResumeInputRequest(SchemaModel):
    input_type: ResumeInputType = ResumeInputType.text
    text: str | None = Field(default=None, description="Pasted resume text or manually extracted PDF text.")
    content_base64: str | None = Field(default=None, description="Optional base64 file content for PDF/image input.")
    filename: str | None = None


class ResumeExtractionResult(SchemaModel):
    input_id: str = Field(default_factory=lambda: new_id("resume_input"))
    input_type: ResumeInputType
    raw_text: str = ""
    status: ResumeExtractionStatus
    warnings: list[str] = Field(default_factory=list)
    needs_manual_correction: bool = False


class ResumeAnalyzerPrompt(SchemaModel):
    task: str
    prompt: str


class ResumeAnalysisResponse(SchemaModel):
    analysis_id: str = Field(default_factory=lambda: new_id("resume_analysis"))
    extraction: ResumeExtractionResult
    analysis: ResumeAnalysis
    analyzer_prompt: ResumeAnalyzerPrompt
    needs_manual_correction: bool = False
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class ResumeAnalysisPreview(SchemaModel):
    analysis_id: str
    analysis: ResumeAnalysis
    extraction: ResumeExtractionResult
    editable_fields: list[str] = Field(
        default_factory=lambda: [
            "candidate_skills",
            "projects",
            "strengths",
            "weaknesses",
            "weak_evidence_skills",
            "resume_summary",
            "uncertainty_notes",
        ]
    )
    needs_manual_correction: bool = False


class ResumeAnalysisCorrectionRequest(SchemaModel):
    candidate_skills: list[str] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    weak_evidence_skills: list[str] = Field(default_factory=list)
    resume_summary: str = Field(..., min_length=1)
    uncertainty_notes: list[str] = Field(default_factory=list)
    raw_resume_text: str | None = None


class ResumeAnalysisCorrectionResponse(SchemaModel):
    analysis_id: str
    analysis: ResumeAnalysis
    manually_corrected: bool = True
    needs_manual_correction: bool = False
