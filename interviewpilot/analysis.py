"""Dependency-free analysis pipeline for the first text-based MVP."""

from __future__ import annotations

import re

from .models import (
    BulletImprovementSuggestion,
    GapAnalysis,
    JDAnalysis,
    ResumeAnalysis,
    ResumeOptimization,
    ResumeProject,
)
from .text_utils import (
    compact_list,
    contains_action_evidence,
    contains_metric,
    extract_skills,
    normalize_space,
    split_lines,
    split_sentences,
    unique_preserve_order,
)


def analyze_jd(jd_text: str) -> JDAnalysis:
    lines = split_lines(jd_text)
    skills = extract_skills(jd_text)
    required: list[str] = []
    preferred: list[str] = []
    responsibilities: list[str] = []

    for line in lines:
        lower = line.casefold()
        line_skills = extract_skills(line)
        if any(marker in lower for marker in ("required", "must", "need", "requirements", "任职要求", "必须")):
            required.extend(line_skills)
        elif any(marker in lower for marker in ("preferred", "nice", "plus", "加分", "优先")):
            preferred.extend(line_skills)
        elif any(marker in lower for marker in ("responsib", "you will", "work on", "负责", "职责")):
            responsibilities.append(line)

    required = unique_preserve_order(required or skills[:6])
    preferred = [skill for skill in unique_preserve_order(preferred) if skill not in required]
    responsibilities = compact_list(responsibilities or split_sentences(jd_text), 6)
    role_title = _extract_role_title(lines)
    interview_focus = _derive_interview_focus(required, preferred, responsibilities)
    uncertainty_notes = []
    if not jd_text.strip():
        uncertainty_notes.append("JD 文本为空；当前分析使用保守默认值。")
    if not skills:
        uncertainty_notes.append("JD 中没有检测到清晰技术技能。")
    if role_title == "目标岗位":
        uncertainty_notes.append("JD 中没有明确岗位名称。")

    return JDAnalysis(
        role_title=role_title,
        required_skills=required,
        preferred_skills=preferred,
        responsibilities=responsibilities,
        interview_focus=interview_focus,
        uncertainty_notes=uncertainty_notes,
        raw_jd_text=jd_text,
    )


def analyze_resume(resume_text: str) -> ResumeAnalysis:
    skills = extract_skills(resume_text)
    projects = _extract_projects(resume_text, skills)
    strengths = _derive_strengths(resume_text, skills, projects)
    weak_evidence = _derive_weak_evidence_skills(resume_text, skills, projects)
    weaknesses = _derive_resume_weaknesses(resume_text, projects, weak_evidence)
    uncertainty_notes = []
    if not resume_text.strip():
        uncertainty_notes.append("简历文本为空；请用户手动粘贴简历内容。")
    if not projects:
        uncertainty_notes.append("未检测到项目模块；项目证据可能不完整。")
    if not skills:
        uncertainty_notes.append("简历中没有检测到清晰技术技能。")

    return ResumeAnalysis(
        candidate_skills=skills,
        projects=projects,
        strengths=strengths,
        weaknesses=weaknesses,
        weak_evidence_skills=weak_evidence,
        resume_summary=_resume_summary(skills, projects),
        uncertainty_notes=uncertainty_notes,
        raw_resume_text=resume_text,
    )


def analyze_gaps(jd: JDAnalysis, resume: ResumeAnalysis) -> GapAnalysis:
    resume_skill_keys = {skill.casefold(): skill for skill in resume.candidate_skills}
    matched = [skill for skill in jd.required_skills + jd.preferred_skills if skill.casefold() in resume_skill_keys]
    missing = [skill for skill in jd.required_skills if skill.casefold() not in resume_skill_keys]
    weak = [
        skill
        for skill in jd.required_skills + jd.preferred_skills
        if skill in resume.weak_evidence_skills and skill.casefold() in resume_skill_keys
    ]
    high_risk = _derive_high_risk_topics(jd, resume, missing, weak)
    focus = unique_preserve_order(missing[:3] + weak[:3] + jd.interview_focus[:3])
    summary = (
        f"匹配到 {len(unique_preserve_order(matched))} 个岗位相关技能；"
        f"{len(unique_preserve_order(missing))} 个必需技能在简历中不可见；"
        f"{len(unique_preserve_order(weak))} 个技能需要更强证据。"
    )
    return GapAnalysis(
        matched_skills=unique_preserve_order(matched),
        missing_skills=unique_preserve_order(missing),
        weak_evidence_skills=unique_preserve_order(weak),
        high_risk_topics=unique_preserve_order(high_risk),
        recommended_focus=focus[:6],
        summary=summary,
    )


