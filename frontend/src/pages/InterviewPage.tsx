import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  Award,
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Clock,
  Flame,
  GitBranch,
  HeartHandshake,
  Mic,
  MicOff,
  Pause,
  Play,
  Radar,
  RotateCcw,
  Send,
  Settings2,
  ShieldAlert,
  Sparkles,
  Target,
  Users,
  Volume2,
  VolumeX,
  Zap,
} from "lucide-react";
import { ChipList, EmptyState } from "../components/Shell";
import { questionTypeLabel, roleLabel } from "../lib/labels";
import { synthesizeInterviewVoice } from "../lib/api";
import type { RouteId } from "../components/Shell";
import type {
  FlowState,
  InterviewAction,
  InterviewType,
  InterviewerPersona,
  InterviewVoiceConfig,
  VoiceProvider,
} from "../types/api";

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

type SpeechRecognitionConstructor = new () => SpeechRecognition;
type SpeechRecognition = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};
type SpeechRecognitionEvent = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
};

interface InterviewPageProps {
  flow: FlowState;
  busy: boolean;
  voiceConfig: InterviewVoiceConfig | null;
  onNavigate: (route: RouteId) => void;
  onStartInterview: (options?: {
    interviewType?: InterviewType;
    interviewerPersona?: InterviewerPersona;
    voiceProvider?: VoiceProvider;
  }) => void;
  onTurn: (action: InterviewAction, answer?: string) => void;
  onGenerateReport: () => void;
}

const interviewTypes: Array<{
  value: InterviewType;
  title: string;
  desc: string;
  icon: typeof BrainCircuit;
}> = [
  { value: "content_focus", title: "内容面", desc: "重点追问知识理解、表达结构和真实掌握边界。", icon: BrainCircuit },
  { value: "role_fit", title: "岗位匹配面", desc: "看经历、动机、协作方式是否能支撑目标岗位训练。", icon: Target },
  { value: "project_deep_dive", title: "项目面", desc: "围绕项目背景、职责边界、技术方案和复盘深挖。", icon: GitBranch },
  { value: "group", title: "群面", desc: "训练观点陈述、倾听回应、冲突协作和总结表达。", icon: Users },
];

const interviewerPersonas: Array<{
  value: InterviewerPersona;
  title: string;
  desc: string;
  icon: typeof HeartHandshake;
}> = [
  { value: "warm", title: "温和面试官", desc: "语气更耐心，仍然要求具体证据。", icon: HeartHandshake },
  { value: "technical", title: "技术面试官", desc: "聚焦机制、实现细节、边界和取舍。", icon: Cpu },
  { value: "pressure", title: "压力面试官", desc: "问题更尖锐，但保持训练边界和尊重。", icon: Flame },
];

