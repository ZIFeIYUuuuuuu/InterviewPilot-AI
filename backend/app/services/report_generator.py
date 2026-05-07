"""Post-interview evaluation and coaching report generation."""

from __future__ import annotations

import re

from backend.app.schemas.coaching import CoachPrompt, Coaching, CoachingImprovement
from backend.app.schemas.common import InterviewMessageRole
from backend.app.schemas.evaluation import (
    Evaluation,
    EvaluationDimensionScores,
    EvaluatorPrompt,
    RubricScore,
)
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.interview import InterviewMessage, InterviewSessionState, LiveInterviewStatus
from backend.app.schemas.optimization import ResumeOptimization
from backend.app.schemas.report import PracticeReport, ReportGenerationResponse
from backend.app.services.coach_prompt import COACH_TASK, build_coach_prompt
from backend.app.services.evaluator_prompt import EVALUATOR_TASK, build_evaluator_prompt
from backend.app.services.llm_client import generate_structured_output

_STRUCTURE_MARKERS = ("context", "first", "then", "because", "therefore", "result", "outcome")
_STRUCTURE_MARKERS_ZH = ("背景", "首先", "然后", "因为", "所以", "结果", "收益", "复盘")
_TECHNICAL_MARKERS = (
    "api",
    "database",
    "schema",
    "cache",
    "latency",
    "test",
    "validation",
    "query",
    "trade-off",
)
_TECHNICAL_MARKERS_ZH = ("接口", "数据库", "缓存", "延迟", "测试", "校验", "查询", "取舍")
_ACTION_MARKERS = ("built", "implemented", "designed", "owned", "optimized", "measured", "debugged")
_ACTION_MARKERS_ZH = ("搭建", "实现", "设计", "负责", "优化", "度量", "排查", "推进")
_CONTROL_ANSWERS = {
    "ended the interview.",
    "skipped the question.",
    "asked to move to the next question.",
    "no substantive answer provided.",
    "已结束面试。",
    "已跳过当前问题。",
    "已请求进入下一题。",
    "未提供有效回答。",
}


class ReportGenerationError(ValueError):
    """Raised when the report cannot be generated from the provided state."""


def generate_practice_report(
    session: InterviewSessionState,
    resume_optimization: ResumeOptimization | None = None,
) -> ReportGenerationResponse:
    if session.status != LiveInterviewStatus.completed:
        raise ReportGenerationError("需要先完成模拟面试，才能生成练习报告。")

    answers = _candidate_answers(session.messages)
    evaluator_prompt_text = build_evaluator_prompt(
        session.jd_analysis,
        session.resume_analysis,
        session.gap_analysis,
        session.interview_plan,
        session.messages,
    )
    evaluation = generate_structured_output(evaluator_prompt_text, Evaluation) or _evaluate_session(
        session, answers
    )
    coach_prompt_text = build_coach_prompt(
        evaluation,
        session.gap_analysis,
        resume_optimization,
        session.messages,
    )
    coaching = generate_structured_output(coach_prompt_text, Coaching) or _create_coaching(
        session.gap_analysis, evaluation, resume_optimization, answers
    )
    report = PracticeReport(
        session_id=session.session_id,
        evaluation=evaluation,
        coaching=coaching,
        gap_analysis=session.gap_analysis,
        resume_optimization=resume_optimization,
    )
    return ReportGenerationResponse(
        report=report,
        evaluator_prompt=EvaluatorPrompt(
            task=EVALUATOR_TASK,
            prompt=evaluator_prompt_text,
        ),
        coach_prompt=CoachPrompt(
            task=COACH_TASK,
            prompt=coach_prompt_text,
        ),
    )


