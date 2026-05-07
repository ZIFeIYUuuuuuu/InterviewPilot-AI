"""Evaluation and coaching report generation for the MVP."""

from __future__ import annotations

from .models import (
    CoachingImprovement,
    CoachingReport,
    Evaluation,
    GapAnalysis,
    InterviewMessage,
    InterviewPlan,
    JDAnalysis,
    ResumeOptimization,
    RubricScore,
)
from .text_utils import contains_metric, normalize_space


RUBRIC_DIMENSIONS = (
    "technical_accuracy",
    "depth",
    "structure",
    "communication",
    "role_fit",
    "evidence_quality",
)


def evaluate_interview(
    jd: JDAnalysis,
    gap: GapAnalysis,
    plan: InterviewPlan,
    messages: list[InterviewMessage],
) -> Evaluation:
    answers = [normalize_space(message.content) for message in messages if message.role == "candidate"]
    answer_text = " ".join(answers)
    dimension_scores = {
        "technical_accuracy": _score_dimension(
            _score_keyword_overlap(answer_text, jd.required_skills),
            "根据回答是否覆盖 JD 关键技术方向评分；真实技术正确性仍建议人工复核。",
        ),
        "depth": _score_dimension(
            _score_depth(answers),
            "根据回答长度、具体程度，以及是否说明技术取舍或结果评分。",
        ),
        "structure": _score_dimension(
            _score_structure(answer_text),
            "根据是否使用背景、行动、结果、首先、然后等结构化表达评分。",
        ),
        "communication": _score_dimension(
            _score_communication(answers),
            "根据回答是否简洁、完整且有实质内容评分。",
        ),
        "role_fit": _score_dimension(
            _score_keyword_overlap(answer_text, gap.matched_skills + gap.recommended_focus),
            "根据回答和目标岗位重点之间的可见连接评分。",
        ),
        "evidence_quality": _score_dimension(
            _score_evidence(answer_text),
            "根据具体项目证据、指标、职责边界和可观察结果评分。",
        ),
    }
    overall = round(sum(score.score for score in dimension_scores.values()) / len(dimension_scores))
    weaknesses = _evaluation_weaknesses(dimension_scores, gap)
    strengths = _evaluation_strengths(dimension_scores)
    risk_flags = gap.high_risk_topics[:]
    if not answers:
        risk_flags.append("没有候选人回答，因此报告置信度较低。")

    return Evaluation(
        overall_score=overall,
        dimension_scores=dimension_scores,
        strengths=strengths,
        weaknesses=weaknesses,
        risk_flags=risk_flags,
        summary=(
            f"{jd.role_title} 练习反馈：综合训练分 {overall}/100。"
            "这只是备考教练反馈，不是招聘判断。"
        ),
    )


def create_coaching_report(
    evaluation: Evaluation,
    gap: GapAnalysis,
    optimization: ResumeOptimization,
    messages: list[InterviewMessage],
) -> CoachingReport:
    improvements: list[CoachingImprovement] = []
    low_dimensions = [
        name for name, score in evaluation.dimension_scores.items() if score.score < 70
    ]
    for dimension in low_dimensions[:3]:
        improvements.append(_improvement_for_dimension(dimension))
    if gap.high_risk_topics:
        improvements.append(
            CoachingImprovement(
                issue="高风险 JD 或简历主题需要提前准备例子。",
                why_it_matters="面试很可能追问弱证据或缺失证据领域。",
                suggestion=f"为这个主题准备一个真实的 STAR 示例：{gap.high_risk_topics[0]}。",
                example_answer_guidance="使用“情境、任务、行动、结果”，再补一个技术取舍和一个复盘收获。",
            )
        )
    if not improvements:
        improvements.append(
            CoachingImprovement(
                issue="继续提升回答的具体程度。",
                why_it_matters="即使表现不错的回答，也会因为补充职责、选择和结果而更稳定。",
                suggestion="为每个核心项目准备一段两分钟深挖回答，以及两个可能追问。",
                example_answer_guidance="先交代背景，再说明你的职责，解释最难的决策，最后用结果收尾。",
            )
        )

    practice_plan = [
        "选择最强的 JD 匹配项目，做一次短项目深挖练习。",
        "重写或标注被优化建议指出的简历 bullet，但不要加入无证据主张。",
        "为每个高风险主题练习一个回答，重点说明取舍和证据。",
    ]
    if messages:
        practice_plan.append("复盘面试记录，标出缺少具体实现细节的回答。")

    return CoachingReport(
        summary="下一轮练习聚焦真实证据、技术深度和更紧凑的回答结构。",
        top_improvements=improvements[:4],
        practice_plan=practice_plan,
        next_round_focus=gap.recommended_focus[:4] or optimization.rewrite_targets[:3],
    )


