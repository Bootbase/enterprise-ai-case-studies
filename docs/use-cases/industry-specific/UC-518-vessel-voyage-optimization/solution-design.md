---
layout: use-case-detail
title: "Solution Design — Autonomous Vessel Voyage Optimization and Fleet Decarbonization"
uc_id: "UC-518"
uc_title: "Autonomous Vessel Voyage Optimization and Fleet Decarbonization"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "Industry-Specific"
category_icon: "🚢"
industry: "Maritime / Shipping"
complexity: "High"
status: "detailed"
slug: "UC-518-vessel-voyage-optimization"
permalink: /use-cases/UC-518-vessel-voyage-optimization/solution-design/
---

## What This Design Covers

This design addresses how a ship operator can continuously optimize vessel speed profiles and routes across a managed fleet, reduce bunker fuel consumption by 4–12% per voyage, and maintain CII ratings at C or above as IMO thresholds tighten annually. The system operates as a decision-support layer: AI generates recommendations, deterministic engines enforce safety and compliance rules, and human operators — masters at sea, fleet managers ashore — retain all final authority.

## Recommended Operating Model

| Decision Area | Recommendation |
|---------------|----------------|
| **Autonomy Model** | Advisory with optional closed-loop speed control. AI recommends route and speed; master or shore-side ops approve. Autonomous RPM adjustment (like DeepSea HyperPilot) is opt-in per vessel after validation. |
| **System of Record** | Fleet management system (e.g., Veson IMOS, Danaos) remains authoritative for commercial fixtures, voyage orders, and P&L. The optimization platform writes recommendations back but does not own commercial state. |
| **Human Decision Points** | Master approves or overrides every route/speed recommendation. Shore-side ops review fleet CII projections weekly. Chartering desk validates speed-consumption warranties before fixture confirmation. |
| **Primary Value Driver** | Fuel cost reduction through continuous speed-profile optimization. CII compliance preservation is the secondary driver, preventing charter-rate discounts and corrective action plans. |

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SHORE-SIDE PLATFORM                        │
│                                                                     │
│  ┌──────────────┐   ┌──────────────────┐   ┌───────────────────┐   │
│  │ Data Ingest  │──▸│  Digital Twin     │──▸│ Optimization      │   │
│  │ Service      │   │  Engine           │   │ Engine            │   │
│  │              │   │                   │   │ (route + speed)   │   │
│  │ • AIS feed   │   │ • Hull model      │   │                   │   │
│  │ • Sensor API │   │ • Engine curves   │   │ • Weather fusion  │   │
│  │ • Weather    │   │ • Fouling state   │   │ • CII projection  │   │
│  │ • Port data  │   │ • Trim tables     │   │ • Multi-objective │   │
│  └──────────────┘   └──────────────────┘   └────────┬──────────┘   │
│                                                      │              │
│  ┌──────────────────────────────────────────────┐    │              │
│  │          Fleet Dashboard & API               │◂───┘              │
│  │  • Per-vessel recommendation + trade-offs    │                   │
│  │  • Fleet CII heatmap + compliance alerts     │                   │
│  │  • Chartering speed-consumption estimates    │                   │
│  └──────────────────────┬───────────────────────┘                   │
└─────────────────────────┼───────────────────────────────────────────┘
                          │ Satellite link (VSAT / LEO)
