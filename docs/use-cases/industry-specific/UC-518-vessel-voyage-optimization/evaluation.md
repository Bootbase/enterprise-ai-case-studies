---
layout: use-case-detail
title: "Evaluation — Autonomous Vessel Voyage Optimization and Fleet Decarbonization"
uc_id: "UC-518"
uc_title: "Autonomous Vessel Voyage Optimization and Fleet Decarbonization"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
category_icon: "🚢"
industry: "Maritime / Shipping"
complexity: "High"
status: "detailed"
slug: "UC-518-vessel-voyage-optimization"
permalink: /use-cases/UC-518-vessel-voyage-optimization/evaluation/
---

## Decision Summary

The business case for AI-driven voyage optimization is strong and well-evidenced. Three independent production deployments — Maersk (130+ vessels), Orca AI (1,200+ vessels), and DeepSea Technologies (300+ vessels at EPS alone) — report fuel savings of 3–12% per voyage. At current bunker prices ($550–650/tonne VLSFO), even a conservative 5% reduction on a mid-size fleet produces seven-figure annual savings. The IMO CII regulation and EU ETS phase-in create a tightening compliance floor that makes inaction increasingly expensive. The main risk is not whether the technology works but whether a given operator can achieve sufficient sensor data quality and crew adoption to realize the published ranges.

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| Maersk — NavAssist on 130 container ships (2025) | Up to 12% fuel reduction in pilot; 9.2% fleet-wide; 16% ETA accuracy improvement; $300M+ annual savings attributed to AI initiatives | Largest container line validates double-digit fuel savings at fleet scale. ETA improvement shows secondary commercial value. |
| Orca AI — 1,200+ vessels across Anglo-Eastern, Seaspan, Gram Car Carriers (2024–2025) | $100K fuel savings per vessel per year; 500 MT CO₂ reduction per ship; 195,000 tonnes total CO₂ reduction in 2024 | Cross-fleet deployment proves the approach works on heterogeneous vessel types (tankers, bulkers, container ships, car carriers). |
| DeepSea Technologies — EPS 300-ship fleet (2024) | Weekly fuel forecasts accurate within 1%; 4–10% fuel savings range across deployments | Vessel-specific digital twins dramatically improve prediction accuracy over generic performance curves. |
| DeepSea / Wallenius Wilhelmsen | Target of up to 10% fuel savings across dozens of vessels | Car-carrier operator validates applicability beyond container and tanker segments. |
| IMO-Norway GreenVoyage2050 — 339,390 container voyages analyzed | JIT arrival optimization reduces fuel and CO₂ by ~14% per voyage | Large-scale academic study confirms that speed optimization (the primary lever in voyage optimization) has significant fuel-reduction potential even without route changes. |
| Orca AI — Seaspan case study (2023–2024) | 37% decrease in close encounters; 35% increase in minimum vessel distance | Safety co-benefit: voyage optimization also reduces collision risk through better situational awareness. |

## Assumptions And Scenario Model

The following scenario models a mid-size fleet operator adopting voyage optimization across 100 vessels. All values are estimated unless noted as published.

