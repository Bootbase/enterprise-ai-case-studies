---
layout: use-case-detail
title: "Solution Design — UC-509: Clinical Trial Patient Matching and Recruitment"
uc_id: "UC-509"
uc_title: "Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "Industry-Specific"
status: "detailed"
slug: "UC-509-clinical-trial-patient-matching"
permalink: /use-cases/UC-509-clinical-trial-patient-matching/solution-design/
---

# UC-509: Autonomous Clinical Trial Patient Matching and Recruitment — Solution Design

## Solution Overview

This solution deploys a multi-agent AI system that autonomously orchestrates clinical trial patient matching — from parsing complex eligibility criteria in trial protocols to scanning structured and unstructured EHR data, scoring patient-trial matches with explainable reasoning, and monitoring enrollment velocity across sites.

The architecture follows a plan-and-execute multi-agent pattern inspired by production systems like IQVIA's orchestrator agents and research frameworks like MAKAR (Multi-Agent Knowledge Augmentation and Reasoning). A central Orchestrator Agent coordinates four specialized worker agents: a Protocol Criteria Agent that decomposes eligibility requirements into machine-executable rules, a Patient Matching Agent that uses RAG over EHR data with medical Chain-of-Thought reasoning, a Site Optimization Agent that predicts enrollment performance using historical data, and an Enrollment Monitor Agent that tracks recruitment velocity and triggers corrective actions.

The system integrates with EHR platforms (Epic, Oracle Health/Cerner) via HL7 FHIR R4 APIs, retrieves trial definitions from ClinicalTrials.gov, and feeds results into Clinical Trial Management Systems (Medidata Rave, Veeva Vault). LangGraph provides graph-based orchestration with checkpointing and human-in-the-loop gates — critical for regulatory compliance and clinical safety.

---

## Architecture

### Architecture Diagram

```
                          +-----------------------------+
                          |      Trial Protocol (PDF)   |
                          |  ClinicalTrials.gov (FHIR)  |
                          +-------------+---------------+
                                        |
                                        v
                          +-------------+---------------+
                          |  Protocol Criteria Agent     |
                          |  (LLM: criteria extraction   |
                          |   + decomposition)           |
                          +-------------+---------------+
                                        |
                       structured eligibility criteria (JSON)
                                        |
                                        v
+------------------+      +-------------+---------------+      +------------------+
|  EHR Systems     |----->|  Patient Matching Agent      |----->|  Match Results   |
|  (Epic, Cerner   |FHIR  |  (RAG + CoT reasoning over  |      |  (scored, ranked |
|   via FHIR R4)   |<---->|   structured + unstructured  |      |   with explain.) |
+------------------+      |   patient data)              |      +--------+---------+
                          +-------------+---------------+               |
                                        ^                               |
                                        |                               v
                          +-------------+---------------+      +--------+---------+
                          |  Orchestrator Agent          |<-----|  HITL Review     |
                          |  (LangGraph StateGraph)      |      |  (edge cases,    |
                          |  - routes between agents     |      |   <threshold)    |
                          |  - manages shared state      |      +------------------+
                          |  - enforces HITL gates       |
                          +---+-------------------+-----+
                              |                   |
                              v                   v
                  +---------------+---+   +-----------+---------+
                  | Site Optimization |   | Enrollment Monitor  |
                  | Agent             |   | Agent               |
                  | (predictive site  |   | (real-time velocity |
                  |  scoring, diversity|   |  tracking, alerts,  |
                  |  analytics)       |   |  corrective actions)|
                  +-------------------+   +---------------------+
                              |                   |
                              v                   v
                     +--------+---------+  +------+----------+
                     | CTMS Integration |  | Dashboards &    |
                     | (Medidata, Veeva)|  | Alerting        |
                     +------------------+  +-----------------+
```

### Component Overview

