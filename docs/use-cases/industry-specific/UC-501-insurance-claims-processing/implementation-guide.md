---
layout: use-case-detail
title: "Implementation Guide — Autonomous Insurance Claims Processing"
uc_id: "UC-501"
uc_title: "Autonomous Insurance Claims Processing with Multi-Agent AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Insurance / Financial Services"
complexity: "High"
status: "detailed"
slug: "UC-501-insurance-claims-processing"
permalink: /use-cases/UC-501-insurance-claims-processing/implementation-guide/
---

## Build Goal

Build a production pilot that handles low-complexity catastrophe claims (food spoilage under AUD $500 from storm-related power outages) end-to-end through a multi-agent pipeline. The first release processes claims from FNOL through payout recommendation in under 5 minutes, presents the recommendation to a human adjuster for approval, and logs the full decision chain for audit. Auto-approval without human review, complex multi-peril claims, bodily injury, and third-party liability claims stay outside the first release. [S1][S5]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python (FastAPI) behind the carrier's API gateway | Python dominates the ML and LLM ecosystem. FastAPI handles async claim processing with good concurrency. |
| **Model access** | Anthropic Claude API for document extraction and claim summarization; XGBoost for fraud anomaly scoring | LLM handles the variety of claim submissions (photos, receipts, free text). Supervised ML provides auditable fraud scores with feature importance. [S6] |
| **Orchestration runtime** | LangGraph for multi-agent workflow with state machine routing | Claims processing needs sequential agent execution with conditional branching (auto-recommend vs. escalate), retry on weather API failures, and human-in-the-loop at the decision gate. [S1] |
| **Core connectors** | Guidewire ClaimCenter Cloud API (CMS), Meteomatics/BOM weather APIs, Shift Technology (fraud), policy administration system | These are the actual systems a carrier integrates with; the pilot must prove the seams work. [S6][S10] |
| **Evaluation / tracing** | OpenTelemetry for distributed traces; LangSmith for prompt evaluation; structured decision logs per claim | Every processed claim needs a traceable decision path for regulatory audit under NAIC Model Bulletin requirements. [S8] |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | FNOL extraction baseline and weather validation | Document extraction prompt suite, receipt/photo extraction evaluation on 300+ labeled claims, weather API adapter with multi-provider fallback, coverage lookup adapter |
| 2 | Fraud scoring model and decision gate | Training dataset from historical claims fraud data, XGBoost anomaly model, deterministic fraud rules engine, decision gate routing logic with configurable thresholds |
| 3 | End-to-end orchestration and CMS integration | LangGraph workflow connecting all agents, Guidewire ClaimCenter API adapter, adjuster review UI for recommendations, payout calculation engine |
| 4 | Measured pilot on catastrophe food spoilage claims | Shadow-mode deployment on live claims, KPI dashboard, adjuster feedback loop, rollback path to manual process, go/no-go for expanded claim types |

## Core Contracts

### State And Output Schemas

The claim state is the core object flowing through every agent. Each agent enriches it; the final state drives the payout recommendation or escalation.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ClaimStatus(str, Enum):
    RECEIVED = "received"
    EXTRACTING = "extracting"
    COVERAGE_CHECK = "coverage_check"
    WEATHER_VALIDATION = "weather_validation"
    FRAUD_SCREENING = "fraud_screening"
    PAYOUT_CALCULATION = "payout_calculation"
    ADJUSTER_REVIEW = "adjuster_review"
    APPROVED = "approved"
    DENIED = "denied"

class ExtractedItem(BaseModel):
    description: str
    amount: float
    confidence: float = Field(ge=0.0, le=1.0)
    source_document: str

class WeatherConfirmation(BaseModel):
    event_confirmed: bool
    event_type: str
    severity: str | None = None
    data_source: str
    location_match: bool

class FraudScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    risk_level: str  # low, medium, high
    flags: list[str]
    top_factors: list[tuple[str, float]]

class ClaimState(BaseModel):
    claim_id: str
    policy_number: str
    status: ClaimStatus
    claim_type: str
    claimed_amount: float
    extracted_items: list[ExtractedItem]
    coverage_verified: bool | None = None
    weather_confirmation: WeatherConfirmation | None = None
    fraud_score: FraudScore | None = None
    recommended_payout: float | None = None
    created_at: datetime
    updated_at: datetime
```

### Tool Interface Pattern

Each agent has scoped tools. The Weather Validation Agent can query weather providers but cannot modify the claim record — it returns confirmation results that the orchestrator merges into state.

```python
from anthropic import Anthropic

client = Anthropic()

weather_tools = [
    {
        "name": "verify_weather_event",
        "description": "Check if a weather event occurred at a specific location and date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "event_date": {"type": "string", "format": "date"},
                "event_type": {
                    "type": "string",
                    "enum": ["storm", "hail", "flood", "cyclone", "lightning"],
                },
                "provider": {
                    "type": "string",
                    "enum": ["meteomatics", "bom", "noaa"],
                    "default": "meteomatics",
                },
            },
            "required": ["latitude", "longitude", "event_date", "event_type"],
        },
    },
    {
        "name": "get_power_outage_records",
        "description": "Check if a power outage was reported in the area on the given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "postcode": {"type": "string"},
                "date": {"type": "string", "format": "date"},
                "utility_provider": {"type": "string"},
            },
            "required": ["postcode", "date"],
        },
    },
]
```

## Orchestration Outline

The workflow is a sequential pipeline with a conditional decision gate. Each agent must complete before the next begins, because downstream agents depend on upstream outputs.

```python
from langgraph.graph import StateGraph, END