export function InterviewPage({
  flow,
  busy,
  voiceConfig,
  onNavigate,
  onStartInterview,
  onTurn,
  onGenerateReport,
}: InterviewPageProps) {
  const [answer, setAnswer] = useState("");
  const [interviewType, setInterviewType] = useState<InterviewType>(
    (flow.interviewPlan?.interview_type as InterviewType) || "project_deep_dive",
  );
  const [interviewerPersona, setInterviewerPersona] = useState<InterviewerPersona>(
    flow.interviewPlan?.interviewer_persona || "technical",
  );
  const [voiceProvider, setVoiceProvider] = useState<VoiceProvider>(
    voiceConfig?.default_provider === "disabled" ? "browser" : voiceConfig?.default_provider || "browser",
  );
  const [voiceNotice, setVoiceNotice] = useState("浏览器语音可作为本地兜底；不支持时仍可文字面试。");
  const [inputMode, setInputMode] = useState<"text" | "voice">("text");
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const voiceBaseAnswerRef = useRef("");
  const keepListeningRef = useRef(false);
  const cloudAudioRef = useRef<HTMLAudioElement | null>(null);
  const live = flow.liveSession;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [live?.messages.length, busy]);

  useEffect(() => {
    if (flow.interviewPlan) {
      setInterviewType(flow.interviewPlan.interview_type as InterviewType);
      setInterviewerPersona(flow.interviewPlan.interviewer_persona || "technical");
    }
  }, [flow.interviewPlan]);

  useEffect(() => {
    if (!voiceConfig) return;
    setVoiceProvider((current) => (current === "disabled" ? "browser" : current || voiceConfig.default_provider));
  }, [voiceConfig]);

  useEffect(() => {
    return () => {
      keepListeningRef.current = false;
      recognitionRef.current?.stop();
      cloudAudioRef.current?.pause();
      window.speechSynthesis?.cancel();
    };
  }, []);

  useEffect(() => {
    if (!live?.latest_question?.question || voiceProvider === "disabled") return;
    speakText(live.latest_question.question);
  }, [live?.latest_question?.question]);

  if (!flow.interviewPlan) {
    return (
      <EmptyState
        actionLabel="先生成分析预览"
        onAction={() => onNavigate("start")}
        title="还没有面试计划。"
      />
    );
  }

  if (!live) {
    return (
      <section className="zip-interview-onboarding">
        <div className="zip-interview-mesh" />
        <div className="zip-interview-welcome">
          <p>
            <Sparkles size={16} />
            沉浸式模拟面试
          </p>
          <h1>
            进入 <span>JD 定向动态追问</span>
          </h1>
          <small>
            目标岗位：{flow.jdAnalysis?.role_title || "未命名岗位"}。系统会跟随后端生成的计划追问项目证据、技术取舍和回答细节，实时阶段不展示评分。
          </small>
        </div>
        <div className="interview-config-panel">
          <header>
            <Settings2 size={18} />
            <span>
              <strong>自由配置本轮面试</strong>
              <small>选择训练类型、面试官风格和语音模式；启动后后端会按配置生成新计划。</small>
            </span>
          </header>
          <div className="interview-config-grid">
            {interviewTypes.map((option) => {
              const Icon = option.icon;
              return (
                <button
                  className={interviewType === option.value ? "selected" : ""}
                  key={option.value}
                  onClick={() => setInterviewType(option.value)}
                  type="button"
                >
                  <Icon size={17} />
                  <strong>{option.title}</strong>
                  <small>{option.desc}</small>
                </button>
              );
            })}
          </div>
          <div className="interview-config-grid persona">
            {interviewerPersonas.map((option) => {
              const Icon = option.icon;
              return (
                <button
                  className={interviewerPersona === option.value ? "selected" : ""}
                  key={option.value}
                  onClick={() => setInterviewerPersona(option.value)}
                  type="button"
                >
                  <Icon size={17} />
                  <strong>{option.title}</strong>
                  <small>{option.desc}</small>
                </button>
              );
            })}
          </div>
          <div className="interview-voice-config">
            <div>
              <Volume2 size={17} />
              <span>
                <strong>语音面试</strong>
                <small>{voiceProfileSummary(voiceConfig, interviewerPersona, voiceProvider)}</small>
              </span>
            </div>
            <select value={voiceProvider} onChange={(event) => setVoiceProvider(event.target.value as VoiceProvider)}>
              <option value="browser">浏览器本地听说</option>
              <option value="aliyun">阿里云百炼语音</option>
              <option value="doubao">豆包语音预留</option>
              <option value="disabled">关闭语音</option>
            </select>
          </div>
          <p className="interview-voice-note">{voiceNotice}</p>
        </div>
        <div className="zip-target-banner">
          <div>
            <Target size={24} />
            <span>
              <strong>{flow.interviewPlan.plan_summary}</strong>
              <small>{flow.interviewPlan.duration_minutes} 分钟 · 最多 {flow.interviewPlan.max_questions} 问</small>
            </span>
          </div>
          <button
            className="zip-primary launch"
            disabled={busy}
            onClick={() => onStartInterview({ interviewType, interviewerPersona, voiceProvider })}
            type="button"
          >
            {busy ? "正在接入 AI 面试官..." : "开启全真训练舱"}
            <Play size={16} />
          </button>
        </div>
        <div className="interview-demo-cues">
          {["追问模糊回答", "核验项目职责", "围绕 JD 风险深入", "评分留到报告页"].map((item) => (
            <span key={item}>
              <Radar size={14} />
              {item}
            </span>
          ))}
        </div>
        <div className="zip-mode-grid">
          {flow.interviewPlan.sections.map((section, index) => (
            <article key={`${section.name}-${index}`}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{section.name}</strong>
              <p>{section.goal}</p>
              <ChipList items={section.focus_topics} />
            </article>
          ))}
        </div>
      </section>
    );
  }

  const section = live.interview_plan.sections[
    Math.min(live.current_section_index, Math.max(0, live.interview_plan.sections.length - 1))
  ];
  const latest = live.latest_question;
  const completed = live.status === "completed";
  const progress = Math.round((live.current_question_count / Math.max(1, live.interview_plan.max_questions)) * 100);

  return (
    <section className="zip-simulation-shell">
      <header className="zip-sim-header">
        <div>
          <span>
            <Zap size={18} />
          </span>
          <div>
            <strong>InterviewPilot-AI</strong>
            <small>候选人训练舱 · JD 定向追问模式</small>
          </div>
        </div>
        <aside>
          <span className={busy ? "zip-live-dot busy" : "zip-live-dot"} />
          {busy ? "AI 面试官正在生成追问" : completed ? "训练完成" : "AI 面试官在线"}
        </aside>
      </header>

      <main className="zip-simulation-grid">
        <aside className="zip-sim-sidebar">
          <div className="zip-persona-card">
            <div className="zip-persona-avatar">P</div>
            <strong>李亦航 · AI 训练官</strong>
            <small>目标岗位追问 / 项目证据核验 / 结构表达观察</small>
            <small>{personaTitle(live.interview_plan.interviewer_persona)} · {typeTitle(live.interview_plan.interview_type as InterviewType)}</small>
            <div className="zip-mini-meter strong">
              <i style={{ width: `${progress}%` }} />
            </div>
            <span>{live.current_question_count}/{live.interview_plan.max_questions} questions</span>
          </div>

          <div className="zip-live-radar">
            <span className={busy ? "active" : ""} />
            <strong>动态追问引擎</strong>
            <small>{section?.goal || "请用真实经历回答当前问题。"}</small>
          </div>

          <div className="zip-side-metrics">
            <Metric icon={<Clock size={15} />} label="训练时长" value={`${live.interview_plan.duration_minutes} min`} />
            <Metric icon={<BrainCircuit size={15} />} label="当前题型" value={latest ? questionTypeLabel[latest.question_type] : "报告阶段"} />
            <Metric icon={<ShieldAlert size={15} />} label="实时评分" value="隐藏" />
            <Metric icon={<Volume2 size={15} />} label="语音模式" value={voiceProviderLabel(live.voice_provider || voiceProvider)} />
          </div>

          <div className="zip-sim-focus">
            <strong>当前追问依据</strong>
            <p>{latest?.expected_signal || "面试已结束，可生成报告。"}</p>
            <ChipList items={section?.focus_topics} />
          </div>

          <div className="followup-proof-card">
            <strong>
              <GitBranch size={15} />
              追问如何产生
            </strong>
            <p>系统根据当前回答是否具体、是否覆盖 JD 重点、是否有项目证据，决定继续追问还是进入下一题。</p>
            <small>实时阶段只显示问题和追问，不显示评分。</small>
          </div>
        </aside>

        <section className="zip-chat-console">
          <div className="zip-chat-top">
            <div>
              <p>实时问答流</p>
              <h1>{latest?.current_section || section?.name || "模拟面试"}</h1>
            </div>
            <span>{latest ? latest.why_this_question : "本轮问题已完成"}</span>
          </div>

          <div className="zip-chat-stream">
            {live.messages.map((message, index) => (
              <article
                className={`zip-chat-bubble ${message.role}${message.role === "interviewer" && index > 0 ? " is-followup" : ""}`}
                key={`${message.created_at || index}-${index}`}
              >
                <small>
                  {roleLabel[message.role] || message.role}
                  {message.section ? ` · ${message.section}` : ""}
                </small>
                <p>{message.content}</p>
              </article>
            ))}
            {busy ? (
              <article className="zip-chat-bubble interviewer thinking">
                <small>
                  <BrainCircuit size={14} />
                  AI 面试官
                </small>
                <p>正在根据你的回答生成下一句追问：会优先看项目证据、技术取舍、职责边界和 JD 重点关联...</p>
              </article>
            ) : null}
            <div ref={bottomRef} />
          </div>

          {completed ? (
            <div className="zip-answer-dock done">
              <div>
                <CheckCircle2 size={18} />
                <span>
                  <strong>面试评估已顺利完成</strong>
                  <small>可以生成练习报告，评分仅用于训练反馈。</small>
                </span>
              </div>
              <button className="zip-primary" disabled={busy} onClick={onGenerateReport} type="button">
                {busy ? "正在生成专家评估报告..." : "结束面试并获取综合评估看板"}
                <Award size={16} />
              </button>
            </div>
          ) : (
            <form
              className="zip-answer-dock"
              onSubmit={(event) => {
                event.preventDefault();
                const payload = inputMode === "voice" ? voiceTranscript.trim() : answer.trim();
                if (!payload) return;
                onTurn("answer", payload);
                setAnswer("");
                setVoiceTranscript("");
              }}
            >
              <div className="zip-dock-ribbon">
                <span>
                  {inputMode === "voice"
                    ? voiceTranscript.trim()
                      ? `语音转写中：${voiceTranscript.trim().length} 个字 · 可暂停后编辑或直接提交`
                      : "语音模式：点击开始回答，系统会持续听，直到你手动暂停"
                    : answer.trim().length
                      ? `当前输入中：${answer.trim().length} 个字 · 回答越具体，追问越能贴近项目细节`
                      : "文字模式：按 Enter 提交，Shift + Enter 换行"}
                </span>
                <button disabled={busy} onClick={() => onTurn("end")} type="button">
                  <Award size={14} />
                  结束面试并获取报告
                </button>
              </div>
              <div className="answer-mode-tabs" aria-label="回答方式">
                <button className={inputMode === "text" ? "selected" : ""} onClick={() => switchInputMode("text")} type="button">
                  文字回答
                </button>
                <button className={inputMode === "voice" ? "selected" : ""} onClick={() => switchInputMode("voice")} type="button">
                  语音回答
                </button>
              </div>
              {inputMode === "text" ? (
                <div className="zip-dock-input">
                  <textarea
                    onChange={(event) => setAnswer(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        if (answer.trim()) {
                          onTurn("answer", answer);
                          setAnswer("");
                        }
                      }
                    }}
                    placeholder="请在此处输入你的回答，建议展示职责、技术选择、取舍和结果..."
                    rows={2}
                    value={answer}
                  />
                  <button className="zip-send" disabled={busy || !answer.trim()} type="submit">
                    <Send size={18} />
                  </button>
                </div>
              ) : (
                <div className="voice-answer-panel">
                  <div className="voice-answer-orb" aria-hidden="true">
                    {listening ? <Mic size={24} /> : <MicOff size={24} />}
                  </div>
                  <div className="voice-answer-content">
                    <strong>{listening ? "正在持续听你回答" : "语音回答已暂停"}</strong>
                    <textarea
                      onChange={(event) => setVoiceTranscript(event.target.value)}
                      placeholder="语音转写会出现在这里。你可以手动修改后提交，不会自动发送。"
                      rows={3}
                      value={voiceTranscript}
                    />
                    <small>{voiceNotice}</small>
                  </div>
                  <div className="voice-answer-actions">
                    <button
                      className={listening ? "is-listening" : ""}
                      disabled={busy || voiceProvider === "disabled"}
                      onClick={toggleListening}
                      type="button"
                    >
                      {listening ? <Pause size={15} /> : <Mic size={15} />}
                      {listening ? "暂停语音" : "开始语音"}
                    </button>
                    <button className="zip-send" disabled={busy || !voiceTranscript.trim()} type="submit">
                      <Send size={16} />
                      提交回答
                    </button>
                  </div>
                </div>
              )}
              <div className="zip-control-row">
                <button disabled={busy || !latest?.question} onClick={() => speakText(latest?.question || "")} type="button">
                  {speaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                  {speaking ? "停止朗读" : "朗读问题"}
                </button>
                <button disabled={busy} onClick={() => onTurn("skip")} type="button">
                  <Pause size={14} />
                  跳过
                </button>
                <button disabled={busy} onClick={() => onTurn("next")} type="button">
                  <Play size={14} />
                  下一题
                </button>
                <button disabled={busy} onClick={() => onTurn("regenerate")} type="button">
                  <RotateCcw size={14} />
                  重新生成
                </button>
              </div>
            </form>
          )}
        </section>
      </main>
    </section>
  );

  async function speakText(text: string, forceBrowser = false) {
    if (!text || voiceProvider === "disabled") return;
    if (speaking && !forceBrowser) {
      cloudAudioRef.current?.pause();
      cloudAudioRef.current = null;
      window.speechSynthesis?.cancel();
      setSpeaking(false);
      return;
    }
    if (!forceBrowser && voiceProvider === "aliyun") {
      setSpeaking(true);
      setVoiceNotice("正在调用阿里云百炼语音合成面试官问题...");
      try {
        const response = await synthesizeInterviewVoice({
          text,
          provider: "aliyun",
          persona: live?.interview_plan.interviewer_persona || interviewerPersona,
          audio_format: "mp3",
          sample_rate: 24000,
        });
        if (!response.used_fallback && (response.audio_url || response.audio_base64)) {
          const source =
            response.audio_url ||
            `data:audio/${response.audio_format || "mp3"};base64,${response.audio_base64 || ""}`;
          await playCloudAudio(source, response.message);
          return;
        }
        setVoiceNotice(response.message || "阿里云语音暂不可用，已切回浏览器本地朗读。");
      } catch {
        setVoiceNotice("阿里云语音请求失败，已切回浏览器本地朗读。");
      }
      setSpeaking(false);
      speakText(text, true);
      return;
    }
    if (!("speechSynthesis" in window)) {
      setVoiceNotice("当前浏览器不支持朗读，已保留文字面试。");
      setSpeaking(false);
      return;
    }
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    const voiceProfile = personaVoiceProfile(live?.interview_plan.interviewer_persona || interviewerPersona);
    utterance.rate = voiceProfile.rate;
    utterance.pitch = voiceProfile.pitch;
    const voice = selectPersonaVoice(voiceProfile.voiceIndex);
    if (voice) {
      utterance.voice = voice;
    }
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => {
      setSpeaking(false);
      setVoiceNotice("朗读失败，已保留文字面试。");
    };
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  }

  function playCloudAudio(source: string, successMessage: string): Promise<void> {
    return new Promise((resolve, reject) => {
      cloudAudioRef.current?.pause();
      window.speechSynthesis?.cancel();
      const audio = new Audio(source);
      cloudAudioRef.current = audio;
      audio.onended = () => {
        setSpeaking(false);
        setVoiceNotice(successMessage || "阿里云语音播放完成。");
        resolve();
      };
      audio.onerror = () => {
        setSpeaking(false);
        reject(new Error("cloud audio playback failed"));
      };
      audio
        .play()
        .then(() => {
          setVoiceNotice(successMessage || "正在播放阿里云面试官语音。");
        })
        .catch((error) => {
          setSpeaking(false);
          reject(error);
        });
    });
  }

  function toggleListening() {
    if (listening) {
      stopListening();
      return;
    }
    startListening();
  }

  function startListening() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceNotice("当前浏览器不支持语音输入，请继续使用文字回答。");
      return;
    }
    const recognition = new Recognition();
    voiceBaseAnswerRef.current = voiceTranscript.trim();
    recognition.lang = "zh-CN";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript || "")
        .join("");
      setVoiceTranscript(() => {
        const prefix = voiceBaseAnswerRef.current ? `${voiceBaseAnswerRef.current} ` : "";
        return `${prefix}${transcript}`.trim();
      });
    };
    recognition.onerror = () => {
      setVoiceNotice("语音输入短暂中断，系统会尝试继续监听；你也可以切到文字回答。");
      setListening(false);
    };
    recognition.onend = () => {
      setListening(false);
      if (keepListeningRef.current) {
        window.setTimeout(() => {
          if (keepListeningRef.current) startListening();
        }, 260);
      }
    };
    recognitionRef.current = recognition;
    keepListeningRef.current = true;
    setVoiceNotice("正在持续听你回答；浏览器断句后会自动续听，你手动暂停前不会自动提交。");
    setListening(true);
    try {
      recognition.start();
    } catch {
      setVoiceNotice("语音输入启动失败，请稍后重试或切到文字回答。");
      setListening(false);
    }
  }

  function stopListening() {
    keepListeningRef.current = false;
    recognitionRef.current?.stop();
    setListening(false);
    setVoiceNotice("语音已暂停；你可以编辑转写内容后提交，或继续语音回答。");
  }

  function switchInputMode(next: "text" | "voice") {
    if (next === "text") {
      stopListening();
    }
    setInputMode(next);
  }
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div>
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function typeTitle(value: InterviewType | string): string {
  return interviewTypes.find((item) => item.value === value)?.title || "JD 定向面";
}