def suggest_resume_optimization(
    jd: JDAnalysis, resume: ResumeAnalysis, gap: GapAnalysis
) -> ResumeOptimization:
    rewrite_targets = []
    suggestions: list[BulletImprovementSuggestion] = []

    if gap.weak_evidence_skills:
        rewrite_targets.append("强化已匹配但证据偏弱的 JD 技能证据。")
        suggestions.append(
            BulletImprovementSuggestion(
                original_issue=f"这些技能被提到，但缺少足够项目证据：{', '.join(gap.weak_evidence_skills[:4])}。",
                why_it_is_weak="面试官很可能追问具体职责、技术取舍和结果。",
                suggested_direction="把每个技能主张连接到简历中真实存在的项目、实现选择或可观察结果。",
                example_rewrite="如果属实：用 <真实技能> 搭建 <功能>，说明 <技术选择> 和观察到的 <量化或定性结果>。",
            )
        )
    if gap.missing_skills:
        rewrite_targets.append("澄清 JD 缺失技能是真实没有，还是只是简历中没有体现。")
        suggestions.append(
            BulletImprovementSuggestion(
                original_issue=f"这些 JD 必需技能在简历中不可见：{', '.join(gap.missing_skills[:4])}。",
                why_it_is_weak="当前简历没有提供证据，模拟面试应该重点压力测试这些领域。",
                suggested_direction="只有候选人有真实经验时才加入技能；否则准备诚实的学习计划或相邻经验说明。",
                example_rewrite="如果你确实用过该技能：在 <真实项目> 中用 <技能> 完成 <具体任务>，并说明 <约束/取舍>。",
            )
        )
    if any(project.evidence_quality == "low" for project in resume.projects):
        rewrite_targets.append("让低证据项目描述更具体。")
        suggestions.append(
            BulletImprovementSuggestion(
                original_issue="部分项目描述缺少行动、技术决策或结果。",
                why_it_is_weak="模糊项目主张会引发难以自洽的追问。",
                suggested_direction="在保持真实的前提下，使用简洁的“行动-场景-结果”结构。",
                example_rewrite="为 <项目场景> 实现 <真实组件>，使用 <真实工具> 解决 <具体问题>。",
            )
        )

    if not suggestions:
        suggestions.append(
            BulletImprovementSuggestion(
                original_issue="本地分析器未发现明显简历证据缺口。",
                why_it_is_weak="这不代表简历已经完整，只表示没有发现显著缺口。",
                suggested_direction="复查 JD 核心要求，确保每个重要主张都有项目例子支撑。",
                example_rewrite="每个重要技能都准备一条真实项目 bullet，包含行动、技术选择和结果。",
            )
        )

    risk_warnings = [
        "不要加入不真实或无法在面试中解释的工具、指标、职责或成果。",
        "简历建议只用于优化表达，不是虚构经历的许可。",
    ]
    if gap.high_risk_topics:
        risk_warnings.append(f"请准备这些主题的追问回答：{', '.join(gap.high_risk_topics[:4])}。")

    return ResumeOptimization(
        optimization_summary=(
            "模拟面试前优先强化 JD 相关证据、项目职责边界和真实具体表达。"
        ),
        rewrite_targets=unique_preserve_order(rewrite_targets),
        bullet_improvement_suggestions=suggestions,
        skill_positioning_suggestions=[
            f"把 {skill} 的最强证据放在最相关项目附近。"
            for skill in gap.matched_skills[:3]
        ],
        risk_warnings=risk_warnings,
    )


