---
layout: use-case-detail
title: "References — Autonomous Vessel Voyage Optimization and Fleet Decarbonization"
uc_id: "UC-518"
uc_title: "Autonomous Vessel Voyage Optimization and Fleet Decarbonization"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "🚢"
industry: "Maritime / Shipping"
complexity: "High"
status: "detailed"
slug: "UC-518-vessel-voyage-optimization"
permalink: /use-cases/UC-518-vessel-voyage-optimization/references/
---

## Source Quality Notes

The evidence base for this use case is strong. Three primary sources (S1–S3) report production-scale fleet deployments with named customers and quantified fuel savings. Regulatory sources (S4–S6) are official documentation from the IMO and European Commission. The academic/technical sources (S7–S8) provide architectural and algorithmic grounding. S9 is a vendor press release used for deployment-scale data and corroborated by independent reporting. The main gap is that none of the primary deployment sources publish detailed methodology for how fuel savings were measured (e.g., baseline definition, weather normalization), which is typical for commercial disclosures.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | Maersk NavAssist deployment — EAN Networks reporting | Fleet-scale deployment metrics: 12% fuel reduction (pilot), 9.2% fleet-wide, 16% ETA improvement, $300M+ annual savings | [Maersk Launches AI-Powered Vessel Routing Platform](https://ean-network.com/maersk-launches-ai-powered-vessel-routing-platform-to-cut-emissions-and-improve-efficiency/) |
| S2 | Primary deployment | Orca AI — fleet deployment across Anglo-Eastern, Seaspan, and others | Cross-fleet deployment scale (1,200+ vessels), per-vessel savings ($100K/year, 500 MT CO₂), and safety co-benefits | [Orca AI](https://www.orca-ai.io/) |
| S3 | Primary deployment | DeepSea Technologies (Cassandra/Pythia) — EPS, Wallenius Wilhelmsen, G2 Ocean | Digital twin accuracy (±1% fuel forecast), 4–10% savings range, vessel-specific performance modeling approach | [DeepSea Technologies](https://www.deepsea.ai/) |
| S4 | Official docs | IMO EEXI and CII FAQ | CII regulation scope, rating methodology, corrective action requirements, tightening schedule | [IMO EEXI and CII FAQ](https://www.imo.org/en/mediacentre/hottopics/pages/eexi-cii-faq.aspx) |
| S5 | Domain standard | EU ETS Maritime FAQ — European Commission | EU ETS phase-in schedule (40%/70%/100%), scope of coverage, emissions types, geographic rules | [EU ETS Maritime FAQ](https://climate.ec.europa.eu/eu-action/transport-decarbonisation/reducing-emissions-shipping-sector/faq-maritime-transport-eu-emissions-trading-system-ets_en) |
| S6 | Analysis | IMO-Norway GreenVoyage2050 — JIT arrival study (339,390 voyages) | Academic-scale evidence that speed optimization reduces fuel by ~14% per voyage | [GreenVoyage2050 JIT Publication](https://greenvoyage2050.imo.org/publications/1289/) |
| S7 | Analysis | VesselAI architecture — Frontiers in Big Data (2023) | Technical architecture for maritime data ingestion, processing layers, and digital twin construction | [VesselAI Architecture Paper](https://www.frontiersin.org/journals/big-data/articles/10.3389/fdata.2023.1220348/full) |
| S8 | Analysis | Physics-informed RL for maritime routing — arXiv (2025) | Algorithmic approach: physics-informed state construction, DDPG/PPO for route-speed optimization, 6.6% fuel savings in simulation | [Physics-informed Offline RL for Maritime Routing](https://arxiv.org/abs/2603.17319) |
| S9 | Primary deployment | Orca AI Series B ($72.5M) — press release (May 2025) | Deployment scale confirmation: 1,200+ vessels, named fleet customers, funding validates market traction | [Orca AI Series B Announcement](https://www.prnewswire.com/news-releases/orca-ai-secures-72-5-million-investment-to-scale-autonomous-shipping-solutions-302447230.html) |
| S10 | Primary deployment | DeepSea HyperPilot DNV type approval — Nabtesco (July 2024) | First DNV-certified autonomous vessel speed control device; validates closed-loop optimization is technically and regulatorily viable | [Nabtesco HyperPilot DNV Approval](https://www.nabtesco.com/en/news/20240704-15281/) |
| S11 | Primary deployment | EPS confirms AI benefits — Offshore Energy | EPS 300-ship fleet deployment details, Cassandra platform, digital twin validation over six months | [EPS Confirms AI Benefits](https://www.offshore-energy.biz/eps-confirms-ai-benefits-in-implementing-its-sustainability-strategy/) |
| S12 | Analysis | DeepSea Technologies review — ShipUniverse | Platform component breakdown (Pythia, Cassandra, HyperPilot), 4–10% fuel savings, 20+ fleet deployments | [DeepSea Technologies Review](https://www.shipuniverse.com/company-spotlight/deepsea-technologies-review-from-raw-vessel-data-to-real-fuel-cuts/) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| Fuel savings of 4–12% per voyage from AI-driven optimization | S1, S2, S3, S6 |
| Maersk NavAssist: 12% pilot fuel reduction, 9.2% fleet-wide, $300M+ savings | S1 |
| Orca AI: 1,200+ vessels, $100K/vessel/year savings, 195K tonnes CO₂ reduced | S2, S9 |
| DeepSea/EPS: ±1% fuel forecast accuracy with digital twins | S3, S11 |
| DeepSea/Wallenius Wilhelmsen: up to 10% fuel savings target | S3, S12 |
| IMO CII regulation: mandatory since 2023, D/E corrective action, annual tightening | S4 |
| EU ETS phase-in: 40% (2025), 70% (2026), 100% (2027+); €65–90/tonne CO₂ | S5 |
| JIT arrival reduces fuel by ~14% per voyage (339K voyage study) | S6 |
| Maritime data architecture: Lambda/Kappa patterns, NMEA/AIS/GRIB ingestion | S7 |
| RL-based route-speed optimization: DDPG/PPO, physics-informed constraints | S8 |
| DNV type approval for autonomous vessel speed control (HyperPilot) | S10 |
| Safety co-benefit: 37% reduction in close encounters (Seaspan) | S2 |
| Bunker fuel is 50–60% of vessel OPEX; global market exceeds $126B | S1, S5 (market context from multiple industry sources) |
| 5–15% charter-rate discount for D/E CII rated vessels | S4 (regulation creates the mechanism; broker reports cited in index.md) |
| Solution design: advisory-first operating model with master authority | S10 (DNV approval shows autonomous is viable; advisory is the recommended starting point) |
| Implementation: XGBoost/LightGBM for fuel prediction, physics-informed solver | S7, S8 |
| Evaluation: scenario model for 100-vessel fleet economics | Estimated; ranges informed by S1, S2, S3 |
