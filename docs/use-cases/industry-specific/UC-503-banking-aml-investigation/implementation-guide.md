---
layout: use-case-detail
title: "Implementation Guide — Autonomous AML Alert Investigation with Agentic AI in Banking"
uc_id: "UC-503"
uc_title: "Autonomous AML Alert Investigation with Agentic AI in Banking"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Banking / Financial Services"
complexity: "High"
status: "detailed"
slug: "UC-503-banking-aml-investigation"
permalink: /use-cases/UC-503-banking-aml-investigation/implementation-guide/
---

## Build Goal

Deliver an agentic investigation system that receives AML alerts from the existing transaction monitoring system, gathers evidence from source systems, and produces a structured investigation package with a draft SAR narrative for compliance officer review. The first production release covers L1 alert triage — scoring, evidence gathering, and disposition recommendation for the high-volume alert queue. Full L2 investigation with network analysis and SAR narrative generation is the second release. Look-back exercises and bulk re-investigation are out of scope for the initial build.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12+ on Kubernetes | Dominant language for ML/AI tooling. Banks with existing Java stacks can use Python microservices behind an API gateway. |
| **Model access** | Anthropic Claude API (narrative generation); scikit-learn/XGBoost (risk scoring) | Claude handles unstructured evidence synthesis and SAR drafting. Supervised ML provides interpretable, auditable risk scores required under SR 11-7. [S10] |
| **Orchestration runtime** | LangGraph (langgraph >= 0.3) | Stateful multi-agent workflows with parallel tool execution, conditional routing, human-in-the-loop checkpoints, and durable state persistence. |
| **Core connectors** | REST adapters per source system; graph query client (Quantexa API or Neo4j Bolt) | Each source system gets a dedicated adapter with retry logic, timeout handling, and structured output mapping. Graph client handles entity resolution queries. |
| **Evaluation / tracing** | OpenTelemetry + LangSmith | Per-investigation traces with latency, tool call success rates, and narrative quality scores. LangSmith provides prompt versioning and regression testing. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Foundation (6 weeks) | Source system adapters operational, investigation state schema validated, dev environment with synthetic alerts | REST adapters for core banking, KYC, sanctions screening. Alert intake pipeline. Investigation state Pydantic models. Synthetic alert generator for testing. |
| 2 — L1 Triage Agent (8 weeks) | Agent triages alerts with evidence gathering and disposition recommendation. Officers review in existing case management UI. | LangGraph orchestration pipeline. Parallel tool execution across source systems. Risk scoring model trained on historical alert outcomes. Disposition recommendation with confidence score. |
| 3 — L2 Investigation + Narrative (8 weeks) | Full investigation with network analysis and SAR-quality narrative generation. | Graph analytics integration (entity resolution, fund flow tracing). SAR narrative generator with grounded citations. Senior investigator escalation path for low-confidence cases. |
| 4 — Pilot + Validation (6 weeks) | Shadow-mode pilot on live alerts alongside human investigators. Metrics validated against release gates. | Side-by-side comparison dashboard. Model validation report per SR 11-7. Examiner-ready documentation. Regulatory affairs review. |

## Core Contracts

### State And Output Schemas

The investigation state schema tracks the full lifecycle from alert intake through disposition. The agent populates fields progressively as it retrieves data from each source system.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class Disposition(str, Enum):
    FILE_SAR = "file_sar"
    CLOSE = "close"
    ESCALATE = "escalate"

class SourceCitation(BaseModel):
    system: str          # e.g. "core_banking", "kyc_cdd", "sanctions"
    record_id: str       # source system record identifier
    retrieved_at: datetime

class InvestigationReport(BaseModel):
    alert_id: str
    customer_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    evidence_summary: str
    network_findings: str | None = None
    sar_narrative: str | None = None
    citations: list[SourceCitation]
    recommended_disposition: Disposition
    confidence: float = Field(ge=0.0, le=1.0)
    gaps: list[str] = Field(default_factory=list,
        description="Data sources that were unavailable or returned errors")
