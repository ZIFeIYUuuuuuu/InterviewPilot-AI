import type { Difficulty, SessionStatus } from "../types/api";

export const difficultyLabel: Record<Difficulty, string> = {
  easy: "稳扎稳打",
  medium: "标准冲刺",
  hard: "高压追问",
};

export const statusLabel: Record<SessionStatus, string> = {
  draft: "草稿",
  analysis_ready: "分析完成",
  interview_ready: "可开始面试",
  in_progress: "训练中",
  report_ready: "报告已生成",
  archived: "已归档",
};

export const dimensionLabel: Record<string, string> = {
  technical_accuracy: "技术准确性",
  depth: "回答深度",
  structure: "结构化表达",
  communication: "沟通清晰度",
  role_fit: "岗位贴合度",
  evidence_quality: "证据质量",
};

export const roleLabel: Record<string, string> = {
  interviewer: "AI 面试官",
  candidate: "我",
  assistant: "AI 助手",
  system: "系统",
};

export const questionTypeLabel: Record<string, string> = {
  new_question: "新问题",
  follow_up: "追问",
  transition: "转场",
};

export function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
