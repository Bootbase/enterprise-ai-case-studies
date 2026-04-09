---
layout: use-case-detail
title: "Evaluation — Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
uc_id: "UC-401"
uc_title: "Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Knowledge Management"
status: "detailed"
slug: "UC-401-regulatory-change-intelligence"
permalink: /use-cases/UC-401-regulatory-change-intelligence/evaluation/
---

## Evaluation Overview

The evidence base for AI in regulatory change management draws from three categories: (1) published production metrics from commercial RegTech platforms (CUBE, AscentAI, Wolters Kluwer) that have deployed at major financial institutions, (2) academic research on regulatory NLP with benchmark precision/recall scores from the RegNLP 2025 workshop at COLING, and (3) industry cost-of-compliance surveys (CUBE, Thomson Reuters, Deloitte) that quantify the baseline manual process. Unlike some enterprise AI use cases, the regulatory domain has both strong academic benchmarks and production deployments with published results.

---

## Baseline (Before AI)

| Metric | Value | Source |
|--------|-------|--------|
| **Obligation extraction time (per major regulation)** | 1,800 hours for MiFID/MiFID II | AscentAI: ING and Commonwealth Bank pre-AI baseline |
| **Regulatory change detection latency** | Days to weeks after publication | Manual monitoring of regulator websites, RSS feeds, and legal news |
| **Compliance cost as % of revenue** | 10-15% of annual revenue for financial services firms | Deloitte regulatory productivity analysis |
| **Compliance cost per employee** | $10,000+ per employee per year at large financial institutions | Thomson Reuters Cost of Compliance Report |
| **Compliance operating cost increase** | 60%+ increase since pre-financial crisis levels | Deloitte |
| **Employee hours growth** | 61% increase in compliance hours between 2016-2023 | Deloitte regulatory compliance analysis |
| **Assessment-to-implementation cycle** | 3-9 months for complex regulatory changes | Industry average from RCM practices |
| **Examination preparation time** | 2-6 weeks of team time to assemble evidence per examination topic | Manual assembly from email chains, shared drives, GRC tools |
| **Total compliance function cost (mid-size bank)** | $50-60 million annually | Thomson Reuters Cost of Compliance 2024 |
| **Total compliance function cost (G-SIB)** | $200-300 million+ annually | Thomson Reuters / IIF / McKinsey estimates |

---

## Published Results (After AI)

| Metric | Before AI | Published AI Result | Change | Source |
|--------|-----------|---------------------|--------|--------|
| **Obligation extraction time (MiFID II)** | 1,800 hours | 2.5 minutes | -99.998% | AscentAI with ING and Commonwealth Bank |
| **Regulatory source coverage** | Dozens of manually-checked websites | 10,000+ issuing bodies, 750 jurisdictions, 80 languages | Orders of magnitude broader | CUBE RegPlatform |
| **Obligation extraction precision** | N/A (manual = high but slow) | 93% precision in obligation filtering | Benchmark from LLM + knowledge graph approach | Academic: LLM + knowledge graph on EU AI Act |
| **Obligation type classification accuracy** | N/A | 99%+ accuracy for obligation types, addressees, predicates | Academic benchmark | Academic: LLM + knowledge graph on EU AI Act |
| **Enforcement action detection** | Manual scanning | 23% YoY increase in detected enforcement actions (157 AI-related insights in 12 months) | More detected, not more occurring — visibility improvement | CUBE 2025 Global Regulatory Risk Report |
| **Regulatory change management cycle time** | 3-9 months | Target: < 30 days | 70-90% reduction | Projected from automation of extraction, assessment, and workflow stages |
| **RCM FTE reduction (European bank)** | 22 FTEs | 8 FTEs | -63% FTE reduction, $2.8M annual savings | KPMG case study (2024) |
| **Regulatory review cycle time (NA bank)** | Manual review cycles | 65% reduction, $4.2M annual savings | Published by named North American bank | Accenture (2023) |
| **RCM time savings from RegTech** | Manual assessment | 40-60% reduction in time to assess regulatory change impact | Industry average across implementations | Celent/Oliver Wyman (2024) |

