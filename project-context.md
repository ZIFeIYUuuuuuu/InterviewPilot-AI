# Project Context

## Scope

InterviewPilot AI is a candidate-facing AI mock interview coach. The first version focuses on helping job seekers prepare for backend, full-stack, and AI application engineering roles.

## Core Product Loop

1. User provides a target JD through text, image, or PDF
2. User provides resume content
3. System parses and analyzes JD and resume
4. System generates gap analysis and resume optimization suggestions
5. System generates a structured interview plan
6. System runs a text-based mock interview with dynamic follow-up
7. System generates structured evaluation and coaching feedback

## Core Modules

- JD parsing and JD analyzer
- Resume parsing and resume analyzer
- Gap analysis
- Resume optimization suggestions
- Interview planner
- Interviewer
- Evaluator
- Coach
- Dashboard and history

## Product Boundaries

- Build for job seekers, not recruiters
- Treat evaluation as coaching feedback, not hiring judgment
- Improve resume phrasing without fabricating experience
- Prioritize text-based quality over voice or video features

## Current Repository State

- Product PRD exists in `docs/PRD.md`
- MVP demo runbook exists in `docs/DEMO_RUNBOOK.md`
- Portfolio/demo positioning brief exists in `docs/PORTFOLIO_BRIEF.md`
- Project-level agent contract exists in `agent.md`
- Repository startup rule exists in `AGENTS.md`
- Codebase now contains a dependency-free Python MVP loop under `interviewpilot/`
- Codebase now contains a FastAPI backend skeleton under `backend/app/`
- Codebase now contains a minimal frontend shell under `frontend/`
- `main.py` delegates to `interviewpilot.cli`
- `tests/test_mvp_flow.py` verifies the text MVP loop
- `tests/test_backend_skeleton.py` verifies the backend health route

## Key Constraints

- Changes must stay aligned with `agent.md` and `docs/PRD.md`
- Memory files must be maintained in UTF-8 without BOM
- Product-facing work should preserve explainability, graceful fallback, and user control
- User-facing product copy and generated fallback content should be Simplified Chinese by default; English API/schema keys are retained only as developer contracts

## Current Architecture

- `backend/app/main.py`: FastAPI application factory and backend runtime entry point
- `backend/app/core/config.py`: environment-backed base settings for service name, version, API prefix, host, port, reload, and CORS
- `backend/app/core/env.py`: minimal `.env` loader for local development without adding a dependency
- `backend/app/api/v1/router.py`: versioned API router composition point for PRD modules
- `backend/app/api/v1/routes/health.py`: health check route at `/api/v1/health`
- `backend/app/api/v1/routes/jd.py`: JD input, analysis, preview, and manual correction routes
- `backend/app/api/v1/routes/resume.py`: resume input, analysis, preview, and manual correction routes
- `backend/app/api/v1/routes/analysis.py`: gap analysis and resume optimization routes
- `backend/app/api/v1/routes/interview.py`: interview planning and live text-session routes
- `backend/app/api/v1/routes/reports.py`: post-interview evaluation and coaching report routes
- `backend/app/api/v1/routes/sessions.py`: product-level session lifecycle and dashboard history routes
- `backend/app/schemas/`: Pydantic schema package for prompt-aligned agent outputs, API entities, report/history models, and orchestration state
- `backend/app/services/jd_extraction.py`: best-effort JD text extraction for text/PDF/image inputs with manual fallback
- `backend/app/services/jd_prompt.py`: JD Analyzer prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/jd_analyzer.py`: JD analyzer service that wires prompt metadata, local conservative analysis, preview storage, and manual correction
- `backend/app/services/resume_extraction.py`: resume text extraction for text input plus PDF manual fallback
- `backend/app/services/resume_prompt.py`: Resume Analyzer prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/resume_analyzer.py`: conservative resume analyzer service that avoids inventing skills, ownership, impact, or project evidence
- `backend/app/services/gap_prompt.py`: Gap Analysis prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/optimization_prompt.py`: Resume Optimization prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/gap_analyzer.py`: evidence-aware gap analysis and truthful resume optimization service
- `backend/app/services/interview_planner_prompt.py`: Interview Planner prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/interview_planner.py`: section-based interview planning service using JD, resume, gap, interview type, difficulty, and duration
- `backend/app/services/interviewer_prompt.py`: Interviewer prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/interview_session.py`: in-memory text mock interview loop with section progression, dynamic follow-up decisions, and control actions
- `backend/app/services/evaluator_prompt.py`: Evaluator prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/coach_prompt.py`: Coach prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/llm_client.py`: optional OpenAI-compatible LLM client for Alibaba Cloud Model Studio/DashScope-style endpoints with schema validation and local fallback
- `backend/app/services/report_generator.py`: completed-session report generation with rubric scoring and actionable coaching
- `backend/app/services/json_store.py`: minimal JSON persistence for workflow sessions, live interview snapshots, stored reports, and history summaries
- `frontend/`: minimal dependency-free SPA frontend with `npm run dev` using a tiny Node HTTP server
- `frontend/server.mjs`: static file server with SPA fallback to `index.html`
- `frontend/src/app.js`: vanilla JavaScript MVP flow for Dashboard, New Interview, Analysis Preview, Interview Session, and Report pages
- `frontend/src/styles.css`: responsive MVP styling and layout primitives for the candidate-facing workflow
- `docs/DEMO_RUNBOOK.md`: demo startup steps, happy-path script, degraded-input check, product-boundary checklist, and demo data reset instructions
- `docs/PORTFOLIO_BRIEF.md`: concise portfolio pitch, demo narrative, screenshot plan, product highlights, and technical highlights
- `interviewpilot/models.py`: dataclass schemas for JD analysis, resume analysis, gap analysis, optimization, interview plans, questions, evaluation, and coaching
- `interviewpilot/analysis.py`: local conservative rules for JD/resume analysis, gap analysis, and truthful resume optimization suggestions
- `interviewpilot/interview.py`: structured interview planning and dynamic follow-up question generation
- `interviewpilot/report.py`: rubric-style practice evaluation and coaching report generation
- `interviewpilot/pipeline.py`: orchestration for building an MVP session from JD text and resume text
- `interviewpilot/cli.py`: CLI demo and file-based text input entry point

