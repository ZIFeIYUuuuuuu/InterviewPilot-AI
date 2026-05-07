"""Gap Analysis and Resume Optimization services."""

from __future__ import annotations

from backend.app.schemas.gap import GapAnalysis, GapAnalysisRequest, GapAnalysisResponse, GapAnalyzerPrompt
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.optimization import (
    BulletImprovementSuggestion,
    ResumeOptimization,
    ResumeOptimizationRequest,
    ResumeOptimizationResponse,
    ResumeOptimizationPrompt,
)
from backend.app.schemas.resume import ResumeAnalysis, ResumeProject
from backend.app.services.gap_prompt import GAP_ANALYSIS_TASK, build_gap_analysis_prompt
from backend.app.services.llm_client import generate_structured_output
from backend.app.services.optimization_prompt import (
    RESUME_OPTIMIZATION_TASK,
    build_resume_optimization_prompt,
)


def analyze_gap(request: GapAnalysisRequest) -> GapAnalysisResponse:
    prompt_text = build_gap_analysis_prompt(request.jd_analysis, request.resume_analysis)
    gap = generate_structured_output(prompt_text, GapAnalysis) or _analyze_gap(
        request.jd_analysis, request.resume_analysis
    )
    return GapAnalysisResponse(
        gap_analysis=gap,
        analyzer_prompt=GapAnalyzerPrompt(
            task=GAP_ANALYSIS_TASK,
            prompt=prompt_text,
        ),
    )


def suggest_resume_optimization(request: ResumeOptimizationRequest) -> ResumeOptimizationResponse:
    prompt_text = build_resume_optimization_prompt(
        request.jd_analysis, request.resume_analysis, request.gap_analysis
    )
    optimization = generate_structured_output(prompt_text, ResumeOptimization) or _suggest_optimization(
        request.jd_analysis, request.resume_analysis, request.gap_analysis
    )
    return ResumeOptimizationResponse(
        resume_optimization=optimization,
        analyzer_prompt=ResumeOptimizationPrompt(
            task=RESUME_OPTIMIZATION_TASK,
            prompt=prompt_text,
        ),
    )


def _analyze_gap(jd: JDAnalysis, resume: ResumeAnalysis) -> GapAnalysis:
    required = _unique(jd.required_skills)
    preferred = _unique(jd.preferred_skills)
    candidate_skills = _unique(resume.candidate_skills)
    candidate_keys = {_key(skill): skill for skill in candidate_skills}
    project_evidence = _project_evidence_by_skill(resume.projects)
    explicit_weak = {_key(skill) for skill in resume.weak_evidence_skills}

    matched: list[str] = []
    missing: list[str] = []
    weak: list[str] = []

    for skill in required:
        key = _key(skill)
        if key not in candidate_keys:
            missing.append(skill)
        elif key in explicit_weak or not project_evidence.get(key):
            weak.append(skill)
        else:
            matched.append(skill)

    for skill in preferred:
        key = _key(skill)
        if key in candidate_keys and key not in explicit_weak and project_evidence.get(key):
            matched.append(skill)
        elif key in candidate_keys:
            weak.append(skill)

    high_risk = _high_risk_topics(jd, resume, missing, weak)
    focus = _unique([
        *missing[:3],
        *weak[:3],
        *high_risk[:3],
        *jd.interview_focus[:3],
    ])[:8]
    summary = (
        f"已找到 {len(_unique(matched))} 个有简历证据支撑的 JD 相关技能；"
        f"{len(_unique(missing))} 个必需技能在简历中不可见；"
        f"{len(_unique(weak))} 个技能出现了但证据偏薄。"
        "“缺失”只表示简历中不可见，不代表候选人一定不会。"
    )
    return GapAnalysis(
        matched_skills=_unique(matched),
        missing_skills=_unique(missing),
        weak_evidence_skills=_unique(weak),
        high_risk_topics=_unique(high_risk),
        recommended_focus=focus,
        summary=summary,
    )


