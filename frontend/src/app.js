const API_BASE = window.INTERVIEWPILOT_API_BASE || "http://127.0.0.1:8000/api/v1";
const STORE_KEY = "interviewpilot.mvp.ui";

const app = document.querySelector("#app");
const state = loadState();

const routes = {
  dashboard: renderDashboard,
  new: renderNewInterview,
  preview: renderAnalysisPreview,
  interview: renderInterviewSession,
  report: renderReport,
};

const labels = {
  route: {
    dashboard: "仪表盘",
    new: "新建面试",
    preview: "分析预览",
    interview: "模拟面试",
    report: "练习报告",
  },
  difficulty: {
    easy: "简单",
    medium: "中等",
    hard: "困难",
  },
  status: {
    draft: "草稿",
    analysis_ready: "分析已完成",
    interview_ready: "可开始面试",
    in_progress: "进行中",
    report_ready: "报告已生成",
    archived: "已归档",
    completed: "已完成",
  },
  role: {
    system: "系统",
    interviewer: "面试官",
    candidate: "候选人",
    assistant: "助手",
  },
  questionType: {
    new_question: "新问题",
    follow_up: "追问",
    transition: "过渡问题",
  },
  dimension: {
    technical_accuracy: "技术准确性",
    depth: "回答深度",
    structure: "表达结构",
    communication: "沟通清晰度",
    role_fit: "岗位匹配度",
    evidence_quality: "证据质量",
  },
};

window.addEventListener("hashchange", render);
render();

function defaultState() {
  return {
    route: "dashboard",
    busy: false,
    error: "",
    productSession: null,
    jdAnalysis: null,
    resumeAnalysis: null,
    gapAnalysis: null,
    resumeOptimization: null,
    interviewPlan: null,
    liveSession: null,
    reportResponse: null,
    history: [],
    historyLoaded: false,
  };
}

function loadState() {
  try {
    return { ...defaultState(), ...JSON.parse(sessionStorage.getItem(STORE_KEY) || "{}") };
  } catch {
    return defaultState();
  }
}

function saveState() {
  sessionStorage.setItem(STORE_KEY, JSON.stringify(state));
}

function routeTo(route) {
  state.route = route;
  saveState();
  window.location.hash = route;
  render();
}

function currentRoute() {
  const hashRoute = window.location.hash.replace("#", "");
  return routes[hashRoute] ? hashRoute : state.route || "dashboard";
}

function render() {
  state.route = currentRoute();
  app.innerHTML = layout(routes[state.route]());
  bindGlobalActions();
  routes[state.route](true);
  saveState();
}

function layout(content) {
  return `
    <header class="topbar">
      <a class="brand" href="#dashboard" data-route="dashboard">
        <span class="brand-mark">IP</span>
        <span>
          <strong>InterviewPilot AI</strong>
          <small>求职者模拟面试教练</small>
        </span>
      </a>
      <nav class="nav">
        ${navLink("dashboard", labels.route.dashboard)}
        ${navLink("new", labels.route.new)}
        ${navLink("preview", labels.route.preview)}
        ${navLink("interview", labels.route.interview)}
        ${navLink("report", labels.route.report)}
      </nav>
    </header>
    <main class="shell">
      ${state.error ? `<div class="alert" role="alert">${escapeHtml(state.error)}</div>` : ""}
      ${state.busy ? `<div class="loading">正在处理面试流程，请稍等...</div>` : ""}
      ${content}
    </main>
  `;
}

function navLink(route, label) {
  const active = state.route === route ? "is-active" : "";
  return `<a class="${active}" href="#${route}" data-route="${route}">${label}</a>`;
}

function bindGlobalActions() {
  document.querySelectorAll("[data-route]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      routeTo(link.dataset.route);
    });
  });
}

