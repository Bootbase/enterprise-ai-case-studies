---
layout: use-case-detail
title: "References — Autonomous Construction Progress Monitoring and Delay Prediction"
uc_id: "UC-512"
uc_title: "Autonomous Construction Progress Monitoring and Delay Prediction"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Construction"
complexity: "High"
status: "detailed"
slug: "UC-512-construction-progress-monitoring"
permalink: /use-cases/UC-512-construction-progress-monitoring/references/
---

## Source Quality Notes

The evidence base includes three primary deployment sources (Buildots/Intel, Doxel/Kaiser Permanente, Buildots/Sir Robert McAlpine) with published production metrics, and two secondary deployment sources (OpenSpace/JLL, OpenSpace/Vinci) with published but less granular results. The Intel case study is the most detailed, with specific rework and delay metrics published by Buildots. The Kaiser Permanente metrics (38% productivity, 96% cost accuracy) come from Doxel's published materials and press coverage; the underlying methodology is not fully disclosed. The McKinsey source provides widely cited industry baseline statistics. The buildingSMART, Autodesk, and Procore sources are official technical documentation. The MDPI paper provides peer-reviewed technical architecture for point cloud and IFC comparison methods.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | Buildots + Intel case study | 4 weeks delay avoided per fab, 4.3% rework cost reduction, 1,100+ model updates flagged. Most detailed published metrics for AI construction progress monitoring. | [Buildots -- Intel Case Study](https://pages.buildots.com/intel-case-study) |
| S2 | Primary deployment | Doxel + Kaiser Permanente -- Viewridge Medical Office | 38% productivity increase, 11% under budget, 96% cost-at-completion accuracy with 6x lead time. Demonstrates autonomous capture via robots with AI analytics. | [Doxel -- Construction Progress Tracking](https://doxel.ai/) |
| S3 | Primary deployment | Buildots + Sir Robert McAlpine -- UK-wide adoption | Tier 1 UK contractor adopted Buildots as preferred partner. Deployed on Royal Bournemouth Hospital and Nottingham NRC. Signals operational maturity beyond pilot stage. | [Construction Management -- Sir Robert McAlpine Adopts Buildots](https://constructionmanagement.co.uk/sir-robert-mcalpine-has-adopted-the-ai-technology-platform-buildots-as-a-preferred-partner/) |
| S4 | Secondary deployment | OpenSpace + JLL -- global project delivery | 50% travel cost reduction for remote verification. Rework avoidance valued at thousands to millions per project. | [OpenSpace -- JLL Case Study](https://www.openspace.ai/resources/case-studies/openspace-improves-jll-project-delivery-through-faster-more-complete-documentation/) |
| S5 | Secondary deployment | OpenSpace + Vinci -- 25 UK projects | 5,200 work-hours saved by automating progress photo capture and documentation across 25 projects. | [OpenSpace -- Visual Intelligence Platform](https://www.openspace.ai/) |
| S6 | Analysis | McKinsey -- The Construction Productivity Imperative | 98% of megaprojects overrun budgets by >30%; 77% are >40% late; $1.6T annual global inefficiency. Widely cited industry baseline. | [McKinsey -- Construction Productivity Imperative](https://www.mckinsey.com/capabilities/operations/our-insights/the-construction-productivity-imperative) |
| S7 | Domain standard | buildingSMART -- BIM Collaboration Format (BCF) | Defines the open standard for model-referenced issue tracking across BIM tools. Used in the design for deviation-to-issue handoff. | [buildingSMART -- BCF Standard](https://technical.buildingsmart.org/standards/bcf/) |
| S8 | Official docs | Autodesk Platform Services (APS) -- BIM 360 and ACC APIs | Model Derivative API for IFC access, Data Exchange Cloud Connector for IFC subsets. Primary BIM integration path. | [Autodesk -- BIM 360 API and Integrations](https://aps.autodesk.com/bim-360-apis-integrations) |
| S9 | Official docs | Procore Developer API | REST API for project management integration: observations, issues, daily logs, schedule sync. Primary PM integration path. | [Procore -- Developer Documentation](https://developers.procore.com/documentation/introduction) |
| S10 | Analysis | Automation of Construction Progress Monitoring by Integrating 3D Point Cloud Data with an IFC-Based BIM Model (MDPI Buildings, 2022) | Peer-reviewed technical architecture for automated progress monitoring using point cloud and IFC comparison. Describes voxel-based occupancy comparison method. | [MDPI -- Point Cloud and IFC Progress Monitoring](https://www.mdpi.com/2075-5309/12/10/1754) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| Intel: 4 weeks delay avoided per fab, 4.3% rework cost reduction, 1,100+ model updates flagged | S1 |
| Kaiser Permanente: 38% productivity increase, 11% under budget, 96% cost-at-completion accuracy | S2 |
| Sir Robert McAlpine adopted Buildots as preferred partner across UK projects | S3 |
| JLL: 50% travel cost reduction, rework avoidance valued at thousands to millions | S4 |
| Vinci: 5,200 work-hours saved across 25 UK projects | S5 |
| 98% of megaprojects overrun by >30%; $1.6T annual inefficiency; 4-6% rework cost baseline | S6 |
| BCF standard for model-referenced issue tracking and interoperability | S7 |
| Autodesk APS Model Derivative API and Data Exchange Cloud Connector for IFC | S8 |
| Procore REST API for observations, issues, and schedule sync | S9 |
| Voxel-based point cloud comparison with IFC for automated progress measurement | S10 |
| Semi-autonomous operating model: AI measures and predicts, humans decide and act | S1, S2, S3 |
| Daily 360-degree capture via hardhat cameras as standard capture method | S1, S3, S5 |
| CV models (YOLO, deep learning) for element detection over LLMs | S1, S10 |
| Scheduling tool remains authoritative for CPM and contractual milestones | S8, S9 |
| Delay prediction using pace-of-progress trends with confidence intervals | S1, S2 |
| IFC as interoperability format for BIM model access | S7, S8, S10 |
