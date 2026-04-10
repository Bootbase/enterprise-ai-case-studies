---
layout: use-case-detail
title: "Evaluation — Autonomous Mortgage Loan Document Processing"
uc_id: "UC-002"
uc_title: "Autonomous Mortgage Loan Document Processing and Underwriting with Agentic AI"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Document Processing"
category_icon: "file-text"
industry: "Financial Services (Mortgage Lending)"
complexity: "High"
status: "detailed"
slug: "UC-002-mortgage-loan-processing"
permalink: /use-cases/UC-002-mortgage-loan-processing/evaluation/
---

## Decision Summary

This is a strong use case with multiple named production deployments and published metrics from lenders of varying sizes. The evidence base is anchored by Rocket Mortgage's SEC-reported efficiency gains ($40M in 2024, 1M hours saved) and four named Ocrolus customer deployments with specific underwriter time savings. The economic case is robust: mortgage origination costs $11,600–$12,600 per loan, personnel costs represent 67% of that total, and document processing is a major share of personnel time. The Freddie Mac Cost to Originate Study confirms that high-rate technology adopters save approximately $2,300 per loan. The business case holds if the system achieves ≥90% classification accuracy and reduces underwriter administrative time by ≥25% — thresholds already demonstrated in production by multiple vendors.

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| Rocket Mortgage — Rocket Logic AI (SEC filings, 2024) | 1M team member hours saved in 2024; $40M efficiency gains; 21M documents classified; 25% fewer touches per loan | Largest retail lender has proven AI document processing at scale (1.5M docs/month). These are SEC-regulated disclosures, not marketing estimates |
| Rocket Close — AWS architecture (2024) | 90% overall accuracy across classification, segmentation, and extraction; processes document packages in under 2 minutes | Two-stage pipeline (Amazon Textract OCR + Claude via Bedrock) achieves production-grade accuracy on 60 document types |
| Ocrolus — American Federal Mortgage | 29% reduction in underwriter time per file; 2 hours saved per loan | Named mid-size lender confirms meaningful per-loan time savings from AI document automation |
| Ocrolus — HomeTrust Bank | 8,500 hours saved annually; $90,000 direct cost savings; keystrokes reduced from hundreds to <100 per application | Demonstrates savings at community bank scale, not just top-10 lender scale |
| Ocrolus — Compeer Financial | 50% increase in processor throughput with same staff | Shows capacity scaling without headcount — critical given industry-wide underwriter shortage |
| Freddie Mac — 2024 Cost to Originate Study | High-rate technology adopters save ~$2,300/loan; personnel = 67% of origination cost; top quartile lenders at $6,900/loan vs. bottom quartile at $16,500/loan | GSE data confirms large cost gap between technology leaders and laggards — document automation is a key differentiator |
| MBA — Q1 2025 Performance Report | Average origination cost: $12,579/loan; industry operating at near break-even ($28 net loss per loan for IMBs) | Tight margins make cost reduction an operational imperative, not an optimization exercise |

## Assumptions And Scenario Model

| Assumption | Value | Basis |
|------------|-------|-------|
| Annual loan volume (mid-size lender) | 30,000 loans/year | Mid-size lender processing 2,500 loans/month; well below top-10 scale but sufficient for ROI |
| Current origination cost per loan | $11,600 | Freddie Mac 2024 Cost to Originate Study average; MBA Q1 2025 reports $12,579, trending higher |
| Document processing share of origination cost | 30–40% | Includes classification, data entry, cross-referencing, condition management, and related underwriter administrative time |
| Current document processing cost per loan | $3,500–$4,600 | Derived from origination cost × document processing share |
| Achievable time reduction per loan | 25–40% of document processing time | Conservative range: Ocrolus customers report 29–50%; Rocket reports 25% fewer touches |
| AI processing cost per loan | $30–$50 | Based on OCR + LLM token costs for 200+ pages per loan at current API pricing; assumes volume pricing |
| Classification accuracy target | ≥ 90% automated (no human touch) | Rocket Logic reports ~70% fully automated classification with overall 90% accuracy; Indecomm claims 95%+ |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current document processing cost** | $105M–$138M/year (30,000 loans × $3,500–$4,600) | Estimated, derived from Freddie Mac and MBA cost data |
| **Expected steady-state cost** | $65M–$95M/year | Estimated, assumes 25–40% reduction in document processing labor plus $30–$50/loan AI cost |
| **Expected annual benefit** | $30M–$55M/year | Estimated, primarily labor reallocation and cycle-time-driven throughput gains |
| **Implementation cost** | $1.5M–$3M (Phase 1–4 over 9–12 months) | Estimated, includes platform build, LOS integration, evaluation harness, pilot operations. Higher than AP invoice automation due to regulatory and integration complexity |
| **Payback view** | 4–8 months after production deployment | Estimated, assuming pilot validates within first quarter and phased rollout reaches 60%+ loan volume within 6 months |