function renderDashboard(bindOnly = false) {
  if (!bindOnly) {
    return `
      <section class="page-grid dashboard-grid">
        <div class="hero-panel">
          <p class="eyebrow">作品集演示 · 面向求职者</p>
          <h1>从 JD 和简历，生成一场有针对性的模拟面试报告。</h1>
          <p>
            InterviewPilot AI 会编排多个专业 Agent，完成岗位分析、简历证据提取、差距诊断、
            自适应追问、结构化评分和具体改进建议。MVP 优先打磨文字版闭环，让训练价值一眼可见。
          </p>
          <div class="demo-strip">
            <span>多 Agent 编排</span>
            <span>动态追问</span>
            <span>结构化评分</span>
            <span>可解释反馈</span>
          </div>
          <div class="actions">
            <button class="primary" data-route="new">开始新的面试</button>
            <button data-action="refresh-history">刷新历史记录</button>
          </div>
        </div>
        <section class="panel">
          <div class="section-heading">
            <span>最近练习</span>
            <small>显示 ${state.history.length} 条</small>
          </div>
          <div class="history-list">
            ${state.history.length ? state.history.map(historyItem).join("") : emptyState("还没有练习记录。开始一场新面试后，这里会显示历史。")}
          </div>
        </section>
      </section>
    `;
  }
  document.querySelector("[data-action='refresh-history']")?.addEventListener("click", () => refreshHistory());
  if (!state.historyLoaded && !state.busy) {
    window.setTimeout(() => {
      if (state.route === "dashboard" && currentRoute() === "dashboard" && !state.historyLoaded) {
        refreshHistory();
      }
    }, 250);
  }
  document.querySelectorAll("[data-report-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      await loadReport(button.dataset.reportId);
      routeTo("report");
    });
  });
}

function historyItem(item) {
  const score = item.overall_score == null ? "暂无报告" : `${item.overall_score}/100`;
  const reportButton = item.latest_report_id
    ? `<button class="small" data-report-id="${item.latest_report_id}">查看报告</button>`
    : `<span class="muted">报告待生成</span>`;
  return `
    <article class="history-item">
      <div>
        <strong>${escapeHtml(item.target_role)}</strong>
        <p>${escapeHtml(labels.status[item.status] || item.status)} · ${score}</p>
        ${item.weak_area_summary?.length ? `<small>${escapeHtml(item.weak_area_summary.slice(0, 2).join(" · "))}</small>` : ""}
      </div>
      ${reportButton}
    </article>
  `;
}

function renderNewInterview(bindOnly = false) {
  if (!bindOnly) {
    return `
      <section class="page-grid">
        <div>
          <p class="eyebrow">第 1 步</p>
          <h1>新建面试</h1>
          <p class="lede">使用内置后端 API 工程师示例，五分钟内演示完整闭环；也可以粘贴文本，或上传 PDF/图片文件。</p>
          <div class="demo-note">
            <strong>演示故事线：</strong>
            候选人有真实的 FastAPI/PostgreSQL 项目证据，但 Redis 深度和 ownership 细节较弱。
            面试会围绕技术取舍追问，对模糊回答继续深挖，最后生成可执行的练习报告。
          </div>
        </div>
        <form class="panel form" id="new-interview-form">
          <label>
            目标岗位
            <input name="targetRole" value="后端 API 工程师" required />
          </label>
          <div class="inline-fields">
            <label>
              难度
              <select name="difficulty">
                <option value="easy">简单</option>
                <option value="medium" selected>中等</option>
                <option value="hard">困难</option>
              </select>
            </label>
            <label>
              时长
              <select name="duration">
                <option value="15">15 分钟</option>
                <option value="20" selected>20 分钟</option>
                <option value="30">30 分钟</option>
                <option value="40">40 分钟</option>
              </select>
            </label>
          </div>
          <label>
            JD 文件（可选，仅支持 PDF 或图片）
            <input name="jdFile" type="file" accept="application/pdf,image/*,.pdf,.png,.jpg,.jpeg,.webp" />
            <small class="field-help">PDF 会尝试自动提取文本；图片当前需要在下方文本框提供识别内容作为兜底。</small>
          </label>
          <label>
            岗位描述 JD 文本
            <textarea name="jdText" rows="8" placeholder="粘贴 JD 文本；如果上传图片，请把图片里的文字也粘贴到这里。">${sampleJD()}</textarea>
          </label>
          <label>
            简历文件（可选，仅支持 PDF 或图片）
            <input name="resumeFile" type="file" accept="application/pdf,image/*,.pdf,.png,.jpg,.jpeg,.webp" />
            <small class="field-help">简历 PDF 会尝试自动提取文本；图片当前需要在下方文本框提供识别内容作为兜底。</small>
          </label>
          <label>
            简历文本
            <textarea name="resumeText" rows="8" placeholder="粘贴简历文本；如果上传图片，请把图片里的文字也粘贴到这里。">${sampleResume()}</textarea>
          </label>
          <div class="actions">
            <button class="primary" type="submit">分析 JD 和简历</button>
            <button type="button" data-action="load-demo-data">重载示例数据</button>
            <button type="button" data-action="clear-flow">清空本地流程</button>
          </div>
        </form>
      </section>
    `;
  }
  document.querySelector("#new-interview-form")?.addEventListener("submit", handleNewInterview);
  document.querySelector("[data-action='load-demo-data']")?.addEventListener("click", () => {
    const form = document.querySelector("#new-interview-form");
    if (!form) return;
    form.elements.targetRole.value = "后端 API 工程师";
    form.elements.difficulty.value = "medium";
    form.elements.duration.value = "20";
    form.elements.jdText.value = sampleJD();
    form.elements.resumeText.value = sampleResume();
  });
  document.querySelector("[data-action='clear-flow']")?.addEventListener("click", () => {
    Object.assign(state, defaultState(), { route: "new" });
    saveState();
    render();
  });
}