def _evaluate_session(session: InterviewSessionState, answers: list[str]) -> Evaluation:
    answer_text = " ".join(answers)
    scores = EvaluationDimensionScores(
        technical_accuracy=_rubric(
            _score_keyword_overlap(answer_text, session.jd_analysis.required_skills, base=42),
            _technical_reason(session.jd_analysis.required_skills, answer_text),
        ),
        depth=_rubric(
            _score_depth(answers),
            "根据回答长度、实现细节、取舍说明和结果证据进行练习评分。",
        ),
        structure=_rubric(
            _score_structure(answer_text),
            "根据回答是否包含清晰顺序、因果关系、背景、行动、理由或结果来判断结构清晰度。",
        ),
        communication=_rubric(
            _score_communication(answers),
            "根据回答是否有实质内容、是否容易跟上、是否避免跳过来判断沟通质量。",
        ),
        role_fit=_rubric(
            _score_keyword_overlap(
                answer_text,
                [*session.gap_analysis.matched_skills, *session.gap_analysis.recommended_focus],
                base=45,
            ),
            "根据回答与 JD 重点、已匹配技能和推荐练习重点之间的可见连接来判断岗位贴合度。",
        ),
        evidence_quality=_rubric(
            _score_evidence(answer_text, [project.name for project in session.resume_analysis.projects]),
            "根据具体项目证据、个人职责、技术决策、指标和结果来判断证据质量。",
        ),
    )
    score_values = [score["score"] for score in scores.model_dump().values()]
    overall = round(sum(score_values) / len(score_values))
    return Evaluation(
        overall_score=overall,
        dimension_scores=scores,
        strengths=_strengths(scores, session.gap_analysis),
        weaknesses=_weaknesses(scores, session.gap_analysis),
        risk_flags=_risk_flags(session.gap_analysis, answers),
        summary=(
            f"{session.jd_analysis.role_title} 练习报告：{overall}/100。"
            "这是基于面试记录生成的备考反馈，不代表招聘或录用判断。"
        ),
    )


def _create_coaching(
    gap: GapAnalysis,
    evaluation: Evaluation,
    resume_optimization: ResumeOptimization | None,
    answers: list[str],
) -> Coaching:
    improvements: list[CoachingImprovement] = []
    dimension_map = evaluation.dimension_scores.model_dump()
    low_dimensions = [name for name, value in dimension_map.items() if value["score"] < 70]
    for dimension in low_dimensions[:3]:
        improvements.append(_improvement_for_dimension(dimension, gap))

    if gap.high_risk_topics:
        improvements.append(
            CoachingImprovement(
                issue="为最高风险岗位主题准备真实可解释的回答。",
                why_it_matters=f"差距分析认为这里可能被追问：{gap.high_risk_topics[0]}。",
                suggestion="准备一个两分钟示例，清楚说明你做过什么、没做过什么，以及证据较薄时会如何补齐能力。",
                example_answer_guidance="建议结构：背景 -> 我的职责 -> 技术选择 -> 取舍 -> 结果 -> 真实边界。",
            )
        )

    if resume_optimization and resume_optimization.risk_warnings:
        improvements.append(
            CoachingImprovement(
                issue="让简历表达和面试证据保持一致。",
                why_it_matters="简历措辞会触发追问，因此每个强化表达都需要具体证据支撑。",
                suggestion=f"复查这条风险提醒，使用该表达前先准备可说明的证据：{resume_optimization.risk_warnings[0]}",
                example_answer_guidance="每条优化后的 bullet 至少配一个实现细节和一个你能如实解释的限制。",
            )
        )

    if not improvements:
        improvements.append(
            CoachingImprovement(
                issue="把表现较好的回答沉淀成可复用模板。",
                why_it_matters="稳定结构能把一次练习中的好回答转化为真实面试中的稳定发挥。",
                suggestion="整理一个回答库：一个项目深挖、一个技术取舍故事、一个短板应对回答。",
                example_answer_guidance="先说问题，再说明你的职责，解释一个关键决策，最后给出结果和复盘。",
            )
        )

    practice_plan = [
        "选择一个弱证据或缺失的 JD 技能，写一段 90 秒真实说明：当前证据是什么、下一步如何补齐。",
        "重做面试记录里最弱的一题，使用“背景 -> 行动 -> 技术决策 -> 取舍 -> 结果”的结构。",
        "围绕简历中最强项目准备两个追问回答，每个都包含实现细节和真实限制。",
    ]
    if resume_optimization and resume_optimization.bullet_improvement_suggestions:
        practice_plan.append(
            "选择一条简历优化建议，在使用更强表达前先补上具体证据。"
        )
    if answers:
        practice_plan.append("复盘面试记录，标出每个缺少具体例子的主张。")

    return Coaching(
        summary="下一轮练习应聚焦：有证据支撑的具体表达、JD 高风险主题，以及更紧凑的回答结构。",
        top_improvements=improvements[:4],
        practice_plan=practice_plan,
        next_round_focus=_next_round_focus(gap, evaluation, resume_optimization),
    )


