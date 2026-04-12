---
layout: use-case-detail
title: "Evaluation — Autonomous Trade Surveillance and Market Abuse Detection"
uc_id: "UC-516"
uc_title: "Autonomous Trade Surveillance and Market Abuse Detection"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Capital Markets"
complexity: "High"
status: "detailed"
slug: "UC-516-trade-surveillance-market-abuse"
permalink: /use-cases/UC-516-trade-surveillance-market-abuse/evaluation/
---

## Decision Summary

This is a strong use case with good evidence quality across multiple primary deployments. Nasdaq's pilot with the Saudi CMA (80% pump-and-dump detection, 33% investigation time reduction) and LSEG's production deployment on Amazon Bedrock (100% recall on price-sensitive news) provide named, metrics-backed reference points from exchange operators. NICE Actimize's SURVEIL-X platform (up to 85% false positive reduction, 4x detection improvement) adds vendor evidence at scale across 1,000+ organizations. The FCA TechSprint provides regulatory endorsement of AI approaches. The business case holds if: (1) the firm processes enough alerts for triage automation to justify the integration cost, and (2) the compliance team validates that AI-assisted investigation packages meet the regulator's expectations for STOR quality and audit trail completeness.

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| Nasdaq AI Surveillance Pilot (Saudi CMA) [S1] | 80% detection rate for pump-and-dump schemes on historical data; 33% reduction in investigation time during proof-of-concept | AI-augmented surveillance detects coordinated manipulation that rules-based templates miss. Investigation time compression is achievable at exchange scale. Platform serves 50+ exchanges and 20+ regulators. |
| LSEG Surveillance Guide on Amazon Bedrock [S2] | 100% precision on non-sensitive news; 100% recall on price-sensitive content using Claude Sonnet | LLM-based news sensitivity classification is production-ready for insider dealing contextualization. Validated on 110 articles covering major news categories from LSEG's Regulatory News Service. |
| NICE Actimize SURVEIL-X with Actimize Intelligence [S3] | Up to 85% false positive reduction; 4x more true misconduct detected vs. rules-based; 150+ languages supported | Generative AI communication analysis materially outperforms keyword-based surveillance. Scale: 1,000+ organizations across 70+ countries. Credit Suisse deployed in 2023 with 30% false positive reduction. |
| FCA Market Abuse Surveillance TechSprint [S4] | 9 international teams demonstrated isolation forests, Bayesian networks, and LLMs enhancing detection of complex abuse types | Regulatory endorsement: the UK's primary financial regulator actively exploring AI for market surveillance, not just tolerating it. |
| ESMA STOR Report 2024 [S6] | 6,763 notifications filed across EU in 2024 (5,981 STORs + 782 other notifications) | Establishes the operational scale of STOR filing and the investigative burden on surveillance teams across the EU. |

## Assumptions And Scenario Model

The scenario below models a mid-size broker-dealer (150–300 alerts/day). Adjust volumes and team sizes for exchange operators or larger firms.

