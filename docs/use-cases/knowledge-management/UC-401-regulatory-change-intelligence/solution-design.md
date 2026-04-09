---
layout: use-case-detail
title: "Solution Design — Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
uc_id: "UC-401"
uc_title: "Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "Knowledge Management"
status: "detailed"
slug: "UC-401-regulatory-change-intelligence"
permalink: /use-cases/UC-401-regulatory-change-intelligence/solution-design/
---

## Solution Overview

The right architecture for regulatory change management is a multi-agent pipeline with event-driven coordination — not a single monolithic agent. The regulatory change lifecycle touches too many distinct cognitive tasks — source monitoring, document classification, obligation extraction, applicability assessment, gap analysis, policy drafting, workflow orchestration, and audit evidence assembly — for one agent to handle reliably. Production systems from CUBE (RegPlatform, 10,000+ issuing bodies, 750 jurisdictions) and AscentAI (RLM Platform, 1,800 hours → 2.5 minutes for MiFID II obligation extraction at ING/CommBank) demonstrate that each stage requires specialized processing: CUBE's proprietary RegLM is fine-tuned specifically for regulatory text classification, entity extraction, citation extraction, and obligation identification — tasks where general-purpose LLMs hallucinate at unacceptable rates on dense legal language.

The recommended design pairs LLM-powered agents for tasks that defied automation for decades — interpreting regulatory language, extracting discrete obligations from multi-hundred-page regulations, assessing applicability against a firm's specific regulatory perimeter, and drafting policy updates — with deterministic services for everything that must be fast, auditable, and reproducible: regulatory feed ingestion, obligation register updates, workflow routing, deadline calculation, and audit evidence assembly. The key insight from 2025 academic research on regulatory NLP is that combining LLMs with knowledge graphs achieves 93% precision in obligation filtering and 99%+ accuracy in classifying obligation types — significantly better than either approach alone.

The reference integration seam targets enterprise GRC platforms (ServiceNow GRC, RSA Archer, MetricStream) via REST API, because the agents augment the existing compliance infrastructure rather than replacing it. The same pattern ports to other GRC platforms by swapping the connector layer.

## Architecture

### Architecture Diagram

```
Regulatory Sources (Regulator feeds / RSS / APIs / CUBE / Wolters Kluwer)
    ↓
Horizon Scanner Agent (Feed monitor + document classifier)
    ↓
Applicable? → [Not Applicable: Archive]
    ↓
    ↓ Potentially Applicable
    ↓
Obligation Extraction Agent (Azure OpenAI structured extraction + knowledge graph)
    ↓
Applicability Assessment Agent (Map obligations to firm's regulatory perimeter)
    ↓
Confidence Level? → [Low Confidence / Ambiguous: Human Review Queue]
    ↓
    ↓ High Confidence: Applicable
    ↓
Gap Analysis Agent (Compare against obligation register + control framework)
    ↓
Gaps Found? → [No Gaps: Confirm Compliance & Log assessment]
    ↓
    ↓ Yes: Policy/Control Gaps
    ↓
Policy Drafting Agent (Generate redline updates to affected policies)
    ↓
Workflow Orchestration Agent (Route through approval chain)
    ↓
Approval Workflow (Legal → Business Line → Compliance Committee)
    ↓
Policy Activation (Updated policies published + training triggered)
    ↓
Audit Evidence Agent (Continuous audit trail assembly)
    ↓
Examination-Ready Evidence Pack (Change → Assessment → Approval → Policy → Training)
```

### Component Overview

| # | Component | Technology / Service | Role |
|---|-----------|----------------------|------|
| 1 | Horizon Scanner Agent | Regulatory feed APIs + LLM classifier | Monitors regulatory publication sources 24/7, classifies incoming documents by type, jurisdiction, and topic, and filters for potential applicability to the firm's licensed activities. |
| 2 | Obligation Extraction Agent | Azure OpenAI GPT-4o structured outputs + knowledge graph | Parses regulatory text into discrete, machine-readable obligations with deontic classification (must/shall/may), addressees, predicates, and conditions. Academic benchmarks: 93% precision in obligation filtering, 99%+ accuracy in obligation type classification. |
| 3 | Applicability Assessment Agent | Azure OpenAI GPT-4o + RAG over regulatory perimeter | Evaluates extracted obligations against the firm's regulatory perimeter (licensed activities, entity types, jurisdictions, product lines) to determine which obligations apply. AscentAI demonstrated this mapping from 1,800 hours to 2.5 minutes for MiFID II. |
| 4 | Gap Analysis Agent | Deterministic comparison + LLM reasoning | Compares new/changed obligations against the firm's existing obligation register and control framework to identify gaps — obligations that are not yet covered by existing policies and controls. |
| 5 | Policy Drafting Agent | Azure OpenAI GPT-4o | Generates redline policy updates: proposed insertions, modifications, and deletions to existing policy documents, with change justification linked to the triggering regulation. |
| 6 | Workflow Orchestration Agent | LangGraph StateGraph + GRC API | Routes assessments and policy drafts through configurable approval chains, tracks deadlines, escalates overdue items, and manages the end-to-end change implementation lifecycle. |
| 7 | Audit Evidence Agent | Deterministic assembly + Azure Blob Storage | Continuously assembles the audit trail: linking each regulatory change to its assessment, policy update, approval record, training completion, and attestation — so the firm is examination-ready at all times. |
| 8 | Regulatory Knowledge Base | Azure AI Search + Azure Blob Storage | Semantic search over the full regulatory corpus, obligation register, control framework, and historical assessments. Provides RAG grounding for all LLM agents. |
| 9 | GRC Connector | REST API client | Reads from and writes to the enterprise GRC platform (ServiceNow GRC, Archer, MetricStream) for obligation register, control framework, and workflow management. |