def _candidate_answers(messages: list[InterviewMessage]) -> list[str]:
    answers = []
    for message in messages:
        if message.role != InterviewMessageRole.candidate:
            continue
        normalized = _normalize(message.content)
        if normalized.casefold() not in _CONTROL_ANSWERS:
            answers.append(normalized)
    return answers


def _rubric(score: int, reason: str) -> RubricScore:
    return RubricScore(score=max(0, min(100, score)), reason=reason)


def _score_keyword_overlap(text: str, keywords: list[str], base: int) -> int:
    cleaned = [_normalize(keyword) for keyword in keywords if _normalize(keyword)]
    if not cleaned:
        return 60
    lower = text.casefold()
    hits = sum(1 for keyword in cleaned if keyword.casefold() in lower)
    return base + round((100 - base) * min(1, hits / max(1, min(len(cleaned), 4))))


def _score_depth(answers: list[str]) -> int:
    if not answers:
        return 20
    avg_words = sum(len(answer.split()) for answer in answers) / len(answers)
    score = 30 + min(40, round(avg_words * 1.4))
    lower = " ".join(answers).casefold()
    if any(marker in lower for marker in ("because", "trade-off", "constraint", "outcome", "latency")):
        score += 15
    if any(marker in " ".join(answers) for marker in ("因为", "取舍", "约束", "结果", "延迟")):
        score += 15
    if any(marker in lower for marker in _ACTION_MARKERS) or any(
        marker in " ".join(answers) for marker in _ACTION_MARKERS_ZH
    ):
        score += 10
    return score


def _score_structure(text: str) -> int:
    if not text.strip():
        return 20
    lower = text.casefold()
    markers = sum(1 for marker in _STRUCTURE_MARKERS if marker in lower)
    markers += sum(1 for marker in _STRUCTURE_MARKERS_ZH if marker in text)
    return 42 + min(48, markers * 8)


def _score_communication(answers: list[str]) -> int:
    if not answers:
        return 20
    substantive = sum(1 for answer in answers if 18 <= len(answer.split()) <= 160)
    return 45 + round(45 * substantive / len(answers))


def _score_evidence(text: str, project_names: list[str]) -> int:
    if not text.strip():
        return 20
    lower = text.casefold()
    score = 38
    if any(marker in lower for marker in _ACTION_MARKERS) or any(marker in text for marker in _ACTION_MARKERS_ZH):
        score += 18
    if any(marker in lower for marker in _TECHNICAL_MARKERS) or any(marker in text for marker in _TECHNICAL_MARKERS_ZH):
        score += 18
    if re.search(r"\d|percent|latency|users|requests|reduced|increased|measured|百分|用户|请求|降低|提升|度量", lower):
        score += 14
    if any(project.casefold() in lower for project in project_names):
        score += 12
    return score


def _technical_reason(required_skills: list[str], text: str) -> str:
    matched = [skill for skill in required_skills if skill.casefold() in text.casefold()]
    if matched:
        return f"面试记录提到了 JD 要求的技术方向：{', '.join(matched[:4])}。"
    return "面试记录没有清晰覆盖 JD 要求的技术方向，因此这里仍是练习风险。"


def _strengths(scores: EvaluationDimensionScores, gap: GapAnalysis) -> list[str]:
    strengths = [
        f"{_dimension_label(name)} 在本轮练习中相对较强。"
        for name, value in scores.model_dump().items()
        if value["score"] >= 80
    ]
    if gap.matched_skills:
        strengths.append(f"已有岗位贴合基础，匹配技能包括：{', '.join(gap.matched_skills[:3])}。")
    return strengths or ["这次面试记录已经提供了足够信息，可用于生成下一步针对性练习建议。"]


def _weaknesses(scores: EvaluationDimensionScores, gap: GapAnalysis) -> list[str]:
    weaknesses = [
        f"{_dimension_label(name)} 需要加强：{value['reason']}"
        for name, value in scores.model_dump().items()
        if value["score"] < 70
    ]
    if gap.weak_evidence_skills:
        weaknesses.append(f"这些技能仍然证据偏薄：{', '.join(gap.weak_evidence_skills[:3])}。")
    if gap.missing_skills:
        weaknesses.append(f"请为这些缺失技能准备真实的短板应对回答：{', '.join(gap.missing_skills[:3])}。")
    return weaknesses or ["本地评估器未发现严重短板；仍建议人工复盘面试细节。"]