| # | Component | Technology / Service | Role |
|---|-----------|---------------------|------|
| 1 | Orchestrator Agent | LangGraph StateGraph | Routes tasks between specialized agents, manages shared state, enforces human-in-the-loop gates |
| 2 | Protocol Criteria Agent | Azure OpenAI GPT-4o | Parses trial protocols (PDF/FHIR), extracts and decomposes I/E criteria into structured JSON rules |
| 3 | Patient Matching Agent | Azure OpenAI GPT-4o + Azure AI Search | RAG over patient EHR data with medical Chain-of-Thought reasoning for criterion-level eligibility |
| 4 | Site Optimization Agent | Azure OpenAI GPT-4o + historical CTMS data | Predictive site scoring, feasibility assessment, diversity gap analysis |
| 5 | Enrollment Monitor Agent | Azure OpenAI GPT-4o + real-time CTMS feeds | Continuous velocity tracking, anomaly detection, corrective action recommendations |
| 6 | EHR Data Layer | FHIR R4 APIs (Epic, Cerner) + fhir.resources | Structured patient data retrieval and normalization |
| 7 | Unstructured NLP Pipeline | Azure AI Document Intelligence + embeddings | Clinical note extraction, chunking, embedding for vector search |
| 8 | Vector Store | Azure AI Search (hybrid) | Combines BM25 lexical search with vector semantic search |
| 9 | CTMS Integration | REST APIs (Medidata Rave, Veeva Vault) | Bidirectional sync of enrollment data and match results |
| 10 | Audit & Compliance Layer | Azure Cosmos DB + Application Insights | Immutable decision logs, reasoning traces, regulatory audit trail |

---

## Data Flow

```
1. [Trigger]    → New trial protocol uploaded OR new patient data arrives via FHIR
2. [Parse]      → Protocol Criteria Agent extracts I/E criteria → structured JSON rules
3. [Retrieve]   → Patient Matching Agent queries FHIR APIs for structured data
                   + vector search over embedded clinical notes (RAG)
4. [Reason]     → LLM evaluates each patient against each criterion using medical
                   Chain-of-Thought → produces criterion-level verdicts + confidence scores
5. [Score]      → Patients ranked by composite match score (0-1); below-threshold
                   matches flagged for human review
6. [Optimize]   → Site Optimization Agent scores sites by predicted enrollment
                   velocity, patient proximity, and diversity targets
7. [Monitor]    → Enrollment Monitor Agent tracks velocity vs. plan; triggers
                   alerts when sites fall behind; recommends corrective actions
8. [HITL Gate]  → Low-confidence matches and corrective actions routed to clinical
                   team for approval before execution
9. [Sync]       → Approved matches and actions pushed to CTMS; audit log written
```

---

## Agent Pattern

| Aspect | Choice |
|--------|--------|
| **Pattern** | Multi-Agent Orchestrator-Worker with RAG |
| **Orchestration** | Graph-based (LangGraph StateGraph with conditional edges) |
| **Human-in-the-Loop** | Confidence-gated escalation (matches < 0.85 score routed to clinical reviewer) |
| **State Management** | Persistent checkpointed state (LangGraph checkpointer with PostgreSQL backend) |
| **Autonomy Level** | Semi-Autonomous (autonomous matching and monitoring; human approval for patient outreach and corrective actions) |

### Why This Pattern?

**Multi-agent orchestrator-worker** was chosen because clinical trial matching requires four distinct capabilities that benefit from specialization:

1. **Protocol parsing** requires document understanding and medical terminology extraction — a different skill than patient matching.
2. **Patient matching** requires RAG over heterogeneous EHR data with clinical reasoning — the most LLM-intensive step.
3. **Site optimization** requires statistical modeling over historical enrollment data — more analytical than generative.
4. **Enrollment monitoring** requires continuous time-series analysis with alerting — an operational pattern.

This mirrors production architectures at IQVIA and the research architecture of MAKAR. ClinicalAgent research demonstrated that multi-agent architectures outperform monolithic LLM approaches on clinical trial tasks.

---

## Integration Points

| System | Integration Method | Direction | Purpose |
|--------|-------------------|-----------|---------|
| Epic EHR | FHIR R4 REST API (SMART on FHIR) | Read | Patient demographics, conditions, observations, medications, clinical notes |
| Oracle Health (Cerner) | FHIR R4 REST API (Ignite) | Read | Same as Epic; Cerner-specific resource profiles |
| ClinicalTrials.gov | FHIR R4 API + REST API v2 | Read | Trial protocol retrieval, eligibility criteria, study status |
| Medidata Rave CTMS | REST API | Bidirectional | Read enrollment targets; write match results and enrollment status |
| Veeva Vault CTMS | REST API | Bidirectional | Same as Medidata; Veeva-specific data model |
| Azure AI Document Intelligence | REST API | Read | Extract text from PDF protocols, lab reports, imaging summaries |
| Azure AI Search | REST API + SDK | Bidirectional | Index/query embedded patient records and trial criteria |
| Azure Cosmos DB | SDK | Write | Immutable audit logs, decision reasoning traces |

---

## Tools & Frameworks