async function handleNewInterview(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const formElement = event.currentTarget;
  const targetRole = form.get("targetRole").toString().trim();
  const jdText = form.get("jdText").toString().trim();
  const resumeText = form.get("resumeText").toString().trim();
  const jdFile = formElement.elements.jdFile.files[0] || null;
  const resumeFile = formElement.elements.resumeFile.files[0] || null;
  const difficulty = form.get("difficulty").toString();
  const duration = Number(form.get("duration"));

  await withBusy(async () => {
    const jdPayload = await buildInputPayload("JD", jdFile, jdText);
    const resumePayload = await buildInputPayload("简历", resumeFile, resumeText);
    const productSession = await api("/sessions", {
      method: "POST",
      body: {
        input: {
          target_role: targetRole,
          jd: {
            text: jdText || `已上传 JD 文件：${jdFile?.name}`,
            source_type: jdPayload.input_type,
            filename: jdFile?.name || null,
          },
          resume: {
            text: resumeText || `已上传简历文件：${resumeFile?.name}`,
            source_type: resumePayload.input_type,
            filename: resumeFile?.name || null,
          },
          interview_type: "targeted_mock",
          difficulty,
          duration_minutes: duration,
        },
      },
    });
    const jd = await api("/jd/analyze", { method: "POST", body: jdPayload });
    const resume = await api("/resume/analyze", { method: "POST", body: resumePayload });
    const gap = await api("/analysis/gap", {
      method: "POST",
      body: { jd_analysis: jd.analysis, resume_analysis: resume.analysis },
    });
    const optimization = await api("/analysis/resume-optimization", {
      method: "POST",
      body: {
        jd_analysis: jd.analysis,
        resume_analysis: resume.analysis,
        gap_analysis: gap.gap_analysis,
      },
    });
    const plan = await api("/interview/plan", {
      method: "POST",
      body: {
        jd_analysis: jd.analysis,
        resume_analysis: resume.analysis,
        gap_analysis: gap.gap_analysis,
        interview_type: "targeted_mock",
        difficulty,
        duration_minutes: duration,
      },
    });
    await api(`/sessions/${productSession.session.session_id}`, {
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

    Object.assign(state, {
      productSession: productSession.session,
      jdAnalysis: jd.analysis,
      resumeAnalysis: resume.analysis,
      gapAnalysis: gap.gap_analysis,
      resumeOptimization: optimization.resume_optimization,
      interviewPlan: plan.interview_plan,
      liveSession: null,
      reportResponse: null,
    });
    routeTo("preview");
  });
}

async function buildInputPayload(label, file, text) {
  if (!file && !text) {
    throw new Error(`请粘贴${label}文本，或上传${label} PDF/图片文件。`);
  }
  if (!file) {
    return { input_type: "text", text };
  }

  const inputType = inputTypeFromFile(file);
  if (!inputType) {
    throw new Error(`${label}文件格式不支持。请上传 PDF、PNG、JPG、JPEG 或 WebP 文件。`);
  }
  if (inputType === "image" && !text) {
    throw new Error(`${label}图片已可选择上传，但当前还没有 OCR。请先把图片里的文字粘贴到文本框作为兜底。`);
  }

  return {
    input_type: inputType,
    filename: file.name,
    content_base64: await readFileAsBase64(file),
    text: text || null,
  };
}

function inputTypeFromFile(file) {
  const name = file.name.toLowerCase();
  if (file.type === "application/pdf" || name.endsWith(".pdf")) {
    return "pdf";
  }
  if (file.type.startsWith("image/") || /\.(png|jpe?g|webp)$/i.test(name)) {
    return "image";
  }
  return "";
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",").pop() : result);
    };
    reader.onerror = () => reject(new Error("读取上传文件失败，请重新选择文件。"));
    reader.readAsDataURL(file);
  });
}

