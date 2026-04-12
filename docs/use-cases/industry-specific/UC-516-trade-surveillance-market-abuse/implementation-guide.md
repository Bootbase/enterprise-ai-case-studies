---
layout: use-case-detail
title: "Implementation Guide — Autonomous Trade Surveillance and Market Abuse Detection"
uc_id: "UC-516"
uc_title: "Autonomous Trade Surveillance and Market Abuse Detection"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Capital Markets"
complexity: "High"
status: "detailed"
slug: "UC-516-trade-surveillance-market-abuse"
permalink: /use-cases/UC-516-trade-surveillance-market-abuse/implementation-guide/
---

## Build Goal

Deliver an agentic triage system that receives alerts from the existing surveillance engine, enriches them with order-book replay, news sensitivity scoring, and communication analysis, then produces scored investigation packages with draft narratives for analyst review. The first production release covers single-venue alert triage for the three highest-volume abuse types: spoofing, layering, and insider dealing. Cross-venue correlation, communication monitoring integration, and novel-pattern detection are second-release targets. Pre-trade risk controls and autonomous STOR filing are out of scope.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12+ on Kubernetes | Dominant language for ML and data processing in capital markets. Most surveillance teams already have Python tooling for quantitative analysis. |
| **Model access** | Anthropic Claude API (narrative generation, news sensitivity); scikit-learn (anomaly detection) | Claude handles unstructured evidence synthesis and communication analysis. LSEG validated Claude for news sensitivity classification on Amazon Bedrock. scikit-learn provides auditable anomaly detection. [S2] |
| **Orchestration runtime** | LangGraph (langgraph >= 0.3) | Stateful multi-step workflows with parallel tool execution, conditional routing by alert severity, and human-in-the-loop checkpoints for analyst review. |
| **Core connectors** | FIX protocol adapter for market data; REST adapters for news feeds, communication archives, and case management | FIX is the industry standard for order/trade data ingestion. Nasdaq SMARTS uses FIX, OMnet, and ITCH protocols. [S5] |
| **Evaluation / tracing** | OpenTelemetry + LangSmith | Per-investigation traces with tool call latency, anomaly scores, and narrative quality metrics. Required for regulatory audit trail under MAR and MiFID II. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Foundation (6 weeks) | Market data adapters operational, alert intake pipeline running, investigation state schema validated | FIX adapter for order-book data ingestion. REST adapters for news feed and case management. Alert intake pipeline with deduplication. Pydantic state models. Synthetic alert generator for testing. |
| 2 — Core Triage Agent (8 weeks) | Agent triages spoofing, layering, and insider dealing alerts with anomaly scoring and news enrichment. Analysts review in existing case management UI. | LangGraph orchestration pipeline. Isolation forest anomaly detection trained on historical order-book features. News sensitivity classifier using Claude. Draft narrative generator with source citations. |
| 3 — Communication + Cross-Venue (8 weeks) | Communication monitoring integration and cross-venue pattern correlation added to triage pipeline. | Communication archive adapter (email, chat, voice transcript search). Cross-venue order pattern matcher. Enhanced narrative covering communication evidence. |
| 4 — Pilot + Validation (6 weeks) | Shadow-mode pilot on live alerts alongside human analysts. Metrics validated against release gates. | Side-by-side comparison dashboard. Model validation report. Regulatory affairs review. Examiner-ready audit documentation. |

## Core Contracts

### State And Output Schemas

The investigation state tracks the full lifecycle from alert intake through disposition recommendation. The agent populates fields as it retrieves data from each source.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class AbuseType(str, Enum):
    SPOOFING = "spoofing"
    LAYERING = "layering"
    WASH_TRADING = "wash_trading"
    INSIDER_DEALING = "insider_dealing"
    PUMP_AND_DUMP = "pump_and_dump"
    FRONT_RUNNING = "front_running"
    UNKNOWN = "unknown"

class Disposition(str, Enum):
    CLOSE_FALSE_POSITIVE = "close_false_positive"
    ESCALATE_FOR_REVIEW = "escalate_for_review"
    RECOMMEND_STOR = "recommend_stor"

class SourceCitation(BaseModel):
    system: str          # e.g. "order_book", "news_feed", "comms_archive"
    record_id: str
    retrieved_at: datetime

