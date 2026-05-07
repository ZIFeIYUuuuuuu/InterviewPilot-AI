# Memory

## Durable Product Decisions

- Product direction is candidate-facing interview preparation, not recruiter-side screening
- The core product loop is JD plus resume to mock interview to evaluation and coaching
- Resume optimization must improve expression only and must not fabricate experience
- Evaluation must be framed as training feedback, not hiring judgment
- The first executable MVP uses a local deterministic rules engine to make the loop testable before LLM integration
- Backend domain schemas should remain aligned to `docs/AGENT_PROMPTS.md` output keys so agent responses can validate without translation glue
- Prompt-aligned Pydantic schemas should reject unknown keys to prevent unsupported or recruiter-side fields from silently entering the product workflow
- Core business prompts are versioned product assets; current prompt contract is v0.2 and requires exactly one schema-matching JSON object, no markdown fences, no prose wrappers, no extra keys, empty arrays for list fields, and null only for explicitly nullable fields
- Prompt changes should record the practical output-quality improvement they are meant to create, not just wording changes
- `InterviewPilotState` is the preferred internal state object for future backend or LangGraph-style orchestration
- JD text input is the reliable MVP path; PDF/image inputs must degrade to manual correction when extraction quality is weak or unavailable
- JD Analyzer prompt metadata should stay aligned with `docs/AGENT_PROMPTS.md` until a real LLM provider replaces the local conservative analyzer
- Resume text input is the reliable MVP path; PDF resume input should use best-effort extraction plus provided text fallback, while image resume input must degrade to manual text correction until OCR is implemented
- Resume Analyzer must never infer unstated ownership, production experience, impact, metrics, or skills; skills-only lines are weak evidence unless tied to project/experience evidence
- Resume-only analysis must not classify JD-required skills as missing; missing-vs-matched belongs to Gap Analysis
- Gap Analysis must distinguish missing required JD skills from weakly evidenced resume skills; a skill present with thin evidence is not missing
- Resume Optimization must never add fictional skills, ownership, metrics, systems, impact, or tools; suggestions may only improve truthful expression and preparation framing
- Live interview sessions must not expose scores, evaluation, or hiring-style judgment; live output is limited to interviewer questions, section state, transcript state, and user controls
- Live interviewer follow-ups must stay anchored to the latest answer, current section, JD/resume context, and gap analysis rather than randomly changing topics
- Regenerating a live interview question should not increment question count or add a candidate answer; skip and next may progress the session without scoring
- Post-interview evaluation may only be generated after the interview session is completed and must be grounded in transcript evidence
- Evaluator scores are practice feedback only; every rubric dimension must include both `score` and `reason`, and reports must not produce pass/fail, hire/no-hire, offer, or rejection verdicts
- Coach output must convert weaknesses, gap analysis, resume optimization risks, and transcript evidence into concrete actions rather than generic encouragement
- MVP persistence is a local JSON store, configurable by `INTERVIEWPILOT_STORE_PATH`; do not introduce heavier database abstractions until the product flow requires them
- Stored reports are the source for report回看/history score summaries; live session scoring should still only happen after interview completion
- External LLM calls are optional and must never be required for MVP completion; invalid model output, network failure, timeout, or missing API key must fall back to the local deterministic engine
- API keys must stay in environment variables such as `INTERVIEWPILOT_LLM_API_KEY` or `DASHSCOPE_API_KEY`; never commit or document real secrets
- All candidate-facing UI copy, fallback analyzer output, interview questions, reports, coaching suggestions, and demo data should be Simplified Chinese by default; API/schema field names may remain English as stable developer contracts

## Current Feature Status

- PRD: active
- Project-level agent contract: active
- Repository startup read-order rule: active
- Memory-file workflow: active
- Application implementation: in_progress
- Text MVP core loop: active
- Local CLI demo: active
- Backend domain schemas: active
- Unified orchestration state: active
- JD input and analysis API: active
- Resume input and analysis API: active
- Gap analysis API: active
- Resume optimization API: active
- Interview planner API: active
- Text mock interview loop API: active
- Post-interview evaluation and coaching report API: active
- Session lifecycle API: active
- Minimal JSON persistence: active
- Dashboard/history API foundation: active
- Image OCR for JD input: not_started
- High-fidelity PDF JD parsing: partial
- High-fidelity PDF resume parsing: not_started
- LLM-backed production agents: not_started
- Optional OpenAI-compatible LLM test path: active
- Prompt v0.2 stability contract: active
- Simplified Chinese user-facing product surface: active

## Repeated User Constraints

- AI must read `agent.md` before reading other project files
- The text from the uploaded rule image must be integrated into repository constraints
- Project memory files must be maintained and treated as part of the workflow
- Every completed phase should update `progress.md`
- Long-term constraints or important decisions should update `memory.md`
- Stable background, architecture, directory, or constraint changes should update `project-context.md`
- The platform should feel fully Chinese to users; avoid English fallback strings such as raw network errors, report advice, section names, or deterministic local-engine output

## High-Risk Areas And Pitfalls

- Do not let product scope drift into recruiter workflows
- Do not produce fake resume improvements or unsupported claims
- Do not bypass the memory files when starting substantial work
- Do not edit memory files in a non-UTF-8 encoding
- Do not treat local rules-based scoring as a real technical correctness judge; it is only MVP practice feedback
- Skill extraction must avoid substring false positives such as `ts` inside `requirements` or `rag` inside ordinary words
- Do not loosen schema validation or add broad catch-all fields unless there is a clear product reason and the risk is documented
- Do not remove the shared prompt response contract from business prompt builders unless an equivalent structured-output mechanism replaces it
- Do not hardcode provider API keys, model secrets, or user credentials into source files, docs, tests, or demo data
- JD parsing failures must return structured analysis plus uncertainty/manual-correction flags, not hard-stop the user flow
- Resume parsing failures must return structured analysis plus uncertainty/manual-correction flags, not hard-stop the user flow
- Frontend upload controls should accept only PDF/image files for JD and resume; unsupported file types should be rejected before API submission
- Resume optimization examples should use conditional language such as "If true" when demonstrating stronger phrasing
- Do not reintroduce English into user-visible fallback outputs when changing local analyzers, interview orchestration, report generation, frontend error handling, or demo data

## Abandoned Or Rejected Approaches

- Treating the product as a recruiter-side screening tool: rejected because current product direction is candidate-facing and lower-risk
- Treating resume optimization as full automatic rewrite in MVP: rejected because it increases hallucination and trust risk
- Adding external dependencies for the first MVP scaffold: rejected because the current goal is a small, reviewable, dependency-free loop
