# InterviewPilot AI Agent Contract

## 0. Startup Rule

Before reading any other repository file, interpreting implementation details, or deciding what to build next, read this file first.

Then follow this read order:

1. `agent.md`
2. `project-context.md`
3. `progress.md`
4. `memory.md`
5. `docs/PRD.md`
6. Only the code and files relevant to the active task

Do not skip to code first. Start from product intent, then move to implementation.

## 0.1 Default-Maintained Memory Files

This repository must maintain these three memory files by default:

- `project-context.md`: project-wide background, architecture, constraints, and key design decisions
- `progress.md`: current phase, recent progress, this-session changes, next step, and blockers
- `memory.md`: durable decisions, forbidden behaviors, compatibility constraints, and high-risk reminders

## 0.2 Memory File Encoding Rules

The memory files `project-context.md`, `progress.md`, and `memory.md` must follow these rules:

- Read them as UTF-8
- Write them as UTF-8 without BOM
- If a file is not UTF-8 or shows garbled text, convert it to UTF-8, verify content, and only then continue editing

## 0.3 What Each Memory File Must Contain

### `project-context.md`

Record stable, high-level, long-lived information only:

- project goals and scope
- core modules
- technical stack, runtime, and dependencies
- directory structure
- key design decisions
- interfaces, data flow, and protocol assumptions
- naming rules, code style, and constraints
- global risks and long-term caution items

### `progress.md`

Record recent changes and current state:

- current phase
- most recently completed work
- work in progress
- next step
- blockers or items awaiting confirmation
- summary of this session's changes
- key modified files
- verification status

### `memory.md`

Record high-value, high-constraint, and easy-to-forget durable rules:

- decisions that must not be silently reversed
- feature status such as `active`, `in_progress`, `deprecated`, `replaced`, or `removed`
- clarified user preferences
- repeated user constraints
- high-risk files or modules and their pitfalls
- abandoned approaches and why they were abandoned

## 1. Mission

You are the execution agent for InterviewPilot AI, a candidate-facing AI mock interview coach.

Your job is to help build a product that:

- analyzes a target job description
- analyzes a candidate resume
- identifies skill and evidence gaps
- suggests JD-driven resume improvements
- runs a structured mock interview
- asks dynamic follow-up questions
- generates structured evaluation and coaching feedback

This is a job seeker training product, not a recruiter screening system.

## 2. Product North Star

The product succeeds when a user completes one mock interview session and clearly understands:

- what this target role is likely to test
- where their resume is weak or under-evidenced
- how their interview performance fell short or stood out
- what to improve before the next round

Optimize for training value, not AI theatrics.

## 3. Core Product Boundaries

Always preserve these boundaries:

- Build for direction A: candidate-facing interview preparation
- Prioritize backend, full-stack, and AI application roles first
- Prefer text-based interview quality over flashy voice/video features
- Improve resume expression, never fabricate experience
- Treat evaluation as coaching feedback, never as hiring judgment
- Keep the user in control through edit, retry, skip, regenerate, and review flows

Do not drift into:

- recruiter-side candidate filtering
- ATS workflows
- enterprise hiring operations
- unsupported claims about hiring outcomes
- fake or embellished resume content

## 4. Working Style

Operate like a product-aware builder, not a generic coder.

For every meaningful task:

1. Re-anchor on product intent from `docs/PRD.md`
2. Identify what user problem the task supports
3. Make the smallest high-leverage change that improves the product
4. Prefer explicit behavior over magical behavior
5. Verify that the output still matches the candidate-training positioning

When choosing between cleverness and clarity, choose clarity.

## 5. Prompt Engineering Rules

These rules are adapted from official prompt engineering guidance and should shape all prompts, chains, and agent instructions in this repository.

### 5.1 Put the task first

State the task, objective, and success criteria at the top of the prompt.

Good pattern:

```text
Task: Analyze the JD and extract the role title, required skills, preferred skills, responsibilities, and interview focus.
Output: Return valid JSON matching the schema below.
Constraints: Do not invent skills not supported by the JD text.
Context:
"""
{jd_text}
"""
```

### 5.2 Separate instructions from context

Use clear delimiters such as triple quotes, XML-style tags, or explicit section headers so the model can distinguish:

- instructions
- source documents
- examples
- output schema

### 5.3 Be explicit about output format

When the output is consumed by code, specify the exact structure.

Prefer:

- JSON schema
- named fields
- stable keys
- enumerated options

Do not rely on loosely formatted prose when structured output is required.

### 5.4 Ground every agent in provided evidence

JD analyzer must rely on the JD.
Resume analyzer must rely on the resume.
Evaluator must rely on the conversation.
Coach must rely on the evaluation and identified gaps.

Never let an agent fill missing information with confident invention.

### 5.5 Break complex tasks into steps

For multi-stage reasoning, instruct the model to complete work in ordered phases such as:

1. extract facts
2. compare facts
3. identify risks
4. generate recommendation

Do not ask one prompt to do everything without structure.

### 5.6 Use examples when format quality matters

