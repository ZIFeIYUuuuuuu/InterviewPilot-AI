"""Resume input, analysis, preview, and correction routes."""

from fastapi import APIRouter, HTTPException

from backend.app.schemas.resume import (
    ResumeAnalysisCorrectionRequest,
    ResumeAnalysisCorrectionResponse,
    ResumeAnalysisPreview,
    ResumeAnalysisResponse,
    ResumeInputRequest,
)
from backend.app.services.resume_analyzer import (
    analyze_resume_input,
    correct_resume_analysis,
    get_resume_preview,
)

router = APIRouter(prefix="/resume")


@router.post("/analyze", response_model=ResumeAnalysisResponse)
def analyze_resume(request: ResumeInputRequest) -> ResumeAnalysisResponse:
    return analyze_resume_input(request)


@router.get("/analyses/{analysis_id}/preview", response_model=ResumeAnalysisPreview)
def preview_resume_analysis(analysis_id: str) -> ResumeAnalysisPreview:
    preview = get_resume_preview(analysis_id)
    if preview is None:
        raise HTTPException(status_code=404, detail="Resume analysis preview not found.")
    return preview


@router.patch("/analyses/{analysis_id}/correction", response_model=ResumeAnalysisCorrectionResponse)
def correct_resume_analysis_route(
    analysis_id: str, request: ResumeAnalysisCorrectionRequest
) -> ResumeAnalysisCorrectionResponse:
    corrected = correct_resume_analysis(analysis_id, request)
    if corrected is None:
        raise HTTPException(status_code=404, detail="Resume analysis preview not found.")
    return corrected
