---
layout: use-case-detail
title: "Evaluation — Autonomous Municipal Building Permit Review"
uc_id: "UC-515"
uc_title: "Autonomous Municipal Building Permit Review"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
category_icon: "building"
industry: "Government / Public Sector"
complexity: "High"
status: "detailed"
slug: "UC-515-municipal-building-permit-review"
permalink: /use-cases/UC-515-municipal-building-permit-review/evaluation/
---

## Decision Summary

The evidence for AI-assisted building permit pre-screening is strong and growing. Multiple U.S. cities have signed multi-million-dollar contracts, and early deployments report large cycle-time reductions. The evidence is strongest for residential permits; commercial and complex structural categories have less production data. The business case holds if the jurisdiction processes enough applications to justify the platform cost (roughly 3,000+ per year) and if the code rule base is kept current. The primary risk is not technical failure but organizational — departments must invest in code digitization and change examiner workflows.

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| City of Austin — Archistar pilot (2024) | 75% accuracy on first residential pilot; 345-day average review backlog pre-deployment | Accuracy is usable for pre-screening but not for autonomous approval. The backlog baseline shows the scale of the problem AI must address. |
| LA County — eCheck pilot (July 2025) | Plan check completed in ~6 days, 2x faster than pre-wildfire baseline | Disaster recovery created an extreme volume spike; AI pre-screening maintained throughput that would have required months under manual-only review. |
| City of Denver — CivCheck contract (March 2026) | $4.6M / 5-year contract; first-pass acceptance target of 80%, up from 37% baseline | Denver's 37% baseline confirms that most applications arrive non-compliant. Doubling first-pass acceptance would cut correction cycles roughly in half. |
| Honolulu DPP — CivCheck launch (December 2025) | Permit pre-check times compressed from ~6 months to days | Pre-screening moved the bottleneck from examiner queue wait to applicant correction time, which applicants control. |
| CivCheck / Clariti — vendor-reported (2025) | 97% accuracy on code interpretation; 99% code book coverage | Vendor-reported; not independently audited. If accurate, this exceeds the Austin pilot accuracy, possibly reflecting a more mature product or different accuracy definition. |
| Hamilton, Ontario — AI scanning pilot | 60% decrease in permit processing times | Published by municipal source; small city provides evidence that the approach works outside large U.S. metro areas. |

## Assumptions And Scenario Model

The following scenario models a mid-size U.S. city building department. Values are estimated unless marked as published.

| Assumption | Value | Basis |
|------------|-------|-------|
| Annual residential permit applications | 8,000 | Mid-size city average; Denver processes ~10,000+ across all types |
| Average examiner fully loaded cost | $110,000/year | Published salary ranges of $70K–$120K plus benefits overhead |
| Examiner capacity (residential reviews per year) | 250–350 | Estimated from 15–30 reviews/month reported in brief, accounting for non-review duties |
| Current first-pass acceptance rate | 35–40% | Denver published 37%; consistent with industry estimates |
| Target first-pass acceptance rate with AI pre-screen | 75–80% | Denver's target of 80%; CivCheck claims this is achievable |
| AI platform annual cost | $700K–$1.2M/year | Estimated from Austin ($3.5M / 3 years ≈ $1.17M/year) and Denver ($4.6M / 5 years ≈ $920K/year) |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current annual review labor cost** | $2.5M–$3.5M (estimated) | 25–30 examiners at $110K fully loaded; typical for a department handling 8,000+ residential applications |
| **Expected steady-state cost** | $2.0M–$2.8M (estimated) | Same headcount repurposed to higher-value work (commercial, complex structural); some attrition absorbed without backfill |
| **Expected benefit** | $500K–$900K/year in avoided backfill and overtime; additional unquantified benefit in housing delivery speed | The primary savings come from not replacing retiring examiners and eliminating overtime during volume spikes |
| **Implementation cost** | $800K–$1.5M first year (estimated) | Platform license ($700K–$1.2M) plus code digitization, integration, and pilot support ($100K–$300K internal effort) |
| **Payback view** | 12–24 months (estimated) | Platform cost is recovered if 3–5 examiner positions are absorbed through attrition rather than refilled; faster housing delivery benefits are harder to quantify but politically significant |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| **Parser accuracy on clean residential plans** | Strength: residential floor plans are the most standardized drawing type; high parser accuracy reported across deployments | Maintain a labeled test set of 200+ plans; re-benchmark quarterly |
| **Parser accuracy on complex or poor-quality drawings** | Risk: scanned hand-drawn plans, heavily annotated sheets, and non-standard formats degrade extraction accuracy | Route low-confidence parses directly to examiner queue without a compliance report; do not publish an unreliable pre-screen |
| **Code rule currency** | Risk: local code amendments can take effect between ICC code cycles; stale rules produce wrong findings that erode examiner trust | Assign a code-maintenance role; each amendment triggers a rule update, test suite update, and re-validation before going live |
| **Examiner trust and adoption** | Risk: if examiners view AI as a job threat or produce findings they frequently override, adoption stalls | Position AI as pre-screening that reduces drudge work, not as examiner replacement. Track and publish override data transparently. Denver's planning department framed it as freeing staff for "more complex parts of their job." |
| **Vendor lock-in** | Risk: proprietary code digitization creates switching costs | Require that digitized rules are exportable in a documented format; include data portability clause in contract |
| **Political and procurement friction** | Risk: municipal procurement cycles are slow; council approval adds 3–6 months; elected officials may be skeptical of AI spending | Denver's 10-1 council approval with a built-in one-year review clause is a pragmatic model; start with a funded pilot, prove metrics, then expand |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| **AI-wrong override rate** | Measures how often examiners disagree with an AI finding because the AI was incorrect (not discretionary) | < 10% within 90 days |
| **First-pass acceptance rate** | Measures whether pre-screening actually improves submission quality | Increase from baseline (e.g., 37%) to ≥ 60% within 6 months |
| **Median time from submission to compliance report delivery** | Measures whether the AI meets the one-business-day SLA | ≤ 1 business day for 95% of residential applications |
| **Correction cycles per application** | Measures whether pre-screening reduces back-and-forth | ≥ 30% reduction vs. non-pre-screened cohort |
| **Examiner satisfaction (survey)** | Measures whether the tool is perceived as helpful rather than burdensome | ≥ 70% positive on quarterly survey |

## Open Questions

- How should accuracy standards differ between residential (high-volume, rule-based) and commercial (lower-volume, more judgment-intensive) project types? Most deployments have started with residential; the threshold for commercial readiness is not yet established.
- What is the right contractual model for code digitization ownership — should the municipality own the digitized rule base, or is it acceptable for the vendor to maintain it as a managed service? Denver and Austin took different approaches.
- How will AI pre-screening interact with third-party plan review firms that some jurisdictions use for overflow? The AI tool may reduce demand for third-party reviewers, creating budget and contract implications.
- As more cities digitize their local codes, is there an opportunity for a shared code repository across jurisdictions adopting the same base ICC codes? ICC Digital Codes provides the base, but local amendments are fragmented.