┌─────────────────────────┼───────────────────────────────────────────┐
│  VESSEL                 ▼                                           │
│  ┌──────────────┐   ┌──────────────────┐   ┌───────────────────┐   │
│  │ Edge Gateway │──▸│ On-board Agent   │──▸│ Bridge Display    │   │
│  │ (sensor hub) │   │ (local cache +   │   │ (ECDIS overlay /  │   │
│  │              │   │  fallback logic) │   │  dedicated screen)│   │
│  │ • NMEA bus   │   │                   │   │                   │   │
│  │ • Fuel flow  │   │ • Stores last     │   │ • Speed/route     │   │
│  │ • Shaft RPM  │   │   recommendation  │   │   recommendation  │   │
│  │ • Draft/trim │   │ • Runs offline    │   │ • Trade-off view  │   │
│  └──────────────┘   └──────────────────┘   └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Role | Notes |
|-----------|------|-------|
| **Data Ingest Service** | Collects sensor telemetry, AIS positions, weather forecasts, and port schedules into a unified time-series store | Must handle intermittent satellite connectivity; buffers on-vessel data and syncs when link is available |
| **Digital Twin Engine** | Maintains a vessel-specific performance model reflecting current hull fouling, engine degradation, and trim response | Calibrated continuously from high-frequency sensor data; replaces generic sea-trial curves |
| **Optimization Engine** | Computes optimal speed profile and route segments by balancing fuel cost, ETA constraints, CII budget, and safety margins | Multi-objective solver; weather and ocean forecasts are primary inputs alongside the digital twin |
| **Fleet Dashboard & API** | Presents recommendations, CII projections, and trade-off analysis to shore-side and on-board users | Exposes API for integration with fleet management and chartering systems |
| **Edge Gateway** | Aggregates on-board sensor data (NMEA 0183/2000, fuel flow, shaft power) and transmits to shore | Runs on vessel hardware; handles protocol translation and local buffering |
| **On-board Agent** | Caches the latest recommendation and provides fallback optimization when satellite link is unavailable | Lightweight model; degrades gracefully to last-known-good speed profile |

## End-to-End Flow

| Step | What Happens | Owner |
|------|--------------|-------|
| 1 | Voyage order created in fleet management system; fixture details (laycan, speed warranty, cargo) sent to optimization platform via API | Chartering desk |
| 2 | Digital twin loads vessel's current performance profile; optimization engine ingests weather forecasts (ECMWF/GFS), ocean currents, and port congestion data | Platform (automated) |
| 3 | Optimization engine computes optimal speed profile and route, producing a recommendation with quantified trade-offs (fuel saved vs. ETA impact vs. CII effect) | Platform (automated) |
| 4 | Recommendation displayed on bridge and shore dashboard; master reviews and accepts, modifies, or overrides | Master / Fleet ops |
| 5 | During voyage, platform re-optimizes every 1–6 hours as weather forecasts update and vessel position changes; revised recommendations pushed to bridge | Platform (automated) |
| 6 | Post-voyage, actual performance compared against plan; digital twin recalibrated; CII impact logged for annual reporting | Performance team |

## AI Responsibilities and Boundaries

| Workflow Area | AI Does | Deterministic System Does | Human Owns |
|---------------|---------|---------------------------|------------|
| **Route planning** | Generates candidate routes considering weather, currents, and traffic density | Enforces SOLAS safety zones, traffic separation schemes, and draft restrictions | Master approves final route; overrides in restricted waters |
| **Speed optimization** | Recommends speed profile balancing fuel, ETA, and CII budget | Enforces minimum maneuvering speed, charter-party speed clauses, and engine safe-operating limits | Master adjusts speed for sea conditions the model cannot observe (visibility, ice, debris) |
| **CII projection** | Forecasts year-end CII rating per vessel and fleet based on planned voyages | Calculates attained CII using IMO DCS formula (CO₂ / capacity × distance) | Sustainability manager decides fleet-level interventions (slow-steam campaigns, hull cleanings, vessel swaps) |
| **Digital twin calibration** | Learns hull fouling rate and engine degradation from sensor deltas over time | Flags sensor drift or anomalous readings for maintenance review | Technical superintendent decides when to drydock or overhaul |

## Integration Seams

| System | Integration Method | Why It Matters |
|--------|--------------------|----------------|
| **Fleet management (Veson IMOS, Danaos, etc.)** | REST API for voyage orders, fixtures, and speed warranties | Commercial state lives here; optimization must respect laycan and charter terms |
| **Weather data (ECMWF, GFS, Spire)** | Scheduled GRIB file pull or streaming API; 6-hourly forecast refresh | Route quality depends on forecast accuracy; ECMWF wave model (HRES-WAM) is the primary input |
| **AIS data provider** | Streaming AIS feed (e.g., MarineTraffic, Spire) | Used for port congestion estimation and traffic-density inputs to route planning |
| **On-board sensor bus (NMEA 0183/2000)** | Edge gateway translates NMEA sentences to structured telemetry; transmits via satellite | Fuel flow, shaft power, GPS, draft, and trim are the minimum sensor set for digital twin calibration |
| **ECDIS / bridge systems** | IEC 61174 route-exchange format or dedicated display overlay | Recommendations must be visible to the master without requiring a separate workstation |
| **IMO DCS / flag-state reporting** | Annual data export in IMO GISIS format | CII rating calculation and corrective action plan submission are regulatory obligations |

