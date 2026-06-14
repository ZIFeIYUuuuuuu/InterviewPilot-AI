import type {
  FlowState,
  GapAnalysis,
  HistoryItem,
  InputType,
  IntakeForm,
  InterviewAction,
  InterviewerPersona,
  InterviewType,
  InterviewPilotState,
  InterviewPlan,
  InterviewSessionState,
  InterviewVoiceConfig,
  VoiceSynthesisRequest,
  VoiceSynthesisResponse,
  JDAnalysis,
  ReportGenerationResponse,
  ResumeAnalysis,
  ResumeOptimization,
  SessionInput,
  VoiceProvider,
} from "../types/api";

declare global {
  interface Window {
    INTERVIEWPILOT_API_BASE?: string;
  }
}

const API_BASE = window.INTERVIEWPILOT_API_BASE || "/api/v1";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || "GET",
    headers: { "Content-Type": "application/json" },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof payload?.detail === "string" ? payload.detail : `请求失败：${response.status}`;
    throw new Error(message);
  }
  return payload as T;
}

type AnalysisInputPayload = {
  input_type: InputType;
  text?: string | null;
  content_base64?: string | null;
  filename?: string | null;
};

type AnalyzeJDResponse = { analysis_id: string; analysis: JDAnalysis; needs_manual_correction?: boolean };
type AnalyzeJDExtractionResponse = AnalyzeJDResponse & {
  extraction?: {
    raw_text?: string;
    status?: string;
    warnings?: string[];
    needs_manual_correction?: boolean;
  };
};
type AnalyzeResumeResponse = {
  analysis_id: string;
  analysis: ResumeAnalysis;
  extraction?: {
    raw_text?: string;
    status?: string;
    warnings?: string[];
    needs_manual_correction?: boolean;
  };
  needs_manual_correction?: boolean;
};
type SessionResponse = { session: InterviewPilotState };
type GapResponse = { gap_analysis: GapAnalysis };
type OptimizationResponse = { resume_optimization: ResumeOptimization };
type PlanResponse = { interview_plan: InterviewPlan };
type LiveResponse = { session: InterviewSessionState };
type HistoryResponse = { items: HistoryItem[] };

export async function runIntakePipeline(form: IntakeForm): Promise<FlowState> {
  const jdPayload = await buildInputPayload("JD", form.jdFile, form.jdText);
  const resumePayload = await buildInputPayload("简历", form.resumeFile, form.resumeText);
  const sessionInput: SessionInput = {
    target_role: form.targetRole,
    jd: {
      text: form.jdText || `已上传 JD 文件：${form.jdFile?.name || "未命名文件"}`,
      source_type: jdPayload.input_type,
      filename: form.jdFile?.name || null,
    },
    resume: {
      text: form.resumeText || `已上传简历文件：${form.resumeFile?.name || "未命名文件"}`,
      source_type: resumePayload.input_type,
      filename: form.resumeFile?.name || null,
    },
    interview_type: form.interviewType || "targeted_mock",
    interviewer_persona: form.interviewerPersona || "technical",
    difficulty: form.difficulty,
    duration_minutes: form.duration,
  };

  const productSession = await request<SessionResponse>("/sessions", {
    method: "POST",
    body: { input: sessionInput },
  });
  const jd = await request<AnalyzeJDResponse>("/jd/analyze", { method: "POST", body: jdPayload });
  const resume = await request<AnalyzeResumeResponse>("/resume/analyze", {
    method: "POST",
    body: resumePayload,
  });
  const gap = await request<GapResponse>("/analysis/gap", {
    method: "POST",
    body: { jd_analysis: jd.analysis, resume_analysis: resume.analysis },
  });
  const optimization = await request<OptimizationResponse>("/analysis/resume-optimization", {
    method: "POST",
    body: {
      jd_analysis: jd.analysis,
      resume_analysis: resume.analysis,
      gap_analysis: gap.gap_analysis,
    },
  });
  const plan = await request<PlanResponse>("/interview/plan", {
    method: "POST",
    body: {
      jd_analysis: jd.analysis,
      resume_analysis: resume.analysis,
      gap_analysis: gap.gap_analysis,
      interview_type: form.interviewType || "targeted_mock",
      interviewer_persona: form.interviewerPersona || "technical",
      difficulty: form.difficulty,
      duration_minutes: form.duration,
    },
  });
  const patched = await request<SessionResponse>(`/sessions/${productSession.session.session_id}`, {
    method: "PATCH",
    body: {
      status: "interview_ready",
      current_step: "interview_planning",
      jd_analysis: jd.analysis,
      resume_analysis: resume.analysis,
      gap_analysis: gap.gap_analysis,
      resume_optimization: optimization.resume_optimization,
      interview_plan: plan.interview_plan,
    },
  });

  return {
    productSession: patched.session,
    jdAnalysis: jd.analysis,
    resumeAnalysis: resume.analysis,
    gapAnalysis: gap.gap_analysis,
    resumeOptimization: optimization.resume_optimization,
    interviewPlan: plan.interview_plan,
    liveSession: null,
    reportResponse: null,
  };
}

