# InterviewPilot AI PRD

- Product: InterviewPilot AI
- Version: v0.1
- Status: Draft
- Last Updated: 2026-04-25
- Owner: Product / Founding Team

## 1. Product Overview

InterviewPilot AI is an AI mock interview coach for job seekers. It helps candidates prepare for a target role by combining the target job description (JD), the candidate's resume, and the candidate's real-time responses to generate a highly targeted mock interview, dynamic follow-up questions, structured scoring, and actionable coaching feedback.

The first version focuses on direction A: a candidate-facing interview preparation product, not a recruiter-side screening product.

### 1.1 Product Positioning

InterviewPilot AI is positioned as:

`An AI interview preparation coach that helps candidates practice for a target role through JD analysis, resume analysis, adaptive questioning, and structured post-interview feedback.`

### 1.2 Product Principles

- Prioritize targeted preparation over generic question generation
- Prioritize training value over AI novelty
- Prioritize a complete practice loop over broad feature coverage
- Prioritize explainability and user trust over opaque automation

### 1.3 Non-Goals

The first version does not aim to provide:

- recruiter-side candidate screening
- ATS or enterprise recruitment workflow support
- voice or video interviews
- broad support for all job categories
- a fully automated resume rewriting product

## 2. Target Users And Core Scenarios

### 2.1 Target User Segments

#### Core Users

- students preparing for internships or campus recruiting
- early-career technical candidates preparing for backend, full-stack, or AI application engineering interviews

#### Secondary Users

- engineers with 1-3 years of experience preparing for job changes

#### Out Of Scope For V1

- non-technical candidates
- senior/staff-level candidates with heavy system design focus
- recruiting teams and hiring organizations

### 2.2 Core User Profile

The core user typically:

- has a resume and at least one or two projects
- can answer some common technical questions, but struggles to align answers with a specific JD
- does not know which parts of their resume are weak or likely to be challenged
- lacks access to repeated, high-quality mock interview practice
- wants fast, concrete feedback before applying or interviewing

### 2.3 Core User Pain Points

- Users do not know what to practice for a specific role
- Users struggle to explain projects with enough depth and specificity
- Users cannot simulate realistic follow-up questioning through static question banks
- Users receive vague feedback and do not know how to improve

### 2.4 Core Scenarios

#### Scenario 1: Pre-Application Preparation

The user finds a role they want to apply for and wants a targeted mock interview before submitting.

#### Scenario 2: Interview Sprint

The user has an interview soon and wants a focused practice session to identify likely weak points.

#### Scenario 3: Post-Interview Reflection

The user completed a real interview and wants to reproduce likely weak areas for additional practice.

### 2.5 JTBD

When I am preparing for a specific technical role, I want to complete a highly targeted mock interview based on the role's JD and my resume, so I can identify my weak points, likely interview risks, and the most important areas to improve before the real interview.

## 3. Product Goals And Value Proposition

### 3.1 User Goals

- prepare more effectively for a specific target role
- identify gaps in role fit, technical depth, and project explanation
- turn one practice session into a clear next-step improvement plan

### 3.2 Product Goals

- deliver a mock interview experience that feels structured and role-aware
- generate feedback that is explainable, actionable, and useful for repeated practice
- create a practice flow that is more valuable than generic LLM chat

### 3.3 MVP Validation Goals

The MVP should validate whether:

- users perceive the generated questions as strongly targeted to the JD and resume
- dynamic follow-up questions improve realism and practice value
- the final report is specific enough to drive another round of practice

### 3.4 Core Value Proposition

InterviewPilot AI helps job seekers prepare for real interviews by combining the target JD, the user's resume, and the user's interview responses to generate targeted interview flows, adaptive follow-up questions, structured evaluation, and actionable coaching suggestions.

### 3.5 Differentiation

Compared to generic LLM chat:

- more structured
- more role-specific
- more explainable
- better aligned to repeated practice

Compared to static question banks:

- personalized to the user and the role
- capable of dynamic follow-up
- able to produce rubric-based evaluation

Compared to human mock interviews:

- cheaper
- easier to repeat
- faster to start

## 4. MVP Scope And Prioritization

### 4.1 MVP Objective