## Control Model

| Risk | Control |
|------|---------|
| **Unsafe route recommendation** (e.g., routing through heavy weather to save fuel) | Hard safety constraints in the optimization solver: maximum significant wave height, wind speed limits, traffic separation compliance. SOLAS constraints are non-negotiable inputs, not soft objectives. |
| **CII projection error leading to false compliance confidence** | Conservative bias in CII projections (use 90th-percentile weather scenarios for remaining voyages). Weekly shore-side review of fleet CII trajectory with manual override capability. |
| **Sensor data quality degradation** | Automated anomaly detection on incoming telemetry; digital twin falls back to last-calibrated state if sensor quality drops below threshold. Alerts technical superintendent. |
| **Satellite link loss during voyage** | On-board agent caches last recommendation and runs a simplified offline model. Master follows standing speed orders until connectivity restores. |
| **Over-reliance on AI recommendations** | Master retains statutory authority under SOLAS. All recommendations logged with acceptance/rejection and reason. Periodic audits of override rates to detect automation bias. |

## Reference Technology Stack

| Layer | Default Choice | Reason | Viable Alternative |
|-------|----------------|--------|--------------------|
| **Model layer** | Gradient-boosted ensemble (XGBoost/LightGBM) for fuel-consumption prediction; physics-informed constraints for hull resistance | Interpretable, fast inference, works well with tabular sensor + weather features; physics priors prevent unrealistic extrapolation | Deep RL (DDPG/PPO) for joint route-speed optimization in complex multi-port voyages |
| **Orchestration** | Event-driven pipeline (Kafka + scheduled batch for forecast ingestion) | Handles intermittent vessel connectivity and high-frequency sensor streams; decouples ingest from optimization | Time-triggered batch pipeline if fleet is small (<50 vessels) |
| **Data store** | Time-series DB (TimescaleDB or InfluxDB) for sensor telemetry; PostgreSQL for voyage state | Sensor data is naturally time-series; voyage and fixture data is relational | Cloud-managed alternatives (Azure Data Explorer, AWS Timestream) |
| **Observability** | Grafana dashboards over Prometheus metrics; structured logging for recommendation audit trail | Standard open-source stack; audit trail is critical for regulatory and commercial dispute resolution | Datadog or equivalent SaaS for smaller teams |

## Key Design Decisions

| Decision | Choice | Why It Fits This Use Case |
|----------|--------|---------------------------|
| **Advisory-first, not autonomous-first** | Recommendations require master approval; autonomous RPM control is opt-in | Statutory requirement (SOLAS) and operator trust. DeepSea's HyperPilot shows autonomous speed control is technically viable (DNV type-approved), but most fleets start advisory. |
| **Vessel-specific digital twin over generic curves** | Each vessel gets its own learned performance model | Sea-trial curves degrade as hulls foul and engines age. DeepSea/EPS achieved ±1% fuel forecast accuracy with vessel-specific twins vs. ±10–15% with generic curves. |
| **Multi-objective optimization (fuel + ETA + CII)** | Single solver balances competing objectives with operator-set priority weights | Fuel-only optimization ignores schedule penalties; CII-only optimization ignores commercial reality. Operators need the trade-off surface, not a single answer. |
| **Edge agent with offline fallback** | On-board component caches recommendations and runs degraded optimization when offline | Satellite connectivity is intermittent and expensive. Vessels must have a usable recommendation even during link outages. |
| **Shore-side fleet CII management layer** | Aggregates per-vessel CII projections into fleet-level compliance view | CII is an annual per-vessel metric, but fleet managers make portfolio decisions (which vessels to slow-steam, when to drydock) that are inherently cross-vessel. |
