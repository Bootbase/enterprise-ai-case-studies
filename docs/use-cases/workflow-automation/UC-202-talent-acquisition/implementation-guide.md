---
layout: use-case-detail
title: "Implementation Guide — Autonomous Talent Acquisition and Candidate Screening with Agentic AI"
uc_id: "UC-202"
uc_title: "Autonomous Talent Acquisition and Candidate Screening with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Workflow Automation"
category_icon: "settings"
industry: "Cross-Industry (Retail, Food Service, Technology, Financial Services, Manufacturing)"
complexity: "High"
status: "detailed"
slug: "UC-202-talent-acquisition"
permalink: /use-cases/UC-202-talent-acquisition/implementation-guide/
---

## Build Goal

Deliver an AI-powered talent acquisition pipeline that screens resumes, engages candidates conversationally, schedules interviews, and synthesizes evaluations — integrated with the organization's ATS. The first production release covers a single high-volume job family (e.g., hourly/frontline or campus hiring) in one jurisdiction. Out of scope for the first release: executive search, internal mobility, workforce planning, and multi-language support beyond English and one additional language.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ on containerized deployment (Docker/Kubernetes) | Python dominates ML/NLP tooling. Containerization supports horizontal scaling during application surges. |
| **Model access** | OpenAI API (GPT-4o) for parsing, matching, and conversation; text-embedding-3-large for semantic search | GPT-4o achieves 0.84 Pearson correlation with human evaluators in resume assessment tasks. Embedding model enables vector-based candidate-job matching. [S12] |
| **Orchestration runtime** | Event-driven pipeline using ATS webhooks (Greenhouse) or polling (Workday) with a task queue (Celery + Redis) | Recruiting is event-driven: each application, stage change, or feedback submission triggers the next step. Task queue handles volume spikes during job posting launches. [S8] |
| **Core connectors** | Greenhouse Harvest API (REST, HTTP Basic Auth, HMAC webhooks) or Workday REST API (OAuth 2.0); Twilio for SMS; Google/Microsoft Calendar API | ATS connector is the critical integration. Greenhouse has the best-documented webhook support; Workday requires polling but dominates enterprise. [S8] |
| **Evaluation / tracing** | LangSmith or Braintrust for LLM trace logging; custom bias dashboard for EEOC four-fifths rule monitoring | Every screening decision needs traceability for compliance audits. Bias metrics are a regulatory requirement, not optional. [S5][S7] |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Foundation (weeks 1–3) | ATS integration working, resume ingestion pipeline running, structured data flowing | ATS API connector with webhook listener, resume parser producing structured JSON, candidate data model, development environment with test data |
| 2 — Core AI (weeks 4–7) | Screening engine scoring candidates, conversational agent handling intake | Semantic matching service with vector store, scoring and ranking logic with configurable thresholds, conversational screening flow (SMS/chat), candidate notification templates |
| 3 — Scheduling and synthesis (weeks 8–10) | Automated interview coordination, evaluation aggregation working | Calendar API integration, scheduling agent with conflict resolution, evaluation synthesizer compiling structured scorecards into decision summaries |
| 4 — Pilot and compliance (weeks 11–14) | Production pilot on one job family, compliance controls validated | Bias audit tooling (four-fifths rule calculator), candidate disclosure and consent flows, jurisdiction-specific compliance configuration (start with one jurisdiction), pilot with 50–100 requisitions, recruiter feedback loop |

## Core Contracts

### State And Output Schemas

The screening pipeline produces a structured candidate assessment for every application. This schema is the contract between the screening engine and the ranking service — and the basis for every compliance audit.