### AI / ML Stack

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| **LLM Provider** | Azure OpenAI Service | HIPAA BAA available; data residency controls; private endpoints; enterprise SLA |
| **Model (Reasoning)** | GPT-4o (2024-11-20) | Best balance of clinical reasoning accuracy and cost; supports structured output (JSON mode); 128K context |
| **Model (Extraction)** | GPT-4o-mini | Lower cost for high-volume criteria extraction and FHIR data normalization |
| **Agent Framework** | LangGraph (v1.0+) | Graph-based orchestration with checkpointing, human-in-the-loop gates, conditional routing |
| **Vector Database** | Azure AI Search (hybrid) | Combines BM25 lexical search (critical for medical codes like ICD-10, LOINC) with vector semantic search |
| **Embedding Model** | text-embedding-3-large (3072d) | High-dimensional embeddings capture clinical semantic nuances |
| **Document Intelligence** | Azure AI Document Intelligence | Extracts structured data from PDF protocols and scanned lab reports |

### Infrastructure Stack

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| **Compute** | Azure Kubernetes Service (AKS) | Existing platform in regulated environments; pod-level network policies for HIPAA |
| **State Store** | Azure Database for PostgreSQL | LangGraph checkpointer backend; transactional consistency |
| **Audit Store** | Azure Cosmos DB | Immutable append-only logs for regulatory audit trails |
| **Monitoring** | Azure Application Insights | End-to-end tracing of agent decisions; LLM call latency metrics |
| **Secret Management** | Azure Key Vault | FHIR client credentials, API keys, connection strings |

---

## Security & Compliance

| Concern | Approach |
|---------|----------|
| **Authentication** | SMART on FHIR (OAuth 2.0) for EHR access; Azure Managed Identity for inter-service communication |
| **Authorization** | FHIR scopes limit patient data access to specific resource types; RBAC on Azure resources |
| **Data at Rest** | AES-256 encryption with customer-managed keys (CMK) in Azure Key Vault |
| **Data in Transit** | TLS 1.3 for all FHIR API calls; Azure Private Endpoints for AI Search and OpenAI |
| **PII Handling** | De-identification layer before LLM processing (Safe Harbor method); patient identifiers replaced with study-specific pseudonyms |
| **Audit Trail** | Every LLM call logged with input hash, output, model version, temperature, reasoning trace; 21 CFR Part 11 compliant |
| **Model Governance** | Azure OpenAI content filters enabled; custom prompt guardrails; model version pinning |
| **Regulatory** | System designed for ICH-GCP compliance; audit trails support FDA inspection readiness |

---

## Scalability & Performance

| Dimension | Approach |
|-----------|----------|
| **Throughput** | 500 patient evaluations/hour per trial; 50 concurrent active trials across 200 sites; burst to 2,000 evaluations/hour via horizontal pod autoscaling |
| **Latency Target** | Single patient-trial match: p50 < 15s, p95 < 45s, p99 < 90s; batch cohort scan: < 4 hours for 100K patient records |
| **Scaling Strategy** | Horizontal pod autoscaling on AKS based on queue depth; separate scaling groups for each agent type |
| **Rate Limits** | Azure OpenAI provisioned throughput (PTU) for predictable latency; queue-based backpressure with Service Bus |
| **Caching** | Protocol criteria cached after parsing; FHIR patient snapshots cached for 24 hours; embedding vectors cached in AI Search index |

---

## Cost Estimate

| Component | Unit Cost | Monthly Estimate (50 active trials) |
|-----------|----------|--------------------------------------|
| **Azure OpenAI GPT-4o (PTU)** | ~$60/hr per PTU | $8,600 (3 PTUs, 60% avg utilization) |
| **Azure OpenAI GPT-4o-mini** | $0.15/1M input tokens | $450 (high-volume extraction tasks) |
| **Azure AI Search (S1)** | $250/month per unit | $500 (2 search units for hybrid index) |
| **text-embedding-3-large** | $0.13/1M tokens | $260 (initial indexing + incremental updates) |
| **AKS (D4s_v5 nodes)** | ~$140/month per node | $1,120 (8 nodes across agent pools) |
| **Azure Database for PostgreSQL** | ~$200/month (GP, 4 vCores) | $200 |
| **Azure Cosmos DB** | ~$0.25/RU/s/month | $400 (audit log writes at ~1,600 RU/s avg) |
| **Azure Document Intelligence** | $1.50/page (custom) | $300 (200 protocols/month avg) |
| **Total** | | **~$11,830/month** |

*Compared to: $500K-$2M/month in manual recruitment costs for a Phase III trial portfolio. Platform ROI typically achieved within the first 1-2 trials.*