def _suggest_optimization(
    jd: JDAnalysis, resume: ResumeAnalysis, gap: GapAnalysis
) -> ResumeOptimization:
    suggestions: list[BulletImprovementSuggestion] = []
    rewrite_targets: list[str] = []
    positioning: list[str] = []
    warnings = [
        "只能补充真实且能在面试中解释清楚的细节。",
        "不要虚构工具、职责、指标、规模、生产环境使用或业务影响。",
    ]

    strongest_project = _strongest_project(resume.projects)
    for skill in gap.weak_evidence_skills[:4]:
        rewrite_targets.append(f"为 {skill} 补充真实项目中的证据。")
        suggestions.append(
            BulletImprovementSuggestion(
                original_issue=f"{skill} 有出现，但项目证据支撑不够强。",
                why_it_is_weak=(
                    "模拟面试会追问该技能如何使用、做过什么取舍，以及产生了什么结果。"
                ),
                suggested_direction=(
                    f"把 {skill} 连接到一个真实项目、实现选择、约束或简历中已有的可观察结果。"
                ),
                example_rewrite=(
                    f"如果属实：在 {strongest_project or '<真实项目>'} 中使用 {skill} 完成 <具体任务>，"
                    "因为 <约束/取舍> 选择了 <技术方案>。"
                ),
            )
        )

    if gap.missing_skills:
        rewrite_targets.append("澄清 JD 必需技能是真实缺失，还是只是没有在简历中体现。")
        suggestions.append(
            BulletImprovementSuggestion(
                original_issue=f"这些 JD 必需技能在简历中不可见：{', '.join(gap.missing_skills[:4])}。",
                why_it_is_weak="岗位可能会考察这些主题，但当前简历没有提供可用于练习的证据锚点。",
                suggested_direction=(
                    "如果没有真实经验，不要把这些技能加进简历；可以准备相邻经验或学习计划的诚实回答。"
                ),
                example_rewrite=(
                    "如果确实属实：在 <真实场景> 中使用 <缺失技能> 完成 <具体任务>。"
                    "如果不属实，就不要写入简历，改为诚实说明相邻经验。"
                ),
            )
        )

    for project in resume.projects:
        if project.evidence_quality.value == "low":
            rewrite_targets.append(f"让项目证据更具体：{project.name}。")
            suggestions.append(
                BulletImprovementSuggestion(
                    original_issue=f"{project.name} 的证据质量偏低，或亮点描述过于模糊。",
                    why_it_is_weak="模糊的项目描述很容易触发职责边界和实现细节追问。",
                    suggested_direction=(
                        "使用“行动 + 技术选择 + 约束/结果”的表达；只有真实存在时才加入指标。"
                    ),
                    example_rewrite=(
                        f"如果属实：在 {project.name} 中用 <真实工具> 搭建 <具体组件>，"
                        "解决 <具体问题>，并获得 <真实结果或复盘>。"
                    ),
                )
            )

    for skill in gap.matched_skills[:4]:
        positioning.append(f"把 {skill} 放在能证明它的项目证据附近。")

    for topic in gap.high_risk_topics[:5]:
        warnings.append(f"可能被面试追问的风险点：{topic}。")

    if not suggestions:
        suggestions.append(
            BulletImprovementSuggestion(
                original_issue="未发现明显的 JD 定向简历证据缺口。",
                why_it_is_weak="本地检查不是完整保证，仍需逐条核对每个 JD 相关主张。",
                suggested_direction="复查每个匹配技能，并为它准备一个具体项目例子。",
                example_rewrite="每个核心技能都准备：背景、你的行动、技术决策、结果和复盘。",
            )
        )

    return ResumeOptimization(
        optimization_summary=(
            "通过强化真实项目证据、澄清弱证据技能主张，并为缺失 JD 要求准备诚实回答来提升岗位贴合度。"
        ),
        rewrite_targets=_unique(rewrite_targets),
        bullet_improvement_suggestions=suggestions[:8],
        skill_positioning_suggestions=_unique(positioning),
        risk_warnings=_unique(warnings),
    )


def _project_evidence_by_skill(projects: list[ResumeProject]) -> dict[str, list[str]]:
    evidence: dict[str, list[str]] = {}
    for project in projects:
        if project.evidence_quality.value == "low":
            continue
        project_text = " ".join([project.name, *project.tech_stack, *project.highlights])
        for skill in project.tech_stack:
            if skill and skill.casefold() in project_text.casefold():
                evidence.setdefault(_key(skill), []).append(project.name)
    return evidence


def _high_risk_topics(
    jd: JDAnalysis, resume: ResumeAnalysis, missing: list[str], weak: list[str]
) -> list[str]:
    risks: list[str] = []
    risks.extend([f"缺少 JD 必需技能证据：{skill}" for skill in missing[:4]])
    risks.extend([f"JD 技能的简历证据偏弱：{skill}" for skill in weak[:4]])
    if not resume.projects:
        risks.append("项目深挖风险：简历中没有清晰项目证据。")
    if any(project.evidence_quality.value == "low" for project in resume.projects):
        low_projects = [project.name for project in resume.projects if project.evidence_quality.value == "low"]
        risks.append(f"项目证据风险：这些项目细节偏少：{', '.join(low_projects[:3])}。")
    if jd.uncertainty_notes:
        risks.append("JD 理解风险：规划面试前请先检查 JD 解析中的不确定项。")
    if resume.uncertainty_notes:
        risks.append("简历证据风险：规划面试前请先检查简历解析中的不确定项。")
    return risks


def _strongest_project(projects: list[ResumeProject]) -> str | None:
    for quality in ("high", "medium", "low"):
        for project in projects:
            if project.evidence_quality.value == quality:
                return project.name
    return None


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        clean = " ".join(str(item).split())
        key = _key(clean)
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def _key(value: str) -> str:
    return " ".join(value.casefold().split())
