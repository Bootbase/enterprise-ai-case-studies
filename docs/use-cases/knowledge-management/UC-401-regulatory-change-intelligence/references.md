---
layout: use-case-detail
title: "References — Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
uc_id: "UC-401"
uc_title: "Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
detail_type: "references"
detail_title: "References"
category: "Knowledge Management"
category_icon: "book-open"
industry: "Cross-Industry (Financial Services, Pharmaceutical, Healthcare, Energy, Insurance)"
complexity: "High"
status: "detailed"
slug: "UC-401-regulatory-change-intelligence"
permalink: /use-cases/UC-401-regulatory-change-intelligence/references/
---

## Source Quality Notes

The strongest evidence in this case study comes from the Ascent/ING/CommBank MiFID II pilot (S2, S3), where obligation extraction accuracy was independently verified at 95% by law firm Pinsent Masons — a rare instance of third-party validation in RegTech. CUBE's scale claims (S1) are supported by its ~1,000 customer base and the Thomson Reuters RI acquisition (S5), though specific accuracy metrics for CUBE's AI extraction are not publicly available. The BPI bank compliance survey (S6) is a primary industry survey of 20 banks covering 2016-2023, providing the most rigorous data on compliance labor trends. Deloitte's compliance cost data (S7) is widely cited but the specific "60%+ increase" figure lacks a detailed published methodology. The Wolters Kluwer launch (S4) is a vendor announcement with no published deployment metrics yet. 4CRisk's speed claims (S10) are vendor-reported without independent verification. The Icon Solutions architecture article (S9) describes a reference architecture, not a named production deployment. Where claims rely on vendor marketing rather than independently verified data, the other files note this explicitly.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | CUBE RegPlatform — enterprise regulatory compliance software | Scale of regulatory content coverage (10,000+ issuing bodies, 750 jurisdictions, 80 languages) and AI-powered automated regulatory intelligence approach. | [CUBE RegPlatform](https://cube.global/solutions/cube-regplatform) |
| S2 | Primary deployment | Ascent RegTech — ING and CBA MiFID II/MiFIR obligation extraction pilot | Core evidence for AI obligation extraction: 1.5 million paragraphs processed, 95% accuracy verified by Pinsent Masons, FCA-observed pilot. | [Ascent Blog](https://www.ascentregtech.com/blog/ing-and-cba-pinpoint-mifid-ii-mifir-obligations-in-2-5-minutes-using-ascent/) |
| S3 | Analysis | Computerworld — "CBA reveals promising regtech AI results, proceeds with caution" | Independent reporting on the ING/CommBank pilot: 95% accuracy, 200-step AI pipeline, 6 months manual work compressed to 2 weeks, and CBA's caution about human oversight requirements. | [Computerworld](https://www.computerworld.com/article/1654353/cba-reveals-promising-regtech-ai-results-proceeds-with-caution.html) |
| S4 | Primary deployment | Wolters Kluwer — Compliance Intelligence launch announcement (October 2025) | Validates market direction: a major compliance content vendor shipping an AI-native regulatory change management product combining structured data, human oversight, and Expert AI workflows. | [Wolters Kluwer News](https://www.wolterskluwer.com/en/news/wolters-kluwer-launches-compliance-intelligence) |
| S5 | Primary deployment | PRNewswire — CUBE completes acquisition of Thomson Reuters Regulatory Intelligence and Oden | Consolidation of the largest regulatory content library. ~1,000 customers, ~200 enterprise accounts (~40% of Tier 1 FIs), 6 operational hubs across 15 countries. | [PRNewswire](https://www.prnewswire.com/news-releases/cube-completes-acquisition-of-thomson-reuters-regulatory-intelligence-and-oden-businesses-302341223.html) |
| S6 | Domain standard | Bank Policy Institute — "Survey Finds Compliance Is Growing Demand on Bank Resources" (2016-2023) | Primary survey data: 61% increase in compliance hours, C-Suite compliance time from 24% to 42%, IT compliance budget from 9.6% to 13.4%. Survey of 20 banks. | [BPI](https://bpi.com/survey-finds-compliance-is-growing-demand-on-bank-resources/) |
| S7 | Analysis | Deloitte — "Cost of Compliance and Regulatory Productivity" | Compliance operating costs up 60%+ since pre-financial crisis levels. Widely cited industry benchmark for compliance cost trends. | [Deloitte](https://www.deloitte.com/us/en/services/consulting/articles/cost-of-compliance-regulatory-productivity.html) |
| S8 | Analysis | A-Team Insight — "Corlytics Enforcement Data Signals Elevated Compliance Risks" | Q3 2024 enforcement penalties up 300% vs Q3 2023. SEC recordkeeping fines $2.7B since 2021. Documents accelerating enforcement risk. | [A-Team Insight](https://a-teaminsight.com/blog/corlytics-enforcement-data-signals-elevated-compliance-risks/) |
| S9 | Analysis | Icon Solutions — "How Agentic AI is Redefining Regulatory Change" | Reference architecture for a six-agent regulatory change management system: research, triage, impact assessment, documentation, operational task, and audit agents. Describes lead-time reduction from weeks to days. | [Icon Solutions](https://iconsolutions.com/blog/how-agentic-ai-is-redefining-regulatory-change) |
| S10 | Primary deployment | 4CRisk.ai — AI-powered regulatory change management | Domain-specific specialized language models (SLMs) for obligation extraction. Published speed claims: 20X faster horizon scanning, 5X faster applicability analysis. 2,400+ regulatory sources. | [4CRisk](https://www.4crisk.ai/regulatory-change-management) |
| S11 | Primary deployment | CUBE — ServiceNow partnership and connector | Production integration pattern: no-code CUBE Connector maps obligations directly to policies, risks, and controls in ServiceNow GRC Regulatory Change Management module. | [CUBE ServiceNow Partnership](https://cube.global/partners/our-partners/servicenow) |
| S12 | Analysis | Fintech Global — "How are AI Agents transforming the future of compliance?" | Survey of RegTech vendors deploying AI agents for compliance: 4CRisk, Cardamon, Red Oak, Flagright, and others. Describes the 80% automation + 20% human-in-the-loop model and explainability requirements. | [Fintech Global](https://fintech.global/2025/12/16/how-are-ai-agents-transforming-the-future-of-compliance/) |
| S13 | Primary deployment | Commonwealth Bank of Australia — CBA and ING RegTech pilot announcement | First-party announcement of the MiFID II pilot: 1.5 million paragraphs processed using NLP and AI, FCA as observer, hundreds of hours saved. | [CommBank Newsroom](https://www.commbank.com.au/guidance/newsroom/cba-ing-regtech-pilot-201802.html) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| CUBE tracks 10,000+ issuing bodies across 750 jurisdictions in 80 languages | S1, S5 |
| CUBE acquired Thomson Reuters Regulatory Intelligence (Dec 2024); ~1,000 customers, ~200 enterprise, ~40% of Tier 1 FIs | S5 |
| ING/CommBank MiFID II pilot: 1.5M paragraphs, 95% accuracy, verified by Pinsent Masons | S2, S3, S13 |
| MiFID II obligation extraction: 6 months manual → 2 weeks with AI; 200-step AI pipeline | S3 |
| Wolters Kluwer Compliance Intelligence launched October 2025; combines structured data, human oversight, and Expert AI | S4 |
| Compliance operating costs up 60%+ since pre-financial crisis levels | S7 |
| Employee hours on compliance up 61% (2016-2023); C-Suite compliance time 24% → 42% | S6 |
| Q3 2024 enforcement penalties up 300% vs Q3 2023; SEC recordkeeping fines $2.7B since 2021 | S8 |
| Six-agent architecture for regulatory change management (research, triage, impact, documentation, operational, audit) | S9 |
| Domain-specific SLMs for obligation extraction: 20X faster scanning, 5X faster applicability analysis | S10 |
| CUBE-ServiceNow Connector: no-code obligation-to-policy-risk-control mapping in GRC | S11 |
| RegTech vendors deploying 80% automation + 20% human-in-the-loop model for compliance AI | S12 |
| Confidence-gated human review as operating model for AI-assisted compliance | S4, S9, S12 |
| Scenario model: 1,000 compliance FTEs, $150/hour, 12 hours/week on monitoring | S6 (compliance time data); cost range is industry estimate |
| Implementation cost estimate: $2-5M for Phase 1-4 | Design recommendation, not published |