def build_claims_graph():
    graph = StateGraph(ClaimState)

    graph.add_node("intake", fnol_intake_agent)
    graph.add_node("coverage", coverage_verification_agent)
    graph.add_node("weather", weather_validation_agent)
    graph.add_node("fraud", fraud_screening_agent)
    graph.add_node("payout", payout_calculation_agent)
    graph.add_node("escalate", prepare_adjuster_escalation)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "coverage")
    graph.add_edge("coverage", "weather")
    graph.add_edge("weather", "fraud")
    graph.add_conditional_edges(
        "fraud",
        route_claim_decision,
        {"recommend_payout": "payout", "escalate": "escalate"},
    )
    graph.add_edge("payout", END)
    graph.add_edge("escalate", END)

    return graph.compile()

def route_claim_decision(state: ClaimState) -> str:
    if not state.coverage_verified:
        return "escalate"
    if not state.weather_confirmation or not state.weather_confirmation.event_confirmed:
        return "escalate"
    if state.fraud_score.risk_level != "low" or state.fraud_score.flags:
        return "escalate"
    if state.claimed_amount > AUTO_RECOMMEND_LIMIT:
        return "escalate"
    return "recommend_payout"
```

The `route_claim_decision` function enforces hard constraints: coverage confirmed, weather event confirmed, low fraud risk, and claim under threshold. These are deterministic checks, not model predictions.

## Prompt And Guardrail Pattern

The FNOL Intake Agent's system prompt drives document extraction from claim submissions including photos and receipts.

```text
You are an insurance claims intake specialist. Your job is to extract
structured data from claim submission documents including photos, receipts,
and written descriptions.

Rules:
1. Extract only information explicitly present in the documents. Never
   infer amounts, dates, or item descriptions that are not stated.
2. For each extracted item, assign a confidence score (0.0-1.0) based on
   clarity. Flag anything below 0.7 for human review.
3. If a required field is missing, return it with value null and
   confidence 0.0 — do not guess.
4. Categorize items using standard categories: food_spoilage,
   property_damage, temporary_accommodation, emergency_repairs.
5. Sum individual item amounts to produce a total claimed amount.
6. Never make coverage judgments, fraud assessments, or payout
   recommendations. Your role is extraction only.

Output format: JSON matching the ClaimState schema with extracted_items
populated.
```

The fraud scoring agent uses a trained ML model, not an LLM, for the actual risk score. The LLM's role is limited to document understanding and summarization — areas where flexibility adds value without creating regulatory exposure in a scored decision. [S8]

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Guidewire ClaimCenter API | REST adapter that creates claim records, updates status, writes agent outputs, and triggers payment workflows | Use ClaimCenter Cloud API v1 endpoints. Map extracted fields to ClaimCenter's data model. All claim state must live in the CMS — agents are stateless processors. [S10] |
| Weather data providers | Multi-provider adapter with fallback chain (Meteomatics primary, BOM/NOAA secondary) | Meteomatics MetX Claims provides purpose-built insurance weather validation with binary yes/no per parameter. BOM covers Australia-specific data. Build common response interface across providers. |
| Fraud detection platform | Adapter to Shift Technology or equivalent, plus local XGBoost model for fast pre-screening | Shift processes 2.6B+ documents and serves hundreds of insurers. Use their API for deep analysis; run a local model for sub-second pre-screening to avoid API latency on every claim. [S6] |
| Policy administration system | Read-only adapter that retrieves policy details: covered perils, limits, deductibles, endorsements, effective dates | Coverage Agent needs real-time policy state. Build a caching layer with short TTL to handle burst volumes during catastrophe events without overloading the PAS. |
| Adjuster review interface | Web UI or CMS plugin that displays the complete agent output chain with approve/modify/reject actions | Must surface: extracted items with confidence, coverage determination, weather confirmation evidence, fraud score with top factors, and recommended payout calculation. Adjuster actions write back to orchestrator. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Document extraction accuracy | Field-level precision and recall on labeled claim submissions (300+ claims across receipt, photo, and description types) | Precision >= 90%, recall >= 85% on required fields before pilot |
| Weather validation accuracy | Agreement rate between agent weather confirmation and manual adjuster verification on historical claims with known weather outcomes | >= 95% agreement on claims with clear weather data available |
| Fraud scoring discrimination | AUC-ROC against historically confirmed fraud cases on held-out test set; false-positive rate on known-good claims | AUC >= 0.80; false-positive rate < 5% |
| Payout calculation accuracy | Percentage of AI-recommended payouts within 5% of what an adjuster would have calculated (measured in shadow mode) | >= 92% within-tolerance rate before enabling live recommendations |
| End-to-end pipeline latency | P95 time from FNOL submission to payout recommendation ready for adjuster review | < 5 minutes for eligible claims [S1] |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode: AI processes every eligible claim in parallel with the manual adjuster workflow, but does not present recommendations to claimants. Compare AI recommendations against adjuster decisions for 60–90 days. Enable adjuster-facing recommendations only after evaluation gates are met. [S1][S5] |
| **Fallback path** | If the AI pipeline fails, a weather provider is unavailable, or any agent returns an error, the claim routes directly to the manual adjuster queue. No claim should be delayed or lost because of an AI system outage. During catastrophe surges, the pipeline gracefully degrades by queuing claims rather than dropping them. |
| **Observability** | Trace every claim end-to-end: extraction confidence per item, coverage determination, weather API response and source, fraud score and factors, payout calculation breakdown, and adjuster decision. Alert on extraction accuracy drops, weather API availability, fraud score distribution shifts, and pipeline latency breaches. |
| **Operations ownership** | Data science team owns model performance and retraining. Claims operations owns adjuster workflow and escalation rules. IT owns CMS integration and system reliability. Compliance owns regulatory documentation and audit review per NAIC requirements. [S8] |
