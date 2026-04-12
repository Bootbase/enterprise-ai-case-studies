---
layout: use-case-detail
title: "References — Autonomous Trade Surveillance and Market Abuse Detection"
uc_id: "UC-516"
uc_title: "Autonomous Trade Surveillance and Market Abuse Detection"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Capital Markets"
complexity: "High"
status: "detailed"
slug: "UC-516-trade-surveillance-market-abuse"
permalink: /use-cases/UC-516-trade-surveillance-market-abuse/references/
---

## Source Quality Notes

The evidence base for this use case is good, with three primary deployment sources from major market infrastructure operators and vendors. Nasdaq's pilot metrics (80% detection, 33% time reduction) come from a corporate press release with a named regulatory partner (Saudi CMA) — credible but pre-production. LSEG's news sensitivity deployment is documented through an AWS case study blog with specific methodology and performance numbers — strong but vendor-partnership published. NICE Actimize's metrics (85% false positive reduction, 4x detection) are vendor-originated; the Credit Suisse 30% figure is more conservative and from a named customer. The FCA TechSprint is a regulatory-endorsed initiative with publicly documented methodology and findings. ESMA and FCA regulatory sources are primary. Trade surveillance analyst cost estimates are derived from salary benchmarks and are directional, not precise. The 90–95% false positive rate for rules-based systems is widely cited across industry sources without a single authoritative study but is consistent across all vendor and regulatory references.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | Nasdaq — AI Capabilities Embedded in Surveillance Platform (October 2025) | Primary evidence for pump-and-dump detection (80%), investigation time reduction (33%), platform scale (50+ exchanges, 20+ regulators), and phased rollout approach. Named pilot partner: Capital Markets Authority of Saudi Arabia. | [Nasdaq press release via Stock Titan](https://www.stocktitan.net/news/NDAQ/nasdaq-embeds-innovative-ai-capabilities-within-its-surveillance-xn5l21tbjg5n.html) |
| S2 | Primary deployment | LSEG — AI-Powered Surveillance Guide on Amazon Bedrock (AWS Machine Learning Blog) | Evidence for LLM-based news sensitivity classification (100% precision on non-sensitive, 100% recall on price-sensitive). Architecture details: Claude Sonnet on Amazon Bedrock, nine-point sensitivity scale, 110-article validation set from Regulatory News Service. | [AWS Machine Learning Blog — LSEG Surveillance Guide](https://aws.amazon.com/blogs/machine-learning/how-london-stock-exchange-group-is-detecting-market-abuse-with-their-ai-powered-surveillance-guide-on-amazon-bedrock/) |
| S3 | Vendor announcement | NICE Actimize — SURVEIL-X Empowered with Generative AI (May 2025) | Evidence for communication analysis capabilities (150+ languages, misconduct-type explanations), false positive reduction (up to 85%), detection improvement (4x vs. rules-based). Platform scale: 1,000+ organizations, 70+ countries. Credit Suisse deployment (2023, 30% FP reduction) mentioned in related coverage. | [NICE press release](https://www.nice.com/press-releases/nice-actimize-empowers-surveil-x-with-generative-ai-launching-a-new-era-in-market-abuse-and-conduct-risk-detection) |
| S4 | Regulatory initiative | FCA — Market Abuse Surveillance TechSprint (May–July 2024) | Regulatory endorsement of AI/ML approaches for market surveillance. Nine international teams demonstrated isolation forests, Bayesian networks, and LLMs enhancing detection. 200+ participants from RegTech, financial institutions, and academia. | [FCA TechSprint page](https://www.fca.org.uk/publications/techsprints/market-abuse-surveillance) |
| S5 | Official docs | Nasdaq — Market Surveillance (SMARTS) Features | Platform capabilities: 200+ venues monitored, 10+ asset classes, 1B+ transactions/day, FIX/OMnet/ITCH protocol support, integrated analyst workbench. | [Nasdaq SMARTS features page](https://www.nasdaq.com/solutions/fintech/nasdaq-market-surveillance/features) |
| S6 | Domain standard | ESMA — Report on Suspicious Transaction and Order Reports (STORs) 2024 | Establishes operational scale: ~7,000 STOR notifications filed per year across EU NCAs. Breakdown by country (Germany 35%, France 15%) and instrument type (primarily shares). | [ESMA STOR Report 2024](https://www.esma.europa.eu/document/report-suspicious-transaction-and-order-reports-stors-2024) |
| S7 | Domain standard | FCA — How to Report Suspected Market Abuse (STOR Filing) | UK STOR filing requirements: who must file, "without delay" obligation, FCA Connect portal process, and UK MAR legal framework. | [FCA STOR guidance](https://www.fca.org.uk/markets/market-abuse/how-report-suspected-market-abuse-firm-or-trading-venue) |
| S8 | Primary deployment | Nasdaq — Generative AI Customer Story (AWS) | Additional context on Nasdaq's use of Amazon Bedrock and SageMaker for surveillance. Entity Research Copilot via Verafin. Serverless architecture. | [AWS Generative AI Customer Story — Nasdaq](https://aws.amazon.com/ai/generative-ai/customers/nasdaq/) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| 90–95% false positive rate in rules-based trade surveillance | S1, S3, S4 (consistent across all sources) |
| Nasdaq pilot: 80% pump-and-dump detection on historical data | S1 |
| Nasdaq pilot: 33% reduction in investigation time during PoC | S1 |
| Nasdaq platform serves 50+ exchanges and 20+ regulators; 1B+ transactions/day | S1, S5 |
| LSEG: 100% precision on non-sensitive news, 100% recall on price-sensitive content | S2 |
| NICE Actimize: up to 85% false positive reduction; 4x more true misconduct detected | S3 |
| NICE Actimize: 150+ languages; communication analysis explains findings with citations | S3 |
| Credit Suisse: 30% false positive reduction with SURVEIL-X (2023 deployment) | S3 (related vendor coverage) |
| FCA TechSprint: isolation forests, Bayesian networks, LLMs enhance detection | S4 |
| ~7,000 STOR notifications filed per year across EU | S6 |
| UK MAR requires STOR filing "without delay" via FCA Connect | S7 |
| Recommended operating model: human-on-the-loop with AI triage and human sign-off on STORs | Design recommendation informed by S1, S4, S7 |
| Expected economics: USD 0.8–1.4M/year in redirected analyst capacity for a mid-size broker-dealer | Estimated scenario model informed by S1, S3 |
| Unsupervised anomaly detection (isolation forest) as primary ML approach for trade surveillance | Design recommendation informed by S4 |
| News sensitivity classification as first-class enrichment for insider dealing alerts | Design recommendation informed by S2 |