## Data Flow

### AI Data Flow

| Stage | What enters the LLM | What comes out | What happens next |
|-------|---------------------|----------------|-------------------|
| Document classification | Raw regulatory publication (title, summary, source, jurisdiction) | Classification labels: document type (legislation/guidance/enforcement/consultation), jurisdiction, topic areas, urgency level, confidence score | Router dispatches applicable documents to obligation extraction. Non-applicable documents archived with classification rationale. |
| Obligation extraction | Regulatory text chunks (2,000-4,000 tokens each), extraction schema, few-shot examples of deontic statements | Structured `Obligation` JSON: obligation text, deontic type (must/shall/may/must-not), addressee, predicate, conditions, effective date, cross-references, confidence | Obligations stored in staging register; forwarded to applicability assessment. |
| Applicability assessment | Extracted obligations + firm's regulatory perimeter definition (licensed activities, entity types, jurisdictions, product lines) + similar past assessments from RAG | `ApplicabilityAssessment` JSON: applicable (yes/no/partial), reasoning, affected entities, affected jurisdictions, confidence score | High-confidence applicable obligations forwarded to gap analysis. Low-confidence routed to human review. |
| Gap analysis | Applicable obligations + existing obligation register entries + current policy and control descriptions from GRC | `GapAssessment` JSON: obligation-to-control mapping, identified gaps, gap severity, recommended actions | Gaps trigger policy drafting agent. No-gap assessments logged as compliance confirmation. |
| Policy drafting | Gap details + current policy document text + regulatory change context + firm's policy style guide | `PolicyRedline` JSON: proposed insertions, modifications, deletions, change justification, regulatory citation | Redlines submitted to approval workflow. Compliance officer reviews before activation. |
| Horizon trend analysis | Batch of recent consultation papers, enforcement trends, regulatory speeches | `TrendReport`: emerging regulatory themes, predicted rulemaking directions, recommended preparedness actions | Quarterly briefing for CCO and Board Risk Committee. |

## LLM Role

| Step | AI Needed? | LLM Role | Why AI Fits |
|------|------------|----------|-------------|
| Source monitoring | No | None | Regulatory feeds are structured RSS/API endpoints; monitoring is a polling/webhook pattern. |
| Document classification | Yes | Classify regulatory text by type, jurisdiction, topic, urgency | Regulatory publications vary in format, language, and structure across jurisdictions. Rules-based classification fails on the diversity of 10,000+ issuing bodies. |
| Obligation extraction | Yes, with knowledge graph grounding | Extract deontic statements, parse obligation structure (addressee, predicate, conditions) | Dense legal language with nested cross-references and conditional clauses. This is the task that consumed 1,800 hours manually at ING/CommBank. LLM + knowledge graph achieves 93% precision. |
| Applicability assessment | Yes, RAG-grounded | Reason about whether obligations apply given the firm's regulatory perimeter | Requires contextual reasoning about entity types, licensed activities, and jurisdictional scope — not a simple lookup. |
| Gap analysis | Hybrid | LLM reasons about semantic similarity between obligations and controls; deterministic matching handles exact matches | Most obligation-to-control mapping involves semantic similarity (not exact match), but structural comparisons are deterministic. |
| Policy drafting | Yes | Generate redline text respecting the firm's policy style and regulatory citation conventions | Policy language must be precise, consistent, and traceable to the regulatory change — a generative task suited to LLM capabilities. |
| Workflow routing | No | None | Approval chains are configurable business rules; routing is deterministic. |
| Deadline calculation | No | None | Effective dates and implementation deadlines are extracted as structured data; calculation is arithmetic. |
| Audit trail assembly | No | None | Evidence linking is a deterministic join across assessment, approval, policy, and training records. |
| Trend analysis / horizon scanning | Yes | Synthesize patterns across consultation papers, enforcement actions, regulatory speeches | Pattern recognition across diverse unstructured sources to identify emerging themes. |

## Agent Pattern

