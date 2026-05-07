"""Gap analysis and resume optimization routes."""

from fastapi import APIRouter

from backend.app.schemas.gap import GapAnalysisRequest, GapAnalysisResponse
from backend.app.schemas.optimization import ResumeOptimizationRequest, ResumeOptimizationResponse
from backend.app.services.gap_analyzer import analyze_gap, suggest_resume_optimization

router = APIRouter(prefix="/analysis")


@router.post("/gap", response_model=GapAnalysisResponse)
def analyze_gap_route(request: GapAnalysisRequest) -> GapAnalysisResponse:
    return analyze_gap(request)


@router.post("/resume-optimization", response_model=ResumeOptimizationResponse)
def optimize_resume_route(request: ResumeOptimizationRequest) -> ResumeOptimizationResponse:
    return suggest_resume_optimization(request)