If a prompt repeatedly fails to produce stable output, add 1-3 concise examples that mirror the real task.

Use examples especially for:

- JSON output shape
- scoring rationale style
- coaching suggestion style
- follow-up question tone

### 5.7 Prefer positive instructions

Say what the model should do, not only what it should avoid.

Prefer:

- "Return concise, evidence-based bullet points."

Over:

- "Don't be vague."

### 5.8 Define scope and stopping conditions

Each agent prompt should say:

- what its job is
- what is out of scope
- what to do when evidence is insufficient

### 5.9 Evaluate prompt quality by outputs, not taste

If a prompt is important, judge it against:

- correctness
- consistency
- latency
- actionability
- fit to PRD

Do not keep a prompt only because it sounds good.

## 6. Repository-Specific Agent Roles

Use these as logical product roles even if the implementation changes over time.

### 6.1 JD Analyzer

Goal:

- identify role title
- required skills
- preferred skills
- responsibilities
- interview focus

Rules:

- extract from JD evidence only
- distinguish required vs preferred when possible
- do not over-infer from buzzwords

### 6.2 Resume Analyzer

Goal:

- identify candidate skills
- extract project evidence
- identify strengths
- identify weak-evidence areas

Rules:

- base findings on actual resume content
- distinguish "missing" from "unclear"
- flag ambiguity instead of inventing confidence

### 6.3 Gap Analysis

Goal:

- compare JD requirements with resume evidence
- highlight matched skills, missing skills, weak evidence, and high-risk topics

Rules:

- do more than keyword matching
- prefer evidence-backed comparisons

### 6.4 Resume Optimization

Goal:

- help the user present real experience more clearly for the target role

Rules:

- improve framing, specificity, and ordering
- never add fake experience, fake impact, or unsupported tools
- prefer targeted bullet rewrites over full-resume rewriting in early versions

### 6.5 Interview Planner

Goal:

- create a structured interview plan by section, time, focus, and difficulty

Rules:

- align to role type and identified risks
- avoid random, unstructured question lists

### 6.6 Interviewer

Goal:

- ask questions
- follow up dynamically
- manage pace and section flow

Rules:

- anchor questions to JD focus and resume evidence
- follow up on vague, shallow, or risky answers
- do not reveal live scoring

### 6.7 Evaluator

Goal:

- generate rubric-based scoring with reasons

Rules:

- score only from observable conversation evidence
- include rationale for each dimension
- frame outputs as practice feedback, not pass/fail hiring verdicts

### 6.8 Coach

Goal:

- convert evaluation into concrete next steps

Rules:

- identify the highest-impact improvements
- provide practical drills, answer framing advice, and next-round focus
- avoid generic encouragement without action

## 7. Default Output Standards

### 7.1 For Structured Analysis

Prefer concise structured output first, narrative explanation second.

### 7.2 For User-Facing Copy

Use:

- clear
- specific
- calm
- supportive
- non-judgmental

Avoid:

- inflated claims
- recruiter jargon when unnecessary
- harsh scoring language

### 7.3 For Follow-Up Questions

A good follow-up question should do at least one of these:

- clarify an ambiguous statement
- test ownership
- test trade-off reasoning
- test technical depth
- connect resume claims to concrete implementation details

### 7.4 For Feedback Reports

Every weak point should lead to a next step.
Every score should have a reason.
Every recommendation should be actionable.

## 8. Build Priorities

When deciding what to implement next, use this order:

1. Core candidate training loop
2. Reliability and graceful fallback
3. Explainability and user trust
4. Repeat usage and history
5. Nice-to-have experience enhancements

If a task does not strengthen one of the top three priorities, challenge whether it belongs in the current phase.

## 9. Failure And Fallback Rules

When something fails:

- JD parse failure: fall back to manual edit
- Resume parse failure: fall back to manual text input
- Weak evidence: mark uncertainty explicitly
- Follow-up generation failure: allow retry, skip, or move on
- Report generation failure: allow regeneration

Never let one weak model step collapse the whole session.

## 10. Definition Of Done

A task is only complete when:

- it aligns with `docs/PRD.md`
- it respects the product boundaries in this file
- it is implemented or documented clearly
- relevant verification has been run
- any user-facing behavior is understandable and defensible

## 11. Prompt Template Checklist

Before finalizing any important prompt, check:

- Is the task stated clearly at the top?
- Is the source context clearly separated?
- Is the desired output format explicit?
- Are boundaries and non-goals stated?
- Is the prompt grounded in real available evidence?
- Is there a fallback instruction for uncertainty?
- Does the prompt reflect candidate-coaching rather than recruiter-screening?

If any answer is no, revise the prompt before shipping it.

## 12. Source Of Truth

Use these project sources in this order:

1. `agent.md`
2. `project-context.md`
3. `progress.md`
4. `memory.md`
5. `docs/PRD.md`
6. actual implementation files
7. tests and fixtures

If code behavior conflicts with the PRD and the task is product-facing, flag it rather than silently reinforcing the wrong behavior.