## Implementation Notes

- The current analyzer is a local deterministic MVP engine, not a final LLM implementation.
- The local engine exists to make the full candidate-facing loop executable and testable before external model integration.
- Optional LLM-backed agent execution is available through OpenAI-compatible chat completions when `INTERVIEWPILOT_LLM_API_KEY` or `DASHSCOPE_API_KEY` is configured. Defaults are `INTERVIEWPILOT_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1` and `INTERVIEWPILOT_LLM_MODEL=glm-5`.
- Local `.env` files are supported for developer convenience, while `.env.example` documents safe placeholder configuration. Real secrets must remain in ignored `.env` files or shell environment variables.
- LLM outputs are validated against strict Pydantic schemas; invalid JSON, schema mismatch, API errors, or timeouts fall back to the local deterministic MVP engine.
- The prompt contract asks LLM-backed agents to return user-facing string values in Simplified Chinese. The deterministic local engine also emits Simplified Chinese for analysis notes, interview questions, reports, coaching suggestions, and graceful fallback messages.
- Backend runtime dependencies are currently limited to FastAPI and Uvicorn.
- Frontend runtime is intentionally dependency-free for this scaffold phase.
- Scores are practice feedback only and must not be presented as hiring decisions.
- API paths should remain grouped around PRD workflow modules: JD intake/analysis, resume intake/analysis, gap analysis, interview sessions, reports, and dashboard history.
- Agent-output schemas live in dedicated files matching the PRD/prompt modules: `jd.py`, `resume.py`, `gap.py`, `optimization.py`, `interview.py`, `evaluation.py`, and `coaching.py`.
- Session/report/history/state entities live in `backend/app/schemas/session.py` and `backend/app/schemas/report.py`.
- `InterviewPilotState` is the stable internal orchestration state for future backend or LangGraph-style workflows. It carries input, analysis outputs, transcript messages, evaluation, coaching, report, errors, and current workflow step.
- Prompt-aligned schemas use strict Pydantic models that reject unknown keys to keep model outputs inspectable and prevent recruiter-side or unsupported fields from silently entering the workflow.
- JD analysis currently supports pasted text as the reliable path. PDF input accepts provided text fallback and attempts best-effort extraction when bytes are supplied; image OCR is not available yet and degrades to manual text correction.
- Resume analysis currently supports pasted text as the reliable path. PDF input accepts provided text fallback and attempts best-effort extraction when bytes are supplied; image OCR is not available yet and degrades to manual text correction.
- The New Interview frontend supports optional file selection for both JD and resume, limited to PDF and image MIME/extensions. Image uploads currently require pasted text fallback because OCR is not implemented.
- Gap analysis consumes structured `JDAnalysis` and `ResumeAnalysis`; it distinguishes matched skills with project evidence, missing required JD skills that are not visible in the resume, and weak evidence skills that are present but under-supported.
- Resume optimization consumes `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis`; suggestions must improve truthful expression only and include likely interview follow-up risks caused by weak or missing evidence.
- Interview planning consumes structured `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis`; it returns section-based plans with `name`, `duration_minutes`, `goal`, `focus_topics`, `max_questions`, and `plan_summary`.
- Interview plan duration mapping is stable for MVP: 10-15 minutes produces 3 sections, 16-30 minutes produces 4 sections, and 31-45 minutes produces 5 sections. Difficulty adjusts goals and question budget.
- Live interview sessions consume `InterviewPlan`, `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis`; they maintain an in-memory transcript, current section index, question count, latest interviewer output, and status.
- Live interview controls are stable for MVP: `answer` may trigger follow-up or a new question, `skip` and `next` force progression, `regenerate` replaces the latest interviewer question without incrementing question count, and `end` completes the session without producing evaluation.
- Live interview output must not expose scores or hiring-style judgments; scoring belongs only to the post-interview Evaluator/Report stage.
- Post-interview reports consume completed interview sessions and optionally resume optimization output. Reports return `PracticeReport` plus Evaluator and Coach prompt metadata.
- Report generation uses six stable rubric dimensions: technical accuracy, depth, structure, communication, role fit, and evidence quality. Every dimension must include a score and reason.
- MVP persistence uses a local JSON store selected by `INTERVIEWPILOT_STORE_PATH`, defaulting to `data/interviewpilot_store.json`. This is intentionally lightweight and replaceable by SQLite/Postgres later.
- Product-level session APIs are stable around `/api/v1/sessions`: create a workflow session, read it, patch analysis/planning artifacts, finish it with an optional stored report, and list history for dashboard needs.
- Report read APIs are stable around `/api/v1/reports/{report_id}` and `/api/v1/reports/sessions/{session_id}/latest`; report generation stores a `StoredPracticeReport` for later review.
- Frontend MVP is a no-build, browser-native SPA. It stores transient UI state in `sessionStorage`, relies on backend persistence for session/report history, and calls the backend through `window.INTERVIEWPILOT_API_BASE` or `http://127.0.0.1:8000/api/v1` by default.
- Frontend network errors are translated into Chinese guidance so raw browser messages such as `Failed to fetch` are not shown to users.
