# UC-042: Autonomous RFP and Proposal Response Generation — Solution Design

## Solution Overview

This solution uses a multi-agent agentic RAG architecture to autonomously handle the end-to-end RFP response lifecycle. An orchestrator agent coordinates a team of specialized agents — each responsible for a distinct phase: document parsing, question classification, knowledge retrieval, draft generation, compliance checking, and quality review. The architecture is modeled as a stateful directed graph (using LangGraph) where each node represents an agent or decision point, enabling conditional branching, iterative refinement loops, and human-in-the-loop interrupts at configurable gates.

The core AI insight is that RFP response is fundamentally a grounded knowledge synthesis problem, not a creative writing problem. Every generated answer must trace back to a verified source document. The system uses Azure AI Search with hybrid retrieval (vector + keyword + semantic reranking) to surface the most relevant content from the organization's proposal library, product documentation, and compliance certifications. GPT-4o then synthesizes retrieval results into responses calibrated to each RFP's tone, format, and compliance requirements — with strict source attribution and confidence scoring to prevent hallucination.

This approach mirrors the architecture of production platforms like Thalamus AI (20+ specialized agents covering every RFP stage) and DeepRFP (autonomous agents for analysis, drafting, and compliance). The multi-agent pattern was chosen over a single monolithic agent because RFP processing involves distinct, independently testable subtasks that benefit from specialized prompts, different temperature settings, and separate evaluation criteria.

---

## Architecture

### Architecture Diagram

```
                                 ┌─────────────────────────┐
                                 │     RFP Document         │
                                 │  (PDF / DOCX / XLSX)     │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                               ┌──────────────────────────┐
                               │   Document Intelligence   │
                               │   (Azure AI Doc Intel)    │
                               └────────────┬─────────────┘
                                            │ Markdown + tables
                                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        LangGraph Orchestrator                            │
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │ Question  │───▸│ Retrieval│───▸│  Draft   │───▸│   Compliance     │   │
│  │ Classifier│    │  Agent   │    │ Generator│    │   Checker        │   │
│  └──────────┘    └──────────┘    └──────────┘    └────────┬─────────┘   │
│       │               │               │                    │             │
│       │               ▼               │                    ▼             │
│       │         ┌──────────┐          │           ┌──────────────────┐  │
│       │         │ Azure AI │          │           │  Quality Review  │  │
│       │         │  Search  │          │           │     Agent        │  │
│       │         │ (Hybrid) │          │           └────────┬─────────┘  │
│       │         └──────────┘          │                    │             │
│       │                               │                    ▼             │
│       │                               │           ┌──────────────────┐  │
│       │                               │           │  Human Review    │  │
│       │                               │           │  Gate (optional) │  │
│       │                               │           └────────┬─────────┘  │
│       ▼                               ▼                    ▼             │
│  ┌──────────┐                  ┌──────────────┐  ┌──────────────────┐  │
│  │ Bid/No-  │                  │ Gap Detector │  │  Final Assembly  │  │
│  │ Bid Score│                  │ + SME Router │  │  + Export        │  │
│  └──────────┘                  └──────────────┘  └──────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
         │                    │                              │
         ▼                    ▼                              ▼
   ┌──────────┐       ┌──────────────┐             ┌──────────────────┐
   │ Salesforce│       │ SharePoint / │             │ Submission-Ready │
   │  (CRM)   │       │ Teams (SMEs) │             │ Document Package │
   └──────────┘       └──────────────┘             └──────────────────┘
```

### Component Overview

| # | Component | Technology / Service | Role |
|---|-----------|---------------------|------|
| 1 | Document Ingestion | Azure AI Document Intelligence (Layout model) | Parses RFP documents (PDF, DOCX, XLSX) into structured Markdown with tables and sections |
| 2 | Orchestrator | LangGraph (StateGraph) | Manages agent workflow as a directed graph with state persistence, conditional routing, and human-in-the-loop interrupts |
| 3 | LLM | Azure OpenAI GPT-4o | Reasoning, extraction, classification, generation, and quality assessment across all agents |
| 4 | Vector Store | Azure AI Search (hybrid + semantic reranking) | Stores and retrieves proposal content library with combined keyword, vector, and semantic search |
| 5 | Embedding Model | Azure OpenAI text-embedding-3-large | Generates 3072-dim embeddings for content library documents and RFP questions |
| 6 | Backend API | FastAPI on AKS | Exposes endpoints for RFP submission, status tracking, and review workflows |
| 7 | Content Store | Azure Blob Storage | Stores source documents (past proposals, product docs, certifications) |
| 8 | State Store | Azure Cosmos DB | Persists LangGraph checkpoint state for long-running RFP workflows |