Enable a user to complete a 15-30 minute text-based mock interview and clearly feel the value of role targeting, dynamic follow-up, and structured feedback.

### 4.2 End-To-End MVP Loop

1. User creates a new interview session
2. User provides the target JD through pasted text, image upload, or PDF upload
3. User provides resume content
4. System parses the JD and resume into structured information
5. User reviews and corrects parsed results if needed
6. System generates gap analysis and resume optimization suggestions
7. System generates an interview plan
8. User begins a text-based mock interview
9. System asks questions and generates dynamic follow-up questions
10. System produces a final evaluation and coaching report

### 4.3 P0 Features

- new interview session creation
- multi-modal JD input: text, image, PDF
- JD parsing preview and manual correction
- resume text input
- JD analyzer
- resume analyzer
- gap analysis
- resume optimization suggestions
- interview planner
- text-based interview session
- dynamic follow-up logic
- structured evaluation report
- coaching suggestions
- lightweight dashboard with recent sessions

### 4.4 P1 Features

- resume PDF upload and parsing
- interview focus summary card before the session starts
- session progress sidebar
- regenerate question action
- focus modes such as project deep dive or fundamentals
- dedicated history page
- one-click retraining based on weak areas
- report export

### 4.5 P2 / Later Features

- voice interviews
- video interviews
- enterprise recruiting workflows
- ATS integrations
- broad non-technical role support
- advanced trend dashboards
- complete automated resume rewriting

## 5. Core User Flow And Page Requirements

### 5.1 Core User Flow

1. User opens New Interview
2. User uploads or pastes JD
3. User uploads or pastes resume
4. System parses JD and extracts role title, skill requirements, responsibilities, and interview focus
5. System parses the resume and extracts projects, skills, strengths, and weak evidence areas
6. System generates gap analysis
7. System generates resume optimization suggestions
8. User chooses whether to review suggestions first or go straight into mock interview
9. System generates an interview plan
10. User enters Interview Session
11. System conducts the interview with dynamic follow-up questions
12. User reaches Report page after the interview
13. User reviews scores, weak points, risks, and next practice recommendations

### 5.2 Page: New Interview

#### Goal

Allow the user to create a targeted interview session with minimal friction.

#### Inputs

- target role
- JD input method: paste text / upload image / upload PDF
- resume input method: paste text / upload PDF in later phase
- interview type
- difficulty
- duration

#### Key Requirements

- support file upload and text input
- automatically extract text from JD materials
- allow manual fallback if extraction fails
- keep setup time under 1-2 minutes for a normal user

### 5.3 Page: Parsed JD And Analysis Preview

#### Goal

Build trust before the interview starts by showing that the system understands the role and the candidate.

#### Display Content

- role title
- required skills
- preferred skills
- responsibilities
- interview focus
- resume summary
- matched skills
- missing skills
- weak evidence skills
- high risk topics
- resume optimization suggestions

#### Key Actions

- confirm and start interview
- manually edit parsed JD
- manually edit resume text
- review optimization suggestions

### 5.4 Page: Interview Session

#### Goal

Provide a structured, realistic, text-based mock interview.

#### Layout

- left: conversation history and current question
- right: current section, focus, remaining questions, difficulty

#### Key Requirements

- follow the generated interview plan
- prioritize JD focus and resume projects
- generate contextual follow-up questions
- allow skip, next, regenerate, and end session actions
- do not display scoring during the live interview

### 5.5 Page: Report

#### Goal

Turn one interview session into a concrete learning artifact.

#### Display Content

- overall score
- rubric-based dimension scores
- scoring reasons
- strengths
- weaknesses
- high risk topics
- evidence gaps
- resume optimization follow-up suggestions
- coaching suggestions
- next practice plan

#### Key Actions

- retry interview
- focus weak areas and train again
- export report
- return to dashboard

### 5.6 Page: Dashboard / History

#### Goal

Support repeat usage and make progress visible.

#### Display Content

- recent sessions
- target role
- total score
- timestamp
- weak area summary
- retrain entry point

## 6. Functional Modules

### 6.1 JD Parsing And JD Analyzer

#### Goal

Convert raw JD material into structured role information that can guide the rest of the workflow.

#### Inputs

