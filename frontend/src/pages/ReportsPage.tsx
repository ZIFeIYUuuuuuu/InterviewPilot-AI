import {
  Award,
  CheckCircle,
  Flame,
  GraduationCap,
  ListChecks,
  Network,
  RotateCcw,
  School,
  ShieldAlert,
  Target,
  UserRound,
} from "lucide-react";
import { ChipList } from "../components/Shell";
import { dimensionLabel, formatDate, statusLabel } from "../lib/labels";
import type { RouteId } from "../components/Shell";
import type { FlowState, HistoryItem, PracticeReport } from "../types/api";

interface ReportsPageProps {
  flow: FlowState;
  history: HistoryItem[];
  onNavigate: (route: RouteId) => void;
  onLoadReport: (reportId: string) => void;
  onLoadSampleReport: () => void;
}

export function ReportsPage({ flow, history, onNavigate, onLoadReport, onLoadSampleReport }: ReportsPageProps) {
  const report = flow.reportResponse?.report || flow.reportResponse?.stored_report?.report || null;
  const isSampleReport = report?.session_id === "sample-commercial-trust-report";

  return (
    <div className="zip-page-stack">
      {report ? (
        <ReportBoard isSample={isSampleReport} report={report} onRetry={() => onNavigate("start")} />
      ) : (
        <section className="report-empty-trust">
          <div className="empty-state__icon">
            <Target size={28} />
          </div>
          <h1>还没有当前报告。你可以先看一份完整样例，再决定是否上传材料。</h1>
          <p>样例报告会展示弱证据、追问示例、评分理由和下一轮练习计划；它不会进入你的训练历史。</p>
          <div>
            <button className="zip-primary" onClick={onLoadSampleReport} type="button">
              查看样例报告
            </button>
            <button className="zip-outline" onClick={() => onNavigate("interview")} type="button">
              去完成模拟面试
            </button>
          </div>
        </section>
      )}

      <section className="review-lens compact" aria-label="报告复用场景">
        <div className="zip-section-heading compact">
          <div>
            <span>报告如何继续使用</span>
            <h3>报告不是终点，而是下一轮训练的任务清单。</h3>
            <p>同一份复盘报告可以用于个人复训、就业辅导和面试前冲刺。</p>
          </div>
        </div>
        <div className="review-lens__grid three">
          <article className="review-lens__card">
            <header>
              <UserRound size={16} />
              <span>C 端个人训练</span>
            </header>
            <strong>按报告弱项重开一轮</strong>
            <p>个人用户看见风险主题、回答短板和练习计划后，可以围绕同一个 JD 继续训练。</p>
          </article>
          <article className="review-lens__card">
            <header>
              <School size={16} />
              <span>B 端高校辅导</span>
            </header>
            <strong>就业老师有可读材料</strong>
            <p>报告把学生准备状态拆成维度、证据和建议，便于做简历门诊、训练营复盘和跟进辅导。</p>
          </article>
          <article className="review-lens__card">
            <header>
              <Network size={16} />
              <span>平台侧工具</span>
            </header>
            <strong>承接求职准备链路</strong>
            <p>平台可把它作为 JD 查看后的准备工具，连接简历优化、模拟训练和历史复盘。</p>
          </article>
        </div>
      </section>

      <section className="zip-history-panel">
        <div className="zip-section-heading compact">
          <div>
            <h3>练习复盘与历史报告 ({history.length})</h3>
            <p>每份报告都服务下一轮训练重点。</p>
          </div>
        </div>
        <div className="zip-history-list">
          {history.length ? (
            history.map((item) => (
              <article
                className={item.latest_report_id ? "is-report-ready" : "is-incomplete"}
                data-tooltip={item.latest_report_id ? "点击展开这场训练的复盘报告" : "该场训练未完成，点击可重回房间继续"}
                key={item.session_id}
                onClick={() => (item.latest_report_id ? onLoadReport(item.latest_report_id) : onNavigate("interview"))}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    item.latest_report_id ? onLoadReport(item.latest_report_id) : onNavigate("interview");
                  }
                }}
              >
                <div>
                  <span>{statusLabel[item.status] || item.status}</span>
                  <strong>{item.target_role}</strong>
                  <small>{formatDate(item.updated_at)}</small>
                </div>
                <ChipList items={item.weak_area_summary.slice(0, 4)} tone="warn" />
                <b>{item.overall_score ?? "--"}</b>
                {item.latest_report_id ? (
                  <button
                    onClick={(event) => {
                      event.stopPropagation();
                      onLoadReport(item.latest_report_id!);
                    }}
                    type="button"
                  >
                    展开 Q&A 复盘 ▾
                  </button>
                ) : null}
              </article>
            ))
          ) : (
            <div className="zip-empty-inline">暂无历史。完成第一轮训练后会自动出现。</div>
          )}
        </div>
      </section>
    </div>
  );
}