---

## Data Flow

```
1. [Trigger]    → Proposal manager uploads RFP document via web UI or API
2. [Parse]      → Document Intelligence extracts structured content (questions, tables, sections)
3. [Classify]   → Question Classifier agent categorizes each question by domain
                   (security, compliance, technical, company info, pricing) and deduplicates
                   against historical question bank
4. [Score]      → Bid/No-Bid agent evaluates fit based on requirements vs. capabilities
                   and historical win patterns; flags recommendation to proposal manager
5. [Retrieve]   → For each question, Retrieval agent runs hybrid search against content
                   library, returning top-k passages with source provenance and freshness date
6. [Generate]   → Draft Generator agent synthesizes retrieved passages into a response,
                   calibrated to RFP tone and format; attaches source citations and
                   confidence score (0-1) per answer
7. [Comply]     → Compliance Checker agent verifies all mandatory requirements are
                   addressed, flags gaps, and validates regulatory statements
8. [Review]     → Quality Review agent checks cross-answer consistency, tone alignment,
                   and factual grounding; triggers re-generation for low-confidence answers
9. [Escalate]   → Gap Detector routes unanswerable questions to specific SMEs via
                   Teams/email with pre-filled context
10. [Gate]      → Human review gate: proposal manager reviews flagged sections;
                   approves or sends back for revision
11. [Assemble]  → Final Assembly exports submission-ready document package
                   (DOCX/PDF) matching RFP format requirements
```

---

## Agent Pattern

| Aspect | Choice |
|--------|--------|
| **Pattern** | Multi-Agent Orchestrator-Worker with Agentic RAG |
| **Orchestration** | Graph-based (LangGraph StateGraph with conditional edges) |
| **Human-in-the-Loop** | Configurable approval gate after compliance check; SME escalation for gaps |
| **State Management** | Persistent state via LangGraph checkpointing to Cosmos DB |
| **Autonomy Level** | Semi-Autonomous — full autonomy on draft generation; human gate before submission |

### Why This Pattern?

**Multi-agent over single agent**: RFP processing involves 6+ distinct subtasks (parsing, classification, retrieval, generation, compliance, quality) that require different system prompts, temperature settings, and evaluation criteria. A single agent with all responsibilities produces worse results because the system prompt becomes too broad and conflicting — the precision needed for compliance checking (temperature 0.0) conflicts with the fluency needed for narrative generation (temperature 0.3). Thalamus AI validated this with 20+ specialized agents; DeepRFP uses dedicated agents per task.

**Graph-based over sequential**: LangGraph's directed graph enables conditional branching (skip bid/no-bid for existing customers), iterative loops (re-generate low-confidence answers), and parallel execution (retrieve for multiple questions simultaneously). A linear chain cannot express the re-generation loops or conditional SME escalation that real RFP workflows require.

**Agentic RAG over fine-tuning**: Content libraries change constantly as products evolve. Fine-tuning would create a model frozen in time. RAG with hybrid retrieval ensures answers are always grounded in current, vetted content — and every claim is traceable to a source document. This is critical for compliance and auditability.

**Alternatives rejected**:
- *CrewAI role-based agents*: Good for brainstorming-style collaboration but lacks the deterministic state management and conditional routing that RFP workflows demand
- *Semantic Kernel with plugins*: Strong Azure integration but better suited for copilot-style single-agent patterns; less natural for complex multi-agent graphs (though viable as an alternative — see below)
- *Fully autonomous (no human gate)*: Rejected because compliance statements carry legal liability; human review before submission is non-negotiable for regulated industries

---

## LLM Role by Agent

| Agent | LLM Task | Temperature | Output Format |
|-------|----------|-------------|---------------|
| **Question Classifier** | Categorize RFP question into domain taxonomy; identify duplicates via semantic similarity | 0.0 | Structured JSON: `{category, subcategory, is_duplicate, duplicate_of}` |
| **Bid/No-Bid Scorer** | Evaluate requirement fit against company capabilities; score opportunity | 0.0 | Structured JSON: `{score, fit_gaps[], recommendation, reasoning}` |
| **Retrieval Agent** | Generate optimized search queries from RFP questions; evaluate retrieval relevance | 0.1 | Search queries + relevance scores |
| **Draft Generator** | Synthesize retrieved passages into a coherent, RFP-calibrated response with citations | 0.3 | Markdown response with inline `[Source: doc_id]` citations |
| **Compliance Checker** | Map RFP mandatory requirements to response sections; identify gaps | 0.0 | Structured JSON: `{requirement_id, addressed: bool, section_ref, gap_description}` |
| **Quality Reviewer** | Assess tone consistency, factual grounding, cross-answer coherence | 0.1 | Structured JSON: `{score, issues[], suggestions[]}` |
| **Gap Detector** | Identify unanswerable questions; determine correct SME routing | 0.0 | Structured JSON: `{question_id, reason, suggested_sme_role, context_summary}` |