- JD text
- JD image
- JD PDF

#### Outputs

- role_title
- required_skills
- preferred_skills
- responsibilities
- interview_focus
- raw_jd_text

#### Requirements

- parse text from multiple input formats
- extract structured role information
- show preview results
- allow manual correction
- degrade to manual text edit if parsing fails

### 6.2 Resume Parsing And Resume Analyzer

#### Goal

Extract candidate signals from the resume for role matching and interview generation.

#### Inputs

- resume text
- resume PDF in later phase

#### Outputs

- candidate_skills
- projects
- strengths
- weaknesses
- weak_evidence_skills
- resume_summary

#### Requirements

- identify projects, skills, and evidence signals
- identify strengths and weak evidence areas
- avoid high-confidence conclusions when resume data is sparse

### 6.3 Gap Analysis

#### Goal

Compare the role requirements and the candidate resume to identify likely interview focus and risk areas.

#### Outputs

- matched_skills
- missing_skills
- weak_evidence_skills
- high_risk_topics
- recommended_focus

#### Requirements

- distinguish missing skills from weak evidence
- go beyond pure keyword matching
- provide guidance for planning and evaluation

### 6.4 Resume Optimization Suggestions

#### Goal

Provide role-specific resume optimization suggestions before the interview begins.

#### Outputs

- optimization_summary
- rewrite_targets
- bullet_improvement_suggestions
- skill_positioning_suggestions
- risk_warnings

#### Requirements

- identify which projects or skills should be emphasized
- suggest where wording is vague or weak
- provide limited rewrite examples
- identify likely interview follow-up risks caused by resume wording

#### Boundaries

- improve expression, not fabricate experience
- do not generate false skills or achievements
- do not attempt full resume rewriting in MVP

### 6.5 Interview Planner

#### Goal

Create a structured mock interview plan based on the role, the resume, and the desired practice mode.

#### Outputs

- interview_type
- duration
- sections
- section_goals
- focus_topics
- max_questions

#### Requirements

- map duration and interview type to a clear section plan
- prioritize high-risk and high-value topics
- keep section count manageable

### 6.6 Interview Orchestration / Interviewer Agent

#### Goal

Run the interview, ask questions, generate follow-up questions, and manage section flow.

#### Inputs

- interview_plan
- messages
- current user answer
- gap_analysis
- resume_analysis

#### Outputs

- current_question
- follow_up_question
- current_section
- question_count
- updated message history

#### Requirements

- follow the interview plan
- keep questions anchored to the JD and resume
- follow up on vague or weak answers
- ask about responsibilities, trade-offs, technical choices, and outcomes
- allow skip, regenerate, next, and end

### 6.7 Evaluator

#### Goal

Generate structured and explainable scoring after the interview.

#### Suggested Rubric Dimensions

- technical_accuracy
- depth
- structure
- communication
- role_fit
- evidence_quality

#### Outputs

- overall_score
- dimension_scores
- score_reasons
- strengths
- weaknesses
- risk_flags

#### Requirements

- score each dimension with reasons
- ground conclusions in the actual conversation
- frame results as training feedback, not hiring decisions

### 6.8 Coach

#### Goal

Translate evaluation outputs into practical next-step improvement guidance.

#### Outputs

- summary
- top_improvements
- example_answer_guidance
- practice_plan
- next_round_focus

#### Requirements

- identify 2-4 key improvements
- give concrete, actionable suggestions
- recommend answer structures where useful
- guide the next round of practice

### 6.9 Dashboard / History

#### Goal

Support repeat usage and progress visibility.

#### Outputs

- recent sessions
- score history
- weak area tags
- retrain suggestions

#### Requirements

- display recent sessions clearly
- allow report revisit
- provide a path to retrain based on weaknesses

## 7. Non-Functional Requirements And Product Rules

### 7.1 Performance Targets

- JD or resume parsing: 5-15 seconds in normal cases
- analysis generation: 15-30 seconds
- next interview question or follow-up: 3-8 seconds
- final report generation: 10-20 seconds

The UI must clearly communicate loading states and progress.

### 7.2 Reliability And Degradation

