# InterviewPilot AI MVP Demo Runbook

This runbook demonstrates the candidate-facing MVP loop:

`JD + resume -> analysis preview -> mock interview -> structured report -> dashboard history`

The demo should emphasize four portfolio points:

- multi-agent orchestration across analysis, planning, interviewing, evaluation, and coaching
- dynamic follow-up questions grounded in the latest candidate answer
- structured rubric scoring with reasons
- explainable, candidate-safe feedback that never becomes a hiring verdict

## 1. Start Backend

From the repository root:

```powershell
python -m pip install -e .
python -m backend.app.main
```

Expected health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

The local MVP store defaults to `data/interviewpilot_store.json`.
For an isolated demo run:

```powershell
$env:INTERVIEWPILOT_STORE_PATH="$PWD\data\demo-store.json"
python -m backend.app.main
```

Optional LLM-backed run through Alibaba Cloud Model Studio / DashScope compatible mode:

```powershell
Copy-Item .env.example .env
notepad .env
python -m backend.app.main
```

Or set variables directly in the current shell:

```powershell
$env:INTERVIEWPILOT_LLM_API_KEY="your-api-key"
$env:INTERVIEWPILOT_LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:INTERVIEWPILOT_LLM_MODEL="glm-5"
$env:INTERVIEWPILOT_LLM_ENABLED="true"
python -m backend.app.main
```

Keep the key in your shell environment only. Do not write it into source files, README examples, screenshots, or committed config. If the external model returns invalid JSON or is unavailable, the backend falls back to the local deterministic MVP engine.

## 2. Start Frontend

In a second terminal:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## 3. Happy Path Demo

1. Open Dashboard.
2. Point out the four value chips: `Multi-Agent Flow`, `Dynamic Follow-Up`, `Structured Score`, and `Explainable Coaching`.
3. Click `Start New Interview`.
4. Keep the sample Backend API Engineer JD and resume, or click `Reload demo data`.
5. Explain the demo storyline:
   - the candidate has real FastAPI/PostgreSQL project evidence
   - Redis and observability are weakly evidenced
   - ownership and impact are under-specified
   - the interview should probe concrete trade-offs instead of asking generic questions
6. Click `Analyze JD and Resume`.
7. On Analysis Preview, show the Agent chain:
   - JD Analyzer
   - Resume Analyzer
   - Gap Analysis
   - Resume Optimizer
   - Interview Planner
8. Confirm these sections are populated:
   - JD Understanding
   - Resume Evidence
   - Gap and Risk
   - Resume optimization preview
   - Interview plan
9. Click `Start Mock Interview`.
10. Answer the first question with a deliberately short answer such as:

```text
I used FastAPI with PostgreSQL and added a few endpoints. I mostly focused on making the API work.
```

11. Submit the answer and point out whether the next question is a follow-up that asks for evidence, trade-offs, ownership, or implementation depth.
12. Optionally test `Regenerate`, `Skip`, or `Next`.
13. Click `End Interview`.
14. Click `Generate Report`.
15. Confirm the Report page shows:
    - overall score
    - six rubric dimensions with reasons
    - strengths, weaknesses, and risk flags
    - coaching actions
    - practice plan
16. Return to Dashboard and confirm the recent session appears.

## 4. Screenshot / Recording Checklist

Recommended capture sequence:

1. Dashboard hero: shows candidate-facing positioning and the four demo value chips.
2. New Interview: shows the default JD/resume demo data and storyline.
3. Analysis Preview: shows the multi-agent chain plus JD/resume/gap panels.
4. Interview Session: shows section, focus topics, progress, and no live scoring.
5. Report: shows rubric dimensions, score reasons, coaching actions, and next practice plan.
6. Dashboard history: shows the completed session is persisted for review.

Suggested voiceover:

```text
InterviewPilot AI is a candidate-facing mock interview coach. It does not screen candidates for employers. It helps a job seeker practice for a specific role by coordinating specialized agents: first understanding the JD and resume, then finding gaps, planning a focused interview, asking contextual follow-ups, and finally producing an explainable coaching report.
```

## 5. Portfolio Talking Points

- **Product judgment:** The MVP validates a complete preparation loop before adding voice/video or enterprise features.
- **Agent architecture:** Each agent has a narrow responsibility and a structured schema, making outputs inspectable and composable.
- **Trust and safety:** Resume optimization cannot fabricate experience, and scores are practice feedback only.
- **UX clarity:** The user sees analysis before the interview, controls the live session, and receives concrete next steps after the report.
- **Engineering restraint:** The project uses a deterministic local engine and lightweight JSON persistence so the flow is testable before production LLM integration.

## 6. Degraded Input Check

The current UI supports pasted text as the reliable MVP path. Backend degradation can be verified with:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/jd/analyze `
  -ContentType "application/json" `
  -Body '{"input_type":"image","filename":"unreadable-jd.png"}'
```

Expected behavior:

- response status is `200`
- `extraction.status` is `manual_required`
- `needs_manual_correction` is `true`
- `analysis.uncertainty_notes` is populated

This confirms parsing failure does not collapse the session flow.

## 7. Product Boundary Check

During demo review, confirm:

- Live Interview Session does not show scores.
- Report disclaimer says scores are practice feedback, not hiring decisions.
- Report and coaching do not produce pass/fail, hire/no-hire, offer, rejection, or recruiter-screening language.
- Resume optimization advice remains conditional and truthful; it should not invent tools, metrics, ownership, or impact.

## 8. Reset Demo Data

If using the default store:

```powershell
Remove-Item .\data\interviewpilot_store.json -Force
```

If using a custom `INTERVIEWPILOT_STORE_PATH`, delete that file instead.

<!-- Legacy checklist retained below for quick skim compatibility. -->

## Quick Checklist

1. Open Dashboard.
2. Click `Start New Interview`.
3. Keep the sample Backend Engineer JD and resume, or paste your own.
4. Click `Analyze JD and Resume`.
5. On Analysis Preview, confirm these sections are populated:
   - JD Understanding
   - Resume Evidence
   - Gap and Risk
   - Resume optimization preview
   - Interview plan
6. Click `Start Mock Interview`.
7. Answer the first question with a concrete project answer.
8. Optionally test `Regenerate`, `Skip`, or `Next`.
9. Click `End Interview`.
10. Click `Generate Report`.
11. Confirm the Report page shows:
    - overall score
    - six rubric dimensions with reasons
    - strengths, weaknesses, and risk flags
    - coaching actions
    - practice plan
12. Return to Dashboard and confirm the recent session appears.
