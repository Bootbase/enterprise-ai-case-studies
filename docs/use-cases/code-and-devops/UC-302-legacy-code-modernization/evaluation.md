---
layout: use-case-detail
title: "Evaluation — Autonomous Legacy Code Modernization and Migration with Agentic AI"
uc_id: "UC-302"
uc_title: "Autonomous Legacy Code Modernization and Migration with Agentic AI"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Code & DevOps"
category_icon: "terminal"
industry: "Cross-Industry (Banking, Financial Services, Government, Insurance, Logistics, Telecommunications)"
complexity: "High"
status: "detailed"
slug: "UC-302-legacy-code-modernization"
permalink: /use-cases/UC-302-legacy-code-modernization/evaluation/
---

## Decision Summary

This is a strong use case if it is scoped correctly. Published results are strongest on code understanding, documentation, dependency analysis, and automated refactoring. They are thinner on fully autonomous cutover. The business case holds when AI compresses discovery and transformation work while deterministic validation and human governance stay in charge of release decisions. [S1][S4][S5][S8][S10]

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| National Organization for Social Insurance with IBM watsonx Code Assistant for Z [S1] | Up to 94% reduction in time to analyze superfluous COBOL code, 79% reduction in time to understand complex applications, and some analysis tasks reduced from 8 hours to 30 minutes | Clear published proof that AI materially improves legacy application understanding before transformation begins. |
| Nomura Research Institute using AWS Transform for mainframe [S4] | Analysis of complex components reduced from about one month to about one week | AI-assisted analysis can shorten the slowest specialist work, not just summarize code. |
| Bankdata and Microsoft open-source migration framework [S6][S7] | Seven-month collaboration produced a semi-autonomous COBOL-to-Java framework; Bankdata reports early tests can convert large volumes with relatively limited manual input | Feasible, but still bounded by hallucination and context-management issues in early iterations. |
| State of Utah ORSIS modernization [S9] | Rewrite was estimated at about US$200 million and five to ten years; automated refactoring completed in 18 months | Incremental refactoring or replatforming remains economically superior to greenfield rewrite for many regulated estates. |
| NN Group mainframe modernization [S10] | Over 10 million lines automatically transformed from COBOL to Java, 80% IT platform cost reduction, payback under three years; 40% of work still went to testing | Large-scale automation can pay off, but testing remains a major share of effort even after automated conversion. |

## Assumptions And Scenario Model

| Assumption | Value | Basis |
|------------|-------|-------|
| Pilot scope | One bounded domain of roughly 300K-800K lines plus its copybooks, JCL, schemas, and curated business scenarios | Estimated. Large enough to show reuse, small enough to validate safely. [S4][S7][S9][S10] |
| Operating model | Hybrid coexistence during pilot | Published. Kyndryl reports 99% of enterprises operate in hybrid environments, and Bankdata explicitly notes some modules are not equally migratable. [S7][S8] |
| Testing share of delivery effort | 40-50% of pilot effort | Mixed. Deloitte reports 40% of NN Group's work went to testing, while AWS says testing typically consumes more than half of modernization timelines and resources. [S5][S10] |
| AI acceleration range | 50-80% faster analysis and documentation, but only 15-30% end-to-end program effort reduction in an early wave | Mixed. Published acceleration is strongest in understanding and analysis. Testing and signoff still dominate release confidence. [S1][S4][S5] |
| Talent model | Internal platform team plus mainframe SMEs and external specialist help | Published. Kyndryl reports 70% of organizations struggle to find the right skills and 74% use external firms. [S8] |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current cost** | Published survey averages are about $7.2M for modernize-on programs and $6.8M for integrate-with programs; rewrite alternatives can be far higher | Published. Kyndryl reports 2025 averages, while Utah's rewrite option was about $200M. [S8][S9] |
| **Expected steady-state cost** | Estimated 70-85% of a comparable non-AI wave after the factory and validation harness are established | Estimated. The savings are real only when the organization can reuse prompts, dependency graphs, and test assets across multiple waves. |
| **Expected benefit** | Estimated 15-30% lower delivery effort on the first serious wave and 25-40% on later waves, with much larger savings in analysis time | Mixed. Published analysis gains are strong; later-wave savings depend on artifact reuse. [S1][S4][S8] |
| **Implementation cost** | Estimated $600K-$1.5M for the first enterprise-grade factory, including ingestion, validation, observability, and pilot change management | Estimated. Higher if the first wave also changes the database platform or transaction model. |
| **Payback view** | Estimated within the second or third modernization wave, not necessarily within the first pilot | Estimated. This is a reuse story; one-off migrations rarely justify a full factory. |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| Business-logic comprehension | Strength: published results show AI can materially reduce time spent understanding opaque COBOL estates. [S1][S4] | Treat generated documentation as a required artifact and keep SMEs focused on validating extracted rules. |
| Non-functional mismatch | Risk: some modules depend on mainframe-specific behavior such as batch throughput, I/O patterns, restart semantics, or latency envelopes. [S7] | Add a retain-or-redesign decision before code generation. Do not force every unit into refactor mode. |
| Testing bottleneck | Risk: testing still dominates timelines even when translation is automated. [S5][S10] | Budget the validation harness as core scope and track equivalence evidence from week one. |
| Compliance and security | Risk: regulated enterprises must preserve auditability, data protection, and traceability while introducing AI into the SDLC. [S8][S13] | Keep prompts, tools, and generated artifacts versioned. Use sanitized test data and immutable evidence packs. |
| Overstated autonomy | Risk: teams may interpret strong analysis gains as proof of safe autonomous release | Keep evaluation gates deterministic and separate model success from release success. The system earns broader autonomy only after pilot evidence exists. |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| Artifact completeness before generation | Prevents false confidence caused by missing copybooks, JCL, scheduler context, or schemas | 100% of pilot units have a signed-off artifact manifest |
| Analysis cycle time per complex unit | Measures whether the AI layer is removing real specialist bottlenecks | At least 50% faster than the pre-pilot baseline for selected units |
| First-pass compile rate | Shows whether generated code is structurally useful or just a drafting aid | At least 80% of generated units compile after the initial review cycle |
| Functional equivalence pass rate | The real go/no-go signal for modernization quality | 100% pass rate on high-criticality scenarios and no unexplained mismatches |
| SME review hours per unit | Validates whether the platform is actually reducing scarce expert dependence | Downward trend by the second wave |

## Open Questions

- What share of the target estate carries transaction or batch-window constraints that make straight COBOL-to-Java conversion the wrong answer?
- Can the enterprise produce enough sanitized test data and golden outputs to make dual-run comparison credible for regulated workloads?
- Which target should be standardized first: Java, .NET, or a mixed portfolio by domain?
- How much of the mainframe estate should remain on the mainframe long term because compliance, performance, or cost economics are still favorable there? [S7][S8]