export async function createInterviewPlanForFlow(
  flow: FlowState,
  interviewType: InterviewType,
  interviewerPersona: InterviewerPersona,
): Promise<InterviewPlan> {
  if (!flow.jdAnalysis || !flow.resumeAnalysis || !flow.gapAnalysis) {
    throw new Error("请先完成 JD、简历和差距分析，再调整面试模式。");
  }
  const response = await request<PlanResponse>("/interview/plan", {
    method: "POST",
    body: {
      jd_analysis: flow.jdAnalysis,
      resume_analysis: flow.resumeAnalysis,
      gap_analysis: flow.gapAnalysis,
      interview_type: interviewType,
      interviewer_persona: interviewerPersona,
      difficulty: flow.interviewPlan?.difficulty || "medium",
      duration_minutes: flow.interviewPlan?.duration_minutes || 20,
    },
  });
  return response.interview_plan;
}

export async function loadInterviewVoiceConfig(): Promise<InterviewVoiceConfig> {
  return request<InterviewVoiceConfig>("/interview/voice/config");
}

export async function extractResumeTextFromFile(file: File): Promise<{
  rawText: string;
  warnings: string[];
  needsManualCorrection: boolean;
}> {
  const name = file.name.toLowerCase();
  if (file.type.startsWith("text/") || /\.(txt|md)$/i.test(name)) {
    const rawText = (await file.text()).trim();
    return {
      rawText,
      warnings: rawText ? [] : ["文件里没有识别到可用文本，请换 PDF 或手动粘贴简历内容。"],
      needsManualCorrection: !rawText,
    };
  }
  const inputType = resumeInputTypeFromFile(file);
  if (!inputType) {
    return {
      rawText: "",
      warnings: ["暂不支持该文件格式。请上传 PDF/DOCX/TXT，或在启动页粘贴简历文本。"],
      needsManualCorrection: true,
    };
  }
  const response = await request<AnalyzeResumeResponse>("/resume/analyze", {
    method: "POST",
    body: {
      input_type: inputType,
      filename: file.name,
      content_base64: await readFileAsBase64(file),
    },
  });
  return {
    rawText: response.extraction?.raw_text || response.analysis.raw_resume_text || "",
    warnings: response.extraction?.warnings || response.analysis.uncertainty_notes || [],
    needsManualCorrection: Boolean(response.needs_manual_correction || response.extraction?.needs_manual_correction),
  };
}

export async function extractJDTextFromFile(file: File): Promise<{
  rawText: string;
  warnings: string[];
  needsManualCorrection: boolean;
}> {
  const name = file.name.toLowerCase();
  if (file.type.startsWith("text/") || /\.(txt|md)$/i.test(name)) {
    const rawText = (await file.text()).trim();
    return {
      rawText,
      warnings: rawText ? [] : ["文件里没有识别到可用文本，请换 PDF/图片或手动粘贴 JD 内容。"],
      needsManualCorrection: !rawText,
    };
  }
  const inputType = inputTypeFromFile(file, "JD");
  if (!inputType) {
    return {
      rawText: "",
      warnings: ["暂不支持该 JD 文件格式。请上传 PDF/图片，或直接粘贴 JD 文本。"],
      needsManualCorrection: true,
    };
  }
  const response = await request<AnalyzeJDExtractionResponse>("/jd/analyze", {
    method: "POST",
    body: {
      input_type: inputType,
      filename: file.name,
      content_base64: await readFileAsBase64(file),
    },
  });
  return {
    rawText: response.extraction?.raw_text || response.analysis.raw_jd_text || "",
    warnings: response.extraction?.warnings || response.analysis.uncertainty_notes || [],
    needsManualCorrection: Boolean(response.needs_manual_correction || response.extraction?.needs_manual_correction),
  };
}

export async function synthesizeInterviewVoice(
  payload: VoiceSynthesisRequest,
): Promise<VoiceSynthesisResponse> {
  return request<VoiceSynthesisResponse>("/interview/voice/synthesize", {
    method: "POST",
    body: payload,
  });
}

