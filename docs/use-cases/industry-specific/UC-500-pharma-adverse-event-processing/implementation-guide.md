---
layout: use-case-detail
title: "Implementation Guide — Autonomous Adverse Event Report Processing in Pharmacovigilance"
uc_id: "UC-500"
uc_title: "Autonomous Adverse Event Report Processing in Pharmacovigilance"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Pharmaceutical / Life Sciences"
complexity: "High"
status: "detailed"
slug: "UC-500-pharma-adverse-event-processing"
permalink: /use-cases/UC-500-pharma-adverse-event-processing/implementation-guide/
---

## Build Goal

The delivery team builds an agentic pipeline that ingests adverse event source documents, extracts ICSR fields, codes medical terminology, drafts clinical narratives, and packages cases for E2B(R3) submission. The first production boundary covers non-serious spontaneous cases from email and portal channels, with autonomous end-to-end processing gated by a confidence threshold. Serious/fatal cases, clinical trial sources, and literature monitoring remain human-processed in the first release, with AI providing pre-population assistance.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ on containerized microservices | Mature NLP/ML ecosystem; validated in GxP environments with appropriate qualification |
| **Model access** | Anthropic Claude API (structured outputs) | Long context handles multi-page source documents; strong structured JSON output for field extraction |
| **Orchestration runtime** | LangGraph | Graph-based state machine maps naturally to ICSR pipeline stages; built-in human-in-the-loop support |
| **Core connectors** | Oracle Argus REST API, MedDRA file dictionary, ESTRI/EV gateway SDK | Safety database writeback, medical coding, and regulatory submission are non-negotiable integration points |
| **Evaluation / tracing** | LangSmith + GxP audit logger | Full trace of every agent decision for regulatory inspection; latency tracking for deadline SLA |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Intake and extraction pipeline on email/portal sources | Document parser, OCR adapter, extraction agent with E2B(R3) field schema, MedDRA RAG index |
| 2 | Triage, coding, and narrative automation | Triage classifier, MedDRA coding agent, narrative drafter, confidence scoring, human escalation routing |
| 3 | Safety database integration and validation | Argus API adapter, deterministic validation engine, duplicate detection, E2B(R3) packager |
| 4 | Pilot with autonomous processing on non-serious cases | Shadow mode → assisted mode → autonomous mode rollout, evaluation harness, SLA monitoring |

## Core Contracts

### State And Output Schemas

The ICSR extraction output conforms to the ICH E2B(R3) data element structure. The pipeline state tracks each case through processing stages with confidence scores at every step.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date

class Seriousness(str, Enum):
    NON_SERIOUS = "non_serious"
    SERIOUS = "serious"
    FATAL = "fatal"

class MedDRACoding(BaseModel):
    verbatim: str
    preferred_term: str
    pt_code: str
    llt_code: str | None = None
    soc: str
    confidence: float = Field(ge=0.0, le=1.0)

class ICSRExtraction(BaseModel):
    """Core ICSR fields aligned to ICH E2B(R3) data elements."""
    case_id: str | None = None
    receipt_date: date
    sender_type: str  # "healthcare_professional", "consumer", "literature"
    patient_age: str | None = None
    patient_sex: str | None = None
    suspect_drug: str
    indication: str | None = None
    adverse_events: list[MedDRACoding]
    event_onset_date: date | None = None
    outcome: str | None = None
    seriousness: Seriousness
    seriousness_criteria: list[str] = []
    reporter_name: str | None = None
    reporter_qualification: str | None = None
    narrative_draft: str | None = None
    overall_confidence: float = Field(ge=0.0, le=1.0)
```

### Tool Interface Pattern

Each agent in the pipeline exposes a narrow tool interface. The MedDRA coding tool demonstrates the pattern: lookup with confidence scoring and fallback.

```python
from langchain_core.tools import tool

@tool
def code_adverse_event(verbatim: str) -> dict:
    """Look up MedDRA coding for an adverse event verbatim term.
    
    Returns the best-match Preferred Term with confidence score.
    Falls back to human review queue if confidence < 0.85.
    """
    # Vector similarity search against MedDRA dictionary index
    results = meddra_index.similarity_search_with_score(verbatim, k=5)
    
    if not results:
        return {"status": "no_match", "requires_human": True}
    
    best_match, score = results[0]
    return {
        "preferred_term": best_match.metadata["pt_name"],
        "pt_code": best_match.metadata["pt_code"],
        "llt_code": best_match.metadata.get("llt_code"),
        "soc": best_match.metadata["soc_name"],
        "confidence": score,
        "requires_human": score < 0.85,
    }
```

## Orchestration Outline

The pipeline is a directed graph where each node represents an agent or validation step. Cases flow through extraction, coding, narrative drafting, and validation, with conditional edges routing low-confidence cases to human review.

```python
from langgraph.graph import StateGraph, END

# Define the ICSR processing graph
workflow = StateGraph(ICSRState)