class InvestigationPackage(BaseModel):
    alert_id: str
    instrument: str
    venue: str
    suspected_abuse_type: AbuseType
    anomaly_score: float = Field(ge=0.0, le=1.0)
    news_sensitivity: str | None = None
    order_book_summary: str
    communication_findings: str | None = None
    narrative: str
    citations: list[SourceCitation]
    recommended_disposition: Disposition
    confidence: float = Field(ge=0.0, le=1.0)
    gaps: list[str] = Field(default_factory=list)
```

### Tool Interface Pattern

Each data source is exposed to the agent as a typed tool. Tools are read-only — the agent gathers evidence but never modifies source systems. Write access is limited to the case management system for persisting investigation results.

```python
from langchain_core.tools import tool

@tool
def replay_order_book(
    instrument: str,
    venue: str,
    window_start: datetime,
    window_end: datetime,
) -> dict:
    """Reconstruct the full order lifecycle for an instrument within
    the alert window. Returns order submissions, modifications,
    cancellations, and executions with timestamps and participant IDs.
    Computes derived features: cancel-to-trade ratio, order lifetime
    distribution, and price impact metrics."""
    # Adapter queries kdb+/tick database
    ...

@tool
def score_news_sensitivity(
    issuer: str,
    window_start: datetime,
    window_end: datetime,
) -> dict:
    """Retrieve and classify news articles for the issuer within the
    alert window. Each article is scored as PRICE_SENSITIVE,
    HARD_TO_DETERMINE, or PRICE_NOT_SENSITIVE using LLM classification.
    Returns articles with scores and reasoning."""
    # Calls Claude API with news article content
    ...

@tool
def search_trader_communications(
    trader_id: str,
    window_start: datetime,
    window_end: datetime,
) -> dict:
    """Search the communication archive for the flagged trader within
    the alert window. Returns matching emails, chats, and voice
    transcript excerpts with misconduct type classification."""
    # Adapter queries communication archiving platform
    ...
```

## Orchestration Outline

The investigation follows a stateful pipeline: alert intake, parallel evidence gathering (order-book replay + news sensitivity + optional communication search), anomaly scoring, narrative generation, and analyst review checkpoint. LangGraph manages state transitions and retries individual tool failures without restarting the full investigation.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

graph = StateGraph(InvestigationState)

# Parallel evidence gathering — order book, news, comms run concurrently
graph.add_node("gather_evidence", gather_evidence_node)
# Anomaly scoring on assembled order-book features
graph.add_node("score_anomaly", score_anomaly_node)
# News sensitivity classification for insider dealing alerts
graph.add_node("classify_news", classify_news_node)
# Draft investigation narrative with grounded citations
graph.add_node("draft_narrative", draft_narrative_node)
# Human review checkpoint — blocks until analyst acts
graph.add_node("analyst_review", analyst_review_node)

graph.add_edge(START, "gather_evidence")
graph.add_edge("gather_evidence", "score_anomaly")
graph.add_conditional_edges("score_anomaly", route_by_abuse_type, {
    "insider_dealing": "classify_news",
    "other": "draft_narrative",
})
graph.add_edge("classify_news", "draft_narrative")
graph.add_edge("draft_narrative", "analyst_review")
graph.add_edge("analyst_review", END)

app = graph.compile(checkpointer=MemorySaver())
```

## Prompt And Guardrail Pattern

The narrative generation prompt enforces investigation structure, grounded citation, and refusal to speculate beyond retrieved evidence.

```text
You are a market surveillance analyst preparing an investigation narrative.

TASK: Write a structured investigation narrative for the alert below.

RULES:
- State the suspected abuse type, instrument, venue, and time window.
- Describe the order/trade pattern that triggered the alert and why
  it deviates from normal behavior for this instrument.
- If news articles were analyzed, state whether price-sensitive news
  was published before, during, or after the flagged trading activity.
- Every factual claim must cite a source system and record ID using
  the format [source:record_id].
- If a data source was unavailable, state what is missing. Do NOT
  infer or speculate to fill gaps.
- Recommend disposition: CLOSE_FALSE_POSITIVE, ESCALATE_FOR_REVIEW,
  or RECOMMEND_STOR with a one-sentence rationale.

ALERT CONTEXT:
{alert_json}

EVIDENCE PACKAGE:
{evidence_json}

OUTPUT FORMAT:
Return a JSON object with fields: narrative (string),
suspected_abuse_type (enum), disposition (enum),
confidence (float 0-1), gaps (list of strings).
```