| Assumption | Value | Basis |
|------------|-------|-------|
| Fleet size | 100 vessels (mix of container, bulk, tanker) | Mid-size operator; scales linearly for larger fleets |
| Average annual fuel consumption per vessel | 8,000 MT (estimated) | Varies by vessel type; container ships ~12,000 MT, bulkers ~5,000 MT |
| Average bunker fuel price (VLSFO) | $600/tonne (estimated, based on 2024 average) | VLSFO traded $550–$1,000/tonne across major ports in 2024 |
| Fuel reduction achieved | 5% in year 1, 8% by year 3 (estimated) | Conservative vs. published 4–12% range; accounts for ramp-up and adoption curve |
| EU ETS carbon price | €80/tonne CO₂ (estimated) | EUA prices ranged €65–90 in 2024; forward curves suggest €90–100 for 2025–2026 |
| CII-related charter discount for D/E rating | 7.5% of time-charter earnings (estimated) | Brokers report 5–15% rate discounts; 7.5% is the midpoint |
| Platform license cost per vessel | $30,000–50,000/year (estimated) | Based on market positioning of DeepSea, Orca AI, and similar vendors |
| Edge hardware cost per vessel (one-time) | $10,000–25,000 (estimated) | Sensor upgrades, gateway hardware, installation. Lower if vessel already has high-frequency sensors. |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current annual fuel cost (fleet)** | $480M (estimated: 100 vessels × 8,000 MT × $600/MT) | Fuel is 50–60% of vessel OPEX |
| **Year 1 fuel savings** | $24M (estimated: 5% of $480M) | Conservative; some vessels may see 8–12% while others ramp up |
| **Year 3 fuel savings** | $38M (estimated: 8% of $480M) | Reflects fleet-wide adoption and digital twin maturity |
| **EU ETS cost avoided** | $5–8M/year (estimated: 5–8% of ~100K tonnes CO₂ × €80) | Phase-in reaches 100% of emissions from 2026; savings grow as coverage increases |
| **CII discount avoidance** | $2–5M/year (estimated) | Depends on how many vessels would otherwise slip to D/E; prevented discount on time-charter earnings |
| **Annual platform cost** | $3–5M (estimated: 100 vessels × $30–50K license) | Excludes internal team cost for fleet performance management |
| **One-time hardware + integration** | $2–4M (estimated: 100 vessels × $20–40K average) | Higher for older vessels needing sensor upgrades; lower for modern tonnage |
| **Payback view** | 2–4 months on fuel savings alone (estimated) | Maersk's published $300M+ savings across ~700 vessels implies rapid payback; the 100-vessel scenario is proportionally consistent |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| **Evidence quality** | Strength: three independent fleet-scale deployments with published metrics (Maersk, Orca AI, DeepSea/EPS) | Cross-reference published savings ranges; run shadow-mode pilot to validate on own fleet before committing |
| **Sensor data quality** | Risk: older vessels may have unreliable or missing fuel flow meters; noon-report data is insufficient for digital twin calibration | Require minimum sensor set (fuel flow, shaft RPM, GPS, draft) as prerequisite for onboarding; invest in sensor upgrades for high-value vessels first |
| **Crew adoption** | Risk: masters may distrust or routinely override AI recommendations, negating fuel savings | Track acceptance rates; investigate high-rejection vessels; involve masters in pilot design; show trade-off rationale, not just a speed number |
| **Weather forecast error** | Risk: inaccurate forecasts (especially beyond 5 days) degrade optimization quality | Use ensemble forecasts for uncertainty quantification; re-optimize every 6 hours; shorter forecast horizons get higher weight |
| **Regulatory change** | Risk: IMO CII methodology may be revised (Phase 2 review runs 2026–2028); EU ETS scope expanding | Design CII calculation as a configurable module; monitor regulatory updates; conservative CII projections absorb methodology shifts |
| **Vendor lock-in** | Risk: proprietary digital twin models and sensor integrations create switching costs | Ensure data portability (own your sensor telemetry and voyage data); negotiate data-export clauses in vendor contracts |
| **Connectivity** | Risk: satellite link outages prevent real-time re-optimization | Edge agent with offline fallback; cache last recommendation; design system to degrade gracefully, not fail |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| **Fuel prediction MAPE** | Validates digital twin accuracy; determines whether recommendations are trustworthy | <5% MAPE on holdout voyage legs |
| **Actual fuel savings vs. baseline** | Proves the business case with real money | ≥3% average across pilot vessels over 3 months |
| **Master acceptance rate** | Measures operational trust and recommendation quality | ≥60% of recommendations accepted without modification |
| **CII projection accuracy** | Confirms the compliance management value proposition | Quarterly projected CII within ±5% of attained |
| **Recommendation safety compliance** | Non-negotiable; a single unsafe recommendation destroys trust | 100% SOLAS constraint compliance across all recommendations |
| **Sensor data uptime per vessel** | Data quality is the prerequisite for everything else | ≥95% of expected telemetry messages received per vessel per day |

## Open Questions

- How much does hull fouling rate vary by trade lane and season, and how quickly must the digital twin recalibrate after a drydocking or hull cleaning to avoid recommending stale speed profiles?
- What is the minimum viable sensor set for operators unwilling to invest in full instrumentation — can AIS-only digital twins (no fuel flow or shaft power) still deliver meaningful fuel savings?
- As IMO Phase 2 of the CII review (2026–2028) may revise the calculation methodology, how should operators hedge against rating-boundary changes that could retroactively reclassify compliant vessels?
- For multi-port voyages with intermediate cargo operations, how should the optimizer balance per-leg fuel efficiency against total-voyage CII and schedule constraints?
- What governance structure is needed when the optimization platform recommends actions that conflict with charterer instructions (e.g., slow-steaming vs. speed-warranty obligations)?