export async function listHistory(): Promise<HistoryItem[]> {
  const response = await request<HistoryResponse>("/sessions");
  return response.items || [];
}

export async function startLiveInterview(
  flow: FlowState,
  voiceProvider: VoiceProvider = "browser",
): Promise<InterviewSessionState> {
  if (!flow.interviewPlan || !flow.jdAnalysis || !flow.resumeAnalysis || !flow.gapAnalysis) {
    throw new Error("请先完成 JD、简历和差距分析，再进入模拟面试。");
  }
  const response = await request<LiveResponse>("/interview/sessions", {
    method: "POST",
    body: {
      session_id: flow.productSession?.session_id || null,
      interview_plan: flow.interviewPlan,
      jd_analysis: flow.jdAnalysis,
      resume_analysis: flow.resumeAnalysis,
      gap_analysis: flow.gapAnalysis,
      voice_provider: voiceProvider,
    },
  });
  return response.session;
}

export async function sendInterviewTurn(
  sessionId: string,
  action: InterviewAction,
  answer?: string,
): Promise<InterviewSessionState> {
  const response = await request<LiveResponse>(`/interview/sessions/${sessionId}/turn`, {
    method: "POST",
    body: { action, answer: answer || null },
  });
  return response.session;
}

export async function generateReport(flow: FlowState): Promise<ReportGenerationResponse> {
  if (!flow.liveSession) {
    throw new Error("还没有可生成报告的面试记录。");
  }
  return request<ReportGenerationResponse>("/reports/generate", {
    method: "POST",
    body: {
      interview_session: flow.liveSession,
      resume_optimization: flow.resumeOptimization,
    },
  });
}

export async function finishProductSession(sessionId: string, reportId: string): Promise<void> {
  await request<SessionResponse>(`/sessions/${sessionId}/finish`, {
    method: "POST",
    body: { report_id: reportId },
  });
}

export async function loadStoredReport(reportId: string): Promise<ReportGenerationResponse> {
  const stored = await request<NonNullable<ReportGenerationResponse["stored_report"]>>(`/reports/${reportId}`);
  return { report: stored.report, stored_report: stored };
}

export function userErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : "";
  if (message === "Failed to fetch" || message.includes("NetworkError") || message.includes("fetch")) {
    return "无法连接后端服务。请确认 FastAPI 后端已启动，或检查 INTERVIEWPILOT_API_BASE 配置。";
  }
  return message || "出现了一点问题，请稍后重试。";
}

async function buildInputPayload(
  label: "JD" | "简历",
  file: File | null,
  text: string,
): Promise<AnalysisInputPayload> {
  const cleanText = text.trim();
  if (!file && !cleanText) {
    throw new Error(`请粘贴${label}文本，或上传${label} PDF/图片文件。`);
  }
  if (!file) {
    return { input_type: "text", text: cleanText };
  }
  const inputType = inputTypeFromFile(file, label);
  if (!inputType) {
    throw new Error(`${label}文件格式不支持。请上传 PDF、PNG、JPG、JPEG 或 WebP 文件。`);
  }
  if (inputType === "image" && !cleanText) {
    throw new Error(`${label}图片上传当前需要文本兜底。请把图片中的文字粘贴到文本框后继续。`);
  }
  return {
    input_type: inputType,
    filename: file.name,
    content_base64: await readFileAsBase64(file),
    text: cleanText || null,
  };
}

function inputTypeFromFile(file: File, label: "JD" | "简历"): InputType | "" {
  const name = file.name.toLowerCase();
  if (file.type === "application/pdf" || name.endsWith(".pdf")) {
    return "pdf";
  }
  if (
    label === "简历" &&
    (file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
      name.endsWith(".docx"))
  ) {
    return "docx";
  }
  if (file.type.startsWith("image/") || /\.(png|jpe?g|webp)$/i.test(name)) {
    return "image";
  }
  return "";
}

function resumeInputTypeFromFile(file: File): "pdf" | "docx" | "" {
  const name = file.name.toLowerCase();
  if (file.type === "application/pdf" || name.endsWith(".pdf")) {
    return "pdf";
  }
  if (
    file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
    name.endsWith(".docx")
  ) {
    return "docx";
  }
  return "";
}

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",").pop() || "" : result);
    };
    reader.onerror = () => reject(new Error("文件读取失败，请重新选择文件。"));
    reader.readAsDataURL(file);
  });
}