Additional economic benefit not modeled above: cycle time reduction from 30–45 days to 20–30 days reduces borrower abandonment (currently ~20% of pipeline) and improves competitive positioning on speed-to-close.

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| Document classification | Strength: multiple vendors demonstrate 90–95%+ accuracy in production across hundreds of document types | Gold-labeled evaluation set; per-type accuracy monitoring; human queue for below-threshold classifications |
| Field extraction accuracy | Strength: structured documents (W-2, 1003) extract reliably; Risk: handwritten documents, poor-quality photos, and non-standard formats degrade accuracy | Dual-extraction comparison for high-stakes fields; OCR quality scoring to flag degraded inputs before LLM processing |
| Cross-reference integrity | Risk: AI may miss subtle discrepancies or flag false positives on legitimate variations (e.g., employer name abbreviations, rounding differences) | Configurable tolerance thresholds per field type; deterministic calculation engine for DTI/LTV — AI identifies discrepancies, rules engine validates materiality |
| Fair lending compliance | Risk: inconsistent AI behavior across borrower demographics could create disparate impact liability | AI processes document content only — no access to demographic fields; periodic fair lending audit comparing outcomes; CFPB Circular 2022-03 requires specific adverse action reasons even for AI-assisted decisions |
| Regulatory timeline compliance | Risk: processing delays or system outages could cause TRID violations (Loan Estimate within 3 business days, Closing Disclosure 3 days before closing) | TRID timeline tracker operates independently of AI pipeline; fallback to manual processing if AI queue exceeds SLA |
| Evidence quality | Risk: most published metrics come from vendor case studies or corporate press releases, not independent benchmarks | Freddie Mac and MBA data provide independent cost baselines; Rocket's SEC filings add regulatory accountability. Pilot measurement against internal manual baseline is essential |
| Vendor lock-in | Risk: deep LOS integration creates switching costs | Build LOS adapter layer with standard interface; extraction schemas are LOS-independent |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| Document classification accuracy | Below-threshold accuracy creates more rework than it saves | ≥ 90% automated classification; ≥ 95% overall (including human-corrected) |
| Field extraction accuracy (income, assets) | Extraction errors propagate into DTI/LTV miscalculations and potential GSE repurchase demands | ≥ 97% exact match on income and asset fields against underwriter-verified baseline |
| Underwriter time per file | The core value proposition — if underwriters don't save time, the ROI fails | ≥ 25% reduction in average underwriter hours per loan file vs. manual baseline |
| Condition roundtrip reduction | Fewer condition cycles directly reduce cycle time and borrower frustration | Average condition cycles < 1.8 (from 2.3 baseline) |
| Processing latency | Borrowers and loan officers expect near-real-time document acknowledgment | < 30 seconds per document classification; < 5 minutes full file cross-reference |
| Zero invalid LOS writes | A single incorrect writeback to a loan file could cause downstream errors in closing or investor delivery | Zero overwrites of underwriter-entered data; 100% AI-field namespace compliance |

## Open Questions

- What is the right confidence threshold for fully automated classification versus human review routing? Rocket's 70% automation rate suggests aggressive thresholds work at scale, but smaller lenders with less training data may need to start more conservatively.
- How does extraction accuracy degrade across non-QM and specialty products (bank statement loans, asset depletion, DSCR) where document formats are less standardized? Deephaven's Ocrolus deployment suggests viability but without published accuracy rates for non-QM documents.
- What is the incremental cost of maintaining GSE guideline rules as Fannie Mae and Freddie Mac update selling guides quarterly? The cross-reference engine depends on current guideline rules — stale rules create false positives or missed conditions.
- How should lenders handle the CFPB's evolving position on AI in lending decisions? Current guidance requires specific adverse action reasons — if AI-generated conditions influence credit decisions, the explainability requirements may extend to the document processing layer.
