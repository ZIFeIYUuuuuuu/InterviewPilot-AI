import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Activity, BarChart3, FileText, Menu, MessageSquareText, Target, UserRound, X, Zap } from "lucide-react";

export type RouteId = "dashboard" | "start" | "resume" | "analysis" | "interview" | "reports";

interface ShellProps {
  route: RouteId;
  busy: boolean;
  error: string;
  onNavigate: (route: RouteId) => void;
  children: ReactNode;
}

const navItems: Array<{ id: RouteId; label: string; short: string }> = [
  { id: "dashboard", label: "工作台", short: "首页" },
  { id: "start", label: "求职启动", short: "启动" },
  { id: "resume", label: "简历优化", short: "简历" },
  { id: "analysis", label: "分析预览", short: "分析" },
  { id: "interview", label: "模拟面试", short: "面试" },
  { id: "reports", label: "报告历史", short: "报告" },
];

export function Shell({ route, busy, error, onNavigate, children }: ShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  function go(next: RouteId) {
    setMenuOpen(false);
    onNavigate(next);
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  return (
    <div className={`app-shell route-${route}`}>
      <header className="workspace-header">
        <button className="workspace-brand" onClick={() => go("dashboard")} type="button" aria-label="InterviewPilot AI 首页">
          <span className="workspace-brand__mark">
            <Zap size={18} />
          </span>
          <span>
            <strong>InterviewPilot AI</strong>
            <small>AI 求职训练平台</small>
          </span>
        </button>

        <nav className="workspace-nav" aria-label="主导航">
          {navItems.map((item) => (
            <button className={route === item.id ? "active" : ""} key={item.id} onClick={() => go(item.id)} type="button">
              {item.label}
            </button>
          ))}
        </nav>

        <div className="workspace-actions">
          <button className="zip-outline small workspace-start-link" onClick={() => go("start")} type="button">
            开始训练
          </button>
          <button className="workspace-profile" type="button" aria-label="用户登录">
            <UserRound size={17} />
          </button>
          <button
            className="mobile-menu-button"
            onClick={() => setMenuOpen((value) => !value)}
            type="button"
            aria-label={menuOpen ? "关闭菜单" : "打开菜单"}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      <aside className={`mobile-drawer ${menuOpen ? "open" : ""}`} aria-hidden={!menuOpen}>
        <div className="mobile-drawer__panel">
          <div className="mobile-drawer__title">
            <strong>InterviewPilot AI</strong>
            <button onClick={() => setMenuOpen(false)} type="button" aria-label="关闭菜单">
              <X size={18} />
            </button>
          </div>
          {navItems.map((item) => (
            <button className={route === item.id ? "active" : ""} key={item.id} onClick={() => go(item.id)} type="button">
              {item.label}
            </button>
          ))}
        </div>
      </aside>

      {error ? <div className="global-alert">{error}</div> : null}

      <main className="workspace-main" data-route={route}>
        {children}
      </main>
    </div>
  );
}

export function EmptyState({ title, actionLabel, onAction }: { title: string; actionLabel: string; onAction: () => void }) {
  return (
    <section className="empty-state">
      <div className="empty-state__icon">
        <Target size={28} />
      </div>
      <h1>{title}</h1>
      <p>先完成前置步骤后，这里会显示真实分析、训练或报告内容。</p>
      <button className="zip-primary" onClick={onAction} type="button">
        {actionLabel}
      </button>
    </section>
  );
}

export function ChipList({ items, tone = "neutral" }: { items?: string[]; tone?: "neutral" | "good" | "warn" }) {
  const values = (items || []).filter(Boolean);
  if (!values.length) {
    return <p className="muted">暂无明确内容。</p>;
  }
  return (
    <div className={`chip-list ${tone}`}>
      {values.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

export const moduleIcons = {
  jd: <Target size={20} />,
  resume: <FileText size={20} />,
  analysis: <BarChart3 size={20} />,
  interview: <MessageSquareText size={20} />,
  report: <Activity size={20} />,
};