```python
from pydantic import BaseModel, Field

class ParsedResume(BaseModel):
    """Structured extraction from resume text. Every field traces
    back to a specific section of the source document."""
    candidate_name: str
    email: str
    phone: str | None = None
    skills: list[str] = Field(description="Extracted technical and soft skills")
    experience_years: float = Field(description="Total relevant experience in years")
    positions: list[dict] = Field(description="List of {title, company, start, end, summary}")
    education: list[dict] = Field(description="List of {degree, institution, year}")
    certifications: list[str] = []
    source_sections: dict[str, str] = Field(
        description="Map of field name to resume text section it was extracted from"
    )

class ScreeningResult(BaseModel):
    """Output of the screening engine for one candidate-job pair."""
    candidate_id: str
    job_requisition_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    skill_match_score: float = Field(ge=0.0, le=1.0)
    experience_match_score: float = Field(ge=0.0, le=1.0)
    routing: str = Field(description="'shortlist' | 'review' | 'decline'")
    explanation: str = Field(description="Two-sentence rationale for the routing decision")
    matched_requirements: list[str]
    unmet_requirements: list[str]
```

### Tool Interface Pattern

The screening engine exposes tools to the orchestrator. Each tool has a narrow scope — it reads specific data, produces structured output, and cannot modify candidate records directly (all writes go through the ATS connector).

```python
from langchain_core.tools import tool

@tool
def parse_resume(resume_text: str, job_requirements: dict) -> ParsedResume:
    """Extract structured candidate data from raw resume text.
    
    Returns ParsedResume with source_sections linking each extracted
    field to the original text. No hallucinated or inferred fields —
    only what the resume explicitly states.
    """
    # LLM call with structured output enforcement
    ...

@tool
def score_candidate(
    parsed: ParsedResume, 
    requirements: dict,
    threshold_config: dict
) -> ScreeningResult:
    """Score a parsed resume against job requirements using semantic
    similarity on skills and experience. Applies deterministic routing
    rules based on threshold_config.
    """
    # Embedding similarity + deterministic threshold logic
    ...
```

## Orchestration Outline

The pipeline is event-driven. A new application event from the ATS triggers the screening flow. Each step produces structured output consumed by the next.

```python
from celery import Celery

app = Celery("recruiting", broker="redis://localhost:6379/0")

@app.task
def handle_new_application(application_event: dict):
    """Triggered by ATS webhook on new_candidate_application.
    Runs screening, routing, and downstream actions."""
    
    # 1. Fetch resume and job requirements from ATS
    resume = ats_client.get_resume(application_event["candidate_id"])
    job_reqs = ats_client.get_job_requirements(application_event["job_id"])
    
    # 2. Parse resume into structured data
    parsed = parse_resume.invoke({"resume_text": resume, "job_requirements": job_reqs})
    
    # 3. Score and route
    result = score_candidate.invoke({
        "parsed": parsed, 
        "requirements": job_reqs,
        "threshold_config": get_threshold_config(application_event["job_id"])
    })
    
    # 4. Write screening result back to ATS
    ats_client.update_candidate_stage(
        candidate_id=application_event["candidate_id"],
        stage=result.routing,
        metadata=result.model_dump()
    )
    
    # 5. Trigger downstream action based on routing
    if result.routing == "shortlist":
        schedule_interview.delay(application_event["candidate_id"])
    elif result.routing == "decline":
        send_decline_notification.delay(application_event["candidate_id"])
    # "review" routes stay in queue for human recruiter
```

## Prompt And Guardrail Pattern

The screening prompt enforces structured extraction only — no generation, no inference beyond what the resume states. The system prompt sets strict boundaries on what the model may and may not do.