| Assumption | Value | Basis |
|------------|-------|-------|
| Daily alert volume | 250 alerts/day (~65,000/year) | Mid-range for a broker-dealer with multi-asset surveillance. Exchange operators process significantly more. |
| False positive rate (current) | 93% | Industry range is 90–95% for rules-based surveillance engines. Mid-point used. |
| Investigation time per alert (current) | 45 minutes average | Blended average across triage (15 min) and deeper investigation (2–22 hours for escalated cases). Most alerts are triaged quickly but a minority consume hours. |
| Surveillance analyst fully loaded cost | USD 120,000/year | US/UK-based analyst with capital markets and compliance experience. Higher than general compliance analysts due to domain specialization. |
| AI-assisted investigation time (target) | 15 minutes average | Agent handles evidence gathering and drafts narrative; analyst reviews pre-scored package. Consistent with Nasdaq's 33% reduction finding. [S1] |
| False positive reduction (target) | 60% | Conservative estimate within NICE Actimize's published 85% range. Not all firms will achieve the upper bound on initial deployment. [S3] |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current surveillance team cost** | ~USD 2.4M/year | 20-person team (typical for a mid-size broker-dealer with multi-asset surveillance) at USD 120K fully loaded. Estimated. |
| **Current investigation capacity** | ~250 alerts/day reviewed; majority of time on false positives | 93% false positive rate means ~233 wasted investigations/day. Estimated from industry baseline. |
| **Expected investigation time savings** | 33–67% per alert | 33% is the Nasdaq pilot result; higher reductions are possible with full enrichment pipeline. Published + estimated. [S1] |
| **Expected false positive reduction** | 60% (conservative) to 85% (published upper bound) | NICE Actimize reports up to 85%. Credit Suisse achieved 30% with an earlier version. Range reflects deployment maturity. Published. [S3] |
| **Annual labor reallocation** | ~USD 0.8–1.4M/year in analyst time redirected to genuine abuse investigation | Fewer false positives to close + faster investigation per alert. Reinvest freed capacity, not headcount reduction. Estimated. |
| **Implementation cost** | USD 1.5–3.5M | Platform build (Phase 1–3), market data integration, communication archive adapter, model validation, regulatory review. Range depends on existing API maturity and number of data sources. Estimated. |
| **Ongoing platform cost** | USD 400K–800K/year | Cloud infrastructure, LLM API costs, market data feeds, model monitoring, and compliance governance. Estimated. |
| **Payback view** | 12–18 months post-production | Net saving of USD 0.8–1.4M/year against USD 1.5–3.5M implementation. Faster payback at exchange scale with higher alert volumes. Risk reduction value (avoiding regulatory fines) is additive but hard to quantify. Estimated. |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| Detection quality | **Strength**: Anomaly detection catches novel patterns that rules-based systems miss. Nasdaq pilot detected 80% of pump-and-dump schemes in historical data. [S1] | Back-test against 12+ months of labeled outcomes before production. Maintain rules-based surveillance engine as parallel safety net during transition. |
| Regulatory acceptance | **Risk**: Regulators may challenge AI-assisted investigations if explainability is insufficient or audit trails are incomplete. | Every investigation produces a full evidence chain with source citations. FCA TechSprint demonstrates regulatory openness to AI, but individual firm engagement with their regulator is essential before pilot. [S4][S7] |
| Narrative hallucination | **Risk**: LLM generates claims not supported by retrieved evidence, creating liability in STOR filings. | Grounded generation with mandatory source citations. Automated citation validation — no ungrounded narrative reaches analyst review. Human reviews and signs every STOR. |
| Market data quality | **Risk**: Order-book replay depends on complete, accurate market data. Gaps in tick data produce incomplete anomaly scores. | Data quality monitoring on ingestion pipeline. Agent documents data gaps in the investigation package rather than inferring. Escalate to manual if order-book data is unavailable. |
| Adversarial adaptation | **Risk**: Sophisticated manipulators may adapt strategies to evade AI detection patterns. | Ensemble models (isolation forest + autoencoder) are harder to reverse-engineer than single models. Regular retraining on confirmed abuse cases. Red-team exercises against known manipulation strategies. |
| Communication privacy | **Risk**: Communication monitoring may breach GDPR or employment law if access is not properly scoped. | Every communication query scoped to specific trader ID and alert time window. Access logged for audit. Legal review of lawful basis (GDPR Article 6(1)(c)) required before deployment. [S3] |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| False positive reduction rate | The core value metric. Measures how much analyst time is freed from closing false alerts. | ≥ 50% reduction vs. rules-only baseline during pilot |
| Disposition agreement rate | Measures whether the agent's recommended disposition matches the analyst's independent judgment. | ≥ 85% agreement during shadow-mode pilot |
| Narrative sufficiency rate | Analysts must be able to use the draft narrative as a starting point for STOR filing without major rewrites. | ≥ 90% of narratives rated "sufficient" by blind analyst review |
| Citation validity | Every claim in the narrative must trace to a retrieved record. Ungrounded citations are a hard failure in a regulatory filing. | 100% citation validity (zero tolerance) |
| False negative rate on confirmed abuse | Alerts the agent recommends closing that were later confirmed as market abuse. Critical safety metric. | ≤ 5% false negative rate on confirmed cases |
| End-to-end investigation latency | Investigation packages must be ready within SLA. Excessive latency negates the automation benefit. | Single-venue: < 3 min. Cross-venue: < 10 min. |

## Open Questions

- **Regulatory expectations vary by jurisdiction.** UK (FCA), EU (ESMA NCAs), and US (SEC/FINRA) may have different expectations for AI-assisted market surveillance. Pre-engagement with the primary regulator is essential before pilot deployment.
- **Cross-venue data access.** Effective detection of cross-market manipulation requires order data from multiple venues. Data sharing agreements between venues and firms are not standardized and may limit the scope of cross-venue correlation in Phase 1.
- **Communication monitoring legal basis.** The lawful basis for AI-powered communication monitoring varies by jurisdiction and employment law regime. Firms must obtain legal counsel on GDPR, ePrivacy, and local labor law requirements before integrating communication analysis.
- **Labeled training data scarcity.** Confirmed market abuse cases represent less than 5% of alerts. Unsupervised approaches address this partly, but supervised models for specific abuse types will need careful handling of class imbalance and may require synthetic augmentation.
- **Crypto and digital asset surveillance.** This design covers regulated traditional markets. Extending to crypto exchanges introduces different regulatory regimes, data formats, and manipulation patterns (e.g., wash trading on unregulated venues) that are not addressed here.