```

### Tool Interface Pattern

Each source system is exposed to the agent as a typed tool. Tools are read-only by design — the agent gathers evidence but never modifies source systems. Write access is limited to the case management system for persisting investigation results.

```python
from langchain_core.tools import tool

@tool
def lookup_customer_profile(customer_id: str) -> dict:
    """Retrieve KYC/CDD profile including beneficial ownership,
    risk rating, and last CDD review date.
    Returns structured profile or error if customer not found."""
    # Adapter calls KYC system REST API
    # Returns: name, entity_type, risk_rating, beneficial_owners,
    #          pep_status, last_review_date, jurisdiction
    ...

@tool
def get_transaction_history(
    customer_id: str,
    lookback_days: int = 90
) -> dict:
    """Retrieve transaction history for the customer within the
    lookback window. Returns aggregated summaries and flagged
    transactions that triggered the alert."""
    # Adapter calls core banking API
    # Returns: transactions, aggregates (volume, count, counterparties)
    ...

@tool
def query_entity_network(
    entity_ids: list[str],
    max_hops: int = 3
) -> dict:
    """Resolve entities and trace financial network up to max_hops.
    Returns resolved entities, relationships, and structural risk
    patterns (circular flows, shell structures)."""
    # Adapter calls graph analytics API (Quantexa/Neo4j)
    ...
```

## Orchestration Outline

The investigation follows a stateful pipeline: alert intake, parallel evidence gathering, analysis, narrative generation, and human review checkpoint. LangGraph manages state transitions and supports retry on individual tool failures without restarting the full investigation.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

graph = StateGraph(InvestigationState)

# Parallel evidence gathering — all source lookups run concurrently
graph.add_node("gather_evidence", gather_evidence_node)
# Risk scoring on assembled evidence
graph.add_node("score_risk", score_risk_node)
# Graph analytics for network analysis (Phase 2)
graph.add_node("analyze_network", analyze_network_node)
# SAR narrative generation with grounded citations
graph.add_node("draft_narrative", draft_narrative_node)
# Human review checkpoint — blocks until officer acts
graph.add_node("officer_review", officer_review_node)

graph.add_edge(START, "gather_evidence")
graph.add_edge("gather_evidence", "score_risk")
graph.add_conditional_edges("score_risk", route_by_risk, {
    "high_risk": "analyze_network",
    "low_risk": "officer_review",  # fast-path for clear false positives
})
graph.add_edge("analyze_network", "draft_narrative")
graph.add_edge("draft_narrative", "officer_review")
graph.add_edge("officer_review", END)

app = graph.compile(checkpointer=MemorySaver())
```

## Prompt And Guardrail Pattern

The narrative generation prompt enforces SAR structure, grounded citation, and refusal to speculate beyond retrieved evidence.

```text
You are an AML investigation analyst preparing a draft SAR narrative.

TASK: Write a structured investigation narrative for the alert below.

RULES:
- Cover all five W's: Who, What, When, Where, Why.
- Every factual claim must cite a source system and record ID
  using the format [source:record_id].
- If a data source was unavailable, state what is missing. Do NOT
  infer or speculate to fill gaps.
- Do not use hedging language like "may have" or "could potentially"
  unless the evidence is genuinely ambiguous — in that case, state
  the ambiguity explicitly.
- Do not include information not present in the evidence package.
- Recommend disposition: FILE_SAR, CLOSE, or ESCALATE with a
  one-sentence rationale.

EVIDENCE PACKAGE:
{evidence_json}

OUTPUT FORMAT:
Return a JSON object with fields: narrative (string), disposition
(enum), confidence (float 0-1), gaps (list of strings).
```

