# Progress

## Current Phase

Chinese interface localization

## Recently Completed

- Wrote the initial PRD in `docs/PRD.md`
- Created `agent.md` as the repository agent contract
- Created `AGENTS.md` to force AI startup read order
- Added memory-file workflow and constraints for `project-context.md`, `progress.md`, and `memory.md`
- Added a reusable prompt pack for the core InterviewPilot AI business agents in `docs/AGENT_PROMPTS.md`
- Implemented a dependency-free Python MVP loop for JD analysis, resume analysis, gap analysis, resume optimization, interview planning, question generation, evaluation, and coaching
- Replaced the PyCharm sample `main.py` with the InterviewPilot CLI entry point
- Added regression tests for the candidate-facing text loop
- Added a FastAPI backend skeleton with configuration, API v1 router composition, Pydantic schemas, and `/api/v1/health`
- Added a minimal frontend shell with `npm run dev`
- Added README startup instructions
- Added prompt-aligned Pydantic schemas for JD analysis, resume analysis, gap analysis, resume optimization, interview planning/messages, evaluation, and coaching
- Added base session, report, history, and orchestration-state schemas
- Added JD input/analyze/preview/correction API routes
- Added JD text parsing and conservative structured JD analysis
- Added JD Analyzer prompt builder aligned to `docs/AGENT_PROMPTS.md`
- Added PDF/image fallback behavior for JD input without blocking the workflow
- Added Resume input/analyze/preview/correction API routes
- Added Resume Analyzer prompt builder aligned to `docs/AGENT_PROMPTS.md`
- Added conservative text resume analysis with weak-evidence and uncertainty handling
- Added PDF resume fallback/manual-correction path
- Added Gap Analysis API that consumes `JDAnalysis` and `ResumeAnalysis`
- Added Resume Optimization API that consumes `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis`
- Added prompt builders for Gap Analysis and Resume Optimization aligned to `docs/AGENT_PROMPTS.md`
- Added evidence-aware matched/missing/weak classification and truthful resume suggestion generation
- Added Interview Planner API that consumes `JDAnalysis`, `ResumeAnalysis`, and `GapAnalysis`
- Added Interview Planner prompt builder aligned to `docs/AGENT_PROMPTS.md`
- Added section-based planning with duration and difficulty mapping
- Added live text interview session API that consumes an interview plan plus JD, resume, and gap analysis
- Added Interviewer prompt builder aligned to `docs/AGENT_PROMPTS.md`
- Added in-memory session message state, current section progression, question count, and latest-question tracking
- Added follow-up vs new-question decision logic for short, vague, or weak answers
- Added live controls for skip, next, regenerate, and end without exposing scores
- Added post-interview report API for completed interview sessions
- Added Evaluator prompt builder aligned to `docs/AGENT_PROMPTS.md`
- Added Coach prompt builder aligned to `docs/AGENT_PROMPTS.md`
- Added rubric-based scoring across technical accuracy, depth, structure, communication, role fit, and evidence quality
- Added coaching output with top improvements, example answer guidance, practice plan, and next-round focus
- Added product-level session lifecycle API for create/read/update/finish
- Added minimal JSON persistence for workflow sessions, live interview snapshots, stored reports, and history summaries
- Added report read APIs by report id and latest report for a session
- Added dashboard/history response with target role, status, score, weak-area summary, and latest report id
- Added MVP frontend pages for Dashboard, New Interview, Analysis Preview, Interview Session, and Report
- Added frontend integration with JD analysis, resume analysis, gap analysis, resume optimization, interview planning, live interview turns, report generation, session finish, and history
- Added section/focus/progress display in the live Interview Session page
- Added structured score and coaching displays in the Report page
- Added MVP demo runbook covering startup, happy path, degraded input, product boundary checks, and demo data reset
- Added readiness tests for complete text flow, report boundary language, and incomplete JD fallback
- Hardened Dashboard history auto-refresh so it does not interrupt immediate navigation clicks
- Added shared v0.2 JSON-only prompt contract coverage across core business prompt builders
- Tuned JD Analyzer, Resume Analyzer, Gap Analysis, Resume Optimization, Interview Planner, Interviewer, Evaluator, and Coach prompts for schema stability, evidence grounding, uncertainty handling, and candidate-facing quality
- Updated `docs/AGENT_PROMPTS.md` with prompt version history and v0.2 quality improvements
- Added minimal prompt quality regression tests covering JSON contract presence, schema-key alignment, and risky-agent guardrails
- Polished the frontend demo narrative for portfolio screenshots and recordings
- Added stronger default Backend API Engineer sample data designed to show gap analysis, dynamic follow-up, and structured report value
- Expanded README with candidate-facing positioning, demo highlights, product highlights, and technical highlights
- Expanded `docs/DEMO_RUNBOOK.md` with a guided portfolio demo script, screenshot checklist, talking points, and boundary checks
- Added `docs/PORTFOLIO_BRIEF.md` as a concise project pitch and demo narrative artifact
- Added optional OpenAI-compatible LLM client for Alibaba Cloud Model Studio/DashScope-style endpoint testing
- Wired JD Analyzer, Resume Analyzer, Gap Analysis, Resume Optimization, Interview Planner, Interviewer, Evaluator, and Coach to try validated LLM JSON output before falling back to local deterministic logic
- Added LLM environment configuration for `INTERVIEWPILOT_LLM_API_KEY`, `DASHSCOPE_API_KEY`, `INTERVIEWPILOT_LLM_BASE_URL`, `INTERVIEWPILOT_LLM_MODEL`, and timeout/enabled flags
- Documented `glm-5` test configuration without storing any real API key
- Added `.env.example` and local `.env` support for easier backend startup with optional LLM configuration
- Added `.gitignore` rules so `.env` and local data artifacts stay out of version control
- Added a lightweight `.env` loader without introducing a new dependency
- Localized the frontend interface to Simplified Chinese, including navigation, page titles, buttons, empty states, status labels, report dimension labels, and default demo data
- Updated the HTML language metadata to `zh-CN`
- Added a prompt-contract instruction for LLM-backed user-facing strings to prefer Simplified Chinese
- Localized backend deterministic fallback output to Simplified Chinese for JD/resume warnings, gap analysis, resume optimization, interview plan sections, live interviewer questions, report scoring reasons, risk flags, coaching suggestions, and CLI demo copy
- Replaced raw frontend network error display such as `Failed to fetch` with Chinese troubleshooting guidance
- Updated regression tests to assert Chinese-facing product boundaries and fallback behavior
- Added JD and resume file upload selectors on the New Interview page, limited to PDF and image files
- Wired frontend file uploads to base64 API payloads while preserving pasted text as fallback
- Added backend resume image input support with manual-correction fallback
- Upgraded resume PDF input from text-only fallback to best-effort PDF text extraction plus manual fallback