workflow.add_node("intake", intake_agent)
workflow.add_node("triage", triage_agent)
workflow.add_node("extract", extraction_agent)
workflow.add_node("code_meddra", meddra_coding_agent)
workflow.add_node("detect_duplicates", duplicate_detector)
workflow.add_node("draft_narrative", narrative_agent)
workflow.add_node("validate", validation_engine)
workflow.add_node("package_e2b", e2b_packager)
workflow.add_node("human_review", human_review_queue)

workflow.set_entry_point("intake")
workflow.add_edge("intake", "triage")

# Triage routes based on seriousness and confidence
workflow.add_conditional_edges("triage", route_by_seriousness, {
    "autonomous": "extract",
    "human_required": "human_review",
})

workflow.add_edge("extract", "code_meddra")
workflow.add_edge("code_meddra", "detect_duplicates")
workflow.add_edge("detect_duplicates", "draft_narrative")
workflow.add_edge("draft_narrative", "validate")

# Validation gates autonomous submission
workflow.add_conditional_edges("validate", check_validation, {
    "pass": "package_e2b",
    "fail": "human_review",
})

workflow.add_edge("package_e2b", END)
workflow.add_edge("human_review", END)
```

## Prompt And Guardrail Pattern

The extraction agent uses a structured system prompt that constrains output to the E2B(R3) field schema and explicitly forbids inference beyond source text.

```text
You are a pharmacovigilance data extraction specialist. Your task is to extract
Individual Case Safety Report (ICSR) fields from the provided source document.

RULES:
- Extract ONLY information explicitly stated in the source document.
- Never infer, assume, or hallucinate clinical details not present in the text.
- If a field cannot be determined from the source, return null for that field.
- For adverse event terms, use the reporter's exact verbatim wording.
- For dates, normalize to ISO 8601 format. If only partial dates exist, use
  the most specific available (year-month if day unknown).
- Assign a confidence score (0.0-1.0) for each extracted field.
- If overall confidence is below 0.70, set requires_human_review to true.

OUTPUT: Return a JSON object conforming to the ICSRExtraction schema.
Do not include any text outside the JSON response.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Safety database writeback | Argus REST API adapter with field mapping from ICSRExtraction to Argus case schema | Map E2B(R3) field IDs to Argus database fields; handle versioning for follow-up/amendment cases |
| MedDRA dictionary service | Vector index rebuilt on each MedDRA release (biannual); exposed as internal API | Index both PT and LLT levels; include synonyms from MedDRA SMQs for broader matching |
| Regulatory submission gateway | E2B(R3) XML generator conforming to ICH message specification; route to ESTRI (FDA) or EV Web Services (EMA) | Validate XML against published XSD before submission; handle acknowledgment parsing for confirmation |
| Email intake | IMAP listener with attachment extraction, OCR for scanned documents, language detection | Support multi-language intake; route non-English to translation step before extraction |
| Audit trail | Immutable log of every agent decision, confidence score, and human override | GxP requirement: 21 CFR Part 11 compliant electronic records with timestamp, user, and reason for change |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Field extraction accuracy | F1 score on held-out set of 500 manually-processed ICSRs; per-field and overall | Overall F1 > 0.85; no critical field (suspect drug, seriousness, event term) below 0.90 |
| MedDRA coding accuracy | Agreement rate with expert-coded gold standard; stratified by term frequency | > 90% agreement at PT level for terms appearing > 10x in training set; > 80% for rare terms |
| Seriousness classification | Sensitivity and specificity on labeled test set (serious vs non-serious) | Sensitivity for serious cases > 0.98 (must not miss serious cases); specificity > 0.90 |
| Narrative quality | Blinded pharmacovigilance specialist scoring on 5-point scale (accuracy, completeness, style) | Mean score > 4.0/5.0; zero instances of hallucinated clinical information |
| End-to-end processing time | Wall-clock time from intake to submission-ready package | < 30 minutes for 95th percentile of non-serious cases |
| Regulatory compliance | Submission acceptance rate at FDA FAERS / EMA EudraVigilance | > 99% acceptance (rejected only for gateway technical issues, not data quality) |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Shadow mode (4 weeks): AI processes cases in parallel, human processes normally, compare outputs. Assisted mode (8 weeks): AI pre-populates, human reviews and corrects. Autonomous mode: non-serious cases with confidence > 0.85 process without human touch |
| **Fallback path** | Circuit breaker on validation failure rate: if > 5% of cases fail validation in a 24-hour window, revert to assisted mode. Human PV specialists continue to have full access to manual workflow at all times |
| **Observability** | Dashboard tracking: cases in pipeline, average processing time, confidence distribution, human escalation rate, deadline compliance (7-day and 15-day), validation failure reasons |
| **Operations ownership** | Pharmacovigilance operations team owns case quality; AI/ML engineering owns model performance and pipeline availability; regulatory affairs owns submission gateway compliance |
