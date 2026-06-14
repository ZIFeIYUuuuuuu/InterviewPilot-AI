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
- Competition product description exists in `docs/PRODUCT_DESCRIPTION.md`
- Competition submission checklist exists in `docs/SUBMISSION_PACKAGE.md`
- Project-level agent contract exists in `agent.md`
- Repository startup rule exists in `AGENTS.md`
- Codebase now contains a dependency-free Python MVP loop under `interviewpilot/`
- Codebase now contains a FastAPI backend skeleton under `backend/app/`
- Codebase now contains a React + Vite + TypeScript frontend under `frontend/`
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
- `backend/app/services/gap_analyzer.py`: evidence-aware gap analysis, free diagnosis preview, and truthful resume optimization service
- `backend/app/services/interview_planner_prompt.py`: Interview Planner prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/interview_planner.py`: section-based interview planning service using JD, resume, gap, interview type, difficulty, and duration
- `backend/app/services/interviewer_prompt.py`: Interviewer prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/interview_session.py`: in-memory text mock interview loop with section progression, dynamic follow-up decisions, and control actions
- `backend/app/services/voice_config.py`: safe voice-provider readiness metadata for browser fallback plus Aliyun/Doubao environment-key placeholders without exposing secrets
- `backend/app/services/voice_synthesis.py`: Aliyun DashScope/CosyVoice HTTP TTS integration for interviewer question playback, with browser fallback metadata when keys, network, provider response, or playback are unavailable
- `backend/app/services/evaluator_prompt.py`: Evaluator prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/coach_prompt.py`: Coach prompt builder aligned to `docs/AGENT_PROMPTS.md`
- `backend/app/services/llm_client.py`: optional OpenAI-compatible LLM client for Alibaba Cloud Model Studio/DashScope-style endpoints with schema validation and local fallback
- `backend/app/services/report_generator.py`: completed-session report generation with rubric scoring and actionable coaching
- `backend/app/services/json_store.py`: minimal JSON persistence for workflow sessions, live interview snapshots, stored reports, and merged history summaries
- `frontend/`: React + Vite + TypeScript frontend for the candidate-facing AI job-search training product
- `frontend/src/main.tsx`: React entry point
- `frontend/src/App.tsx`: frontend route/state orchestrator for Dashboard, Start, Resume Optimization, Analysis Preview, Interview, and Reports pages
- `frontend/src/lib/api.ts`: typed API client for existing `/api/v1` backend capabilities, including sessions, JD/resume analysis, gap analysis, resume optimization, interview planning/live session, and reports
- `frontend/src/lib/storage.ts`: sessionStorage persistence for the current frontend workflow state
- `frontend/src/lib/labels.ts`: Chinese display labels for statuses, dimensions, roles, and difficulty
- `frontend/src/components/Shell.tsx`: zip/workbench-style shared shell with sticky top navigation, brand/status area, mobile drawer, empty state, and chip list helpers
- `frontend/src/pages/`: page-level React components for dashboard/workbench, intake, resume optimizer, analysis preview, interview cockpit, and reports/history
- `frontend/src/styles.css`: non-Vectr zip/workbench responsive visual system for the AI job-search training platform, including product dashboard modules, launch/intake cards, resume optimization desk, analysis map, dark immersive interview cockpit, report/history board, and mobile-safe layouts
- `.github/workflows/pages.yml`: GitHub Pages deployment workflow that installs frontend dependencies, builds the Vite app, and publishes `frontend/dist`
- `docs/DEMO_RUNBOOK.md`: demo startup steps, happy-path script, degraded-input check, product-boundary checklist, and demo data reset instructions
- `docs/PORTFOLIO_BRIEF.md`: concise portfolio pitch, demo narrative, screenshot plan, product highlights, and technical highlights
- `docs/PRODUCT_DESCRIPTION.md`: competition-facing product说明书 source document
- `docs/SUBMISSION_PACKAGE.md`: same-day submission checklist with material mapping, demo links, and local run instructions
- `output/pdf/InterviewPilotAI_Product_Description.pdf`: generated product说明书 PDF for competition upload
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
- Frontend runtime now uses React/Vite/TypeScript plus `lucide-react` for the product interface. The later Vectr / GSAP / Lenis / Three homepage experiment has been removed from the active frontend.
- Scores are practice feedback only and must not be presented as hiring decisions.
- API paths should remain grouped around PRD workflow modules: JD intake/analysis, resume intake/analysis, gap analysis, interview sessions, reports, and dashboard history.
- Agent-output schemas live in dedicated files matching the PRD/prompt modules: `jd.py`, `resume.py`, `gap.py`, `optimization.py`, `interview.py`, `evaluation.py`, and `coaching.py`.
- Session/report/history/state entities live in `backend/app/schemas/session.py` and `backend/app/schemas/report.py`.
- `InterviewPilotState` is the stable internal orchestration state for future backend or LangGraph-style workflows. It carries input, analysis outputs, transcript messages, evaluation, coaching, report, errors, and current workflow step.
- Prompt-aligned schemas use strict Pydantic models that reject unknown keys to keep model outputs inspectable and prevent recruiter-side or unsupported fields from silently entering the workflow.
- JD analysis currently supports pasted text as the reliable path. PDF input accepts provided text fallback and attempts best-effort extraction when bytes are supplied. Scanned/image-only JD PDFs and JD images can use best-effort local OCR when Tesseract/PyMuPDF tessdata is available, then still require manual correction because OCR may be imperfect.
- Resume analysis currently supports pasted text as the reliable path. PDF input accepts provided text fallback and attempts best-effort extraction when bytes are supplied; DOCX input uses best-effort text extraction from standard document XML. Scanned/image-only resume PDFs can use best-effort local OCR when Tesseract/PyMuPDF tessdata is available, then still require manual correction because OCR may be imperfect. Image-only DOCX and standalone resume images degrade to manual text correction.
- Local OCR runtime can use project-local language data under `data/tessdata`; `INTERVIEWPILOT_TESSDATA_PREFIX` overrides this path. The current Windows dev machine has Tesseract at `D:\Program Files\Tesseract-OCR\tesseract.exe` and local `chi_sim`, `eng`, and `osd` traineddata files.
- The New Interview frontend supports optional file selection for both JD and resume, limited to PDF and image MIME/extensions. Image uploads currently require pasted text fallback because OCR is not implemented.
- Gap analysis consumes structured `JDAnalysis` and `ResumeAnalysis`; it distinguishes matched skills with project evidence, missing required JD skills that are not visible in the resume, and weak evidence skills that are present but under-supported.
- `/api/v1/analysis/preview` consumes `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis` and returns a stable free diagnosis preview with a training-only preview score, top issues, weak evidence, follow-up questions, report summary, and privacy/boundary note.
- Resume optimization consumes `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis`; suggestions must improve truthful expression only and include likely interview follow-up risks caused by weak or missing evidence. Each bullet suggestion carries an `evidence_boundary` so rewrites stay grounded in existing user material.
- Interview planning consumes structured `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis`; it returns section-based plans with `name`, `duration_minutes`, `goal`, `focus_topics`, `max_questions`, and `plan_summary`.
- Interview planning now supports stable interview type options: JD 定向模拟、内容理解、岗位匹配、项目深挖、群面训练. It also preserves interviewer persona options: 温和型、技术深挖型、压力型.
- Interview plan duration mapping is stable for MVP: 10-15 minutes produces 3 sections, 16-30 minutes produces 4 sections, and 31-45 minutes produces 5 sections. Difficulty adjusts goals and question budget. The deterministic plan covers the required flow in compressed or full form: opening/project entry, JD skill follow-up, weak-evidence follow-up, pressure/boundary scenario follow-up, and closing.
- Live interview sessions consume `InterviewPlan`, `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis`; they maintain an in-memory transcript, current section index, question count, latest interviewer output, and status.
- Live interview sessions should reuse the product workflow `session_id` when one already exists, so reports, history, and workflow state stay attached to one interview lifecycle.
- Live interview controls are stable for MVP: `answer` may trigger follow-up or a new question, `skip` and `next` force progression, `regenerate` replaces the latest interviewer question without incrementing question count, and `end` completes the session without producing evaluation.
- Live interview output must not expose scores or hiring-style judgments; scoring belongs only to the post-interview Evaluator/Report stage.
- Voice interview support is intentionally progressive: the backend exposes `/api/v1/interview/voice/config` for provider readiness and `/api/v1/interview/voice/synthesize` for Aliyun DashScope/CosyVoice TTS. The frontend uses browser SpeechRecognition for candidate speech input and prefers backend Aliyun audio for interviewer playback when selected, falling back to browser speechSynthesis when keys, network, provider response, or playback are unavailable. Missing provider keys must not block text interview or browser voice fallback.
- Post-interview reports consume completed interview sessions and optionally resume optimization output. Reports return `PracticeReport` plus Evaluator and Coach prompt metadata.
- Report generation uses six stable rubric dimensions: technical accuracy, depth, structure, communication, role fit, and evidence quality. Every dimension must include a score and reason. Completed sessions with insufficient substantive transcript return an explicit insufficient-evidence evaluation instead of pretending to judge performance.
- MVP persistence uses a local JSON store selected by `INTERVIEWPILOT_STORE_PATH`, defaulting to `data/interviewpilot_store.json`. This is intentionally lightweight and replaceable by SQLite/Postgres later.
- Dashboard history merges workflow-session state and live-interview state by `session_id` so one user interview appears once even while it is in progress or after a report is generated.
- Product-level session APIs are stable around `/api/v1/sessions`: create a workflow session, read it, patch analysis/planning artifacts, finish it with an optional stored report, and list history for dashboard needs.
- Report read APIs are stable around `/api/v1/reports/{report_id}` and `/api/v1/reports/sessions/{session_id}/latest`; report generation stores a `StoredPracticeReport` for later review.
- Frontend v0.2 is a React + Vite + TypeScript app with `lucide-react` icons to match the provided reference frontends. It stores transient UI state in `sessionStorage`, relies on backend persistence for session/report history, and calls the backend through `window.INTERVIEWPILOT_API_BASE` or same-origin `/api/v1` by default.
- Vite uses relative static asset paths so the generated `frontend/dist` build works when hosted under the GitHub Pages project path `/InterviewPilot-AI/`.
- Vite dev server proxies `/api` to `http://127.0.0.1:8000`, so local frontend development avoids browser CORS while still preserving the backend `/api/v1` contract.
- The old dependency-free frontend shell (`frontend/server.mjs`, `frontend/src/app.js`, and the old CSS implementation) has been replaced and should not be reintroduced as the primary frontend structure.
- The active frontend direction is the zip-reference recreation: the homepage is a dense product workbench aligned to `interviewpilot-ai.zip` / `.tmp_zip_read/zip2`, while the interview page keeps the dark immersive cockpit style aligned to `interviewpilot-ai (1).zip` / `.tmp_zip_read/zip1`.
- The homepage now foregrounds the real product loop inside the workbench itself: `简历分析与优化` and `JD 定向模拟面试` are the two primary entry modules, with analysis, cockpit, report history, and boundary modules arranged in the zip-like card rhythm.
- Business pages continue using the existing API-backed workflow surfaces and shared visual system; this rollback changes presentation, not route structure or backend contracts.
- The demo-ready frontend still exposes the clear recording path `输入 JD 和简历 -> 分析 -> 面试 -> 报告`, and any sample JD/resume content must be triggered by explicit user action rather than prefilled by default.
- The 求职启动 page no longer pre-fills demo JD/resume content by default; users provide real target-role, JD, and resume inputs before the frontend calls the existing backend intake pipeline.
- Frontend network errors are translated into Chinese guidance so raw browser messages such as `Failed to fetch` are not shown to users.
- Homepage and route visual verification screenshots are captured under `output/playwright/`. The current zip-reference validation captures `zip-reference-dashboard.png`, `zip-reference-start.png`, `zip-reference-resume.png`, `zip-reference-analysis.png`, `zip-reference-interview.png`, `zip-reference-reports.png`, `zip-reference-mobile-dashboard.png`, and `zip-reference-interview-active.png`.
