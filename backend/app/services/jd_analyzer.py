"""JD analyzer service.

This service wires the documented JD Analyzer prompt into the backend while
using a conservative local analyzer until an LLM provider is introduced.
"""

from __future__ import annotations

from backend.app.schemas.jd import (
    JDAnalysis,
    JDAnalysisCorrectionRequest,
    JDAnalysisCorrectionResponse,
    JDAnalysisPreview,
    JDAnalysisResponse,
    JDAnalyzerPrompt,
    JDInputRequest,
)
from backend.app.services.jd_extraction import extract_jd_text
from backend.app.services.jd_prompt import JD_ANALYZER_TASK, build_jd_analyzer_prompt
from backend.app.services.llm_client import generate_structured_output
from interviewpilot.analysis import analyze_jd as local_analyze_jd


_JD_ANALYSIS_STORE: dict[str, JDAnalysisResponse] = {}


def analyze_jd_input(request: JDInputRequest) -> JDAnalysisResponse:
    extraction = extract_jd_text(request)
    prompt_text = build_jd_analyzer_prompt(extraction.raw_text)
    analysis = _analyze_text(extraction.raw_text, extraction.warnings, prompt_text)
    prompt = JDAnalyzerPrompt(
        task=JD_ANALYZER_TASK,
        prompt=prompt_text,
    )
    response = JDAnalysisResponse(
        extraction=extraction,
        analysis=analysis,
        analyzer_prompt=prompt,
        needs_manual_correction=extraction.needs_manual_correction or bool(analysis.uncertainty_notes),
    )
    _JD_ANALYSIS_STORE[response.analysis_id] = response
    return response


def get_jd_preview(analysis_id: str) -> JDAnalysisPreview | None:
    response = _JD_ANALYSIS_STORE.get(analysis_id)
    if response is None:
        return None
    return JDAnalysisPreview(
        analysis_id=response.analysis_id,
        analysis=response.analysis,
        extraction=response.extraction,
        needs_manual_correction=response.needs_manual_correction,
    )


def correct_jd_analysis(
    analysis_id: str, request: JDAnalysisCorrectionRequest
) -> JDAnalysisCorrectionResponse | None:
    response = _JD_ANALYSIS_STORE.get(analysis_id)
    if response is None:
        return None
    corrected = JDAnalysis(**request.model_dump())
    updated = response.model_copy(update={"analysis": corrected, "needs_manual_correction": False})
    _JD_ANALYSIS_STORE[analysis_id] = updated
    return JDAnalysisCorrectionResponse(
        analysis_id=analysis_id,
        analysis=corrected,
        needs_manual_correction=False,
    )


def _analyze_text(raw_text: str, extraction_warnings: list[str], prompt: str) -> JDAnalysis:
    if not raw_text.strip():
        return JDAnalysis(
            role_title="目标岗位",
            required_skills=[],
            preferred_skills=[],
            responsibilities=[],
            interview_focus=[],
            uncertainty_notes=[
                "没有可用的 JD 文本。请粘贴或手动修正 JD 后继续。",
                *extraction_warnings,
            ],
            raw_jd_text=raw_text,
        )

    llm_analysis = generate_structured_output(prompt, JDAnalysis)
    if llm_analysis is not None:
        notes = [*llm_analysis.uncertainty_notes, *extraction_warnings]
        return llm_analysis.model_copy(
            update={
                "raw_jd_text": llm_analysis.raw_jd_text or raw_text,
                "uncertainty_notes": list(dict.fromkeys(note for note in notes if note)),
            }
        )

    local = local_analyze_jd(raw_text)
    notes = [*local.uncertainty_notes, *extraction_warnings]
    if not local.required_skills and not local.responsibilities:
        notes.append("JD 解析置信度较低，因为必需技能和岗位职责不够清晰。")
    return JDAnalysis(
        role_title=local.role_title,
        required_skills=local.required_skills,
        preferred_skills=local.preferred_skills,
        responsibilities=local.responsibilities,
        interview_focus=local.interview_focus,
        uncertainty_notes=list(dict.fromkeys(note for note in notes if note)),
        raw_jd_text=local.raw_jd_text,
    )
