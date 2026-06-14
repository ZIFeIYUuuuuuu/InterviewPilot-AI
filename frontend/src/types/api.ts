export type Difficulty = "easy" | "medium" | "hard";
export type InterviewType = "targeted_mock" | "content_focus" | "role_fit" | "project_deep_dive" | "group";
export type InterviewerPersona = "warm" | "technical" | "pressure";
export type VoiceProvider = "disabled" | "browser" | "aliyun" | "doubao";
export type SessionStatus =
  | "draft"
  | "analysis_ready"
  | "interview_ready"
  | "in_progress"
  | "report_ready"
  | "archived";
export type WorkflowStep =
  | "jd_analysis"
  | "resume_analysis"
  | "gap_analysis"
  | "resume_optimization"
  | "interview_planning"
  | "interview"
  | "evaluation"
  | "coaching"
  | "report";
export type InputType = "text" | "pdf" | "image" | "docx";
export type InterviewAction = "answer" | "skip" | "next" | "end" | "regenerate";
export type LiveInterviewStatus = "in_progress" | "completed";

export interface SourceText {
  text: string;
  source_type: string;
  filename?: string | null;
}

export interface SessionInput {
  target_role: string;
  jd: SourceText;
  resume: SourceText;
  interview_type: InterviewType;
  interviewer_persona?: InterviewerPersona;
  difficulty: Difficulty;
  duration_minutes: number;
}

export interface JDAnalysis {
  role_title: string;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  interview_focus: string[];
  uncertainty_notes: string[];
  raw_jd_text?: string | null;
}

export interface ResumeProject {
  name: string;
  tech_stack: string[];
  highlights: string[];
  evidence_quality: "high" | "medium" | "low";
}

export interface ResumeAnalysis {
  candidate_skills: string[];
  projects: ResumeProject[];
  strengths: string[];
  weaknesses: string[];
  weak_evidence_skills: string[];
  resume_summary: string;
  uncertainty_notes: string[];
  raw_resume_text?: string | null;
}

export interface GapAnalysis {
  matched_skills: string[];
  missing_skills: string[];
  weak_evidence_skills: string[];
  high_risk_topics: string[];
  recommended_focus: string[];
  summary: string;
}

export interface BulletImprovementSuggestion {
  original_issue: string;
  why_it_is_weak: string;
  suggested_direction: string;
  example_rewrite: string;
  evidence_boundary?: string;
}

export interface ResumeOptimization {
  optimization_summary: string;
  rewrite_targets: string[];
  bullet_improvement_suggestions: BulletImprovementSuggestion[];
  skill_positioning_suggestions: string[];
  risk_warnings: string[];
}

export interface InterviewSection {
  name: string;
  duration_minutes: number;
  goal: string;
  focus_topics: string[];
}

export interface InterviewPlan {
  interview_type: InterviewType;
  interviewer_persona: InterviewerPersona;
  duration_minutes: number;
  difficulty: Difficulty;
  sections: InterviewSection[];
  max_questions: number;
  plan_summary: string;
}

export interface InterviewerOutput {
  question_type: "new_question" | "follow_up" | "transition";
  current_section: string;
  question: string;
  why_this_question: string;
  expected_signal: string;
}

export interface InterviewMessage {
  role: "system" | "interviewer" | "candidate" | "assistant";
  content: string;
  section?: string | null;
  message_id?: string | null;
  created_at?: string;
}

export interface InterviewSessionState {
  session_id: string;
  status: LiveInterviewStatus;
  interview_plan: InterviewPlan;
  jd_analysis: JDAnalysis;
  resume_analysis: ResumeAnalysis;
  gap_analysis: GapAnalysis;
  voice_provider?: VoiceProvider;
  messages: InterviewMessage[];
  current_section_index: number;
  current_question_count: number;
  latest_question?: InterviewerOutput | null;
  last_action?: InterviewAction | null;
  started_at?: string;
  updated_at?: string;
}

export interface DimensionScore {
  score: number;
  reason: string;
}

export interface Evaluation {
  overall_score: number;
  dimension_scores: Record<string, DimensionScore>;
  strengths: string[];
  weaknesses: string[];
  risk_flags: string[];
}

export interface CoachingImprovement {
  issue: string;
  why_it_matters: string;
  suggestion: string;
  example_answer_guidance: string;
}

export interface Coaching {
  summary?: string;
  top_improvements: CoachingImprovement[];
  practice_plan: string[];
  next_round_focus: string[];
}

export interface PracticeReport {
  session_id: string;
  evaluation: Evaluation;
  coaching: Coaching;
  gap_analysis: GapAnalysis;
  resume_optimization?: ResumeOptimization | null;
  disclaimer: string;
}

export interface StoredPracticeReport {
  report_id: string;
  session_id: string;
  report: PracticeReport;
  generated_at: string;
}

export interface ReportGenerationResponse {
  report: PracticeReport;
  stored_report?: StoredPracticeReport | null;
}

export interface InterviewPilotState {
  session_id: string;
  status: SessionStatus;
  current_step: WorkflowStep;
  input?: SessionInput | null;
  jd_analysis?: JDAnalysis | null;
  resume_analysis?: ResumeAnalysis | null;
  gap_analysis?: GapAnalysis | null;
  resume_optimization?: ResumeOptimization | null;
  interview_plan?: InterviewPlan | null;
  messages: InterviewMessage[];
  evaluation?: Evaluation | null;
  coaching?: Coaching | null;
  report?: unknown;
  errors: string[];
  created_at: string;
  updated_at: string;
}

export interface HistoryItem {
  session_id: string;
  target_role: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  overall_score?: number | null;
  weak_area_summary: string[];
  latest_report_id?: string | null;
}

export interface IntakeForm {
  targetRole: string;
  jdText: string;
  resumeText: string;
  jdFile: File | null;
  resumeFile: File | null;
  difficulty: Difficulty;
  duration: number;
  interviewType?: InterviewType;
  interviewerPersona?: InterviewerPersona;
}

export interface FlowState {
  productSession: InterviewPilotState | null;
  jdAnalysis: JDAnalysis | null;
  resumeAnalysis: ResumeAnalysis | null;
  gapAnalysis: GapAnalysis | null;
  resumeOptimization: ResumeOptimization | null;
  interviewPlan: InterviewPlan | null;
  liveSession: InterviewSessionState | null;
  reportResponse: ReportGenerationResponse | null;
}

export interface VoiceProviderStatus {
  provider: VoiceProvider;
  display_name: string;
  configured: boolean;
  enabled: boolean;
  required_env_vars: string[];
  model?: string | null;
  voice_id?: string | null;
  note: string;
}

export interface VoicePersonaProfile {
  persona: InterviewerPersona;
  display_name: string;
  model: string;
  voice_id: string;
  speech_rate: number;
  note: string;
}

export interface InterviewVoiceConfig {
  default_provider: VoiceProvider;
  browser_fallback_available: boolean;
  providers: VoiceProviderStatus[];
  persona_profiles: VoicePersonaProfile[];
  privacy_or_boundary_note: string;
}

export interface VoiceSynthesisRequest {
  text: string;
  provider: VoiceProvider;
  persona: InterviewerPersona;
  audio_format?: string;
  sample_rate?: number;
}

export interface VoiceSynthesisResponse {
  provider: VoiceProvider;
  persona: InterviewerPersona;
  model?: string | null;
  voice_id?: string | null;
  audio_url?: string | null;
  audio_base64?: string | null;
  audio_format: string;
  sample_rate: number;
  used_fallback: boolean;
  message: string;
  request_id?: string | null;
  expires_at?: number | null;
}