function renderAnalysisPreview(bindOnly = false) {
  if (!bindOnly) {
    if (!state.jdAnalysis || !state.resumeAnalysis || !state.gapAnalysis) {
      return missingFlow("还没有分析结果。请先新建一场面试。", "new");
    }
    return `
      <section>
        <div class="page-title">
          <p class="eyebrow">第 2 步</p>
          <h1>分析预览</h1>
          <p>开始面试前，系统会先展示对岗位、简历证据、差距风险和简历准备建议的理解。</p>
          <div class="agent-chain">
            <span>JD 分析 Agent</span>
            <span>简历分析 Agent</span>
            <span>差距分析 Agent</span>
            <span>简历优化 Agent</span>
            <span>面试规划 Agent</span>
          </div>
        </div>
        <div class="cards three">
          ${card("JD 理解", [
            strongLine("岗位", state.jdAnalysis.role_title),
            listBlock("硬性要求", state.jdAnalysis.required_skills),
            listBlock("面试重点", state.jdAnalysis.interview_focus),
          ])}
          ${card("简历证据", [
            listBlock("技能", state.resumeAnalysis.candidate_skills),
            listBlock("项目", state.resumeAnalysis.projects?.map((project) => project.name)),
            listBlock("弱证据", state.resumeAnalysis.weak_evidence_skills),
          ])}
          ${card("差距与风险", [
            listBlock("已匹配", state.gapAnalysis.matched_skills),
            listBlock("缺失", state.gapAnalysis.missing_skills),
            listBlock("高风险", state.gapAnalysis.high_risk_topics),
          ])}
        </div>
        <section class="panel">
          <div class="section-heading"><span>简历优化预览</span><small>只优化真实表达，不虚构经历</small></div>
          <p>${escapeHtml(state.resumeOptimization?.optimization_summary || "暂无简历优化摘要。")}</p>
          ${bulletList(state.resumeOptimization?.risk_warnings)}
        </section>
        <section class="panel">
          <div class="section-heading"><span>面试计划</span><small>最多 ${state.interviewPlan.max_questions} 个问题</small></div>
          <div class="timeline">
            ${state.interviewPlan.sections.map((section) => `
              <article>
                <strong>${escapeHtml(section.name)}</strong>
                <p>${escapeHtml(section.goal)}</p>
                <small>${section.duration_minutes} 分钟 · ${escapeHtml((section.focus_topics || []).join("，"))}</small>
              </article>
            `).join("")}
          </div>
        </section>
        <div class="actions">
          <button class="primary" data-action="start-interview">开始模拟面试</button>
          <button data-route="new">编辑输入</button>
        </div>
      </section>
    `;
  }
  document.querySelector("[data-action='start-interview']")?.addEventListener("click", startInterview);
}

async function startInterview() {
  await withBusy(async () => {
    const response = await api("/interview/sessions", {
      method: "POST",
      body: {
        interview_plan: state.interviewPlan,
        jd_analysis: state.jdAnalysis,
        resume_analysis: state.resumeAnalysis,
        gap_analysis: state.gapAnalysis,
      },
    });
    state.liveSession = response.session;
    routeTo("interview");
  });
}

function renderInterviewSession(bindOnly = false) {
  if (!bindOnly) {
    if (!state.liveSession) {
      return missingFlow("还没有进行中的面试。请先从分析预览开始。", "preview");
    }
    const section = activeSection();
    const latest = state.liveSession.latest_question;
    const progress = `${state.liveSession.current_question_count}/${state.liveSession.interview_plan.max_questions}`;
    return `
      <section class="interview-layout">
        <aside class="panel sticky">
          <p class="eyebrow">第 3 步</p>
          <h2>${escapeHtml(section?.name || "模拟面试")}</h2>
          <p>${escapeHtml(section?.goal || "请用具体证据回答当前问题。")}</p>
          <p class="fine-print">面试官会根据你的最新回答，判断是进入新问题还是继续追问。</p>
          <div class="metric-row">
            <span>进度</span>
            <strong>${progress}</strong>
          </div>
          <div class="chips">${(section?.focus_topics || []).map(chip).join("")}</div>
          <p class="fine-print">实时面试过程中不会展示评分；反馈只会在结束面试后生成。</p>
        </aside>
        <section class="panel conversation-panel">
          <div class="section-heading">
            <span>${latest ? escapeHtml(labels.questionType[latest.question_type] || latest.question_type) : "当前问题"}</span>
            <small>${escapeHtml(labels.status[state.liveSession.status] || state.liveSession.status)}</small>
          </div>
          <div class="conversation">
            ${state.liveSession.messages.map(messageBubble).join("")}
          </div>
          ${state.liveSession.status === "completed" ? completedInterviewActions() : answerForm()}
        </section>
      </section>
    `;
  }
  document.querySelector("#answer-form")?.addEventListener("submit", (event) => submitTurn(event, "answer"));
  document.querySelectorAll("[data-turn-action]").forEach((button) => {
    button.addEventListener("click", () => submitControl(button.dataset.turnAction));
  });
  document.querySelector("[data-action='generate-report']")?.addEventListener("click", generateReport);
}

