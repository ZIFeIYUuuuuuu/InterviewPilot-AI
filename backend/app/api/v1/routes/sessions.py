"""Product-level session lifecycle and dashboard history routes."""

from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.common import SessionStatus, WorkflowStep, utc_now
from backend.app.schemas.session import (
    HistoryResponse,
    InterviewPilotState,
    InterviewReportEntity,
    SessionCreateRequest,
    SessionFinishRequest,
    SessionResponse,
    SessionUpdateRequest,
)
from backend.app.services.json_store import (
    StoreError,
    create_session,
    get_report,
    get_session,
    list_history,
    update_session,
)

router = APIRouter(prefix="/sessions")


@router.post("", response_model=SessionResponse)
def create_session_route(request: SessionCreateRequest) -> SessionResponse:
    state = InterviewPilotState(
        input=request.input,
        status=SessionStatus.draft,
        current_step=WorkflowStep.jd_analysis,
    )
    try:
        return SessionResponse(session=create_session(state))
    except StoreError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("", response_model=HistoryResponse)
def list_session_history_route(
    limit: int = Query(default=20, ge=1, le=100)
) -> HistoryResponse:
    try:
        return HistoryResponse(items=list_history(limit))
    except StoreError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/{session_id}", response_model=SessionResponse)
def get_session_route(session_id: str) -> SessionResponse:
    state = get_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(session=state)


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session_route(session_id: str, request: SessionUpdateRequest) -> SessionResponse:
    state = get_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    for field in request.model_fields_set:
        setattr(state, field, getattr(request, field))
    state.updated_at = utc_now()
    try:
        return SessionResponse(session=update_session(state))
    except StoreError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/{session_id}/finish", response_model=SessionResponse)
def finish_session_route(session_id: str, request: SessionFinishRequest) -> SessionResponse:
    state = get_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.report_id:
        stored_report = get_report(request.report_id)
        if stored_report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        if stored_report.session_id != session_id:
            raise HTTPException(status_code=409, detail="Report belongs to a different session")
        state.evaluation = stored_report.report.evaluation
        state.coaching = stored_report.report.coaching
        state.report = InterviewReportEntity(
            report_id=stored_report.report_id,
            session_id=session_id,
            evaluation=stored_report.report.evaluation,
            coaching=stored_report.report.coaching,
            generated_at=stored_report.generated_at,
        )
        state.status = SessionStatus.report_ready
        state.current_step = WorkflowStep.report
    else:
        state.status = SessionStatus.archived
        state.current_step = WorkflowStep.report

    state.updated_at = utc_now()
    try:
        return SessionResponse(session=update_session(state))
    except StoreError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