- JD parsing failures must fall back to manual editing
- resume parsing failures must fall back to manual text input
- follow-up generation failures must support retry, skip, next, or end
- report generation failures must support regeneration
- single-step failure must not destroy the full session

### 7.3 AI Output Rules

#### Analysis Rules

- prefer structured outputs
- use conservative phrasing when confidence is low
- do not invent missing facts

#### Follow-Up Rules

- follow-up questions must connect to the JD, the resume, or the user's answer
- avoid random topic switching
- use follow-ups to clarify, verify, and deepen

#### Evaluation Rules

- every score must include a reason
- scores must be grounded in interview content
- scores represent training feedback only

#### Coaching Rules

- suggestions must be actionable
- avoid vague motivational filler
- do not encourage fabrication or exaggeration

### 7.4 Explainability And Trust

- users must be able to inspect parsed JD information
- gap analysis must distinguish missing skills, weak evidence, and risk topics
- report low scores must explain why
- resume suggestions should point to specific content where possible

### 7.5 User Control

Users must be able to:

- edit parsed JD content
- edit resume content
- skip questions
- regenerate questions
- end the interview early
- regenerate reports
- retrain based on weak points

### 7.6 Privacy And Data Principles

- JD and resume data should only be used for the interview workflow and history features
- users should understand if session data is stored
- resumes and interview records should not be publicly exposed
- users should be able to delete historical sessions in later versions

### 7.7 Product Ethics And Boundaries

- the product is a training assistant, not a hiring decision engine
- resume optimization improves framing, not truthfulness
- the product must not encourage fabricated experience
- the product must not claim to predict hiring outcomes
- the product must not produce discriminatory or irrelevant judgments

## 8. Success Metrics And Acceptance Criteria

### 8.1 MVP Validation Questions

- Do users perceive the interview as targeted to the role and the resume?
- Do users perceive the follow-up questions as realistic and useful?
- Do users perceive the final report as specific and actionable?

### 8.2 Core Metrics

#### Funnel Metrics

- session creation completion rate
- mock interview completion rate
- report view completion rate
- second-session rate

#### Experience Metrics

- perceived question relevance score
- perceived follow-up realism score
- perceived report usefulness score
- perceived actionability score

#### Quality Metrics

- JD parsing success rate
- resume parsing success rate
- follow-up generation success rate
- report generation success rate
- average response latency
- parsed result correction rate

### 8.3 MVP Acceptance Criteria

#### Flow Acceptance

- users can complete the full flow from input to final report
- parsing failure does not block session completion
- the interview supports multiple rounds of Q&A
- final reports can be generated consistently

#### Experience Acceptance

- users can see that the interview is based on the JD and resume
- the session contains at least some contextual follow-up questions
- low scores include explicit reasons
- resume optimization suggestions are concrete

#### Quality Acceptance

- no major session state corruption
- waiting times remain within acceptable bounds
- known failure states have graceful fallback behavior
- outputs do not violate truthfulness and safety boundaries

## 9. Roadmap

### 9.1 MVP

Focus: validate the candidate training loop.

Includes:

- JD multi-modal input
- JD parsing and correction
- resume text input
- JD analysis
- resume analysis
- gap analysis
- resume optimization suggestions
- interview planning
- text-based mock interview
- dynamic follow-up
- structured report
- coaching guidance
- lightweight dashboard

### 9.2 V1.1

Focus: improve repeat usage and product completeness.

Includes:

- resume PDF parsing
- standalone history page
- one-click retraining on weak areas
- focus modes
- report export
- richer progress comparison
- better follow-up strategies

### 9.3 V2

Focus: expand beyond the initial interview loop.

Possible additions:

- voice interview mode
- broader role coverage
- stronger resume optimization
- personalized growth profile
- real interview reflection mode

### 9.4 Roadmap Principle

The roadmap should prioritize training effectiveness and repeat usage before adding enterprise recruitment workflows, advanced media modes, or broad horizontal expansion.

## 10. Open Questions

- Should resume PDF parsing be included in MVP or delayed to v1.1?
- Should the first version support only backend, full-stack, and AI application roles, or include frontend from day one?
- Should users be able to edit the full parsed JD schema directly, or only selected fields?
- Should reports be exportable in MVP or only after retention features are added?