Guardrails enforced at the orchestration layer:
- Narrative citations are validated against actual tool call results. Any citation referencing a record not in the evidence package triggers rejection and re-generation.
- Trader identity and communication content are used within the investigation context only and never logged to observability systems in cleartext. GDPR Article 6(1)(c) lawful basis.
- If the agent cannot retrieve order-book data (the minimum required input), it routes the alert back to the manual queue rather than producing a partial investigation.

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Alert intake from surveillance engine | Event listener or polling adapter that reads new alerts from the surveillance platform and creates investigation state objects. | Nasdaq SMARTS supports FIX-based alert export. NICE Actimize provides REST APIs. Deduplicate by alert ID. Expect 500–800 alerts/day at a mid-size broker-dealer. [S1][S5] |
| Order-book replay adapter | Query client that retrieves the full order lifecycle for an instrument/venue/time window and computes derived features (cancel-to-trade ratio, order lifetime, price impact). | kdb+ is standard for tick data in capital markets. If the firm uses a different time-series store, the adapter must still return the same feature schema. Expect sub-second query latency for single-instrument windows. |
| News feed integration | REST adapter to news provider (RNS, SEC EDGAR, Bloomberg B-PIPE) with LLM classification pipeline. | LSEG's implementation classifies articles on a nine-point sensitivity scale. For the triage agent, a three-class output (sensitive / hard to determine / not sensitive) is sufficient. Cache classifications to avoid re-processing. [S2] |
| Communication archive integration | REST adapter to archiving platform (NICE Compliancentral, Global Relay, Smarsh) with search scoped to trader ID and time window. | Communication access is the most sensitive integration. Scope every query to the specific trader and alert window. Log all access for GDPR compliance. Some firms require a second approval step before communication retrieval. [S3] |
| Case management writeback | REST adapter that persists the investigation package to the case management system. | Write operations require idempotency keys. Analyst disposition is written by the case management UI, not by the agent. Agent never modifies alert status directly. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Anomaly detection accuracy | Back-test isolation forest against 12 months of labeled alert outcomes (escalated vs. closed). Measure precision, recall, and AUC on confirmed abuse cases. | AUC ≥ 0.85; false negative rate ≤ 5% on confirmed STORs |
| News sensitivity classification | Compare LLM classifications against analyst labels on a test set of 200+ news articles covering major news categories. | ≥ 95% recall on price-sensitive articles (per LSEG benchmark) [S2] |
| Narrative quality | Blind review by 3 surveillance analysts: score each AI-generated narrative on completeness, accuracy (no unsupported claims), and actionability (sufficient for disposition decision). | ≥ 90% of narratives rated "sufficient for disposition" without major edits |
| Citation grounding | Automated validation: every citation in the narrative must map to a record in the evidence package. | 100% citation validity (hard gate) |
| Disposition agreement | Compare agent-recommended disposition against analyst final decision on the same alerts during shadow-mode pilot. | ≥ 85% agreement rate |
| Latency | Measure end-to-end time from alert intake to investigation package ready for review. | Single-venue triage: < 3 minutes. Cross-venue investigation: < 10 minutes. |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode: agent triages every alert in parallel with human analysts, results not shown. Compare outcomes for 4–6 weeks. Graduate to assist mode: analysts see AI investigation packages alongside their own triage. Graduate to primary mode: analysts review AI packages directly, triaging manually only on escalations. Matches Nasdaq's phased rollout to surveillance clients. [S1] |
| **Fallback path** | If the agent is unavailable, alerts route to the existing manual triage queue. The surveillance engine and case management system continue operating independently. No hard dependency on the agent for alert processing or STOR filing. |
| **Observability** | Trace every investigation: tool call latency, success/failure per data source, anomaly score distribution, narrative generation time, analyst override rate. Alert on: data adapter failure rate > 5%, investigation latency exceeding SLA, citation validation failures > 0%. |
| **Operations ownership** | Joint ownership between the market surveillance team (investigation quality, regulatory readiness) and the technology/AI team (model performance, system reliability). Surveillance analyst retains accountability for every STOR filing. Model governance: quarterly back-testing, annual validation, model inventory updates per firm's model risk framework. |
