---
layout: use-case-detail
title: "Implementation Guide — Autonomous Vessel Voyage Optimization and Fleet Decarbonization"
uc_id: "UC-518"
uc_title: "Autonomous Vessel Voyage Optimization and Fleet Decarbonization"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "🚢"
industry: "Maritime / Shipping"
complexity: "High"
status: "detailed"
slug: "UC-518-vessel-voyage-optimization"
permalink: /use-cases/UC-518-vessel-voyage-optimization/implementation-guide/
---

## Build Goal

Deliver a voyage optimization platform that ingests vessel sensor data and weather forecasts, maintains per-vessel digital twins, and produces speed-profile and route recommendations for a pilot fleet of 5–10 vessels. The first production boundary covers single-leg voyages with advisory recommendations displayed on a shore-side dashboard. Autonomous on-board speed control, multi-leg optimization, and fleet-wide CII portfolio management are second-release targets.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ services on Kubernetes | Dominant language for ML/scientific computing; containerized for fleet-scale horizontal scaling |
| **Model access** | XGBoost/LightGBM for fuel-consumption prediction; SciPy or OR-Tools for route-speed optimization solver | Tabular sensor + weather features suit gradient-boosted trees; physics-informed constraints integrate cleanly with optimization solvers |
| **Orchestration runtime** | Apache Kafka for sensor stream ingestion; Airflow for scheduled forecast pull and batch re-optimization | Decouples intermittent vessel telemetry from compute; Airflow handles the 6-hourly weather-forecast-triggered re-optimization cycle |
| **Core connectors** | NMEA parser (e.g., pynmea2) on edge; GRIB decoder (cfgrib/xarray) for weather; REST adapters for fleet management and AIS APIs | These are the actual data formats in the maritime domain |
| **Evaluation / tracing** | MLflow for model versioning and experiment tracking; Grafana + Prometheus for runtime metrics; structured JSON logs for recommendation audit trail | Audit trail is both a regulatory and commercial requirement (voyage disputes reference recommendation logs) |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Data foundation (8–10 weeks) | Sensor telemetry and weather data flowing reliably for pilot vessels; historical voyage data loaded | Edge gateway deployment on pilot vessels; NMEA-to-telemetry pipeline; weather GRIB ingestion; time-series store; historical data backfill |
| 2 — Digital twin and prediction model (6–8 weeks) | Per-vessel fuel-consumption model trained and validated against historical voyages | Digital twin calibration pipeline; XGBoost fuel-prediction model; backtesting harness comparing predicted vs. actual fuel per voyage leg |
| 3 — Optimization engine and dashboard (6–8 weeks) | Shore-side dashboard showing route/speed recommendations with trade-off analysis for pilot voyages | Multi-objective solver (fuel + ETA + CII); recommendation API; fleet dashboard with per-vessel and fleet CII projection views |
| 4 — Pilot and closed-loop (8–12 weeks) | Live advisory recommendations on pilot vessels; master feedback loop; CII tracking validated against IMO DCS submissions | Bridge display integration or dedicated tablet app; recommendation acceptance/rejection logging; post-voyage performance comparison reports |

## Core Contracts

### State And Output Schemas

The central contract is the voyage optimization request and the resulting recommendation. The request carries the commercial and physical constraints; the response carries a speed profile, projected fuel, and CII impact.

```python
from pydantic import BaseModel
from datetime import datetime

class VoyageRequest(BaseModel):
    voyage_id: str
    vessel_id: str
    origin_port: str  # UN/LOCODE
    destination_port: str
    departure_time: datetime
    laycan_end: datetime  # latest acceptable arrival
    cargo_deadweight_tonnes: float
    speed_warranty_knots: float | None = None  # charter-party speed clause
    cii_budget_remaining: float | None = None  # gCO2 / (dwt * nm) left for the year

class SpeedSegment(BaseModel):
    waypoint_lat: float
    waypoint_lon: float
    recommended_speed_knots: float
    expected_fuel_mt: float  # metric tonnes for this segment
    expected_duration_hours: float

class VoyageRecommendation(BaseModel):
    voyage_id: str
    vessel_id: str
    segments: list[SpeedSegment]
    total_fuel_mt: float
    total_duration_hours: float
    estimated_arrival: datetime
    projected_cii_impact: float  # gCO2 / (dwt * nm) this voyage adds
    fuel_saved_vs_baseline_mt: float
    trade_off_note: str  # e.g., "Slowing 0.3 kn saves 18 MT fuel, delays arrival 5h"
```

### Tool Interface Pattern

The optimization engine exposes three tool-like services that the orchestrator calls in sequence. Each is stateless and idempotent.

```python
# 1. Digital twin: returns vessel performance model for current state
def get_vessel_performance(vessel_id: str, as_of: datetime) -> VesselPerformanceModel:
    """Loads the latest calibrated hull-resistance and engine-efficiency
    curves for this vessel. Falls back to last-calibrated model if
    recent sensor data is missing."""
    ...

# 2. Weather grid: returns forecast along candidate routes
def get_weather_grid(
    origin: tuple[float, float],
    destination: tuple[float, float],
    departure: datetime,
    forecast_hours: int = 240
) -> xr.Dataset:
    """Returns ECMWF HRES wind, wave, and current forecasts on a
    0.25-degree grid covering the route corridor. Uses cached GRIB
    files refreshed every 6 hours."""
    ...

# 3. Optimizer: takes performance model + weather + constraints, returns recommendation
def optimize_voyage(
    request: VoyageRequest,
    performance: VesselPerformanceModel,
    weather: xr.Dataset
) -> VoyageRecommendation:
    """Multi-objective solver: minimizes fuel subject to ETA constraint,
    CII budget, and SOLAS safety limits (max wave height, wind speed).
    Returns Pareto-optimal recommendation with trade-off note."""
    ...
```