def _score_dimension(score: int, reason: str) -> RubricScore:
    return RubricScore(score=max(0, min(100, score)), reason=reason)


def _score_keyword_overlap(text: str, keywords: list[str]) -> int:
    if not keywords:
        return 60
    lower = text.casefold()
    hits = sum(1 for keyword in keywords if keyword.casefold() in lower)
    return 45 + round(55 * min(1, hits / max(1, min(len(keywords), 4))))


def _score_depth(answers: list[str]) -> int:
    if not answers:
        return 20
    avg_words = sum(len(answer.split()) for answer in answers) / len(answers)
    score = 35 + min(45, round(avg_words * 1.5))
    joined = " ".join(answers).casefold()
    if any(marker in joined for marker in ("trade-off", "because", "result", "learned", "constraint")):
        score += 15
    return score


def _score_structure(text: str) -> int:
    lower = text.casefold()
    markers = ("first", "then", "finally", "context", "action", "result", "because", "therefore")
    return 45 + min(45, sum(10 for marker in markers if marker in lower))


def _score_communication(answers: list[str]) -> int:
    if not answers:
        return 20
    complete = sum(1 for answer in answers if len(answer.split()) >= 18)
    return 45 + round(45 * complete / len(answers))


def _score_evidence(text: str) -> int:
    score = 45
    lower = text.casefold()
    if contains_metric(text):
        score += 20
    if any(marker in lower for marker in ("built", "implemented", "designed", "owned", "deployed", "optimized")):
        score += 20
    if any(marker in lower for marker in ("result", "outcome", "users", "latency", "reduced", "increased")):
        score += 15
    return score


def _evaluation_weaknesses(
    dimension_scores: dict[str, RubricScore], gap: GapAnalysis
) -> list[str]:
    weaknesses = [
        f"{_dimension_label(name)} 需要改进：{score.reason}"
        for name, score in dimension_scores.items()
        if score.score < 70
    ]
    if gap.weak_evidence_skills:
        weaknesses.append(f"这些技能的简历证据仍然偏弱：{', '.join(gap.weak_evidence_skills[:3])}。")
    if gap.missing_skills:
        weaknesses.append(f"请围绕这些缺失 JD 技能准备诚实回答：{', '.join(gap.missing_skills[:3])}。")
    return weaknesses or ["本地评估器未发现明显短板；请继续人工复盘。"]


def _evaluation_strengths(dimension_scores: dict[str, RubricScore]) -> list[str]:
    strengths = [
        f"{_dimension_label(name)} 在本轮练习中相对较强。"
        for name, score in dimension_scores.items()
        if score.score >= 80
    ]
    return strengths or ["本轮会话已经产生足够证据，可用于生成针对性教练建议。"]


def _improvement_for_dimension(dimension: str) -> CoachingImprovement:
    labels = {
        "technical_accuracy": "把回答连接到 JD 中的具体技术概念。",
        "depth": "补充实现深度和技术取舍。",
        "structure": "使用更清晰的回答结构。",
        "communication": "让回答完整但保持简洁。",
        "role_fit": "把经历更直接地连接到目标岗位。",
        "evidence_quality": "用项目证据支撑主张。",
    }
    return CoachingImprovement(
        issue=labels.get(dimension, "提升回答质量。"),
        why_it_matters="该维度拉低了练习分数，也可能影响真实面试中的自信和表达稳定性。",
        suggestion="准备一个可复用回答模板，并针对两个追问进行练习。",
        example_answer_guidance="建议结构：背景 -> 我的行动 -> 技术决策 -> 取舍 -> 结果 -> 下次会如何改进。",
    )


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
