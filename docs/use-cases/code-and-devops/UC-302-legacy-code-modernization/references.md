---
layout: use-case-detail
title: "References — Autonomous Legacy Code Modernization and Migration with Agentic AI"
uc_id: "UC-302"
uc_title: "Autonomous Legacy Code Modernization and Migration with Agentic AI"
detail_type: "references"
detail_title: "References"
category: "Code & DevOps"
category_icon: "terminal"
industry: "Cross-Industry (Banking, Financial Services, Government, Insurance, Logistics, Telecommunications)"
complexity: "High"
status: "detailed"
slug: "UC-302-legacy-code-modernization"
permalink: /use-cases/UC-302-legacy-code-modernization/references/
---

## Source Quality Notes

The evidence base is strongest on three areas. First, IBM's NOSI case study and AWS's published customer quote provide direct evidence that AI-assisted analysis materially speeds up legacy-code understanding. Second, AWS and IBM product documentation provide high-quality primary material on the actual modernization workflow, including decomposition, transformation, and semantic validation. Third, Deloitte's Utah and NN Group case studies provide strong non-AI baseline evidence about program economics, automated refactoring, and the continuing weight of testing. The weakest area is broad, independent evidence for fully autonomous large-estate migration. Bankdata and Microsoft's published work is valuable because it is concrete and technical, but it remains early-stage and should be treated as a design reference rather than proof of universal production outcomes. Kyndryl's survey is useful for market context, economics, talent, and compliance, but it is not a deployment case study. NIST SP 800-218A is control guidance, not performance evidence.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | IBM case study: National Organization for Social Insurance | Published deployment metrics for AI-assisted COBOL understanding and documentation speed | [National Organization for Social Insurance](https://www.ibm.com/case-studies/national-organization-for-social-insurance) |
| S2 | Official docs | IBM watsonx Code Assistant for Z overview | Official capability reference for understand, refactor, transform, and validate stages, plus role model | [About IBM watsonx Code Assistant for Z](https://www.ibm.com/docs/en/watsonx/watsonx-code-assistant-4z/2.x?topic=welcome-overview-watsonx-code-assistant-z) |
| S3 | Official docs | AWS Transform for modernizing mainframe applications user guide | Official workflow reference for analysis, decomposition, human-in-the-loop control, and supported legacy artifacts | [AWS Transform for modernizing mainframe applications](https://docs.aws.amazon.com/m2/latest/userguide/qt-webapp-mainframe.html) |
| S4 | Primary deployment / vendor announcement | AWS Transform GA blog with mainframe and Nomura Research Institute details | Published acceleration claims and named-customer quote for complex component analysis | [Transform Enterprise Workloads up to 4x Faster with Agentic AI](https://aws.amazon.com/blogs/migration-and-modernization/aws-transform-generally-available/) |
| S5 | Official technical write-up | AWS Transform testing blog | Detailed testing guidance for functional equivalence, data collection, comparison, and governance boundaries | [Accelerating mainframe modernization testing with AWS Transform](https://aws.amazon.com/blogs/migration-and-modernization/accelerating-mainframe-modernization-testing-with-aws-transform/) |
| S6 | Primary deployment | Bankdata news announcement | Direct statement of the seven-month Microsoft and Bankdata collaboration and the semi-autonomous COBOL-to-Java framework scope | [Microsoft and Bankdata launch open-source AI framework for modernizing legacy systems](https://www.bankdata.dk/about/news/microsoft-and-bankdata-launch-open-source-ai-framework-for-modernizing-legacy-systems) |
| S7 | Official technical write-up | Microsoft Azure blog on COBOL migration and mainframe modernization | Technical design reference for preprocessing, chunking, Graph RAG, worker-agent split, deterministic tests, and Semantic Kernel orchestration | [How We Use AI Agents for COBOL Migration and Mainframe Modernization](https://devblogs.microsoft.com/all-things-azure/how-we-use-ai-agents-for-cobol-migration-and-mainframe-modernization/) |
| S8 | Analysis / survey | Kyndryl 2025 State of Mainframe Modernization Survey Report | Market context for hybrid operating models, skills shortages, compliance pressure, program cost ranges, and ROI | [Kyndryl’s 2025 State of Mainframe Modernization Survey Report](https://www.kyndryl.com/content/dam/kyndrylprogram/doc/en/2025/mainframe-modernization-report.pdf) |
| S9 | Case study | Deloitte Insights: State of Utah ORSIS modernization | Baseline economics for rewrite vs automated refactoring and evidence for incremental migration | [The state of Utah moves from COBOL to cloud in 18 months](https://www.deloitte.com/us/en/insights/topics/technology-management/tech-trends/2024/legacy-modernization-mainframe-case-study.html?icid=top_legacy-modernization-mainframe-case-study) |
| S10 | Case study | Deloitte Insights: NN Group mainframe modernization | Large-scale automated transformation benchmark, testing share, cost takeout, and payback data | [IT modernization helps insurer future-proof applications](https://www.deloitte.com/us/en/insights/topics/technology-management/tech-trends/2024/it-modernization-helps-nn-group-future-proof-mainframe-applications.html) |
| S11 | Official docs | Microsoft Learn: ChatCompletionAgent | Official reference for the agent pattern used in the implementation guide's orchestration example | [Exploring the Semantic Kernel ChatCompletionAgent](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-types/chat-completion-agent) |
| S12 | Official docs | Microsoft Learn: Semantic Kernel plugins | Official reference for exposing deterministic modernization tools as plugins with function calling | [What is a Plugin?](https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/) |
| S13 | Domain standard | NIST SP 800-218A | Secure-development control guidance for AI-enabled software delivery and acquisition workflows | [NIST SP 800-218A](https://csrc.nist.gov/pubs/sp/800/218/a/final) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| AI-assisted legacy modernization is most credible when used first for understanding, documentation, and dependency analysis rather than unsupervised cutover | S1, S4, S6, S7 |
| IBM watsonx Code Assistant for Z supports understand, refactor, transform, and validate stages including semantic-equivalence validation | S2 |
| AWS Transform supports analysis, decomposition, human-in-the-loop modernization, and legacy artifacts including COBOL, JCL, CICS, Db2, and VSAM | S3, S4 |
| Testing is the primary release-confidence mechanism and often consumes 40% to more than half of modernization effort | S5, S10 |
| Not every COBOL module is equally migratable because of non-functional dependencies such as batch throughput, I/O handling, and JCL orchestration | S7 |
| Bankdata and Microsoft collaborated for seven months on a semi-autonomous COBOL-to-Java framework, and early iterations suffered from hallucination and context issues before workflow redesign | S6, S7 |
| Hybrid coexistence is the default enterprise modernization posture rather than a one-step mainframe exit | S7, S8 |
| Skills shortages and compliance pressure materially shape modernization operating models | S8 |
| Published survey economics: $7.2M modernize-on, $6.8M integrate-with, and 288-362% ROI ranges | S8 |
| Utah's ORSIS case shows why organizations favor incremental migration over rewrite when rewrite economics are prohibitive | S9 |
| NN Group demonstrates that large automated transformations can deliver material platform savings, but testing remains a major share of work | S10 |
| The implementation guide's orchestration pattern uses Semantic Kernel's documented ChatCompletionAgent and plugin model | S7, S11, S12 |
| The recommended control model uses versioned prompts, explicit tool boundaries, and auditable evidence packs for AI-enabled software delivery | S5, S12, S13 |
| Solution design sections on operating model, architecture, AI boundaries, and integration seams | S2, S3, S5, S7, S8 |
| Evaluation sections on evidence strength, assumptions, economics, and rollout KPIs | S1, S4, S5, S8, S9, S10 |