Guardrails enforced at the orchestration layer:
- Narrative citations are validated against the actual tool call results. Any citation referencing a record not in the evidence package triggers rejection and re-generation.
- PII from source systems is used within the investigation context only and never logged to observability systems in cleartext.
- If the agent cannot retrieve data from 3+ critical systems, it escalates to a human investigator rather than producing a partial report.

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Alert intake from TMS | Event listener or polling adapter that reads new alerts from the TMS alert queue and creates investigation state objects. | Most TMS platforms (Actimize, Verafin, Fircosoft) support webhook or message queue export. If not, poll the alert table on a short interval. Deduplicate by alert ID. |
| Core banking + KYC adapters | REST client adapters with structured response mapping, retry with exponential backoff, and circuit breaker for system outages. | Banks typically have an internal API gateway. Each adapter maps vendor-specific response schemas to the canonical investigation state model. Expect 200–500ms latency per call. |
| Graph analytics integration | Query client that submits entity identifiers and receives resolved network, risk patterns, and fund flow traces. | Quantexa provides a REST API for CDI queries. Neo4j uses Bolt protocol. Pre-compute entity resolution on nightly batch; real-time queries traverse the pre-resolved graph. [S7][S14] |
| Case management writeback | REST adapter that persists the investigation package (evidence summary, narrative draft, risk score, citations) to the case management system. | Write operations require idempotency keys to prevent duplicate entries. Officer disposition is written by the case management UI, not by the agent. |
| SAR filing pipeline | Export adapter that formats approved SARs for FinCEN BSA E-Filing (XML) or the bank's filing intermediary. | Agent does not file directly. The existing SAR filing workflow is preserved — the agent contributes the narrative and structured data, the officer approves, and the filing system submits. [S3] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Evidence retrieval completeness | For a labeled test set of 500 alerts, compare the data points retrieved by the agent against what a human investigator gathered for the same alerts. Measure recall of critical evidence fields. | ≥ 95% recall on critical fields (customer profile, triggering transactions, sanctions hits) |
| Risk scoring accuracy | Back-test the ML risk scoring model against 12 months of labeled alert outcomes (SAR filed vs. closed). Measure precision, recall, and AUC. | AUC ≥ 0.85; false negative rate ≤ 5% on confirmed SARs |
| Narrative quality | Blind review by 3 BSA officers: score each AI-generated narrative on completeness (five W's covered), accuracy (no unsupported claims), and actionability (sufficient for filing decision). | ≥ 90% of narratives rated "sufficient for filing decision" without major edits |
| Citation grounding | Automated validation: every citation in the narrative must map to a record in the evidence package. | 100% citation validity (hard gate — no ungrounded citations in production) |
| Disposition agreement | Compare agent-recommended disposition against officer final decision on the same alerts during shadow-mode pilot. | ≥ 85% agreement rate; disagreements reviewed for systematic bias |
| Latency | Measure end-to-end time from alert intake to investigation package ready for review. | L1 triage: < 2 minutes. L2 investigation: < 15 minutes. |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode: agent investigates every alert in parallel with human investigators, but results are not shown to officers. Compare outcomes for 4–6 weeks. Graduate to assist mode: officers see the AI investigation package alongside their own work. Graduate to primary mode: officers review AI packages directly, investigating manually only on escalations. [S1] |
| **Fallback path** | If the agent is unavailable or degraded, alerts route to the existing manual investigation queue. The TMS and case management system continue to operate independently. No hard dependency on the agent for alert processing. |
| **Observability** | Trace every investigation: tool call latency, success/failure per source system, risk score distribution, narrative generation time, officer override rate. Alert on: source system adapter failure rate > 5%, average investigation latency exceeding SLA, citation validation failure rate > 0%. |
| **Operations ownership** | Joint ownership between the AML compliance team (investigation quality, regulatory readiness) and the AI/ML engineering team (model performance, system reliability). BSA officer retains accountability for every SAR filing. Model governance follows SR 11-7: quarterly back-testing, annual independent validation, model inventory updates. [S10] |
