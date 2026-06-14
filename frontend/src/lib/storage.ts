import type { FlowState } from "../types/api";

const STORE_KEY = "interviewpilot.ai.frontend.v2";

export const emptyFlow: FlowState = {
  productSession: null,
  jdAnalysis: null,
  resumeAnalysis: null,
  gapAnalysis: null,
  resumeOptimization: null,
  interviewPlan: null,
  liveSession: null,
  reportResponse: null,
};

export function loadFlow(): FlowState {
  try {
    const raw = sessionStorage.getItem(STORE_KEY);
    return raw ? { ...emptyFlow, ...JSON.parse(raw) } : emptyFlow;
  } catch {
    return emptyFlow;
  }
}

export function saveFlow(flow: FlowState): void {
  sessionStorage.setItem(STORE_KEY, JSON.stringify(flow));
}

export function clearFlow(): FlowState {
  sessionStorage.removeItem(STORE_KEY);
  return emptyFlow;
}
