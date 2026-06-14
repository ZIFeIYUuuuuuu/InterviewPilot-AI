import { useEffect, useState } from "react";
import { CustomCursor } from "./components/CustomCursor";
import { Shell, type RouteId } from "./components/Shell";
import {
  createInterviewPlanForFlow,
  finishProductSession,
  generateReport,
  listHistory,
  loadInterviewVoiceConfig,
  loadStoredReport,
  runIntakePipeline,
  sendInterviewTurn,
  startLiveInterview,
  userErrorMessage,
} from "./lib/api";
import { samplePracticeReport } from "./lib/sampleEvidence";
import { clearFlow, loadFlow, saveFlow } from "./lib/storage";
import { AnalysisPage } from "./pages/AnalysisPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InterviewPage } from "./pages/InterviewPage";
import { ReportsPage } from "./pages/ReportsPage";
import { ResumePage } from "./pages/ResumePage";
import { StartPage } from "./pages/StartPage";
import type {
  FlowState,
  HistoryItem,
  IntakeForm,
  InterviewAction,
  InterviewType,
  InterviewerPersona,
  InterviewVoiceConfig,
  VoiceProvider,
} from "./types/api";

const routes: RouteId[] = ["dashboard", "start", "resume", "analysis", "interview", "reports"];

function routeFromHash(): RouteId {
  const value = window.location.hash.replace("#/", "") as RouteId;
  return routes.includes(value) ? value : "dashboard";
}

export default function App() {
  const [route, setRoute] = useState<RouteId>(routeFromHash);
  const [flow, setFlow] = useState<FlowState>(loadFlow);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [voiceConfig, setVoiceConfig] = useState<InterviewVoiceConfig | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const syncRoute = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", syncRoute);
    return () => window.removeEventListener("hashchange", syncRoute);
  }, []);

  useEffect(() => {
    saveFlow(flow);
  }, [flow]);

  useEffect(() => {
    refreshHistory(false);
    loadInterviewVoiceConfig().then(setVoiceConfig).catch(() => setVoiceConfig(null));
  }, []);

  function navigate(next: RouteId) {
    setRoute(next);
    window.location.hash = `/${next}`;
  }

  async function runTask(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await work();
    } catch (caught) {
      setError(userErrorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function refreshHistory(showError = true) {
    try {
      setHistory(await listHistory());
    } catch (caught) {
      if (showError) setError(userErrorMessage(caught));
    }
  }

  function handleResetAndStart() {
    setFlow(clearFlow());
    navigate("start");
  }

  function handleIntakeSubmit(form: IntakeForm) {
    runTask(async () => {
      const nextFlow = await runIntakePipeline(form);
      setFlow(nextFlow);
      await refreshHistory(false);
      navigate("resume");
    });
  }

  function handleStartInterview(options?: {
    interviewType?: InterviewType;
    interviewerPersona?: InterviewerPersona;
    voiceProvider?: VoiceProvider;
  }) {
    runTask(async () => {
      let nextFlow = flow;
      const requestedType = options?.interviewType || flow.interviewPlan?.interview_type;
      const requestedPersona = options?.interviewerPersona || flow.interviewPlan?.interviewer_persona;
      if (
        requestedType &&
        requestedPersona &&
        flow.interviewPlan &&
        (flow.interviewPlan.interview_type !== requestedType ||
          flow.interviewPlan.interviewer_persona !== requestedPersona)
      ) {
        const interviewPlan = await createInterviewPlanForFlow(flow, requestedType, requestedPersona);
        nextFlow = { ...flow, interviewPlan, liveSession: null };
      }
      const liveSession = await startLiveInterview(nextFlow, options?.voiceProvider || "browser");
      setFlow((current) => ({ ...current, interviewPlan: nextFlow.interviewPlan, liveSession }));
      navigate("interview");
    });
  }

  function handleTurn(action: InterviewAction, answer?: string) {
    if (!flow.liveSession) return;
    runTask(async () => {
      const liveSession = await sendInterviewTurn(flow.liveSession!.session_id, action, answer);
      setFlow((current) => ({ ...current, liveSession }));
    });
  }

  function handleGenerateReport() {
    runTask(async () => {
      const response = await generateReport(flow);
      if (flow.productSession?.session_id && response.stored_report?.report_id) {
        await finishProductSession(flow.productSession.session_id, response.stored_report.report_id);
      }
      setFlow((current) => ({ ...current, reportResponse: response }));
      await refreshHistory(false);
      navigate("reports");
    });
  }

  function handleLoadReport(reportId: string) {
    runTask(async () => {
      const response = await loadStoredReport(reportId);
      setFlow((current) => ({ ...current, reportResponse: response }));
      navigate("reports");
    });
  }

  function handleLoadSampleReport() {
    setFlow((current) => ({
      ...current,
      reportResponse: {
        report: samplePracticeReport,
        stored_report: null,
      },
    }));
    navigate("reports");
  }

  function handleLoadSampleAnalysis() {
    setFlow((current) => ({
      ...current,
      reportResponse: {
        report: samplePracticeReport,
        stored_report: null,
      },
    }));
    navigate("analysis");
  }

  return (
    <>
      <CustomCursor />
      <Shell busy={busy} error={error} onNavigate={navigate} route={route}>
        {route === "dashboard" ? (
          <DashboardPage
            flow={flow}
            history={history}
            onLoadSampleAnalysis={handleLoadSampleAnalysis}
            onNavigate={navigate}
          />
        ) : null}
        {route === "start" ? <StartPage busy={busy} onSubmit={handleIntakeSubmit} /> : null}
        {route === "resume" ? <ResumePage flow={flow} onNavigate={navigate} /> : null}
        {route === "analysis" ? (
          <AnalysisPage busy={busy} flow={flow} onNavigate={navigate} onStartInterview={handleStartInterview} />
        ) : null}
        {route === "interview" ? (
          <InterviewPage
            busy={busy}
            flow={flow}
            voiceConfig={voiceConfig}
            onGenerateReport={handleGenerateReport}
            onNavigate={navigate}
            onStartInterview={handleStartInterview}
            onTurn={handleTurn}
          />
        ) : null}
        {route === "reports" ? (
          <ReportsPage
            flow={flow}
            history={history}
            onLoadReport={handleLoadReport}
            onLoadSampleReport={handleLoadSampleReport}
            onNavigate={navigate}
          />
        ) : null}
      </Shell>
    </>
  );
}