function ReportBoard({ isSample = false, report, onRetry }: { isSample?: boolean; report: PracticeReport; onRetry: () => void }) {
  const dimensions = Object.entries(report.evaluation.dimension_scores || {});
  const topWeakness = report.evaluation.weaknesses[0] || report.evaluation.risk_flags[0] || "暂无明确弱点";
  const nextAction = report.coaching.practice_plan[0] || report.coaching.next_round_focus[0] || "按报告建议完成下一轮练习";
  return (
    <section className="zip-report-board">
      <div className="zip-report-top">
        <div>
          <p>
            <Award size={16} />
            {isSample ? "产品样例报告" : "练习复盘报告"}
          </p>
          <h1>一份可执行的训练复盘报告</h1>
          <small>{report.disclaimer}</small>
          {isSample ? <span className="sample-report-badge">示例内容，不是用户历史</span> : null}
        </div>
        <div className="zip-report-score">
          <strong>{report.evaluation.overall_score}</strong>
          <span>总分 100</span>
        </div>
      </div>

      <div className="report-reading-path">
        {["先看总分与维度", "再看优势与风险", "最后执行下一轮练习动作"].map((item, index) => (
          <span key={item}>
            {String(index + 1).padStart(2, "0")} / {item}
          </span>
        ))}
      </div>

      <section className="report-value-grid" aria-label="报告复盘价值">
        <article>
          <header>
            <ListChecks size={16} />
            <span>评分理由</span>
          </header>
          <strong>{dimensions[0] ? `${dimensionLabel[dimensions[0][0]] || dimensions[0][0]}：${dimensions[0][1].score}` : "维度评分"}</strong>
          <p>{dimensions[0]?.[1].reason || "每个维度都保留原因，便于知道分数来自哪类回答表现。"}</p>
        </article>
        <article>
          <header>
            <Flame size={16} />
            <span>弱点定位</span>
          </header>
          <strong>{topWeakness}</strong>
          <p>弱点会和风险主题一起进入下一轮练习，避免报告停留在总结层面。</p>
        </article>
        <article>
          <header>
            <Target size={16} />
            <span>下一轮训练建议</span>
          </header>
          <strong>{nextAction}</strong>
          <p>建议按顺序执行，先补证据，再练结构，最后重开同一 JD 的模拟面试。</p>
        </article>
      </section>

      <div className="zip-score-card-grid">
        {dimensions.map(([key, value]) => (
          <article key={key}>
            <span>{dimensionLabel[key] || key}</span>
            <strong>{value.score}</strong>
            <p>{value.reason}</p>
          </article>
        ))}
      </div>

      <section className="zip-tool-grid secondary">
        <article className="zip-tool-card">
          <div className="zip-section-heading compact">
            <div>
              <h3>
                <GraduationCap size={18} />
                教练建议
              </h3>
              <p>把评分原因转换为下一轮训练动作。</p>
            </div>
          </div>
          <div className="zip-coaching-stack">
            {report.coaching.top_improvements.map((item) => (
              <article key={item.issue}>
                <h4>{item.issue}</h4>
                <p>{item.why_it_matters}</p>
                <strong>{item.suggestion}</strong>
                <small>{item.example_answer_guidance}</small>
              </article>
            ))}
          </div>
        </article>

        <aside className="zip-right-rail">
          <article className="zip-radar-card">
            <header>
              <h3>
                <CheckCircle size={17} />
                答卷突出长处
              </h3>
            </header>
            <ChipList items={report.evaluation.strengths} tone="good" />
          </article>
          <article className="zip-radar-card">
            <header>
              <h3>
                <Flame size={17} />
                改进提升方向
              </h3>
            </header>
            <ChipList items={[...report.evaluation.weaknesses, ...report.evaluation.risk_flags]} tone="warn" />
          </article>
          <article className="zip-ledger">
            <header>
              <div>
                <ShieldAlert size={16} />
                <span>
                  <strong>下一轮练习计划</strong>
                  <small>建议按顺序完成</small>
                </span>
              </div>
            </header>
            <div className="zip-vertical-list">
              {report.coaching.practice_plan.map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
            <button className="zip-primary small" onClick={onRetry} type="button">
              <RotateCcw size={15} />
              再做一轮训练
            </button>
          </article>
        </aside>
      </section>
    </section>
  );
}
