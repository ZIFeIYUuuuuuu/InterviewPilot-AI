import { ArrowRight, Brain, CheckCircle, FileText, GitCompareArrows, MessageSquareText, SearchCheck, ShieldAlert, Sparkles } from "lucide-react";
import { ChipList } from "../components/Shell";
import type { RouteId } from "../components/Shell";
import { samplePracticeReport } from "../lib/sampleEvidence";
import type { BulletImprovementSuggestion, FlowState, InterviewPlan, JDAnalysis, ResumeAnalysis } from "../types/api";

interface AnalysisPageProps {
  flow: FlowState;
  onNavigate: (route: RouteId) => void;
  onStartInterview: () => void;
  busy: boolean;
}

const sampleRewrite: BulletImprovementSuggestion = {
  original_issue: "负责了公司电商后台订单系统的开发，参与接口联调和页面功能支持。",
  why_it_is_weak: "描述像流水账，缺少系统复杂度、技术选型和量化结果。",
  suggested_direction: "把项目改成 STAR 结构，突出核心链路、技术动作和结果指标。",
  example_rewrite: "梳理订单状态机和接口幂等边界；如果你确实有压测或线上记录，可以补充真实流量约束、验证方式和可核验结果。",
  evidence_boundary: "不要补造并发量、QPS 或百分比；只能写你能解释来源的数据和职责。",
};

const sampleJD: JDAnalysis = {
  role_title: "后端 API 工程师（产品样例）",
  required_skills: ["Golang", "MySQL", "Redis", "RESTful API", "缓存一致性"],
  preferred_skills: ["Docker", "消息队列", "云服务部署"],
  responsibilities: ["负责核心 API 设计", "维护订单链路稳定性", "定位线上性能问题"],
  interview_focus: ["项目职责边界", "缓存一致性", "数据库索引", "接口异常处理"],
  uncertainty_notes: [],
};

const sampleResume: ResumeAnalysis = {
  candidate_skills: ["Golang", "MySQL", "Redis", "Docker", "RESTful API"],
  projects: [
    {
      name: "电商后台订单系统",
      tech_stack: ["Golang", "MySQL", "Redis"],
      highlights: ["负责订单接口开发，参与联调和基础缓存接入。"],
      evidence_quality: "medium",
    },
  ],
  strengths: ["熟悉 Golang 开发，接过一些接口。"],
  weaknesses: ["项目描述偏流水账，缺少技术动作和量化结果。"],
  weak_evidence_skills: ["Redis", "Docker", "高并发"],
  resume_summary: "产品样例：原始简历具备后端项目基础，但技术方案、职责边界和量化结果表达不足。",
  uncertainty_notes: [],
};

const samplePlan: InterviewPlan = {
  interview_type: "project_deep_dive",
  interviewer_persona: "technical",
  duration_minutes: 20,
  difficulty: "medium",
  sections: [
    { name: "项目切入", duration_minutes: 4, goal: "确认候选人真实参与边界。", focus_topics: ["职责边界", "项目背景"] },
    { name: "缓存追问", duration_minutes: 6, goal: "检查 Redis 使用是否有机制理解。", focus_topics: ["缓存一致性", "失效策略"] },
    { name: "接口质量", duration_minutes: 5, goal: "检查异常处理和接口稳定性。", focus_topics: ["错误码", "日志定位"] },
  ],
  max_questions: 8,
  plan_summary: "样例训练路径会围绕项目职责、缓存一致性、接口质量和量化复盘连续追问。",
};

function focusLabelForQuestion(item: string): string {
  if (item.includes("数据库索引")) {
    return "数据库索引设计/优化";
  }
  return item.replace(/\s*取舍\s*/g, "").trim() || item;
}

