"""Resume analyzer service.

This service wires the documented Resume Analyzer prompt into the backend
while using a conservative local analyzer until an LLM provider is introduced.
"""

from __future__ import annotations

from backend.app.schemas.resume import (
    ResumeAnalysis,
    ResumeAnalysisCorrectionRequest,
    ResumeAnalysisCorrectionResponse,
    ResumeAnalysisPreview,
    ResumeAnalysisResponse,
    ResumeAnalyzerPrompt,
    ResumeInputRequest,
    ResumeProject,
)
from backend.app.services.resume_extraction import extract_resume_text
from backend.app.services.resume_prompt import RESUME_ANALYZER_TASK, build_resume_analyzer_prompt
from backend.app.services.llm_client import generate_structured_output
from interviewpilot.analysis import analyze_resume as local_analyze_resume


_RESUME_ANALYSIS_STORE: dict[str, ResumeAnalysisResponse] = {}


def analyze_resume_input(request: ResumeInputRequest) -> ResumeAnalysisResponse:
    extraction = extract_resume_text(request)
    prompt_text = build_resume_analyzer_prompt(extraction.raw_text)
    analysis = _analyze_text(extraction.raw_text, extraction.warnings, prompt_text)
    prompt = ResumeAnalyzerPrompt(
        task=RESUME_ANALYZER_TASK,
        prompt=prompt_text,
    )
    response = ResumeAnalysisResponse(
        extraction=extraction,
        analysis=analysis,
        analyzer_prompt=prompt,
        needs_manual_correction=extraction.needs_manual_correction or bool(analysis.uncertainty_notes),
    )
    _RESUME_ANALYSIS_STORE[response.analysis_id] = response
    return response


def get_resume_preview(analysis_id: str) -> ResumeAnalysisPreview | None:
    response = _RESUME_ANALYSIS_STORE.get(analysis_id)
    if response is None:
        return None
    return ResumeAnalysisPreview(
        analysis_id=response.analysis_id,
        analysis=response.analysis,
        extraction=response.extraction,
        needs_manual_correction=response.needs_manual_correction,
    )


def correct_resume_analysis(
    analysis_id: str, request: ResumeAnalysisCorrectionRequest
) -> ResumeAnalysisCorrectionResponse | None:
    response = _RESUME_ANALYSIS_STORE.get(analysis_id)
    if response is None:
        return None
    corrected = ResumeAnalysis(**request.model_dump())
    updated = response.model_copy(update={"analysis": corrected, "needs_manual_correction": False})
    _RESUME_ANALYSIS_STORE[analysis_id] = updated
    return ResumeAnalysisCorrectionResponse(
        analysis_id=analysis_id,
        analysis=corrected,
        needs_manual_correction=False,
    )


def _analyze_text(raw_text: str, extraction_warnings: list[str], prompt: str) -> ResumeAnalysis:
    if not raw_text.strip():
        return ResumeAnalysis(
            candidate_skills=[],
            projects=[],
            strengths=[],
            weaknesses=["简历文本缺失，因此无法分析候选人证据。"],
            weak_evidence_skills=[],
            resume_summary="没有可用的简历文本。",
            uncertainty_notes=[
                "请粘贴或手动修正简历文本后继续。",
                "单独的简历分析不会判断 JD 必需技能是否缺失；缺失与匹配由后续 Gap Analysis 结合 JD 判断。",
                *extraction_warnings,
            ],
            raw_resume_text=raw_text,
        )

    llm_analysis = generate_structured_output(prompt, ResumeAnalysis)
    if llm_analysis is not None:
        notes = [
            *llm_analysis.uncertainty_notes,
            *extraction_warnings,
            "单独的简历分析只识别弱证据；JD 定向的缺失技能由后续 Gap Analysis 判断。",
        ]
        return llm_analysis.model_copy(
            update={
                "raw_resume_text": llm_analysis.raw_resume_text or raw_text,
                "uncertainty_notes": list(dict.fromkeys(note for note in notes if note)),
            }
        )

    local = local_analyze_resume(raw_text)
    notes = [*local.uncertainty_notes, *extraction_warnings]
    projects = [
        ResumeProject(
            name=project.name,
            tech_stack=project.tech_stack,
            highlights=project.highlights,
            evidence_quality=project.evidence_quality,
        )
        for project in local.projects
        if not _is_skills_only_project(project.name, project.highlights)
    ]
    weak_evidence_skills = local.weak_evidence_skills
    weaknesses = local.weaknesses
    if local.candidate_skills and not projects:
        weak_evidence_skills = list(dict.fromkeys([*weak_evidence_skills, *local.candidate_skills]))
        weaknesses = list(
            dict.fromkeys([*weaknesses, "简历中列出的技能没有连接到项目或经历证据。"])
        )
        notes.append("检测到了技能，但项目证据缺失或不清晰。")
    if not local.candidate_skills:
        notes.append("没有检测到明确候选人技能；这代表简历证据缺失，不代表候选人一定不会这些技能。")
    notes.append("单独的简历分析只识别弱证据；JD 定向的缺失技能由后续 Gap Analysis 判断。")

    return ResumeAnalysis(
        candidate_skills=local.candidate_skills,
        projects=projects,
        strengths=local.strengths,
        weaknesses=weaknesses,
        weak_evidence_skills=weak_evidence_skills,
        resume_summary=local.resume_summary,
        uncertainty_notes=list(dict.fromkeys(note for note in notes if note)),
        raw_resume_text=local.raw_resume_text,
    )


def _is_skills_only_project(name: str, highlights: list[str]) -> bool:
    combined = " ".join([name, *highlights]).strip().casefold()
    return combined.startswith("skills") or combined.startswith("技能")