## In Progress

- JD/resume PDF upload is available with best-effort extraction; image upload is available as a selectable input but still requires pasted text fallback until OCR is implemented

## Next Step

- Restart frontend/backend if already running, then test one JD PDF and one resume PDF through the New Interview page

## Blockers / Awaiting Confirmation

- Final choice of first supported role categories beyond backend, full-stack, and AI application roles
- Whether resume PDF parsing belongs in MVP or v1.1
- No `.git` repository is initialized in the current workspace, so git-based diff/commit workflow is unavailable

## This Session Summary

- Re-read startup files in repository order before making changes
- Re-read startup files and PRD before localizing UI
- Converted user-facing frontend labels and page copy to Simplified Chinese
- Added Chinese display mappings for route names, session statuses, message roles, question types, difficulty labels, and report dimensions
- Converted the default demo JD/resume text to Chinese while preserving technical terms
- Converted deterministic backend/local-engine user-visible strings to Simplified Chinese, including report/coaching content that previously appeared in English
- Added Chinese handling for frontend fetch/network errors and Chinese skill aliases used by demo text
- Updated tests that intentionally check product-boundary language so they verify the new Chinese copy
- Added optional PDF/image upload controls for both JD and resume in the New Interview form
- Added frontend file-type validation and base64 conversion before calling `/jd/analyze` and `/resume/analyze`
- Added resume image fallback behavior and best-effort resume PDF extraction in the backend
- Verified the upload controls render in a real browser

## Key Modified Files

- `frontend/index.html`
- `frontend/src/app.js`
- `frontend/src/styles.css`
- `backend/app/schemas/report.py`
- `backend/app/schemas/resume.py`
- `backend/app/services/gap_analyzer.py`
- `backend/app/services/interview_planner.py`
- `backend/app/services/interview_session.py`
- `backend/app/services/jd_analyzer.py`
- `backend/app/services/jd_extraction.py`
- `backend/app/services/report_generator.py`
- `backend/app/services/resume_analyzer.py`
- `backend/app/services/resume_extraction.py`
- `backend/app/services/prompt_contract.py`
- `interviewpilot/analysis.py`
- `interviewpilot/interview.py`
- `interviewpilot/report.py`
- `interviewpilot/cli.py`
- `interviewpilot/text_utils.py`
- `tests/test_gap_optimization_api.py`
- `tests/test_interview_planner_api.py`
- `tests/test_interview_session_api.py`
- `tests/test_jd_api.py`
- `tests/test_mvp_flow.py`
- `tests/test_mvp_readiness.py`
- `tests/test_report_api.py`
- `tests/test_resume_api.py`
- `memory.md`
- `project-context.md`
- `progress.md`

## Verification Status

- `node --check frontend/src/app.js` passed
- `node --check frontend/server.mjs` passed
- `INTERVIEWPILOT_LLM_ENABLED=false python -m unittest discover -s tests` passed: 48 tests
- `python -m compileall backend interviewpilot` passed
- Playwright Chinese UI smoke check passed for Dashboard and New Interview
- Playwright upload-control smoke check passed for New Interview: JD and resume file inputs restrict `accept` to PDF/images and show Chinese upload guidance
