import {
  ArrowRight,
  Clock3,
  FileUp,
  MessageSquareText,
  Sparkles,
  Target,
} from "lucide-react";
import type { DragEvent } from "react";
import { useEffect, useRef, useState } from "react";
import type { RouteId } from "../components/Shell";
import { extractResumeTextFromFile, userErrorMessage } from "../lib/api";
import type { FlowState, HistoryItem } from "../types/api";

interface DashboardPageProps {
  flow: FlowState;
  history: HistoryItem[];
  onNavigate: (route: RouteId) => void;
  onLoadSampleAnalysis: () => void;
}

const lightningRoles = ["Java 后端", "高并发后端", "AI Agent 工程师", "RAG 工程师", "产品经理", "全栈工程师"] as const;

const questionTemplates = [
  {
    role: "Java 后端",
    targetRole: "Java 后端",
    source: "Java Guides / Redis 主题",
    topic: "缓存一致性",
    prompt: "商品下架后，Redis 热门列表和 MySQL 状态如何保持一致？如果缓存删除失败，你会怎么兜底？",
    tags: ["Redis", "一致性", "项目深挖"],
  },
  {
    role: "后端系统设计",
    targetRole: "高并发后端",
    source: "InterviewBit / ByteByteGo 主题",
    topic: "削峰与限流",
    prompt: "秒杀接口突然涌入 10 倍流量，你会把限流、队列、库存扣减和失败重试放在哪些层？",
    tags: ["高并发", "架构", "压力测试"],
  },
  {
    role: "AI Agent 工程师",
    targetRole: "AI Agent 工程师",
    source: "DataCamp / Agentic AI 主题",
    topic: "Agent 评测",
    prompt: "一个工具调用型 Agent 经常答错，你如何设计 evals、trace 和回归集来定位问题？",
    tags: ["Evals", "Tracing", "Agent"],
  },
  {
    role: "RAG 工程",
    targetRole: "RAG 工程师",
    source: "公开 RAG 面试题型",
    topic: "召回质量",
    prompt: "用户问到文档里没有的内容时，RAG 系统应该如何拒答、追问或触发人工确认？",
    tags: ["RAG", "幻觉", "兜底"],
  },
  {
    role: "产品经理",
    targetRole: "产品经理",
    source: "Exponent / PM 指标主题",
    topic: "指标拆解",
    prompt: "一个功能 DAU 上升但留存下降，你会如何拆指标、找原因并决定是否继续推进？",
    tags: ["Metrics", "取舍", "复盘"],
  },
  {
    role: "项目深挖",
    targetRole: "Java 后端",
    source: "真实面试追问题型",
    topic: "责任边界",
    prompt: "你说“负责核心模块”，具体哪些设计是你定的？哪些是团队已有方案？你怎么证明贡献？",
    tags: ["Ownership", "STAR", "尖锐追问"],
  },
] as const;

const dropzoneHandoffStages = ["接收简历文件...", "识别简历文字...", "已填入启动页简历框..."] as const;

const radarDimensions = [
  { key: "fundamentals", label: "基础知识", base: 62 },
  { key: "project", label: "项目深挖", base: 58 },
  { key: "architecture", label: "架构思维", base: 54 },
  { key: "communication", label: "表达结构", base: 66 },
  { key: "pressure", label: "压力应对", base: 52 },
] as const;