def _risk_flags(gap: GapAnalysis, answers: list[str]) -> list[str]:
    risks = gap.high_risk_topics[:]
    answer_text = " ".join(answers).casefold()
    for skill in gap.missing_skills[:3]:
        if skill.casefold() not in answer_text:
            risks.append(f"面试记录没有回应该缺失 JD 技能：{skill}。")
    for skill in gap.weak_evidence_skills[:3]:
        if skill.casefold() not in answer_text:
            risks.append(f"该弱证据技能还需要准备可面试说明的例子：{skill}。")
    if not answers:
        risks.append("没有可用的实质回答，因此报告置信度较低。")
    return _dedupe(risks)


def _improvement_for_dimension(dimension: str, gap: GapAnalysis) -> CoachingImprovement:
    details = {
        "technical_accuracy": (
            "把回答和 JD 要求的技术概念连接起来。",
            "报告显示必需技术方向在回答中的可见度偏弱。",
            f"选择一个 JD 主题，例如 {(gap.recommended_focus or gap.missing_skills or ['核心岗位要求'])[0]}，准备包含实现细节的具体说明。",
        ),
        "depth": (
            "补充实现深度和技术取舍。",
            "面试官通常会追问第一层答案背后的职责边界和判断依据。",
            "每个项目回答都补一个约束、一个被你放弃的替代方案，以及一个结果或复盘。",
        ),
        "structure": (
            "使用更清晰的回答结构。",
            "有结构的回答能让技术深度在时间压力下更容易被听懂。",
            "用“背景 -> 行动 -> 技术决策 -> 结果”重练同一个回答。",
        ),
        "communication": (
            "让回答完整，但不要发散。",
            "过短或跳过的回答会减少可用于教练反馈的证据。",
            "每个核心回答控制在 60-90 秒，然后主动留下一个最值得追问的技术点。",
        ),
        "role_fit": (
            "把例子直接连接到目标岗位。",
            "如果回答只停留在项目本身，JD 相关价值会被弱化。",
            "每个回答开头先点明它对应的 JD 职责或面试重点。",
        ),
        "evidence_quality": (
            "用具体项目证据支撑主张。",
            "当面试回答缺少职责、指标或实现细节时，简历主张会变成风险点。",
            "每个主张都附一个证据：你搭建了什么、度量了什么、改变了什么或学到了什么。",
        ),
    }
    issue, why, suggestion = details.get(
        dimension,
        ("提升回答质量。", "该维度拉低了练习分数。", "准备一个更具体的例子。"),
    )
    return CoachingImprovement(
        issue=issue,
        why_it_matters=why,
        suggestion=suggestion,
        example_answer_guidance="建议结构：背景 -> 我的职责 -> 技术选择 -> 取舍 -> 结果 -> 下一步改进。",
    )


def _next_round_focus(
    gap: GapAnalysis,
    evaluation: Evaluation,
    resume_optimization: ResumeOptimization | None,
) -> list[str]:
    focus = [*gap.high_risk_topics[:2], *gap.recommended_focus[:3]]
    low_dimensions = [
        _dimension_label(name)
        for name, value in evaluation.dimension_scores.model_dump().items()
        if value["score"] < 70
    ]
    focus.extend(low_dimensions[:2])
    if resume_optimization:
        focus.extend(resume_optimization.rewrite_targets[:2])
    return _dedupe(focus)[:6] or ["项目深挖", "JD 风险主题", "回答结构"]


def _dimension_label(name: str) -> str:
    labels = {
        "technical_accuracy": "技术准确性",
        "depth": "回答深度",
        "structure": "回答结构",
        "communication": "沟通表达",
        "role_fit": "岗位贴合度",
        "evidence_quality": "证据质量",
    }
    return labels.get(name, name.replace("_", " "))


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        clean = _normalize(item)
        key = clean.casefold()
        if clean and key not in seen:
            result.append(clean)
            seen.add(key)
    return result