export function AnalysisPage({ flow, onNavigate, onStartInterview, busy }: AnalysisPageProps) {
  const isSample = !flow.jdAnalysis || !flow.resumeAnalysis || !flow.gapAnalysis || !flow.interviewPlan;
  const jd = flow.jdAnalysis || sampleJD;
  const resume = flow.resumeAnalysis || sampleResume;
  const gap = flow.gapAnalysis || samplePracticeReport.gap_analysis;
  const plan = flow.interviewPlan || samplePlan;
  const suggestion = flow.resumeOptimization?.bullet_improvement_suggestions[0] || samplePracticeReport.resume_optimization?.bullet_improvement_suggestions[0] || sampleRewrite;
  const concreteSuggestions =
    flow.resumeOptimization?.bullet_improvement_suggestions.length
      ? flow.resumeOptimization.bullet_improvement_suggestions
      : samplePracticeReport.resume_optimization?.bullet_improvement_suggestions.length
        ? samplePracticeReport.resume_optimization.bullet_improvement_suggestions
        : [sampleRewrite];
  const project = resume.projects[0];
  const beforeText = suggestion.original_issue || project?.highlights[0] || "熟悉 Golang 开发，接过一些接口。";
  const afterText = suggestion.example_rewrite || suggestion.suggested_direction;
  const matchRate = Math.min(96, Math.round((gap.matched_skills.length / Math.max(1, jd.required_skills.length + gap.missing_skills.length)) * 100));

  return (
    <div className="analysis-compare-page">
      <section className="analysis-compare-shell" aria-label="简历改写前后对比">
        <aside className="analysis-before-pane">
          <header>
            <span>
              <FileText size={16} />
              {isSample ? "产品样例：原始简历盲审" : "原始简历盲审"}
            </span>
            <h1>平庸不是经历不够，而是证据没有被看见。</h1>
            <p>{resume.resume_summary}</p>
          </header>

          <div className="resume-paper-card muted">
            <section>
              <small>个人优势</small>
              <p>{resume.strengths[0] || "熟悉 Golang 开发，接过一些接口。"}</p>
            </section>
            <section>
              <small>项目经历</small>
              <p>{beforeText}</p>
            </section>
            <section>
              <small>盲审风险</small>
              <ChipList items={[...resume.weak_evidence_skills, ...gap.missing_skills].slice(0, 6)} tone="warn" />
            </section>
          </div>

          <div className="analysis-mini-proof">
            {[
              ["JD 要求", jd.required_skills.length],
              ["简历技能", resume.candidate_skills.length],
              ["匹配度", `${matchRate}%`],
            ].map(([label, value]) => (
              <article key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </div>
        </aside>

        <main className="analysis-after-pane">
          <header>
            <span>
              <Sparkles size={16} />
              {isSample ? "产品样例：AI 深度魔改版" : "AI 深度魔改版"}
            </span>
            <h1>经过 STAR 法则重塑后的核心亮点</h1>
            <p>{gap.summary}</p>
          </header>

          <div className="resume-paper-card upgraded">
            <section>
              <small>核心项目：{project?.name || jd.role_title}</small>
              <p>
                {afterText.split(/(幂等|压测|真实流量约束|可核验结果|Redis|MySQL|Golang)/g).map((part) =>
                  /幂等|压测|真实流量约束|可核验结果|Redis|MySQL|Golang/.test(part) ? (
                    <mark className="ai-annotated" data-note="批注：此处补充了可追问的底层技术栈或量化结果。" key={`${part}-${afterText.indexOf(part)}`}>
                      {part}
                    </mark>
                  ) : (
                    part
                  ),
                )}
              </p>
            </section>
            <section>
              <small>3 个尖锐追问</small>
              <div className="sharp-question-list">
                {(gap.high_risk_topics.length ? gap.high_risk_topics : plan.sections.flatMap((section) => section.focus_topics)).slice(0, 3).map((item, index) => (
                  <p key={`${item}-${index}`}>
                    <MessageSquareText size={14} />
                    你在 {focusLabelForQuestion(item)} 上的具体方案、边界条件和权衡是什么？
                  </p>
                ))}
              </div>
            </section>
            <section>
              <small>岗位匹配证据</small>
              <ChipList items={gap.matched_skills} tone="good" />
            </section>
          </div>

          <div className="analysis-proof-grid">
            <article>
              <Brain size={17} />
              <strong>训练路径</strong>
              <p>核心技术栈和边界场景经验验证追问会贯穿整轮训练。</p>
            </article>
            <article>
              <ShieldAlert size={17} />
              <strong>风险地图</strong>
              <p>{[...gap.missing_skills, ...gap.high_risk_topics].slice(0, 4).join("、") || "暂无明显风险"}</p>
            </article>
            <article>
              <GitCompareArrows size={17} />
              <strong>不是普通 AI 聊天</strong>
              <p>从旧简历到深度魔改：先解析 JD 与简历证据，再生成训练地图、定向追问和复盘报告。</p>
            </article>
          </div>
        </main>
      </section>

      <section className="analysis-action-plan" aria-label="具体修改清单">
        <header>
          <span>
            <SearchCheck size={16} />
            具体怎么改
          </span>
          <h2>把每个弱点拆成“原问题 → 为什么弱 → 怎么写 → 证据边界”。</h2>
          <p>这里不替你编造经历，只把已有材料改成更容易被追问、也更经得起追问的表达。</p>
        </header>
        <div className="analysis-action-grid">
          {concreteSuggestions.slice(0, 4).map((item, index) => (
            <article key={`${item.original_issue}-${index}`}>
              <div className="analysis-action-index">{String(index + 1).padStart(2, "0")}</div>
              <section>
                <small>原问题</small>
                <p>{item.original_issue}</p>
              </section>
              <section>
                <small>为什么弱</small>
                <p>{item.why_it_is_weak}</p>
              </section>
              <section>
                <small>建议方向</small>
                <p>{item.suggested_direction}</p>
              </section>
              <section className="is-rewrite">
                <small>可参考改写</small>
                <p>{item.example_rewrite}</p>
              </section>
              <section>
                <small>证据边界</small>
                <p>{item.evidence_boundary || "只能使用你真实做过、能解释清楚的项目事实；缺少指标时用条件表达补充。"}</p>
              </section>
            </article>
          ))}
        </div>
      </section>

      <section className="analysis-sticky-cta" aria-label="立即上传或开始训练">
        <div>
          <SearchCheck size={18} />
          <span>羡慕这样的简历吗？立刻上传你的旧简历，免费获取同款大厂风诊断报告。</span>
        </div>
        <div>
          <button className="zip-outline small" onClick={() => onNavigate("start")} type="button">
            立即上传
          </button>
          <button className="zip-primary small" disabled={busy} onClick={isSample ? () => onNavigate("start") : onStartInterview} type="button">
            {busy ? "启动中..." : isSample ? "用我的简历生成" : "进入模拟面试"}
            <ArrowRight size={15} />
          </button>
        </div>
      </section>

      <section className="analysis-launch-checks" aria-label="启动前检查">
        {["JD 分析已完成", "简历分析已完成", "差距地图已生成", "面试计划已生成"].map((item) => (
          <span key={item}>
            <CheckCircle size={13} />
            {item}
          </span>
        ))}
      </section>
    </div>
  );
}