function activeSection() {
  const sections = state.liveSession?.interview_plan?.sections || [];
  return sections[Math.min(state.liveSession.current_section_index || 0, Math.max(0, sections.length - 1))];
}

function messageBubble(message) {
  return `
    <article class="message ${message.role}">
      <small>${escapeHtml(labels.role[message.role] || message.role)}${message.section ? ` · ${escapeHtml(message.section)}` : ""}</small>
      <p>${escapeHtml(message.content)}</p>
    </article>
  `;
}

function answerForm() {
  return `
    <form id="answer-form" class="answer-box">
      <textarea name="answer" rows="5" placeholder="建议按：背景、你的角色、技术选择、取舍、结果 来回答。" required></textarea>
      <div class="actions">
        <button class="primary" type="submit">提交回答</button>
        <button type="button" data-turn-action="skip">跳过</button>
        <button type="button" data-turn-action="next">下一题</button>
        <button type="button" data-turn-action="regenerate">重新生成</button>
        <button type="button" data-turn-action="end">结束面试</button>
      </div>
    </form>
  `;
}

function completedInterviewActions() {
  return `
    <div class="completion-box">
      <strong>面试已结束。</strong>
      <p>生成一份包含评分和改进建议的结构化练习报告。</p>
      <button class="primary" data-action="generate-report">生成报告</button>
    </div>
  `;
}

async function submitTurn(event) {
  event.preventDefault();
  const answer = new FormData(event.currentTarget).get("answer").toString();
  await submitControl("answer", answer);
}

async function submitControl(action, answer = null) {
  await withBusy(async () => {
    const response = await api(`/interview/sessions/${state.liveSession.session_id}/turn`, {
      method: "POST",
      body: { action, answer },
    });
    state.liveSession = response.session;
    render();
  });
}

async function generateReport() {
  if (!state.liveSession || !state.productSession) return;
  await withBusy(async () => {
    const interviewSession = { ...state.liveSession, session_id: state.productSession.session_id };
    const response = await api("/reports/generate", {
      method: "POST",
      body: {
        interview_session: interviewSession,
        resume_optimization: state.resumeOptimization,
      },
    });
    state.reportResponse = response;
    if (response.stored_report?.report_id) {
      await api(`/sessions/${state.productSession.session_id}/finish`, {
        method: "POST",
        body: { report_id: response.stored_report.report_id },
      });
    }
    await refreshHistory({ silent: true });
    routeTo("report");
  });
}

function renderReport(bindOnly = false) {
  if (!bindOnly) {
    const report = state.reportResponse?.report || state.reportResponse?.stored_report?.report;
    if (!report) {
      return missingFlow("还没有加载报告。请先完成面试，或从仪表盘打开历史报告。", "dashboard");
    }
    const dimensions = report.evaluation.dimension_scores;
    return `
      <section>
        <div class="page-title report-title">
          <div>
            <p class="eyebrow">第 4 步</p>
            <h1>练习报告</h1>
            <p>${escapeHtml(report.disclaimer)}</p>
          </div>
          <div class="score-ring">${report.evaluation.overall_score}<small>/100</small></div>
        </div>
        <div class="cards two">
          ${Object.entries(dimensions).map(([name, value]) => `
            <article class="card score-card">
              <strong>${escapeHtml(labels.dimension[name] || name.replaceAll("_", " "))}</strong>
              <span>${value.score}/100</span>
              <p>${escapeHtml(value.reason)}</p>
            </article>
          `).join("")}
        </div>
        <div class="cards two">
          ${card("优势", [bulletList(report.evaluation.strengths)])}
          ${card("弱点与风险", [bulletList([...(report.evaluation.weaknesses || []), ...(report.evaluation.risk_flags || [])])])}
        </div>
        <section class="panel">
          <div class="section-heading"><span>教练建议</span><small>下一轮练习</small></div>
          <div class="coaching-list">
            ${report.coaching.top_improvements.map((item) => `
              <article>
                <strong>${escapeHtml(item.issue)}</strong>
                <p>${escapeHtml(item.why_it_matters)}</p>
                <p><b>行动建议：</b> ${escapeHtml(item.suggestion)}</p>
                <small>${escapeHtml(item.example_answer_guidance)}</small>
              </article>
            `).join("")}
          </div>
          <h3>练习计划</h3>
          ${bulletList(report.coaching.practice_plan)}
          <h3>下一轮重点</h3>
          <div class="chips">${(report.coaching.next_round_focus || []).map(chip).join("")}</div>
        </section>
        <div class="actions">
          <button data-route="dashboard">返回仪表盘</button>
          <button data-route="new">再练一场</button>
        </div>
      </section>
    `;
  }
}