---

## Quality Assessment

### Where the AI excels

| Capability | Evidence | Interpretation |
|------------|----------|----------------|
| **Obligation extraction from dense regulatory text** | AscentAI: 1,800 hours → 2.5 minutes for MiFID II. Academic: 93% precision, 99%+ classification accuracy. | Extracting structured obligations from unstructured legal text is the core unlock — the task that consumed the most human hours and now scales to any regulation volume. |
| **Multi-jurisdictional coverage at machine speed** | CUBE monitors 10,000+ issuing bodies across 750 jurisdictions in 80 languages. | No human team can manually monitor this breadth. AI eliminates the coverage gap that causes missed regulatory changes. |
| **Consistency and auditability** | Every AI assessment produces structured output with reasoning, confidence score, and source citation. | Manual assessments vary by analyst; AI assessments are consistent and fully traceable — critical for examination readiness. |
| **Speed on repetitive applicability assessment** | Once the regulatory perimeter is defined, applicability assessment for each new obligation takes seconds rather than hours. | The highest-volume, lowest-judgment task in the RCM workflow is the one most suited to automation. |
| **Pattern detection across jurisdictions** | AI can identify similar obligations emerging across multiple jurisdictions simultaneously. | Humans process jurisdictions sequentially; AI can detect converging regulatory trends. |

### Where the AI still has limitations

| Capability | Evidence | Why It Matters |
|------------|----------|----------------|
| **Accuracy on long documents (100+ pages)** | LLMs show 10-20% accuracy drop on prompts exceeding 1,000 characters of regulatory context. | Major regulations (Basel III.1, MiFID II, EU AI Act) span hundreds of pages. Chunking mitigates but doesn't eliminate this. |
| **Novel regulatory domains** | The EU AI Act created entirely new obligation types (AI risk classification, conformity assessment) that have no precedent in the training data. | First-time extraction on novel regulatory domains has lower precision until few-shot examples are added. |
| **Cross-border conflict resolution** | Conflicting obligations across jurisdictions (e.g., EU data localization vs. US CLOUD Act) require strategic judgment. | AI can detect conflicts but cannot make the business decision about which regime takes precedence. Always requires human review. |
| **Interpretation of regulatory intent** | Regulatory text often uses deliberately ambiguous language ("proportionate," "adequate," "appropriate") that depends on supervisory practice rather than literal meaning. | AI extracts what the text says; understanding what regulators mean requires domain expertise and supervisory dialogue. |
| **Integration with legacy GRC systems** | Many GRC platforms have limited API capabilities, especially older on-premises installations. | The technical AI pipeline may be ready before the integration layer, creating a last-mile problem. |

---

## Failure Analysis

| Failure Mode | Frequency (estimated) | Impact | Practical Mitigation |
|--------------|----------------------|--------|----------------------|
| **Hallucinated regulatory cross-references** | 8-15% of generated regulatory summaries contain material inaccuracies; LLMs hallucinate legal citations 12-23% of the time depending on model and task. | High — a false citation can misdirect compliance efforts | Structured output schema with citation validation; "never invent references" prompt rule; post-extraction validation against known regulation IDs; RAG grounding. |
| **Missed obligations in long documents** | 5-15% on documents exceeding 50 pages without chunking | High — a missed obligation creates a compliance gap | Article-boundary chunking with overlap; multiple extraction passes; recall-focused evaluation against gold set. |
| **False positive applicability assessment** | 30-50% without tuning; 10-15% after calibration | Medium — wastes compliance officer time on non-applicable obligations (alert fatigue) | Start with narrow regulatory perimeter; calibrate thresholds on historical data; target < 15% false positive rate after tuning. |
| **False negative applicability assessment** | 2-5% estimated | Critical — missing an applicable obligation exposes the firm to enforcement risk | Conservative thresholds: when in doubt, classify as "requires_review"; err toward false positive over false negative. |
| **Principles-based regulation failure** | Accuracy drops from ~90% to ~65% on principles-based regulation (e.g., FCA "treating customers fairly") vs. rules-based regulation | Medium — many jurisdictions (UK, Australia) use principles-based approaches | Route principles-based provisions to human review; add jurisdiction-specific few-shot examples; accept higher human involvement for principles-based regimes. |
| **Inconsistent extraction across prompt versions** | Variable — any prompt change can shift extraction behavior | Medium — creates audit challenges if past and present extractions are not comparable | Version-lock prompts; regression testing against gold set on every change; log prompt version with every extraction. |