### Prompt Strategy

**System prompts** are domain-specialized per agent. The Draft Generator, for example, receives explicit grounding instructions:

```
You are an expert proposal writer for {company_name}. Your task is to draft
an RFP response based EXCLUSIVELY on the retrieved source passages below.

RULES:
1. Every factual claim MUST be supported by a retrieved passage.
2. If no passage supports a claim, do NOT include it — flag it as a gap.
3. Cite sources inline as [Source: {document_id}].
4. Match the tone of the RFP (formal/technical/conversational).
5. Never fabricate statistics, customer names, or certifications.
6. If the retrieved content is outdated (>12 months), flag for review.

RETRIEVED PASSAGES:
{retrieved_passages}

RFP QUESTION:
{question_text}

RESPONSE FORMAT:
- Answer in 1-3 paragraphs
- Include inline citations
- End with confidence score (0.0-1.0) and source list
```

**Few-shot examples** are embedded for the Question Classifier to ensure consistent categorization across RFP formats. The Compliance Checker uses a **structured output schema** (JSON mode) to produce machine-parseable gap analyses.

---

## Integration Points

| System | Integration Method | Direction | Purpose |
|--------|--------------------|-----------|---------|
| Azure AI Document Intelligence | REST API (prebuilt-layout model) | Inbound | Parse RFP documents into structured Markdown |
| Azure AI Search | REST API / Python SDK | Bidirectional | Index content library; hybrid search for retrieval |
| Azure OpenAI | Python SDK (openai) | Outbound | LLM inference for all agents |
| Azure Blob Storage | Azure SDK | Read | Store and retrieve source documents |
| Azure Cosmos DB | LangGraph checkpoint serde | Bidirectional | Persist workflow state across long-running RFPs |
| Salesforce CRM | REST API | Read | Pull opportunity data for bid/no-bid scoring |
| SharePoint / OneDrive | Microsoft Graph API | Read | Ingest product docs, past proposals, certifications |
| Microsoft Teams | Graph API / Webhooks | Outbound | Route SME review requests with pre-filled context |
| Procurement Portals (Ariba, Jaggaer) | Portal-specific API or manual upload | Outbound | Final submission (often manual due to portal constraints) |

---

## Tools & Frameworks

### AI / ML Stack

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| **LLM Provider** | Azure OpenAI | Enterprise compliance (data residency, SLAs), Managed Identity auth, content filtering |
| **Model** | GPT-4o (primary), GPT-4o-mini (classification tasks) | GPT-4o for strong reasoning + structured output; GPT-4o-mini for high-volume classification at lower cost |
| **Agent Framework** | LangGraph 0.3.x | Stateful graph orchestration with conditional edges, checkpointing, and human-in-the-loop — purpose-built for multi-agent workflows |
| **Vector Database** | Azure AI Search | Hybrid search (keyword + vector + semantic reranking) in a single query; managed service with RBAC |
| **Embedding Model** | text-embedding-3-large (3072 dims) | Highest accuracy for semantic similarity; Matryoshka support for cost/quality tradeoff |
| **Document Parsing** | Azure AI Document Intelligence | Pre-built layout model handles PDF, DOCX, XLSX without custom training; outputs structured Markdown |

### Infrastructure Stack

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| **Compute** | AKS (or Azure Container Apps) | Scalable, existing enterprise infrastructure |
| **Storage** | Azure Blob Storage | Source document storage with lifecycle management |
| **State Store** | Azure Cosmos DB | LangGraph checkpoint persistence for long-running workflows |
| **Monitoring** | Application Insights | Existing observability stack; custom metrics for LLM quality |
| **CI/CD** | GitHub Actions | Existing pipeline infrastructure |

### Open-Source Alternatives

