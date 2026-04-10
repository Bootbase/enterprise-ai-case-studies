---
layout: use-case-detail
title: "Implementation Guide — Autonomous Property and Casualty Insurance Underwriting"
uc_id: "UC-511"
uc_title: "Autonomous Property and Casualty Insurance Underwriting"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Insurance"
complexity: "High"
status: "detailed"
slug: "UC-511-insurance-underwriting-automation"
permalink: /use-cases/UC-511-insurance-underwriting-automation/implementation-guide/
---

## Build Goal

Build a production pilot that covers one line of business (e.g., small commercial property), handles submission intake from email and portal, auto-quotes standard in-appetite risks, and escalates everything else to the underwriter workbench with an AI-prepared summary. The first release should demonstrate straight-through processing for standard risks and measurable cycle time improvement. Multi-line support, broker negotiation automation, and portfolio-level analytics stay outside the first release. [S1][S4]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python (FastAPI) behind the carrier's API gateway | Python has the strongest ecosystem for ML, document processing, and LLM orchestration. FastAPI handles async submission processing well. |
| **Model access** | Anthropic Claude API for document extraction and summarization; XGBoost for risk scoring | LLMs handle the variety of unstructured submission documents. Supervised ML provides auditable risk scores with feature importance. [S3][S5] |
| **Orchestration runtime** | LangGraph for multi-agent workflow with state machine routing | Submission processing needs conditional branching (auto-quote vs. escalation), retry on third-party API failures, and human-in-the-loop support. |
| **Core connectors** | Guidewire Cloud API (PAS), vendor REST APIs (LexisNexis, Verisk, Nearmap), SMTP/IMAP (email intake) | These are the actual systems a carrier integrates with; the pilot must prove the seams work. [S2][S5][S6] |
| **Evaluation / tracing** | OpenTelemetry for distributed traces; LangSmith for prompt evaluation; MLflow for scoring model versioning | Every auto-quoted submission needs a traceable decision path for regulatory audit. [S8] |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Data pipeline and extraction baseline | Email ingestion service, document classifier, extraction prompt suite, ACORD schema parser, accuracy evaluation on 500+ labeled submissions |
| 2 | Risk scoring model and appetite engine | Training dataset from historical underwriting decisions, XGBoost scoring model, deterministic appetite rules engine, evaluation against held-out submission set |
| 3 | End-to-end orchestration and PAS integration | LangGraph workflow connecting intake through quote delivery, Guidewire API adapter, third-party enrichment connectors, underwriter workbench UI for escalated submissions |
| 4 | Measured pilot on one line of business | Shadow-mode deployment on live submissions, KPI dashboard, underwriter feedback loop, rollback path to manual process, go/no-go for auto-quoting |

## Core Contracts

### State And Output Schemas

The submission record is the core state object that flows through every agent. Each agent enriches it; the final state drives the quote or escalation decision.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class SubmissionStatus(str, Enum):
    RECEIVED = "received"
    EXTRACTING = "extracting"
    ENRICHING = "enriching"
    SCORING = "scoring"
    AUTO_QUOTING = "auto_quoting"
    ESCALATED = "escalated"
    QUOTED = "quoted"
    DECLINED = "declined"

class ExtractedField(BaseModel):
    field_name: str
    value: str | float | None
    confidence: float = Field(ge=0.0, le=1.0)
    source_document: str

class RiskScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    appetite_match: bool
    confidence: float = Field(ge=0.0, le=1.0)
    top_factors: list[tuple[str, float]]  # feature name, importance
    escalation_reasons: list[str]

class SubmissionState(BaseModel):
    submission_id: str
    line_of_business: str
    status: SubmissionStatus
    extracted_fields: list[ExtractedField]
    enrichment_data: dict  # third-party data keyed by provider
    risk_score: RiskScore | None = None
    quote_premium: float | None = None
    created_at: datetime
    updated_at: datetime
```

### Tool Interface Pattern

Each agent has scoped tools. The Enrichment Agent, for example, can call third-party data providers but cannot modify the submission record directly — it returns enrichment results that the orchestrator merges into state.

```python
from anthropic import Anthropic

client = Anthropic()

enrichment_tools = [
    {
        "name": "pull_loss_history",
        "description": "Retrieve 5-year loss history for the named insured from LexisNexis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_name": {"type": "string"},
                "fein": {"type": "string", "description": "Federal EIN"},
                "years": {"type": "integer", "default": 5},
            },
            "required": ["business_name"],
        },
    },
    {
        "name": "pull_property_characteristics",
        "description": "Retrieve property data (construction, year built, roof condition) from Verisk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string"},
                "include_aerial": {"type": "boolean", "default": True},
            },
            "required": ["address"],
        },
    },
]
```

## Orchestration Outline

The workflow is a state machine, not a linear pipeline. Each agent transition depends on the previous agent's output and the decision gate's routing logic.

```python
from langgraph.graph import StateGraph, END

