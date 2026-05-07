"""Minimal JSON persistence for MVP sessions, live interviews, and reports."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock
from typing import Any

from pydantic import ValidationError

from backend.app.schemas.common import SessionStatus, utc_now
from backend.app.schemas.interview import InterviewSessionState, LiveInterviewStatus
from backend.app.schemas.report import PracticeReport, StoredPracticeReport
from backend.app.schemas.session import HistoryItem, InterviewPilotState

_LOCK = RLock()
_DEFAULT_STORE_PATH = Path("data/interviewpilot_store.json")


class StoreError(RuntimeError):
    """Raised when the local MVP store cannot be read or written."""


def create_session(state: InterviewPilotState) -> InterviewPilotState:
    with _LOCK:
        data = _read_store()
        data["sessions"][state.session_id] = state.model_dump(mode="json")
        _write_store(data)
    return state


def get_session(session_id: str) -> InterviewPilotState | None:
    with _LOCK:
        raw = _read_store()["sessions"].get(session_id)
    if raw is None:
        return None
    return InterviewPilotState.model_validate(raw)


def update_session(state: InterviewPilotState) -> InterviewPilotState:
    state.updated_at = utc_now()
    with _LOCK:
        data = _read_store()
        if state.session_id not in data["sessions"]:
            raise KeyError(state.session_id)
        data["sessions"][state.session_id] = state.model_dump(mode="json")
        _write_store(data)
    return state


def save_live_interview(session: InterviewSessionState) -> InterviewSessionState:
    with _LOCK:
        data = _read_store()
        data["live_interviews"][session.session_id] = session.model_dump(mode="json")
        _write_store(data)
    return session


def get_live_interview(session_id: str) -> InterviewSessionState | None:
    with _LOCK:
        raw = _read_store()["live_interviews"].get(session_id)
    if raw is None:
        return None
    return InterviewSessionState.model_validate(raw)


def save_report(report: PracticeReport) -> StoredPracticeReport:
    stored = StoredPracticeReport(session_id=report.session_id, report=report)
    with _LOCK:
        data = _read_store()
        data["reports"][stored.report_id] = stored.model_dump(mode="json")
        data["session_reports"].setdefault(report.session_id, []).append(stored.report_id)
        _write_store(data)
    return stored


def get_report(report_id: str) -> StoredPracticeReport | None:
    with _LOCK:
        raw = _read_store()["reports"].get(report_id)
    if raw is None:
        return None
    return StoredPracticeReport.model_validate(raw)


def get_latest_report_for_session(session_id: str) -> StoredPracticeReport | None:
    with _LOCK:
        data = _read_store()
        report_ids = data["session_reports"].get(session_id, [])
        if not report_ids:
            return None
        raw = data["reports"].get(report_ids[-1])
    if raw is None:
        return None
    return StoredPracticeReport.model_validate(raw)


def list_history(limit: int = 20) -> list[HistoryItem]:
    with _LOCK:
        data = _read_store()
        sessions = [
            _history_from_workflow(raw, data)
            for raw in data["sessions"].values()
        ]
        live_sessions = [
            _history_from_live(raw, data)
            for raw in data["live_interviews"].values()
        ]
    items = [item for item in [*sessions, *live_sessions] if item is not None]
    items.sort(key=lambda item: item.updated_at, reverse=True)
    return items[: max(1, min(limit, 100))]


def clear_store_for_tests() -> None:
    with _LOCK:
        _write_store(_empty_store())


def _history_from_workflow(raw: dict[str, Any], data: dict[str, Any]) -> HistoryItem | None:
    try:
        state = InterviewPilotState.model_validate(raw)
    except ValidationError:
        return None
    latest_report = _latest_report_from_data(state.session_id, data)
    target_role = state.input.target_role if state.input else "Untitled interview"
    return HistoryItem(
        session_id=state.session_id,
        target_role=target_role,
        status=state.status,
        created_at=state.created_at,
        updated_at=state.updated_at,
        overall_score=latest_report.report.evaluation.overall_score if latest_report else None,
        weak_area_summary=_weak_area_summary(latest_report.report) if latest_report else [],
        latest_report_id=latest_report.report_id if latest_report else None,
    )


def _history_from_live(raw: dict[str, Any], data: dict[str, Any]) -> HistoryItem | None:
    try:
        session = InterviewSessionState.model_validate(raw)
    except ValidationError:
        return None
    latest_report = _latest_report_from_data(session.session_id, data)
    status = (
        SessionStatus.report_ready
        if latest_report
        else SessionStatus.in_progress
        if session.status == LiveInterviewStatus.in_progress
        else SessionStatus.interview_ready
    )
    return HistoryItem(
        session_id=session.session_id,
        target_role=session.jd_analysis.role_title,
        status=status,
        created_at=session.started_at,
        updated_at=session.updated_at,
        overall_score=latest_report.report.evaluation.overall_score if latest_report else None,
        weak_area_summary=_weak_area_summary(latest_report.report) if latest_report else [],
        latest_report_id=latest_report.report_id if latest_report else None,
    )


def _latest_report_from_data(session_id: str, data: dict[str, Any]) -> StoredPracticeReport | None:
    report_ids = data["session_reports"].get(session_id, [])
    if not report_ids:
        return None
    raw = data["reports"].get(report_ids[-1])
    if raw is None:
        return None
    return StoredPracticeReport.model_validate(raw)


def _weak_area_summary(report: PracticeReport) -> list[str]:
    result: list[str] = []
    for weakness in report.evaluation.weaknesses[:2]:
        result.append(weakness)
    for focus in report.coaching.next_round_focus[:2]:
        if focus not in result:
            result.append(focus)
    return result[:4]


def _read_store() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return _empty_store()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StoreError(f"Could not read persistence store: {error}") from error
    return _normalize_store(data)


def _write_store(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_normalize_store(data), ensure_ascii=False, indent=2)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(path)
    except OSError as error:
        raise StoreError(f"Could not write persistence store: {error}") from error


def _store_path() -> Path:
    configured = os.getenv("INTERVIEWPILOT_STORE_PATH", "").strip()
    return Path(configured) if configured else _DEFAULT_STORE_PATH


def _empty_store() -> dict[str, Any]:
    return {
        "sessions": {},
        "live_interviews": {},
        "reports": {},
        "session_reports": {},
    }


def _normalize_store(data: dict[str, Any]) -> dict[str, Any]:
    normalized = _empty_store()
    for key in normalized:
        value = data.get(key, {})
        normalized[key] = value if isinstance(value, dict) else {}
    return normalized