| Component | Alternative | Trade-off |
|-----------|------------|-----------|
| LangGraph | Semantic Kernel (Microsoft Agent Framework) | Better C#/.NET support and native Azure integration; less flexible for complex multi-agent graphs |
| LangGraph | CrewAI | Simpler role-based agent setup; lacks deterministic state management and conditional routing |
| Azure AI Search | Weaviate / Qdrant / pgvector | Self-managed, lower cost; loses integrated semantic reranking and managed hybrid search |
| Azure Document Intelligence | LlamaParse / Unstructured.io | Open-source; requires more tuning for complex table extraction |

---

## Security & Compliance

| Concern | Approach |
|---------|----------|
| **Authentication** | Managed Identity for all Azure service-to-service calls; Entra ID for user authentication |
| **Authorization** | RBAC on Azure AI Search indexes (per-client content isolation); proposal-level access controls in application layer |
| **Data at Rest** | Azure-managed encryption (AES-256); option for CMK on Blob Storage and Cosmos DB |
| **Data in Transit** | TLS 1.2+ enforced; Private Endpoints for AI Search and OpenAI in production |
| **PII Handling** | Client-confidential RFP content processed within Azure tenant boundary; no data sent to third-party services; content filters enabled on Azure OpenAI |
| **Audit Trail** | Every agent action logged with: input hash, output, source citations, confidence score, human decisions; stored in immutable append-only log |
| **Model Governance** | Azure OpenAI content filters enabled; custom guardrails prevent generation of pricing, legal commitments, or competitor disparagement without human approval |

---

## Scalability & Performance

| Dimension | Approach |
|-----------|---------|
| **Throughput** | 5-10 concurrent RFPs; 50-200 questions per RFP processed in parallel batches |
| **Latency Target** | Question classification: < 2s; Retrieval + generation per question: < 10s; Full RFP first draft (200 questions): < 30 minutes |
| **Scaling Strategy** | Horizontal pod autoscaling on AKS; queue-based processing for RFP intake; parallel agent execution within LangGraph |
| **Rate Limits** | Azure OpenAI provisioned throughput (PTU) for predictable latency at scale; fallback to pay-as-you-go for burst |
| **Caching** | Semantic cache for repeated/similar questions (hash of question embedding → cached response); content library embeddings pre-computed and indexed |

---

## Cost Estimate

| Component | Unit Cost | Monthly Estimate (150 RFPs/month, ~200 questions each) |
|-----------|-----------|--------------------------------------------------------|
| **LLM API — GPT-4o** | $2.50/1M input, $10/1M output tokens | ~$1,200 (est. 150M input + 60M output tokens/month) |
| **LLM API — GPT-4o-mini** | $0.15/1M input, $0.60/1M output | ~$50 (classification tasks) |
| **Embeddings** | $0.13/1M tokens | ~$30 (content library re-indexing + query embeddings) |
| **Azure AI Search** | S1 tier ($250/month) or S2 ($1,000) | ~$500 (S1 with semantic reranking add-on) |
| **Document Intelligence** | $10/1,000 pages (prebuilt layout) | ~$150 (est. 15,000 pages/month) |
| **Cosmos DB** | 400 RU/s serverless | ~$50 |
| **Blob Storage** | $0.018/GB | ~$10 |
| **Compute (AKS)** | 2-4 node D4s_v5 | ~$600 |
| **Total** | | **~$2,600/month** |

Compared to a proposal team costing $50K-$150K/month in fully loaded salaries and SME opportunity cost, this represents a 95%+ cost reduction for draft generation.

---

## Alternatives Considered

| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| Single-agent monolithic (one large prompt) | Simpler to build and deploy; fewer moving parts | System prompt too broad; competing objectives (precision vs. fluency); hard to evaluate individual steps | Cannot match quality of specialized agents; no conditional routing for edge cases |
| Fine-tuned model on past proposals | No retrieval latency; potentially faster responses | Content frozen at training time; expensive to retrain as products evolve; no source attribution; compliance risk from hallucination | Content freshness is critical — RAG ensures current answers with provenance |
| Commercial SaaS (Loopio, Responsive, Thalamus AI) | Fastest time to production; proven at scale; maintained by vendor | Vendor lock-in; limited customization; data leaves enterprise boundary; $50K-200K/year licensing | Valid for many enterprises; custom build justified when deep system integration, data sovereignty, or unique workflow requirements exist |
| Semantic Kernel single-agent with plugins | Excellent Azure integration; C#/.NET native; Microsoft Agent Framework backing | Less flexible for complex multi-agent graphs; plugin model better for copilot than autonomous workflow | Strong alternative for .NET shops; LangGraph chosen for graph expressiveness and Python ecosystem alignment |
