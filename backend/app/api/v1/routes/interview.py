"""Interview planning and live text-session routes."""

from fastapi import APIRouter, HTTPException

from backend.app.schemas.interview import (
    InterviewPlanRequest,
    InterviewPlanResponse,
    InterviewSessionResponse,
    InterviewSessionStartRequest,
    InterviewSessionState,
    InterviewTurnRequest,
)
from backend.app.services.interview_session import (
    advance_interview_session,
    get_interview_session,
    start_interview_session,
)
from backend.app.services.interview_planner import create_interview_plan

router = APIRouter(prefix="/interview")


@router.post("/plan", response_model=InterviewPlanResponse)
def create_interview_plan_route(request: InterviewPlanRequest) -> InterviewPlanResponse:
    return create_interview_plan(request)


@router.post("/sessions", response_model=InterviewSessionResponse)
def start_interview_session_route(request: InterviewSessionStartRequest) -> InterviewSessionResponse:
    return start_interview_session(request)


@router.get("/sessions/{session_id}", response_model=InterviewSessionState)
def get_interview_session_route(session_id: str) -> InterviewSessionState:
    session = get_interview_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return session


@router.post("/sessions/{session_id}/turn", response_model=InterviewSessionResponse)
def advance_interview_session_route(
    session_id: str, request: InterviewTurnRequest
) -> InterviewSessionResponse:
    response = advance_interview_session(session_id, request)
    if response is None:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return response