```text
You are a resume screening assistant. Your job is to extract structured
information from the candidate's resume and match it against the job
requirements provided.

RULES:
- Extract ONLY information explicitly stated in the resume.
- Do NOT infer, assume, or hallucinate qualifications not present.
- For each extracted field, include the source text section it came from.
- Score skill matches using semantic similarity, not keyword overlap.
- If a requirement cannot be assessed from the resume, mark it as "unable
  to assess" — do not guess.
- Do NOT assess or reference the candidate's name, gender, age, ethnicity,
  photo, or any protected characteristic.
- Output MUST conform to the ParsedResume and ScreeningResult schemas.
  No free-text narrative.

OUTPUT FORMAT: JSON matching the provided schema. No additional commentary.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| ATS inbound (application events) | Webhook listener (Greenhouse) or polling service (Workday) that captures new applications and stage changes | Greenhouse delivers webhooks with HMAC SHA-256 signatures — validate on every request. Workday lacks native webhooks; poll every 60 seconds with cursor-based pagination to avoid missing events. [S8] |
| ATS outbound (stage updates) | API client that writes screening results, stage transitions, and audit metadata back to the ATS | Every AI decision must be recorded in the ATS for compliance. Include the ScreeningResult JSON as structured metadata on the candidate record. Rate limits: iCIMS caps at 10,000 API calls/day. |
| SMS / chat (candidate messaging) | Twilio adapter for SMS, WebSocket handler for embedded web chat, with conversation state persisted per candidate | Conversational flow must be stateful across sessions — candidates may respond hours or days later. Store conversation state keyed by candidate ID. Support opt-out keywords per TCPA requirements. |
| Calendar (interview scheduling) | Google Calendar API or Microsoft Graph API adapter that reads interviewer availability and creates bookings | Handle timezone normalization. Implement conflict detection with 15-minute buffer between interviews. Send calendar invites with video conferencing links auto-generated. |
| Bias monitoring (compliance) | Batch job that computes selection rates by demographic group across all screening decisions and flags four-fifths rule violations | Run daily or weekly depending on volume. Output feeds the compliance dashboard. Retain historical snapshots for audit. Demographics come from voluntary self-identification in the ATS, not from AI inference. [S5][S7] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Resume parsing accuracy | Compare AI-extracted fields against human-annotated gold set of 200 resumes. Measure per-field precision and recall. | Precision ≥ 0.90 and recall ≥ 0.85 across all structured fields |
| Screening-to-human agreement | Pearson correlation between AI screening scores and recruiter rankings on a shared set of 100 candidates per job family. | Correlation ≥ 0.80 (published benchmark: 0.84 with multi-agent framework) [S12] |
| Adverse impact / bias | Four-fifths rule analysis on screening outcomes by race, ethnicity, and sex across pilot population. | No group selection rate below 80% of highest-performing group rate [S7] |
| Candidate satisfaction | Post-interaction survey (CSAT) sent after screening, scheduling, and decline communications. | ≥ 85% positive rating in pilot (target: 90%+ at steady state) |
| Scheduling completion rate | Percentage of shortlisted candidates with confirmed interview bookings within 48 hours. | ≥ 85% in pilot (target: 90%+ at steady state) |
| End-to-end latency | Time from application submission to screening result delivered to ATS. | ≤ 60 seconds for 95th percentile |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one high-volume job family (hourly or campus) in one jurisdiction. Run AI screening in parallel with human screening for the first 2 weeks ("shadow mode") to validate accuracy before switching to AI-primary. Expand to additional job families after pilot KPIs are met. Chipotle rolled out across 3,500 restaurants in phases over 8 months. [S2] |
| **Fallback path** | If AI screening is disabled, applications route directly to recruiter review queues in the ATS — the pre-AI workflow. The ATS remains the system of record at all times, so no candidate data is lost. Conversational agent falls back to static auto-reply templates. |
| **Observability** | Trace every screening decision end-to-end: resume ingestion → parsing → scoring → routing → ATS writeback. Alert on: parsing failure rate > 5%, screening latency > 120s, ATS API errors, bias metric threshold breaches. Dashboard includes time-to-fill trend, screening volume, routing distribution, and candidate satisfaction. |
| **Operations ownership** | Talent acquisition operations owns the pipeline configuration (screening criteria, thresholds, templates). Engineering owns infrastructure, ATS integration health, and model performance. Compliance/legal owns bias audit review and jurisdiction configuration updates. |