def build_underwriting_graph():
    graph = StateGraph(SubmissionState)

    graph.add_node("intake", intake_agent)
    graph.add_node("enrich", enrichment_agent)
    graph.add_node("score", scoring_agent)
    graph.add_node("auto_quote", quote_agent)
    graph.add_node("escalate", prepare_underwriter_summary)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "enrich")
    graph.add_edge("enrich", "score")
    graph.add_conditional_edges(
        "score",
        route_decision,  # checks appetite_match, confidence, authority
        {"auto_quote": "auto_quote", "escalate": "escalate"},
    )
    graph.add_edge("auto_quote", END)
    graph.add_edge("escalate", END)

    return graph.compile()

def route_decision(state: SubmissionState) -> str:
    score = state.risk_score
    if (
        score.appetite_match
        and score.confidence >= 0.85
        and not score.escalation_reasons
        and (state.quote_premium or 0) <= AUTHORITY_LIMIT
    ):
        return "auto_quote"
    return "escalate"
```

The `route_decision` function enforces the hard constraints: appetite match, confidence threshold, no escalation flags, and authority limit. These are deterministic checks, not model predictions.

## Prompt And Guardrail Pattern

The Intake Agent's system prompt drives document extraction. It must produce structured output that downstream agents can rely on.

```text
You are a commercial insurance submission intake specialist. Your job is
to extract structured data from broker submission documents.

Rules:
1. Extract only fields present in the document. Never infer or estimate
   values that are not explicitly stated.
2. For each extracted field, assign a confidence score (0.0-1.0) based
   on clarity of the source text. Flag anything below 0.7 for human review.
3. If a required field is missing from the document, return it with
   value null and confidence 0.0 — do not guess.
4. Map values to ACORD field names where applicable (e.g., BuildingConstruction,
   YearBuilt, OccupancyType).
5. If the document contains multiple locations or coverages, return each
   as a separate entry in the locations array.
6. Never make underwriting judgments. Do not comment on risk quality,
   pricing, or whether the submission should be accepted.

Output format: JSON matching the ExtractedField schema.
```

The scoring agent uses a trained ML model, not an LLM, for the actual risk score. The LLM's role is limited to document understanding and summary generation — areas where its flexibility adds value without creating regulatory exposure. [S3][S8]

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Email submission ingestion | IMAP listener that monitors the underwriting inbox, classifies messages as submissions vs. follow-ups, and extracts attachments for processing | Most carriers receive 60–70% of submissions via email. The classifier must distinguish new submissions from broker replies and quote follow-ups. [S7] |
| Guidewire PolicyCenter API | REST adapter that creates submission records, updates status, writes enrichment data, and posts final quotes | Use Guidewire Cloud API's submission endpoints. Map extracted fields to PolicyCenter's data model. All state must live in the PAS. [S5] |
| Third-party data enrichment | Adapter per provider (LexisNexis, Verisk, Nearmap) with retry logic, rate limiting, and response caching | Each provider has different authentication, rate limits, and response formats. Build a common enrichment interface that normalizes responses. [S2][S6] |
| Rating engine | API call or library invocation that passes enriched risk data and returns calculated premium | The rating engine is the pricing authority. The AI pipeline feeds data to it but never modifies rate tables or filed factors. |
| Underwriter workbench | Web UI or PAS plugin that displays AI-prepared risk summaries for escalated submissions with approve/modify/decline actions | Must surface extraction confidence, scoring rationale with top factors, and enrichment data. Underwriter actions write back to the orchestrator. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Document extraction accuracy | Field-level precision and recall on labeled submission set (500+ documents across application, loss run, and SOV types) | Precision >= 92%, recall >= 88% on required fields before pilot [S5] |
| Risk scoring discrimination | AUC-ROC against historical loss outcomes on held-out test set; calibration plot for predicted vs. actual loss ratios | AUC >= 0.75; calibration error < 5% across deciles [S3] |
| Escalation quality | Percentage of AI-escalated submissions that underwriters agree warranted escalation (measured via feedback loop) | >= 85% underwriter agreement rate on escalation decisions |
| Auto-quote accuracy | Percentage of auto-quoted submissions where the AI quote is within 5% of what an underwriter would have quoted (measured in shadow mode) | >= 90% within-tolerance rate before enabling live auto-quoting |
| Bias monitoring | Disparate impact ratio across protected-class proxies (geography, credit tier) on auto-quote acceptance rates | Ratio between 0.8 and 1.25 (four-fifths rule) across all monitored dimensions [S8] |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode: AI processes every submission in parallel with the human underwriter, but does not deliver quotes. Compare AI decisions against human decisions for 60–90 days. Enable auto-quoting only after evaluation gates are met on the shadow-mode data. [S1][S4] |
| **Fallback path** | If the AI pipeline fails or a data provider is unavailable, the submission routes directly to the manual underwriting queue. No submission should be blocked or lost because of an AI system outage. |
| **Observability** | Trace every submission end-to-end: extraction confidence per field, enrichment source and latency, scoring factors and decision, quote amount, and final outcome. Alert on extraction accuracy drops, scoring confidence distribution shifts, and auto-quote rate anomalies. |
| **Operations ownership** | Data science team owns model performance and retraining. Underwriting operations owns submission flow and escalation rules. IT owns PAS integration and system reliability. Compliance owns bias monitoring and audit review. |
