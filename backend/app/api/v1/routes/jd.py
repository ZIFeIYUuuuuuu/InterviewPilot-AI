"""JD input, analysis, preview, and correction routes."""

from fastapi import APIRouter, HTTPException

from backend.app.schemas.jd import (
    JDAnalysisCorrectionRequest,
    JDAnalysisCorrectionResponse,
    JDAnalysisPreview,
    JDAnalysisResponse,
    JDInputRequest,
)
from backend.app.services.jd_analyzer import analyze_jd_input, correct_jd_analysis, get_jd_preview

router = APIRouter(prefix="/jd")


@router.post("/analyze", response_model=JDAnalysisResponse)
def analyze_jd(request: JDInputRequest) -> JDAnalysisResponse:
    return analyze_jd_input(request)


@router.get("/analyses/{analysis_id}/preview", response_model=JDAnalysisPreview)
def preview_jd_analysis(analysis_id: str) -> JDAnalysisPreview:
    preview = get_jd_preview(analysis_id)
    if preview is None:
        raise HTTPException(status_code=404, detail="JD analysis preview not found.")
    return preview


@router.patch("/analyses/{analysis_id}/correction", response_model=JDAnalysisCorrectionResponse)
def correct_jd_analysis_route(
    analysis_id: str, request: JDAnalysisCorrectionRequest
) -> JDAnalysisCorrectionResponse:
    corrected = correct_jd_analysis(analysis_id, request)
    if corrected is None:
        raise HTTPException(status_code=404, detail="JD analysis preview not found.")
    return corrected
