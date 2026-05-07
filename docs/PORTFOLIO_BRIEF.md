# InterviewPilot AI Portfolio Brief

## One-Line Description

InterviewPilot AI is a candidate-facing AI mock interview coach that turns a target JD and resume into a role-aware practice interview, dynamic follow-up questions, structured scoring, and actionable coaching feedback.

## Short Project Description

InterviewPilot AI helps technical job seekers practice for a specific role instead of preparing from generic question banks. The MVP analyzes a target job description and resume, identifies matched skills, missing skills, weak evidence, and high-risk topics, then generates a section-based mock interview. During the live text session, the interviewer can ask contextual follow-up questions based on the candidate's latest answer. After the interview, the system produces a rubric-based practice report with score reasons, risk flags, coaching actions, and a next practice plan.

The product is intentionally candidate-facing: it is not a recruiter screening tool, does not make hiring decisions, and does not fabricate resume content. Resume suggestions focus on truthful phrasing and interview readiness.

## Demo Narrative

Use the built-in Backend API Engineer sample. The candidate has credible FastAPI and PostgreSQL project experience, but Redis, observability, and ownership metrics are weakly evidenced. This setup creates a clean demonstration of the product loop: the analysis identifies risk, the planner turns that risk into interview sections, the interviewer follows up on vague answers, and the report converts performance gaps into concrete practice actions.

## What To Show

1. Dashboard: candidate-facing positioning and the four value chips.
2. New Interview: JD/resume inputs and demo storyline.
3. Analysis Preview: multi-agent chain, JD understanding, resume evidence, gap/risk cards, and interview plan.
4. Interview Session: section focus, progress, dynamic follow-up, and no live scoring.
5. Report: six rubric dimensions with reasons, strengths/weaknesses, coaching actions, and next practice plan.
6. Dashboard History: persisted session/report review.

## Product Highlights

- Targeted preparation from the user's actual JD and resume.
- Multi-agent workflow with clear responsibilities and structured handoffs.
- Dynamic follow-up instead of static question lists.
- Explainable report with rubric scores and reasons.
- Candidate-safe boundaries: no recruiter verdicts and no fabricated resume claims.

## Technical Highlights

- FastAPI backend with modular workflow routes for intake, analysis, interview sessions, reports, and history.
- Strict Pydantic schemas aligned to agent prompts for predictable structured outputs.
- Versioned JSON-only prompt contract prepared for production LLM integration.
- Local deterministic MVP engine to make the full loop testable before external model calls.
- Lightweight JSON persistence for demo-friendly session and report review.
- No-build frontend SPA for fast local demos and simple screenshot/recording flows.

## Suggested Interview Pitch

```text
InterviewPilot AI is an AI mock interview coach for candidates. I built it around a full preparation loop rather than a single chatbot: it analyzes the JD, extracts resume evidence, identifies gaps, plans a focused interview, asks dynamic follow-ups, and generates structured coaching feedback. The key product boundary is that it helps job seekers practice; it never acts as a recruiter screening system or invents resume claims.
```
