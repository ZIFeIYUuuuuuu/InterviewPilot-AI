"""Post-interview evaluation and coaching report routes."""

from fastapi import APIRouter, HTTPException

from backend.app.schemas.report import (
    ReportGenerationRequest,
    ReportGenerationResponse,
    SessionReportRequest,
    StoredPracticeReport,
)
from backend.app.services.interview_session import get_interview_session
from backend.app.services.json_store import (
    StoreError,
    get_latest_report_for_session,
    get_report,
    save_report,
)
from backend.app.services.report_generator import ReportGenerationError, generate_practice_report

router = APIRouter(prefix="/reports")


@router.post("/generate", response_model=ReportGenerationResponse)
def generate_report_route(request: ReportGenerationRequest) -> ReportGenerationResponse:
    try:
        response = generate_practice_report(request.interview_session, request.resume_optimization)
        stored_report = save_report(response.report)
        return response.model_copy(update={"stored_report": stored_report})
    except ReportGenerationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except StoreError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/sessions/{session_id}", response_model=ReportGenerationResponse)
def generate_session_report_route(
    session_id: str, request: SessionReportRequest
) -> ReportGenerationResponse:
    session = get_interview_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found")
    try:
        response = generate_practice_report(session, request.resume_optimization)
        stored_report = save_report(response.report)
        return response.model_copy(update={"stored_report": stored_report})
    except ReportGenerationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except StoreError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/{report_id}", response_model=StoredPracticeReport)
def get_report_route(report_id: str) -> StoredPracticeReport:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/sessions/{session_id}/latest", response_model=StoredPracticeReport)
def get_latest_session_report_route(session_id: str) -> StoredPracticeReport:
    report = get_latest_report_for_session(session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found for session")
    return report