---

## Cost Analysis

### Operational Costs

Estimated for a mid-size financial institution monitoring 200-300 issuing bodies across 10-20 jurisdictions, processing 50-100 regulatory changes per month requiring full pipeline analysis.

| Cost Component | Monthly Cost | Notes |
|----------------|-------------|-------|
| **LLM API (extraction, assessment, drafting)** | `$5k-$12k estimated` | Based on ~500-2,000 obligations/month at $3-6 per obligation (extraction + assessment + gap analysis). |
| **Azure AI Search** | `$1k-$3k estimated` | S1/S2 tier for regulatory corpus (100K+ documents), obligation register, and control framework indexes. |
| **Compute (container workers + API)** | `$2k-$5k estimated` | Azure Container Apps with autoscaling for parallel extraction. |
| **Knowledge graph (Neo4j/Cosmos DB)** | `$1k-$3k estimated` | Regulation-obligation-control relationship graph. |
| **Message queue + storage + monitoring** | `$1k-$2k estimated` | Service Bus, Blob Storage, Application Insights. |
| **Total (incremental AI costs)** | **`$10k-$25k estimated`** | Excludes regulatory feed subscriptions (existing cost). |

### ROI Calculation

| Factor | Value |
|--------|-------|
| **Previous cost (annual, RCM team)** | `$1.2M-$2.5M estimated` — 8-15 compliance analysts/officers dedicated to regulatory change management at $130K-$170K fully loaded. |
| **AI solution cost (annual)** | `$120K-$300K estimated` — incremental AI operating costs above. |
| **Regulatory feed subscriptions (annual)** | `$360K-$960K` — existing cost (CUBE, Wolters Kluwer, etc.), not incremental. |
| **Efficiency gain** | `60-70% reduction in manual monitoring and extraction time` — based on AscentAI's demonstrated 99.998% time reduction for obligation extraction. |
| **Redeployable capacity (annual)** | `$720K-$1.75M estimated` — 60-70% of RCM team capacity redirected from monitoring/extraction to strategic risk advisory. |
| **Net savings (annual)** | `$420K-$1.45M estimated` — redeployable capacity minus AI operating costs. |
| **Implementation cost** | `$300K-$800K estimated` — GRC integration, knowledge base setup, gold set creation, phased rollout over 6-12 months. |
| **Payback period** | `~3-12 months estimated` |

### Grounding in Published Data

AscentAI's headline result provides strong validation: ING and Commonwealth Bank reduced MiFID II obligation extraction from 1,800 hours to 2.5 minutes. At compliance officer rates ($80-$120/hour), those 1,800 hours represent $144K-$216K of labor for a single regulation. A firm that processes 10-20 major regulatory changes per year realizes $1M+ in extraction labor savings alone.

CUBE's revenue more than doubling since 2024 — and their acquisitions of Thomson Reuters Regulatory Intelligence, Acin, and Kodex AI — signals strong market demand and willingness to pay for automated regulatory intelligence.

The 23% YoY increase in enforcement actions (Corlytics 2025) means the cost of missing a regulatory change is increasing, making the risk-avoidance ROI increasingly compelling.

---

## User Feedback

### Quantitative (from published deployments)

| Metric | Result | Source |
|--------|--------|--------|
| ING MiFID II obligation extraction time | 2.5 minutes (from 1,800 hours manual) | AscentAI case study |
| Commonwealth Bank MiFID II processing | Same result as ING — 2.5 minutes | AscentAI case study |
| CUBE surveyed compliance officers | 2,000+ senior risk and compliance leaders across 12 global markets | CUBE Cost of Compliance Report 2025 |
| Regulatory insights detected (CUBE, AI-related) | 157 in 12 months (June 2024-May 2025), nearly double the previous year | CUBE 2025 report |