| Aspect | Choice |
|--------|--------|
| **Pattern** | Multi-agent pipeline with event-driven coordination |
| **Orchestration** | Event-driven: agents triggered by regulatory feed updates, assessment completions, approval decisions; LangGraph StateGraph for intra-pipeline coordination |
| **Human-in-the-Loop** | Confidence-based escalation: low-confidence applicability assessments, all policy redlines before activation, high-impact regulatory changes always require human review |
| **State Management** | GRC platform is the system of record for obligations and controls; LangGraph checkpointing for in-flight pipeline state; Azure Blob Storage for regulatory document corpus |
| **Autonomy Level** | Semi-autonomous: routine monitoring, extraction, and classification are fully automated; applicability assessment and policy changes require human approval gates |

## Tools & Frameworks

### AI / ML Stack

| Component | Technology | Why Chosen |
|-----------|------------|------------|
| **LLM Provider** | Azure OpenAI | Enterprise compliance (data residency, SLAs, content filtering), private endpoint support, integration with Azure identity. |
| **Model (extraction/assessment)** | GPT-4o | Strong reasoning on dense legal text, structured output support, 128K context window for long regulatory documents. |
| **Model (classification/triage)** | GPT-4o-mini | Cost-effective for high-volume classification tasks where full reasoning is not required. |
| **Agent Framework** | LangGraph (Python) | StateGraph for typed pipeline state, conditional routing, human-in-the-loop interrupts, and checkpointing. Production-proven at C.H. Robinson for complex classification. |
| **Vector Database** | Azure AI Search | Managed hybrid search (keyword + semantic) over regulatory corpus; supports multi-language search across 80+ languages matching CUBE's coverage. |
| **Embedding Model** | text-embedding-3-large (baseline); legal-domain-optimized alternative | text-embedding-3-large is a solid baseline. Legal-domain-specific models achieve +25% over baseline on legal benchmarks. |
| **Knowledge Graph** | Neo4j or Azure Cosmos DB for Apache Gremlin | Represent regulation-obligation-control-policy relationships as a graph for traversal-based gap analysis. |
| **Structured Extraction** | Azure OpenAI structured outputs (JSON mode) | Enforces JSON schema compliance for all extraction and assessment agents. |

### Infrastructure Stack

| Component | Technology | Why Chosen |
|-----------|------------|------------|
| **Compute** | AKS or Azure Container Apps | Horizontal scaling for parallel obligation extraction across multi-hundred-page regulations. |
| **Message Queue** | Azure Service Bus | Event-driven trigger for agents; handles bursty regulatory publication schedules (end-of-quarter surges). |
| **Storage** | Azure Blob Storage + Azure SQL | Blob for regulatory document corpus and evidence artifacts; SQL for obligation register and assessment records. |
| **Monitoring** | Application Insights / OpenTelemetry | Trace agent decisions, confidence scores, escalation rates, and processing latency. |

## Scalability & Performance

| Dimension | Approach |
|-----------|----------|
| **Throughput** | Process 100-500 new regulatory publications per day across all monitored jurisdictions. Obligation extraction at 50-200 obligations/hour per agent instance, scaling horizontally via queue-based fan-out. |
| **Latency Target** | Document classification: < 10 seconds. Obligation extraction from a 100-page regulation: < 5 minutes (parallelized by section). Applicability assessment: < 30 seconds per obligation. End-to-end detection-to-assessment: < 24 hours. |
| **Scaling Strategy** | Horizontal pod autoscaling per agent type, triggered by Service Bus queue depth. Peak volumes during major regulatory overhauls (Basel III.1, EU AI Act rollout) absorbed by adding extraction worker replicas. |
| **Rate Limits** | Azure OpenAI provisioned throughput for extraction agent (highest token consumption); standard deployment for classification and assessment agents. |
| **Caching** | Cache regulatory perimeter definitions, control framework snapshots, and frequently-referenced regulatory cross-references. Never cache confidential gap assessments across sessions. |

## Cost Estimate

| Component | Unit Cost | Monthly Estimate |
|-----------|-----------|------------------|
| **LLM API calls** (extraction, classification, assessment, drafting) | ~$0.03-0.15 per obligation processed | $5k-$12k estimated |
| **Regulatory feed subscriptions** (CUBE, Wolters Kluwer, or equivalent) | Commercial licensing | $30k-$80k estimated (existing cost, not incremental) |
| **Vector DB / AI Search** (regulatory corpus indexing) | Azure AI Search S1/S2 | $1k-$3k estimated |
| **Compute** (AKS workers, API services) | Container runtime | $2k-$5k estimated |
| **Knowledge Graph** (Neo4j or Cosmos DB Gremlin) | Managed service | $1k-$3k estimated |
| **Message queue + storage + monitoring** | Service Bus, Blob, App Insights | $1k-$2k estimated |
| **Total (incremental AI costs)** | | **$10k-$25k estimated** |

For comparison, a compliance team of 8-15 analysts dedicated to regulatory change management at a mid-size financial institution represents $1M-$2.5M annually in fully-loaded compensation. The AI system does not replace the team but enables them to handle 3-5x more regulatory changes with the same headcount — or maintain coverage as regulatory volume continues its 23% YoY growth without proportional headcount growth.