function personaTitle(value: InterviewerPersona | string): string {
  return interviewerPersonas.find((item) => item.value === value)?.title || "技术面试官";
}

function voiceProviderLabel(value: VoiceProvider | string): string {
  return {
    browser: "浏览器",
    aliyun: "阿里云",
    doubao: "豆包预留",
    disabled: "关闭",
  }[value] || "浏览器";
}

function voiceProfileSummary(
  config: InterviewVoiceConfig | null,
  persona: InterviewerPersona,
  provider: VoiceProvider,
): string {
  if (provider !== "aliyun") {
    return config?.privacy_or_boundary_note || "后端语音配置读取失败时，前端仍可使用浏览器本地兜底。";
  }
  const profile = config?.persona_profiles?.find((item) => item.persona === persona);
  if (!profile) {
    return "阿里云语音已选择；后端会按面试官类型选择默认音色。";
  }
  return `${profile.display_name}：${profile.model} / ${profile.voice_id} / 语速 ${profile.speech_rate}`;
}

function personaVoiceProfile(value: InterviewerPersona | string) {
  if (value === "warm") {
    return { rate: 0.92, pitch: 1.08, voiceIndex: 0 };
  }
  if (value === "pressure") {
    return { rate: 1.14, pitch: 0.82, voiceIndex: 2 };
  }
  return { rate: 1, pitch: 0.96, voiceIndex: 1 };
}

function selectPersonaVoice(index: number) {
  if (!("speechSynthesis" in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  const zhVoices = voices.filter((voice) => voice.lang.toLowerCase().startsWith("zh"));
  if (!zhVoices.length) return null;
  return zhVoices[index % zhVoices.length];
}