### Qualitative

"AscentAI provides regulatory change management to keep track of and implement new rules and regulations across different regions." — RegTech Analyst, on AscentAI's production deployment.

"Financial services research indicates that the direct and indirect cost of compliance averaged 19% of annual revenue depending on firm size." — Deloitte, Cost of Compliance and Regulatory Productivity analysis.

"For a Compliance Officer, it can feel like you are looking at tens to hundreds of sites at once." — CUBE, on the manual regulatory monitoring problem.

---

## Lessons Learned

### What Worked Well (from published implementations)

- **Obligation extraction is the breakthrough task.** AscentAI's 1,800-hours-to-2.5-minutes result on MiFID II demonstrates that LLM-based extraction is the single highest-ROI component. Start here.
- **Knowledge graph + LLM outperforms either alone.** Academic research at RegNLP 2025 shows 93% precision on obligation filtering when combining LLMs with knowledge graphs — significantly better than either approach in isolation.
- **Commercial regulatory feeds solve the source monitoring problem.** CUBE's 10,000+ issuing bodies across 750 jurisdictions is infeasible to replicate. Use commercial feeds for monitoring; build AI for the firm-specific layers (applicability, gap analysis, policy drafting).
- **Structured output schemas prevent hallucination.** Forcing the LLM to fill a defined obligation schema rather than generate free-form text reduces hallucinated citations and invented obligation text.
- **Phased rollout by jurisdiction de-risks.** Start with the firm's home jurisdiction (best-understood regulations, existing gold set available), then expand to additional jurisdictions as extraction proves reliable.

### What Didn't Work

- **General-purpose LLMs on raw regulatory text without chunking.** The 10-20% accuracy drop on long documents is well-documented. Teams that fed full regulations to GPT-4 without chunking got unreliable results.
- **Attempting full autonomy on policy changes.** Regulatory examination bodies (OCC, FCA, ECB SSM) expect human accountability for compliance decisions. Any system that autonomously activates policy changes without human approval creates regulatory risk.
- **Ignoring the GRC integration challenge.** The AI pipeline can be built faster than the GRC integration layer. Teams that built the AI first and left integration for later ended up with a system that produced good assessments but couldn't persist them to the system of record.

### What We'd Do Differently

- **Build the gold set first.** Creating a labeled evaluation set of obligations from 10-20 regulations before building the extraction agent provides the measurement foundation for every subsequent improvement.
- **Start with a single regulation type.** Rather than targeting all regulatory changes at once, start with a single type (e.g., supervisory guidance updates) where the format is more consistent and the volume is manageable.
- **Invest early in GRC API integration.** The GRC connector is not a glamorous component, but it determines whether AI assessments persist to the system of record or end up in a disconnected spreadsheet.

---

## Next Steps

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| High | Build gold set: label obligations from 20 regulations across 3 jurisdictions | Foundation for measuring and improving extraction accuracy; enables regression testing. |
| High | Deploy horizon scanner + document classifier for home jurisdiction | Immediate value: automated monitoring replaces manual daily website checking. |
| High | Build obligation extraction agent and validate against gold set | Target: 90%+ precision, 85%+ recall before deploying to production. |
| Medium | Integrate GRC connector for obligation register read/write | Enables extracted obligations to flow into the firm's system of record. |
| Medium | Deploy applicability assessment agent with human review loop | Semi-automated: AI drafts assessments, compliance officers validate. Calibrate confidence thresholds. |
| Medium | Add gap analysis and policy drafting agents | Complete the pipeline from detection to remediation recommendation. |
| Low | Expand to additional jurisdictions (EU, UK, US, APAC) | Add jurisdiction-specific few-shot examples and regulatory perimeter definitions. |
| Low | Add regulatory horizon scanning / trend analysis | Quarterly briefing for CCO on emerging regulatory themes across jurisdictions. |
