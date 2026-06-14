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
- JD text input is the reliable MVP path; PDF/image inputs use best-effort extraction plus local OCR when Tesseract/PyMuPDF tessdata is available. OCR output must be marked partial/manual-correction because recognition can contain errors; if OCR is unavailable or empty, return structured manual fallback instead of blocking the flow.
- JD Analyzer prompt metadata should stay aligned with `docs/AGENT_PROMPTS.md` until a real LLM provider replaces the local conservative analyzer
- Resume text input is the reliable MVP path; PDF resume input should use best-effort extraction plus provided text fallback. Scanned/image-only resume PDFs may use local Tesseract/PyMuPDF OCR when available, but OCR output must be marked partial/manual-correction because recognition can contain errors. Standalone image resume input still degrades to manual text correction until image OCR is explicitly implemented.
- DOCX resume input supports best-effort text extraction from standard `.docx` document XML without adding dependencies. If the DOCX is image-only, corrupt, encrypted, or has no extractable text, backend must return a structured manual-fallback response asking for pasted text or a text-layer PDF rather than silently pretending to parse it.
- Local OCR language data is expected at `data/tessdata` unless `INTERVIEWPILOT_TESSDATA_PREFIX` or `TESSDATA_PREFIX` is set. Keep `data/` ignored; traineddata files are runtime assets, not source files or secrets.
- Resume Analyzer must never infer unstated ownership, production experience, impact, metrics, or skills; skills-only lines are weak evidence unless tied to project/experience evidence
- Resume-only analysis must not classify JD-required skills as missing; missing-vs-matched belongs to Gap Analysis
- Gap Analysis must distinguish missing required JD skills from weakly evidenced resume skills; a skill present with thin evidence is not missing
- Resume Optimization must never add fictional skills, ownership, metrics, systems, impact, or tools; suggestions may only improve truthful expression and preparation framing
- Resume Optimization bullet suggestions must include `evidence_boundary`, and example rewrites must use conditional wording when facts or metrics are not already present in the user's material.
- Live interview sessions must not expose scores, evaluation, or hiring-style judgment; live output is limited to interviewer questions, section state, transcript state, and user controls
- Live interviewer follow-ups must stay anchored to the latest answer, current section, JD/resume context, and gap analysis rather than randomly changing topics
- Interview type configuration is active: keep `targeted_mock`, `content_focus`, `role_fit`, `project_deep_dive`, and `group` as stable API options unless a migration path is provided.
- Interviewer persona configuration is active: keep `warm`, `technical`, and `pressure` as stable API options. Pressure mode may be sharper but must remain respectful, candidate-facing, and must not expose live scoring.
- The deterministic interview plan must preserve the core section flow: opening/project entry, JD skill follow-up, weak-evidence follow-up, pressure/boundary scenario, and closing; shorter durations may combine adjacent stages but should not omit the intent.
- Regenerating a live interview question should not increment question count or add a candidate answer; skip and next may progress the session without scoring
- Live interview state should reuse the product workflow `session_id` whenever the interview belongs to an existing workflow session; do not create a second user-visible history identity for the same interview lifecycle
- Post-interview evaluation may only be generated after the interview session is completed and must be grounded in transcript evidence
- Completed sessions with insufficient substantive transcript should report "not enough evidence" style training feedback with reasons instead of forcing normal scores.
- Evaluator scores are practice feedback only; every rubric dimension must include both `score` and `reason`, and reports must not produce pass/fail, hire/no-hire, offer, or rejection verdicts
- Coach output must convert weaknesses, gap analysis, resume optimization risks, and transcript evidence into concrete actions rather than generic encouragement
- MVP persistence is a local JSON store, configurable by `INTERVIEWPILOT_STORE_PATH`; do not introduce heavier database abstractions until the product flow requires them
- Dashboard history must merge workflow-session and live-interview state by `session_id`; do not list both stores as separate visible records for one interview
- Stored reports are the source for report回看/history score summaries; live session scoring should still only happen after interview completion
- Frontend v0.2 primary implementation is React + Vite + TypeScript; do not reintroduce the old vanilla `frontend/src/app.js` + `frontend/server.mjs` shell as the main frontend
- The frontend default API base is same-origin `/api/v1`; Vite dev proxies `/api` to `http://127.0.0.1:8000` to avoid local CORS while preserving the backend route contract
- GitHub Pages static demo must deploy the built Vite output from `frontend/dist`; do not publish the raw `frontend/` source directory as the Pages artifact
- The product frontend information architecture should keep resume optimization as a first-class module, not a small secondary card
- The mock interview cockpit must stay visually and behaviorally unified with the rest of the AI job-search training product, and must not expose live scoring
- The user later explicitly requested a rollback to the earliest zip-reference recreation version. The active homepage must stay as the zip-style product workbench sourced from `interviewpilot-ai.zip`, not the later InterviewArk / GSAP landing page.
- The active visual pairing is fixed for now: main homepage/workbench follows `.tmp_zip_read/zip2`, while the immersive interview cockpit follows `.tmp_zip_read/zip1`.
- User clarified the website should primarily present two main functions on the homepage: 1) resume analysis and resume optimization, 2) mock interview based on the resume plus target JD. The homepage should not show too much content and should not rely on oversized typography to communicate value.
- The active homepage should build commercial trust before asking for sensitive resume input: first show what the user provides, what the system produces, and concrete sample output such as weak evidence, gap analysis, follow-up questions, and report shape.
- Homepage copy should feel like a real user-facing product, not a judge-demo page. Avoid `评审理解区`, contest recording language, fake progress, fake metrics, and fake recent-history patterns.
- The two core product outcomes must stay visible early: `简历分析与优化` and `JD 定向模拟面试`, but they should be proven through output examples rather than feature-card promises.
- Commercial trust sections should include privacy/data boundary, free-preview boundary, and a concrete comparison with generic ChatGPT use.
- Sample reports and sample materials must always be clearly labeled as product examples, never real user history, and must not be inserted into user history.
- Homepage `查看完整样例报告` should route to the analysis preview proof page first, then guide users to `/start`; do not bypass the visual proof step by sending sample-curious users directly to reports.
- The explicit `使用示例材料体验` button should fill the Start page JD/resume textareas with the e-commerce backend / Redis cache sample, but examples must remain opt-in and editable.
- The homepage primary conversion promise should be `免费生成我的预览报告` or equivalent, not a vague `输入 JD 和简历`; paid intent depends on users first seeing their own material preview.
- Do not expand local history rows on the homepage. If history exists, show an isolated `本机训练历史` notice and route users to the reports page, so old local data is not confused with fake samples.
- Price anchors may be shown as product packaging (`免费预览`, `单次完整训练`, `月度练习`) but paid tiers must stay `待定` until a real payment system and entitlement boundary exist.
- If homepage or intake examples are added later, they must be triggered by an explicit `示例数据` button or equivalent user action; never default-pre-fill fake JD or resume data.
- The extracted zip folders appear semantically reversed relative to the user's wording: `.tmp_zip_read/zip2` contains the main workbench components, while `.tmp_zip_read/zip1` contains the immersive interview system; use the actual component structure as the visual source of truth
- External LLM calls are optional and must never be required for MVP completion; invalid model output, network failure, timeout, or missing API key must fall back to the local deterministic engine
- API keys must stay in environment variables such as `INTERVIEWPILOT_LLM_API_KEY` or `DASHSCOPE_API_KEY`; never commit or document real secrets
- Voice provider keys must stay in environment variables such as `INTERVIEWPILOT_ALIYUN_VOICE_API_KEY` and `INTERVIEWPILOT_DOUBAO_VOICE_API_KEY`; the backend may report whether keys are configured but must never return key values. Browser speech fallback and plain text interview must remain available when provider keys are missing or provider calls fail.
- Aliyun voice playback is active through `/api/v1/interview/voice/synthesize`, not just voice-id configuration. To hear Aliyun audio by default, set `INTERVIEWPILOT_VOICE_PROVIDER=aliyun`; otherwise users can choose `阿里云百炼语音` on the interview setup screen. If synthesis or audio playback fails, the frontend must fall back to browser speech without breaking the interview.
- Live voice interview UX must keep text and voice as freely switchable input modes. Browser speech recognition may stop after sentence boundaries, so the frontend should auto-restart listening until the user explicitly pauses. Voice transcripts must remain editable and must not auto-submit answers.
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
- React/Vite/TypeScript frontend: active
- GitHub Pages static demo workflow: active
- Old vanilla frontend shell: replaced
- Image OCR for JD input: active
- High-fidelity PDF JD parsing: partial
- High-fidelity PDF resume parsing: partial
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
- Frontend should present a full AI 求职训练 / 求职辅导 product loop, not a single mock-interview demo
- User explicitly rejected a loose "inspired by the zip" redesign; future frontend edits should preserve zip-like module order, card density, button treatment, spacing, and navigation unless a backend/API mismatch forces a minimal change
- User explicitly requested a rollback away from Vectr-style homepage structure, not just a reduction of "Vectr flavor." Future frontend edits should preserve the zip-like product workbench homepage and immersive interview cockpit unless explicitly directed otherwise.
- Current frontend direction is not another full-site redesign. Preserve the existing route/API/business flow and business-page surfaces while keeping the restored zip-style homepage/workbench and dark interview cockpit stable.
- Frontend visual direction should reduce full-screen card noise: use background contrast, whitespace, dividers, and large translucent section numbers before adding nested card borders.
- Bright blue should be reserved for the dominant page-level CTA or active dynamic signal; secondary actions such as global `开始训练` should stay outline/low-emphasis when another primary CTA is present.
- Resume and analysis rewrite content should favor top-to-bottom reading flow over narrow side-by-side columns, especially for technical text and STAR rewrites.
- Live interview should feel like an IM-style conversation on the dark cockpit surface: AI questions left-aligned with subtle feature bars, candidate answers right-aligned as bubbles, and the sidebar prioritizing `当前追问依据` over dense static metrics.

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
- Do not add recruiter-side screening language, offer prediction, hiring verdicts, 内推/投递 promises, or ATS-pass claims to the frontend
- Do not reintroduce membership/credits/energy monetization concepts from the zip references; if the reference has those widgets, translate them into neutral training status/训练点 language or remove them
- Do not reintroduce prefilled fake JD/resume values into the 求职启动 page as default user data. If examples are needed later, make them an explicit user action and label them clearly as examples.
- Do not let local frontend development call `http://127.0.0.1:8000/api/v1` directly by default; use same-origin `/api/v1` plus dev proxy unless deployment explicitly overrides `window.INTERVIEWPILOT_API_BASE`
- Do not let the homepage expand into a long marketing page. The active homepage is the zip-style workbench entry, not a GSAP narrative landing page.

## Abandoned Or Rejected Approaches

- Treating the product as a recruiter-side screening tool: rejected because current product direction is candidate-facing and lower-risk
- Treating resume optimization as full automatic rewrite in MVP: rejected because it increases hallucination and trust risk
- Adding external dependencies for the first MVP scaffold: rejected because the current goal is a small, reviewable, dependency-free loop
- Keeping the old MVP vanilla frontend as the primary UI: rejected because the product now needs a portfolio/competition-grade full frontend and explicit resume optimization/interview/report modules
- Vectr-style long-scroll homepage with FAQ/footer/Three.js spectacle remains rejected.
- The later InterviewArk / GSAP / Lenis four-scene homepage is also no longer the active direction after the user's rollback request to the zip-reference recreation.