async function loadReport(reportId) {
  await withBusy(async () => {
    const stored = await api(`/reports/${reportId}`);
    state.reportResponse = { stored_report: stored, report: stored.report };
  });
}

async function refreshHistory({ silent = false } = {}) {
  if (!silent) state.busy = true;
  try {
    const response = await api("/sessions");
    state.history = response.items || [];
    state.historyLoaded = true;
    state.error = "";
  } catch (error) {
    state.error = error.message;
  } finally {
    state.busy = false;
    saveState();
    if (!silent) render();
  }
}

async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `请求失败：${response.status}`);
  }
  return payload;
}

async function withBusy(work) {
  state.busy = true;
  state.error = "";
  render();
  try {
    await work();
  } catch (error) {
    state.error = userErrorMessage(error);
    render();
  } finally {
    state.busy = false;
    saveState();
    render();
  }
}

function userErrorMessage(error) {
  const message = error?.message || "";
  if (message === "Failed to fetch" || message.includes("NetworkError") || message.includes("fetch")) {
    return "无法连接后端服务。请确认后端已启动，并且 API 地址配置正确。";
  }
  return message || "出现了一点问题。";
}

function missingFlow(message, route) {
  return `
    <section class="panel empty-panel">
      <h1>${escapeHtml(message)}</h1>
      <button class="primary" data-route="${route}">继续</button>
    </section>
  `;
}

function card(title, blocks) {
  return `
    <article class="card">
      <h3>${escapeHtml(title)}</h3>
      ${blocks.join("")}
    </article>
  `;
}

function strongLine(label, value) {
  return `<p><b>${escapeHtml(label)}：</b>${escapeHtml(value || "未找到")}</p>`;
}

function listBlock(label, items = []) {
  return `<div><b>${escapeHtml(label)}</b>${bulletList(items)}</div>`;
}

function bulletList(items = []) {
  const values = (items || []).filter(Boolean);
  if (!values.length) return `<p class="muted">暂无内容。</p>`;
  return `<ul>${values.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function chip(value) {
  return `<span class="chip">${escapeHtml(value)}</span>`;
}

function emptyState(message) {
  return `<div class="empty">${escapeHtml(message)}</div>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function sampleJD() {
  return `后端 API 工程师
硬性要求：Python、FastAPI、PostgreSQL、Redis、API 设计、自动化测试、线上 API 问题排查。
加分项：Docker、异步任务处理、可观测性、云部署经验。
岗位职责：构建可靠的客户侧 API，优化数据库访问，思考缓存与延迟，编写测试，排查线上问题，并与产品团队协作。
面试重点：API 边界、数据库取舍、缓存策略、模糊问题下的问题排查、职责边界和清晰沟通。`;
}

function sampleResume() {
  return `后端 API 项目
使用 Python、FastAPI 和 PostgreSQL 构建了一个面试练习应用的后端服务。设计了请求校验结构，实现了会话和报告 API 路由，并为数据访问行为编写测试。

项目细节：
- 为会话和报告增加了 JSON 持久化。
- 实现了健康检查、API 路由和报告生成接口。
- 在数据结构变化过程中排查过校验错误。

技能：Python、FastAPI、PostgreSQL、测试、API 设计。
弱项：Redis 和生产级可观测性主要来自课程探索，需要更充分的面试准备。
职责边界说明：简历提到了后端 API，但还没有量化延迟、规模或故障影响。`;
}