## Orchestration Outline

The optimization cycle runs on two triggers: (1) a new voyage order arrives from the fleet management system, and (2) a scheduled 6-hourly weather forecast refresh triggers re-optimization for all active voyages.

```python
# Simplified Airflow DAG for voyage re-optimization on weather refresh
from airflow.decorators import dag, task
from datetime import timedelta

@dag(schedule="0 */6 * * *", catchup=False)
def reoptimize_active_voyages():

    @task
    def get_active_voyages() -> list[str]:
        """Fetch voyage IDs with status='sailing' from voyage store."""
        return voyage_store.list_active()

    @task
    def reoptimize(voyage_id: str) -> dict:
        request = voyage_store.get_request(voyage_id)
        performance = get_vessel_performance(request.vessel_id, datetime.utcnow())
        weather = get_weather_grid(
            current_position(request.vessel_id),
            (request.destination_port_lat, request.destination_port_lon),
            datetime.utcnow(),
        )
        recommendation = optimize_voyage(request, performance, weather)
        voyage_store.save_recommendation(recommendation)
        push_to_vessel(request.vessel_id, recommendation)
        return recommendation.model_dump()

    voyages = get_active_voyages()
    reoptimize.expand(voyage_id=voyages)
```

## Prompt And Guardrail Pattern

This system is primarily physics-based optimization, not LLM-driven. However, an LLM component generates the human-readable trade-off summaries shown to masters and fleet managers.

```text
SYSTEM: You are a voyage optimization assistant for commercial shipping.
Your job is to summarize the optimizer output into a concise trade-off
note for the ship's master.

RULES:
- State the recommended speed change and its fuel/time impact in one sentence.
- If the recommendation deviates from the charter-party speed warranty,
  flag this explicitly.
- Never recommend ignoring weather safety limits.
- If CII budget is tight, state how many gCO2/(dwt*nm) remain for the year.
- Use nautical units (knots, nautical miles, metric tonnes).

OUTPUT FORMAT:
One paragraph, max 60 words. No bullet points. No hedging language.

EXAMPLE:
"Reducing speed from 13.2 to 12.8 kn for the next 48h saves an estimated
22 MT of fuel (≈$13,200) and delays arrival by 3.5h, within the laycan
window. This voyage would consume 4.2 gCO2/(dwt*nm), keeping the vessel
on track for a C rating this year."
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| **Edge gateway (vessel)** | NMEA sentence parser + satellite uplink buffer | Use pynmea2 for NMEA 0183; buffer telemetry locally in SQLite when satellite link is down; batch-upload on reconnect. Minimum sensor set: GPS, fuel flow meter, shaft RPM, draft sensors. |
| **Weather data pipeline** | GRIB file downloader + decoder on 6-hourly schedule | Pull ECMWF HRES-WAM and GFS from open APIs or licensed feeds. Decode with cfgrib into xarray datasets. Cache decoded grids for 12 hours to handle re-optimization retries. |
| **Fleet management system** | REST adapter for voyage orders and fixture data | Map Veson IMOS or Danaos voyage-order schema to VoyageRequest. Poll for new/updated fixtures or receive webhook. Write back recommendation acceptance status for P&L tracking. |
| **Bridge display** | Tablet web app or ECDIS overlay showing current recommendation | For pilot, a dedicated tablet running a lightweight web UI is simpler than ECDIS integration. Show: recommended speed, ETA, fuel forecast, and trade-off note. Master taps accept/modify/reject. |
| **IMO DCS reporting** | Annual CII data export | Aggregate per-voyage fuel and distance data into the IMO GISIS format. Compare attained CII against required CII by vessel type and size. Flag vessels trending toward D/E rating. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| **Fuel prediction accuracy** | Mean absolute percentage error (MAPE) of predicted vs. actual fuel consumption per voyage leg, measured on holdout voyages | MAPE < 5% (industry baseline with noon reports is 10–15%; DeepSea reports ±1% with high-frequency data) |
| **Optimization quality** | Percentage fuel reduction vs. the master's original voyage plan on the same route and weather conditions (A/B comparison) | ≥3% average fuel reduction across pilot voyages |
| **Recommendation safety** | Zero recommendations that violate SOLAS constraints (maximum wave height, wind speed, traffic separation schemes) | 100% constraint compliance on all generated recommendations |
| **CII projection accuracy** | Deviation between projected year-end CII and actual attained CII, measured quarterly | Projection within ±5% of attained CII at each quarterly checkpoint |
| **User acceptance rate** | Percentage of recommendations accepted without modification by the master | ≥60% acceptance rate during pilot (indicates recommendations are operationally realistic) |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with 5–10 vessels on a single trade lane (e.g., Asia–Europe container route) where weather variability is high and fuel savings potential is largest. Run in shadow mode for 4–6 weeks (recommendations generated but not acted on) to validate prediction accuracy before going advisory. |
| **Fallback path** | If the platform is unavailable, vessels revert to traditional weather-routing advisories and manual speed orders from the operations center. The edge agent caches the last recommendation for up to 72 hours. |
| **Observability** | Track: recommendation latency (target <5 min after forecast refresh), sensor data freshness per vessel (alert if >2 hours stale), model prediction error per voyage leg, and master acceptance/rejection rates with reasons. |
| **Operations ownership** | Fleet performance team owns the platform in production. They review weekly CII projections, investigate vessels with high rejection rates, and coordinate with technical superintendents on digital twin recalibration after drydocking or engine overhaul. |