def _extract_role_title(lines: list[str]) -> str:
    for line in lines[:8]:
        lower = line.casefold()
        if any(token in lower for token in ("engineer", "developer", "backend", "full-stack", "ai", "工程师")):
            return normalize_space(re.sub(r"^(job title|role|position|职位)[:：]\s*", "", line, flags=re.I))[:80]
    return "目标岗位"


def _derive_interview_focus(
    required: list[str], preferred: list[str], responsibilities: list[str]
) -> list[str]:
    focus = [f"{skill} 的深度和实践取舍" for skill in required[:4]]
    if preferred:
        focus.append(f"加分项经验：{', '.join(preferred[:3])}")
    if responsibilities:
        focus.append("与岗位职责相关的项目职责边界和实现细节")
    return unique_preserve_order(focus)[:6]


def _extract_projects(resume_text: str, skills: list[str]) -> list[ResumeProject]:
    lines = split_lines(resume_text)
    project_lines = [
        line
        for line in lines
        if any(marker in line.casefold() for marker in ("project", "项目", "built", "implemented", "developed", "系统"))
    ]
    if not project_lines and lines:
        project_lines = [line for line in lines if extract_skills(line)][:3]

    projects: list[ResumeProject] = []
    for index, line in enumerate(project_lines[:4], start=1):
        project_skills = extract_skills(line) or skills[:3]
        evidence_quality = "high" if contains_metric(line) and contains_action_evidence(line) else "medium"
        if not contains_metric(line) and len(line.split()) < 18:
            evidence_quality = "low"
        projects.append(
            ResumeProject(
                name=_project_name(line, index),
                tech_stack=project_skills,
                highlights=[line],
                evidence_quality=evidence_quality,
            )
        )
    return projects


def _project_name(line: str, index: int) -> str:
    clean = normalize_space(line)
    match = re.match(r"([^:：|-]{3,50})[:：|-]", clean)
    if match:
        return match.group(1).strip()
    return f"项目 {index}"


def _derive_strengths(
    resume_text: str, skills: list[str], projects: list[ResumeProject]
) -> list[str]:
    strengths = []
    if skills:
        strengths.append(f"体现了 {', '.join(skills[:5])} 相关经验。")
    if projects:
        strengths.append(f"包含 {len(projects)} 条可用于面试讨论的项目证据。")
    if contains_metric(resume_text):
        strengths.append("包含至少一个量化结果或规模信号。")
    return strengths or ["简历中可分析证据有限；建议让用户补充更多细节。"]


def _derive_weak_evidence_skills(
    resume_text: str, skills: list[str], projects: list[ResumeProject]
) -> list[str]:
    evidence_text = " ".join(" ".join(project.highlights) for project in projects)
    weak = []
    for skill in skills:
        if skill.casefold() not in evidence_text.casefold():
            weak.append(skill)
    if projects and all(project.evidence_quality == "low" for project in projects):
        weak.extend(skills[:4])
    return unique_preserve_order(weak)


def _derive_resume_weaknesses(
    resume_text: str, projects: list[ResumeProject], weak_evidence: list[str]
) -> list[str]:
    weaknesses = []
    if not projects:
        weaknesses.append("项目证据不够清晰。")
    if weak_evidence:
        weaknesses.append("部分已列技能没有和项目证据强连接。")
    if not contains_metric(resume_text):
        weaknesses.append("简历缺少量化结果或规模信号。")
    return weaknesses or ["本地分析器未发现明显短板；仍建议人工复查。"]


def _resume_summary(skills: list[str], projects: list[ResumeProject]) -> str:
    if not skills and not projects:
        return "需要更结构化的简历文本，才能进行可靠分析。"
    return f"检测到 {len(skills)} 个技能和 {len(projects)} 条项目证据。"


def _derive_high_risk_topics(
    jd: JDAnalysis, resume: ResumeAnalysis, missing: list[str], weak: list[str]
) -> list[str]:
    risks = []
    risks.extend([f"缺少 JD 要求证据：{skill}" for skill in missing[:3]])
    risks.extend([f"{skill} 的简历证据偏弱" for skill in weak[:3]])
    if not resume.projects:
        risks.append("简历项目证据较少，项目深挖可能会困难")
    if jd.required_skills and not resume.candidate_skills:
        risks.append("简历技能不明确，因此技术贴合度难以评估")
    return risks