export function DashboardPage({ flow, history, onLoadSampleAnalysis, onNavigate }: DashboardPageProps) {
  const [selectedRole, setSelectedRole] = useState<(typeof lightningRoles)[number]>("Java 后端");
  const [dropzoneHighlighted, setDropzoneHighlighted] = useState(false);
  const [dropzoneMode, setDropzoneMode] = useState<"idle" | "dragging" | "handoff" | "error">("idle");
  const [dropzoneStage, setDropzoneStage] = useState(0);
  const [dropzoneNotice, setDropzoneNotice] = useState("");
  const [interviewEntryHighlighted, setInterviewEntryHighlighted] = useState(false);
  const [radarVisible, setRadarVisible] = useState(false);
  const [spoilerVisible, setSpoilerVisible] = useState(false);
  const dropzoneRef = useRef<HTMLLabelElement | null>(null);
  const interviewEntryRef = useRef<HTMLDivElement | null>(null);
  const radarRef = useRef<HTMLElement | null>(null);
  const spoilerRef = useRef<HTMLElement | null>(null);
  const dropzoneTimers = useRef<number[]>([]);
  const hasHistory = history.length > 0;
  const isSampleReport = flow.reportResponse?.report.session_id === "sample-commercial-trust-report";
  const hasActiveTraining = Boolean(
    flow.productSession || flow.jdAnalysis || flow.resumeAnalysis || flow.gapAnalysis || flow.interviewPlan || (flow.reportResponse && !isSampleReport),
  );
  const activeTarget = flow.productSession?.input?.target_role;
  const activeSummary = flow.gapAnalysis?.summary || flow.resumeOptimization?.optimization_summary || "";
  const radarScores = buildRadarScores(flow);

  function goStartWithRole(role: string) {
    window.sessionStorage.setItem("interviewpilot_prefill_role", role);
    window.sessionStorage.setItem("interviewpilot_prefill_duration", "10");
    onNavigate("start");
  }

  function focusResumeDropzone() {
    dropzoneRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    setDropzoneHighlighted(true);
    window.setTimeout(() => setDropzoneHighlighted(false), 1800);
  }

  function clearDropzoneTimers() {
    dropzoneTimers.current.forEach((timer) => window.clearTimeout(timer));
    dropzoneTimers.current = [];
  }

  async function startResumeHandoff(file?: File) {
    if (!file) {
      return;
    }
    clearDropzoneTimers();
    setDropzoneMode("handoff");
    setDropzoneStage(0);
    setDropzoneNotice("");
    window.sessionStorage.setItem("interviewpilot_resume_filename", file.name);
    dropzoneTimers.current = [window.setTimeout(() => setDropzoneStage(1), 360)];
    try {
      const result = await extractResumeTextFromFile(file);
      const warnings = result.warnings.filter(Boolean);
      if (!result.rawText.trim()) {
        window.sessionStorage.setItem(
          "interviewpilot_prefill_resume_notice",
          warnings[0] || "没有识别到可填入的简历文字，请换 PDF/TXT 或在启动页粘贴。",
        );
        setDropzoneMode("error");
        setDropzoneStage(2);
        setDropzoneNotice("没有识别到文字，已为你打开启动页继续补充。");
        dropzoneTimers.current.push(window.setTimeout(() => onNavigate("start"), 900));
        return;
      }
      window.sessionStorage.setItem("interviewpilot_prefill_resume_text", result.rawText.trim());
      window.sessionStorage.setItem(
        "interviewpilot_prefill_resume_notice",
        warnings[0] || `已从 ${file.name} 识别文字并填入简历输入框，你可以继续编辑。`,
      );
      setDropzoneStage(2);
      setDropzoneNotice(result.needsManualCorrection ? "已识别文字，建议进入后快速检查格式。" : "已识别文字，正在填入启动页。");
      dropzoneTimers.current.push(window.setTimeout(() => onNavigate("start"), 680));
    } catch (error) {
      window.sessionStorage.setItem("interviewpilot_prefill_resume_notice", userErrorMessage(error));
      setDropzoneMode("error");
      setDropzoneStage(2);
      setDropzoneNotice("识别请求失败，已为你打开启动页继续补充。");
      dropzoneTimers.current.push(window.setTimeout(() => onNavigate("start"), 900));
    }
  }

  function handleDropzoneDragOver(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    if (dropzoneMode !== "handoff") {
      setDropzoneMode("dragging");
    }
  }

  function handleDropzoneDragLeave(event: DragEvent<HTMLLabelElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null) && dropzoneMode === "dragging") {
      setDropzoneMode("idle");
    }
  }

  function handleDropzoneDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    startResumeHandoff(file);
  }

  function selectTrainingTemplate(role: (typeof lightningRoles)[number]) {
    setSelectedRole(role);
    interviewEntryRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    setInterviewEntryHighlighted(true);
    window.setTimeout(() => setInterviewEntryHighlighted(false), 1800);
  }

  useEffect(() => {
    const radarElement = radarRef.current;
    if (!radarElement) {
      return undefined;
    }

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion || !("IntersectionObserver" in window)) {
      setRadarVisible(true);
      return undefined;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setRadarVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.42 },
    );
    observer.observe(radarElement);

    return () => observer.disconnect();
  }, []);

  useEffect(() => () => clearDropzoneTimers(), []);

  useEffect(() => {
    const spoilerElement = spoilerRef.current;
    if (!spoilerElement) {
      return undefined;
    }

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion || !("IntersectionObserver" in window)) {
      setSpoilerVisible(true);
      return undefined;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setSpoilerVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.36 },
    );
    observer.observe(spoilerElement);

    return () => observer.disconnect();
  }, []);

  return (
    <div className="dashboard-workbench commercial-trust-page">
      <section className="trust-hero" aria-label="产品首页">
        <div className="trust-hero__promise">
          <p>
            <Sparkles size={16} />
            InterviewArk / 面试舟
          </p>
          <h1>简历有头，面试不愁。</h1>
          <small>上传旧简历先识别文字并带入启动页；补充目标岗位/JD 后，再生成诊断报告和 5 分钟闪电面试。</small>
          <div className="trust-hero__actions">
            <button className="zip-primary launch" onClick={() => onNavigate("start")} type="button">
              免费获取简历诊断
              <ArrowRight size={16} />
            </button>
            <button className="zip-outline" onClick={onLoadSampleAnalysis} type="button">
              查看完整样例报告
            </button>
          </div>
          <div className="trust-proof-line" aria-label="产品边界">
            <span>训练反馈，不做外部结果结论</span>
            <span>只改表达，不造经历</span>
            <span>样例明确标注，不伪装历史</span>
          </div>
        </div>

        <aside className="conversion-entry-panel" aria-label="简历优化和模拟面试入口">
          <label
            className={`resume-dropzone ${dropzoneHighlighted ? "is-highlighted" : ""} is-${dropzoneMode}`}
            onDragLeave={handleDropzoneDragLeave}
            onDragOver={handleDropzoneDragOver}
            onDrop={handleDropzoneDrop}
            ref={dropzoneRef}
            role="button"
            tabIndex={0}
          >
            <span className="dropzone-pulse-frame">
              {dropzoneMode === "handoff" ? (
                <>
                  <i className="dropzone-loader">
                    <FileUp size={26} />
                  </i>
                  <strong>{dropzoneHandoffStages[dropzoneStage]}</strong>
                  <small>{dropzoneNotice || "已接收文件，正在解析 PDF/DOCX/TXT。"}</small>
                  <span className="dropzone-progress" aria-hidden="true">
                    <b />
                  </span>
                </>
              ) : (
                <>
                  <i>
                    <FileUp size={28} />
                  </i>
                  <strong>
                    {dropzoneMode === "dragging"
                      ? "松手，开始识别简历"
                      : dropzoneMode === "error"
                        ? "识别失败，请换 PDF/TXT"
                        : "拖入或点击上传旧简历"}
                  </strong>
                  <small>
                    {dropzoneMode === "error"
                      ? dropzoneNotice
                      : "支持 PDF/DOCX/TXT 识别后填入启动页；扫描版 PDF 会尽量 OCR，结果需校对"}
                  </small>
                </>
              )}
            </span>
            <input
              accept=".pdf,.txt,.md,.docx,application/pdf,text/plain,text/markdown,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="resume-upload-input"
              disabled={dropzoneMode === "handoff"}
              onChange={(event) => {
                const file = event.target.files?.[0];
                event.currentTarget.value = "";
                startResumeHandoff(file);
              }}
              type="file"
            />
          </label>

          <div className={`lightning-interview-entry ${interviewEntryHighlighted ? "is-highlighted" : ""}`} ref={interviewEntryRef}>
            <header>
              <span>
                <MessageSquareText size={16} />
                模拟面试入口
              </span>
              <strong>选择岗位，开始 5 分钟闪电面试。</strong>
            </header>
            <p className="interview-link-hint">可选：若已在上方上传简历，AI 面试官将自动结合简历提问。</p>
            <label>
              <span>目标岗位</span>
              <select value={selectedRole} onChange={(event) => setSelectedRole(event.target.value as (typeof lightningRoles)[number])}>
                {lightningRoles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </label>
            <button className="zip-primary launch" onClick={() => goStartWithRole(selectedRole)} type="button">
              开始5分钟闪电面试
              <ArrowRight size={16} />
            </button>
            <small>可进入后补充 JD；采用快速诊断引擎，5 秒内即可直达面试房间。</small>
          </div>
        </aside>
      </section>

      <section className={`result-proof-band ${spoilerVisible ? "is-spoiler-visible" : ""}`} aria-label="样例结果链路" ref={spoilerRef}>
        <div className="commercial-section-heading">
          <span>核心功能深度剧透</span>
          <h2>不是告诉你“能优化”，而是直接展示它怎么帮你改、怎么追问。</h2>
        </div>
        <div className="feature-spoiler-grid">
          <article className="spoiler-card resume-rewrite-spoiler">
            <header>
              <span>简历优化</span>
              <strong>STAR 法则智能润色</strong>
            </header>
            <div className="rewrite-compare">
              <section>
                <small>Before</small>
                <p>负责了某高并发模块的开发。</p>
              </section>
              <section>
                <small>After</small>
                <p>
                  梳理订单状态机，引入<mark>幂等校验</mark>；如果确有压测记录，再补充<mark>真实流量约束</mark>和<mark>可核验结果</mark>。
                </p>
              </section>
            </div>
            <p>告别流水账，自动提炼底层硬核技术栈与业务结果。</p>
          </article>

          <article className="spoiler-card interview-followup-spoiler">
            <header>
              <span>模拟面试</span>
              <strong>全真实、多模态的面试现场</strong>
            </header>
            <div className="followup-chat-flow">
              <p className="candidate-line">我在项目里用了 Redis 缓存热门商品列表。</p>
              <p className="ai-line">如果商品下架，缓存和数据库如何保持一致？</p>
              <div>
                <span>Follow-up</span>
                <span>压力测试</span>
                <span>基础考察</span>
              </div>
            </div>
            <p>不是死板题库，AI 会根据你的每一次回答进行针对性追问，击碎面试紧张感。</p>
          </article>
        </div>
      </section>

      <section className="sample-report-preview" aria-label="通关全景图预告">
        <div className="commercial-section-heading">
          <span>通关全景图</span>
          <h2>进入后看到你的求职驾驶舱：能力短板、训练路径和下一关目标一眼清楚。</h2>
        </div>
        <div className="career-cockpit-preview">
          <article className={`ability-radar-card ${radarVisible ? "is-radar-visible" : ""}`} ref={radarRef}>
            <header>
              <span>能力雷达图</span>
              <strong>{flow.resumeAnalysis ? "当前五维 vs 预计优化后" : "当前五维 vs 示例优化预期"}</strong>
            </header>
            <div className="radar-visual" aria-label="八股熟练度、项目深挖、架构思维、沟通表达、抗压能力能力雷达图">
              <div className="radar-grid" aria-hidden="true" />
              <div className="radar-shape radar-shape--projected" style={{ clipPath: radarPolygon(radarScores, "projected") }} />
              <div className="radar-shape radar-shape--current" style={{ clipPath: radarPolygon(radarScores, "current") }} />
              <div className="radar-corner-labels" aria-hidden="true">
                {radarScores.map((item) => (
                  <span key={item.label}>
                    <strong>{item.label}</strong>
                    <small>{item.current} / {item.projected}</small>
                  </span>
                ))}
              </div>
              <div className="radar-legend" aria-hidden="true">
                <span><i /> 当前</span>
                <span><b /> 预计优化后</span>
              </div>
            </div>
            <div className="radar-score-list" aria-label="五维具体分数">
              {radarScores.map((item) => (
                <section key={item.label}>
                  <div>
                    <strong>{item.label}</strong>
                    <small>{item.current} → {item.projected}</small>
                  </div>
                  <span>
                    <i style={{ width: `${item.current}%` }} />
                    <b style={{ width: `${item.projected}%` }} />
                  </span>
                  <p>{item.reason}</p>
                </section>
              ))}
            </div>
          </article>

          <article className="boss-path-card">
            <header>
              <span>Java / Go 后端通关路径</span>
              <strong>从简历诊断到终面复盘</strong>
            </header>
            <div className="boss-path">
              {["简历初筛", "基础八股面", "核心项目深挖面", "架构设计面", "HR/心理素质面"].map((item, index) => (
                <div className={index < 2 ? "done" : index === 2 ? "active" : ""} key={item}>
                  <i>{index + 1}</i>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </article>
        </div>
        <p className="career-cockpit-caption">注册进入你的专属求职驾驶舱，把面试变成一场有胜算通关的游戏。</p>
      </section>

      <section className="commercial-table-section" aria-label="公开题型训练模板">
        <div className="commercial-section-heading">
          <span>公开题型训练模板</span>
          <h2>把网上高频面试题型，改造成会连续追问的训练卡片。</h2>
        </div>
        <div className="question-marquee" aria-label="循环播放的题型模板">
          <div className="question-marquee__track">
            {[...questionTemplates, ...questionTemplates].map(({ role, targetRole, source, topic, prompt, tags }, index) => (
              <button className="question-template-card" key={`${role}-${topic}-${index}`} onClick={() => selectTrainingTemplate(targetRole)} type="button">
                <header>
                  <span>{role}</span>
                  <small>{source}</small>
                </header>
                <strong>{topic}</strong>
                <p>{prompt}</p>
                <div>
                  {tags.map((tag) => (
                    <em key={tag}>{tag}</em>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </div>
        <div className="question-training-proof">
          <article>
            <header>
              <span>题库不是终点</span>
              <small>Question bank → Drill</small>
            </header>
            <p>题型参考公开面试资料主题，并重新改写为训练模板；进入训练后会结合你的 JD、简历和上一轮回答继续追问。</p>
          </article>
          <article>
            <header>
              <span>输出不是背答案</span>
              <small>Follow-up → Report</small>
            </header>
            <p>系统会记录你在哪个环节答得浅：概念、方案取舍、项目证据，还是压力追问，再进入报告复盘。</p>
          </article>
        </div>
      </section>

      <section className="footer-diagnosis-cta" aria-label="底部行动召唤">
        <div>
          <span>最后一步</span>
          <h2>别让一份及格线以下的简历，浪费了你宝贵的面试机会。</h2>
          <p>先做一次免费诊断，看清楚简历短板、追问风险和下一步训练路线。</p>
        </div>
        <button className="footer-diagnosis-cta__button" onClick={focusResumeDropzone} type="button">
          立即开始免费诊断
          <ArrowRight size={20} />
        </button>
      </section>

      {hasActiveTraining ? (
        <section className="active-training-strip" aria-label="当前训练">
          <div>
            <span>
              <Target size={15} />
              当前训练
            </span>
            <strong>{activeTarget || "已开始的训练"}</strong>
            <p>{activeSummary || "继续完成当前 JD、简历、面试和报告流程。"}</p>
          </div>
          <div className="active-training-actions">
            <button className="zip-outline small" onClick={() => onNavigate("analysis")} type="button">
              查看当前分析
            </button>
            <button className="zip-primary small" onClick={() => onNavigate(flow.reportResponse ? "reports" : "interview")} type="button">
              继续训练
            </button>
          </div>
        </section>
      ) : null}

      <section className="history-trust-section" aria-label="真实历史记录">
        <div className="commercial-section-heading">
          <span>本机训练历史</span>
          <h2>首页不展示历史条目，避免把本地旧记录误看成样例或假数据。</h2>
        </div>
        {hasHistory ? (
          <div className="history-isolated-notice">
            <Clock3 size={22} />
            <strong>检测到 {history.length} 条本机训练记录</strong>
            <p>这些记录来自你当前浏览器和后端环境，不是产品样例。为了避免误解，首页不直接展开历史详情。</p>
            <button className="zip-outline small" onClick={() => onNavigate("reports")} type="button">
              去报告历史查看
            </button>
          </div>
        ) : (
          <div className="honest-empty-history">
            <Clock3 size={22} />
            <strong>暂无训练历史</strong>
            <p>这里不会放默认岗位、默认百分比或看起来像真实记录的占位数据。完成第一轮训练后，历史报告会出现在这里。</p>
          </div>
        )}
      </section>
    </div>
  );
}

function buildRadarScores(flow: FlowState) {
  const matched = flow.gapAnalysis?.matched_skills.length || 0;
  const weak = flow.gapAnalysis?.weak_evidence_skills.length || 0;
  const missing = flow.gapAnalysis?.missing_skills.length || 0;
  const projects = flow.resumeAnalysis?.projects.length || 0;
  const hasOptimization = Boolean(flow.resumeOptimization);
  return radarDimensions.map((dimension, index) => {
    const current = Math.max(
      38,
      Math.min(88, dimension.base + matched * 3 + projects * 2 - weak * 4 - missing * 5 + index),
    );
    const lift = hasOptimization ? 8 + Math.max(0, 4 - weak) : flow.resumeAnalysis ? 6 : 10;
    return {
      label: dimension.label,
      current,
      projected: Math.min(96, current + lift),
      reason: radarReason(dimension.key, weak, missing, hasOptimization),
    };
  });
}

function radarReason(key: (typeof radarDimensions)[number]["key"], weak: number, missing: number, hasOptimization: boolean) {
  const suffix = hasOptimization ? "优化建议已生成，可作为下一轮训练目标。" : "上传并分析后会展示预计提升。";
  if (key === "project") return weak ? `项目证据偏薄，需补职责边界和结果复盘；${suffix}` : `项目证据可继续深挖；${suffix}`;
  if (key === "architecture") return missing ? `JD 仍有缺口，需补方案取舍和边界场景；${suffix}` : `架构表达可围绕取舍强化；${suffix}`;
  if (key === "communication") return `建议按 STAR/总分总组织回答；${suffix}`;
  if (key === "pressure") return `建议提前准备短板诚实说明和追问兜底；${suffix}`;
  return `基础知识要和 JD 技能点绑定复习；${suffix}`;
}

function radarPolygon(scores: ReturnType<typeof buildRadarScores>, key: "current" | "projected") {
  const outerPoints = [
    [50, 5],
    [94, 37],
    [77, 90],
    [23, 90],
    [6, 37],
  ];
  const points = scores.map((score, index) => {
    const value = score[key] / 100;
    const [x, y] = outerPoints[index];
    const px = 50 + (x - 50) * value;
    const py = 50 + (y - 50) * value;
    return `${px.toFixed(1)}% ${py.toFixed(1)}%`;
  });
  return `polygon(${points.join(", ")})`;
}
