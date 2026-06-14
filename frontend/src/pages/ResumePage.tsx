import { AlertTriangle, ArrowRight, FileCheck, FileText, Lock, SearchCheck, Sparkles, UploadCloud, Workflow } from "lucide-react";
import { ChipList } from "../components/Shell";
import type { RouteId } from "../components/Shell";
import type { BulletImprovementSuggestion, FlowState } from "../types/api";

interface ResumePageProps {
  flow: FlowState;
  onNavigate: (route: RouteId) => void;
}

const fallbackSuggestion: BulletImprovementSuggestion = {
  original_issue: "项目描述停留在“负责开发”，缺少技术方案、边界条件和结果指标。",
  why_it_is_weak: "面试官无法判断你做的是业务 CRUD、系统设计，还是关键链路治理。",
  suggested_direction: "用 STAR 结构补齐场景、任务、动作和结果，并把技术关键词绑定到真实项目证据。",
  example_rewrite: "围绕订单状态流转梳理接口边界；如果你确实实现过分布式锁、防重幂等或压测记录，可以补充真实约束、验证方式和可核验结果。",
  evidence_boundary: "不要补造并发量、QPS 或百分比；只有你能解释来源的数据才写进简历。",
};

export function ResumePage({ flow, onNavigate }: ResumePageProps) {
  const resume = flow.resumeAnalysis;
  const optimization = flow.resumeOptimization;
  const gap = flow.gapAnalysis;
  const targetRole = flow.productSession?.input?.target_role || flow.jdAnalysis?.role_title || "Go 后端工程师";
  const resumeFile = flow.productSession?.input?.resume?.filename || window.sessionStorage.getItem("interviewpilot_resume_filename") || "尚未上传真实简历";
  const suggestions = optimization?.bullet_improvement_suggestions.length ? optimization.bullet_improvement_suggestions : [fallbackSuggestion];
  const weakItems = [
    ...(resume?.weaknesses || []),
    ...(gap?.weak_evidence_skills.map((item) => `${item} 证据不足`) || []),
    ...(gap?.missing_skills.map((item) => `JD 要求 ${item}，简历未体现`) || []),
  ].slice(0, 3);
  const score = resume && gap ? Math.max(58, Math.min(92, 76 + gap.matched_skills.length * 3 - weakItems.length * 4)) : null;
  const project = resume?.projects[0];
  const outputLocked = !resume;

  return (
    <div className="resume-console-page">
      <aside className="resume-control-panel" aria-label="简历诊断控制区">
        <section className="resume-file-card">
          <span>
            <FileText size={16} />
            当前简历
          </span>
          <strong>{resumeFile}</strong>
          <button className="zip-outline small" onClick={() => onNavigate("start")} type="button">
            重新上传
          </button>
        </section>

        <section className="resume-config-card">
          <header>
            <span>
              <SearchCheck size={16} />
              目标岗位设定
            </span>
            <strong>让诊断结果贴近真实求职方向。</strong>
          </header>
          <label>
            <span>方向</span>
            <input readOnly value={targetRole} />
          </label>
          <label>
            <span>级别</span>
            <select defaultValue="campus">
              <option value="intern">实习</option>
              <option value="campus">校招</option>
              <option value="junior">1-3 年</option>
            </select>
          </label>
          <label>
            <span>粘贴目标岗位 JD（可选，精准匹配）</span>
            <textarea
              readOnly
              value={flow.productSession?.input?.jd?.text?.slice(0, 220) || "比如：熟悉高并发、MySQL、Redis、服务治理，具备项目复盘和问题定位能力..."}
            />
          </label>
        </section>

        <button className="resume-analysis-button" onClick={() => onNavigate("analysis")} type="button">
          <Sparkles size={18} />
          {resume ? "查看深度分析结果" : "去上传材料开始深度分析"}
          <ArrowRight size={17} />
        </button>

        <section className="resume-control-note">
          <Lock size={16} />
          <p>控制区只锁定你的求职意向；右侧报告基于真实解析结果渲染，不伪造历史或成功率。</p>
        </section>
      </aside>

      <main className={`resume-output-panel ${outputLocked ? "is-locked" : "is-active"}`} aria-label="核心诊断与报告生成区">
        <section className="resume-score-board">
          <div>
            <span>整体评估得分</span>
            <strong>{score ? `${score} / 100` : "-- / 100"}</strong>
            <p>{optimization?.optimization_summary || "在左侧配置目标岗位并上传简历后，AI 将在此处生成结构化诊断报告。"}</p>
          </div>
          <div className="resume-score-orb" aria-hidden="true">
            {score || "--"}
          </div>
        </section>

        <section className="resume-hard-issues">
          <header>
            <AlertTriangle size={17} />
            <span>闪电诊断结论（3 个硬伤）</span>
          </header>
          {weakItems.length ? (
            weakItems.map((item, index) => (
              <p key={`${item}-${index}`}>
                <b>{index + 1}</b>
                {item}
              </p>
            ))
          ) : (
            ["缺乏大流量高并发实战指标", "技术栈出现但缺少项目证据", "职责边界和结果复盘不够清楚"].map((item, index) => (
              <p className="is-placeholder" key={item}>
                <b>{index + 1}</b>
                {item}
              </p>
            ))
          )}
        </section>

        <section className="resume-pipeline">
          <div className="resume-section-heading">
            <span>
              <Workflow size={16} />
              优化建议流水线
            </span>
            <strong>把“做过什么”改成“为什么值得被追问”。</strong>
          </div>
          {suggestions.map((item, index) => (
            <article className="resume-pipeline-card" key={`${item.original_issue}-${index}`}>
              <header>
                <span>{project?.name || `项目 ${index + 1}`}</span>
                <small>{item.why_it_is_weak}</small>
              </header>
              <div className="resume-pipeline-compare">
                <section>
                  <small>优化前风险</small>
                  <p>{item.original_issue}</p>
                </section>
                <section>
                  <small>优化后方向</small>
                  <p>{item.example_rewrite || item.suggested_direction}</p>
                </section>
              </div>
            </article>
          ))}
        </section>

        <section className="resume-evidence-dock">
          <article>
            <span>
              <FileCheck size={15} />
              技术栈证据
            </span>
            <ChipList items={resume?.candidate_skills || ["Golang", "Redis", "MySQL", "分布式锁"]} />
          </article>
          <article>
            <span>
              <UploadCloud size={15} />
              建议补强
            </span>
            <ChipList items={optimization?.rewrite_targets || ["核心项目量化", "职责边界", "追问风险"]} tone="warn" />
          </article>
        </section>

        {!outputLocked ? (
          <section className="resume-interview-activation">
            <div>
              <span>下一步训练</span>
              <strong>针对以上 3 个尖锐追问，立即开始 5 分钟模拟面试对抗</strong>
              <p>系统会带着当前 JD、简历证据和风险地图进入面试房间，追问会优先围绕弱证据展开。</p>
            </div>
            <button className="zip-primary launch" onClick={() => onNavigate("interview")} type="button">
              进入面试房间
              <ArrowRight size={16} />
            </button>
          </section>
        ) : null}

        {outputLocked ? (
          <div className="resume-output-lock" aria-hidden="true">
            <Sparkles size={28} />
            <strong>在左侧上传简历后，此处的智能复盘引擎将实时激活...</strong>
            <p>分数、硬伤、追问风险和 STAR 改写会基于你的真实材料生成。</p>
          </div>
        ) : null}
      </main>
    </div>
  );
}
