"""JD analysis schemas aligned to the JD Analyzer prompt."""

from enum import Enum

from pydantic import Field

from backend.app.schemas.common import SchemaModel, new_id, utc_now


class JDInputType(str, Enum):
    text = "text"
    image = "image"
    pdf = "pdf"


class JDExtractionStatus(str, Enum):
    extracted = "extracted"
    partial = "partial"
    failed = "failed"
    manual_required = "manual_required"


class JDAnalysis(SchemaModel):
    role_title: str = Field(..., min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    interview_focus: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    raw_jd_text: str | None = None


class JDInputRequest(SchemaModel):
    input_type: JDInputType = JDInputType.text
    text: str | None = Field(default=None, description="Pasted JD text or manually corrected extracted text.")
    content_base64: str | None = Field(default=None, description="Optional base64 file content for PDF/image input.")
    filename: str | None = None


class JDExtractionResult(SchemaModel):
    input_id: str = Field(default_factory=lambda: new_id("jd_input"))
    input_type: JDInputType
    raw_text: str = ""
    status: JDExtractionStatus
    warnings: list[str] = Field(default_factory=list)
    needs_manual_correction: bool = False


class JDAnalyzerPrompt(SchemaModel):
    task: str
    prompt: str


class JDAnalysisResponse(SchemaModel):
    analysis_id: str = Field(default_factory=lambda: new_id("jd_analysis"))
    extraction: JDExtractionResult
    analysis: JDAnalysis
    analyzer_prompt: JDAnalyzerPrompt
    needs_manual_correction: bool = False
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class JDAnalysisPreview(SchemaModel):
    analysis_id: str
    analysis: JDAnalysis
    extraction: JDExtractionResult
    editable_fields: list[str] = Field(
        default_factory=lambda: [
            "role_title",
            "required_skills",
            "preferred_skills",
            "responsibilities",
            "interview_focus",
            "uncertainty_notes",
        ]
    )
    needs_manual_correction: bool = False


class JDAnalysisCorrectionRequest(SchemaModel):
    role_title: str = Field(..., min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    interview_focus: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    raw_jd_text: str | None = None


class JDAnalysisCorrectionResponse(SchemaModel):
    analysis_id: str
    analysis: JDAnalysis
    manually_corrected: bool = True
    needs_manual_correction: bool = False
