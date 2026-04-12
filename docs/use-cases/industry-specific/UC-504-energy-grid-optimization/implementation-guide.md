---
layout: use-case-detail
title: "Implementation Guide — Autonomous Energy Grid Optimization and DER Orchestration with Agentic AI"
uc_id: "UC-504"
uc_title: "Autonomous Energy Grid Optimization and DER Orchestration with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Energy / Utilities"
complexity: "High"
status: "detailed"
slug: "UC-504-energy-grid-optimization"
permalink: /use-cases/UC-504-energy-grid-optimization/implementation-guide/
---

## Build Goal

Deliver a portfolio optimization platform that ingests real-time grid telemetry and weather data, produces demand and generation forecasts, co-optimizes dispatch across battery storage and aggregated DERs, and submits bids to wholesale and ancillary-services markets. The first production boundary covers a single battery-storage site (50–150 MW) with FCAS market participation and economic dispatch. DER aggregation and residential demand response are Phase 3 additions. Full VPP orchestration across a mixed portfolio is the Phase 4 target.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12+ microservices on Kubernetes | Energy ML ecosystem (PyTorch, scikit-learn, PuLP/OR-Tools) is Python-native. Kubernetes handles scaling and rolling deployments for always-on grid operations. |
| **Model access** | Self-hosted models (PyTorch for forecasting, XGBoost for price prediction) | Sub-second inference latency requirements rule out external API calls in the dispatch loop. Models run co-located with the optimizer. |
| **Orchestration runtime** | Apache Kafka (event streaming) + Temporal (durable workflow orchestration) | Kafka handles high-throughput telemetry ingestion; Temporal manages multi-step workflows (bid submission, settlement reconciliation) with built-in retry and state persistence. [S1][S7] |
| **Core connectors** | DNP3 client library (pydnp3), IEEE 2030.5 gateway, ISO/RTO market API adapters | Direct control of field devices and market systems. Protocol choice is dictated by the asset type and regulatory jurisdiction. [S3][S6] |
| **Evaluation / tracing** | MLflow (model versioning and experiment tracking) + OpenTelemetry (dispatch tracing) + TimescaleDB (time-series storage) | Every dispatch decision must be traceable for regulatory audit. MLflow tracks forecast model performance across retraining cycles. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Data foundation and single-site telemetry | Kafka ingestion pipeline, SCADA connector, weather API integration, TimescaleDB storage, historical data backfill for model training. |
| 2 | Forecasting and single-site battery dispatch | Demand and solar forecast models, MILP-based battery optimizer for a single BESS site, DNP3 dispatch adapter, FCAS bid submission for one ancillary-services market. |
| 3 | DER aggregation and demand response | IEEE 2030.5 / OpenADR gateway, residential device enrollment, aggregated load forecasting, demand-response dispatch within the portfolio optimizer. |
| 4 | Full VPP and multi-market portfolio optimization | Portfolio-level co-optimization across storage, DERs, and generation assets. Multi-market bidding (energy + FCAS + capacity). Operator dashboard with override controls. |

## Core Contracts

### State And Output Schemas

The portfolio optimizer consumes a `PortfolioState` snapshot every 5 minutes and produces a `DispatchPlan` with per-asset setpoints and market bids.

```python
from pydantic import BaseModel
from datetime import datetime

class AssetState(BaseModel):
    asset_id: str
    asset_type: str          # "bess" | "solar" | "wind" | "der_aggregate"
    capacity_mw: float
    current_output_mw: float
    soc_pct: float | None    # State of charge — BESS only
    available: bool

class ForecastWindow(BaseModel):
    timestamp: datetime
    horizon_minutes: int
    demand_mw: list[float]
    solar_mw: list[float]
    wind_mw: list[float]
    price_aud_mwh: list[float]

class PortfolioState(BaseModel):
    timestamp: datetime
    grid_frequency_hz: float
    assets: list[AssetState]
    forecast: ForecastWindow

class AssetSetpoint(BaseModel):
    asset_id: str
    target_mw: float          # Positive = discharge/export; negative = charge/import
    mode: str                 # "economic" | "contingency_fcas" | "regulation"

class MarketBid(BaseModel):
    market: str               # "energy" | "raise_6s" | "raise_60s" | "lower_6s" | "regulation"
    price_aud_mwh: float
    quantity_mw: float
    interval_start: datetime

class DispatchPlan(BaseModel):
    timestamp: datetime
    setpoints: list[AssetSetpoint]
    bids: list[MarketBid]
    reserve_margin_mw: float
```

### Tool Interface Pattern

Each agent exposes a tool interface that the portfolio optimizer calls. Tools enforce their own safety constraints before executing.

```python
from typing import Protocol

class StorageDispatchTool(Protocol):
    async def dispatch(self, setpoint: AssetSetpoint) -> dict:
        """Send charge/discharge command to a BESS asset via DNP3.

        Validates: SOC within [10%, 90%], ramp rate within asset limits,
        thermal status from BMS. Rejects command and returns error
        if any constraint is violated.
        """
        ...

class MarketBidTool(Protocol):
    async def submit_bid(self, bid: MarketBid) -> dict:
        """Submit a bid to the ISO/RTO market gateway.

        Validates: bid format against market rules, position limits
        against operator-defined thresholds, submission deadline.
        Returns confirmation with bid ID or rejection reason.
        """
        ...
```

## Orchestration Outline

The main dispatch loop runs on a 5-minute cycle for economic optimization, with a separate sub-second loop for contingency frequency response.

```python
import asyncio
from datetime import datetime, timedelta

async def economic_dispatch_loop(
    forecaster, optimizer, storage_tool, der_tool, market_tool, state_store
):
    """5-minute economic dispatch cycle."""
    while True:
        cycle_start = datetime.utcnow()

        # 1. Gather current state
        portfolio_state = await state_store.get_current_state()

        # 2. Update forecasts
        forecast = await forecaster.predict(
            horizon=timedelta(hours=4),
            resolution_minutes=5,
        )
        portfolio_state.forecast = forecast

        # 3. Co-optimize across all assets and markets
        plan = optimizer.solve(portfolio_state)

        # 4. Execute dispatch and bids concurrently
        await asyncio.gather(
            *[storage_tool.dispatch(sp) for sp in plan.setpoints if sp.mode == "economic"],
            *[der_tool.dispatch(sp) for sp in plan.setpoints if "der" in sp.asset_id],
            *[market_tool.submit_bid(bid) for bid in plan.bids],
        )

        # 5. Log decision for audit
        await state_store.log_dispatch(plan)

        # Sleep until next 5-minute boundary
        elapsed = (datetime.utcnow() - cycle_start).total_seconds()
        await asyncio.sleep(max(0, 300 - elapsed))
```

## Prompt And Guardrail Pattern

This system uses ML models and mathematical optimization rather than LLM prompts for its core dispatch loop. The guardrail pattern is constraint-based rather than prompt-based.

```text
PORTFOLIO OPTIMIZER CONSTRAINTS (configured by operator):

1. Reserve margin: Hold {reserve_pct}% of committed FCAS capacity as unallocated reserve.
2. SOC bounds: Never discharge below {soc_min}% or charge above {soc_max}%.
3. Ramp limits: Respect per-asset ramp rate limits from the asset registry.
4. Position limits: Total market exposure must not exceed {max_position_mw} MW per market.
5. Revenue floor: Do not bid below {min_price_aud} AUD/MWh in energy markets.
6. Curtailment priority: Shed load in priority order — industrial DR first, then commercial, then residential last.
7. Override: Any operator command immediately supersedes optimizer output.

CONTINGENCY MODE TRIGGERS:
- Grid frequency deviation > ±0.15 Hz from 50 Hz → activate contingency FCAS response.
- Communication loss to >20% of assets → hold current setpoints, alert operator.
- Battery thermal alarm → reduce output to 50%, alert operator.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| SCADA / EMS telemetry | OPC-UA client that subscribes to frequency, voltage, and power-flow measurements and publishes to Kafka. | Typical SCADA systems expose 10,000+ data points. Subscribe only to dispatch-relevant tags. Maintain a tag-mapping configuration that operators can update without code changes. |
| Battery management system | DNP3 master that sends setpoint commands and reads back SOC, temperature, and status. | Use pydnp3 or OpenDNP3. Implement watchdog heartbeat — if the AI platform stops sending heartbeats, the BMS defaults to safe state. Latency budget: < 50 ms for contingency FCAS path. [S1][S5] |
| ISO/RTO market gateway | Market-specific API adapter per jurisdiction (AEMO MMS API, PJM eMarket API, CAISO OASIS API). | Each ISO has different bid formats, submission windows, and authentication. Build a market-adapter interface so the optimizer is market-agnostic; implement one adapter per target market. [S4][S5] |
| DER aggregation | IEEE 2030.5 server that manages device registration, group membership, and setpoint distribution. | Expect 100,000+ concurrent device connections. Use connection pooling and batch setpoint distribution. California Rule 21 mandates IEEE 2030.5; other jurisdictions may accept OpenADR. [S3][S6] |
| Weather and forecast data | REST client pulling NWP outputs (GFS, ECMWF) and satellite imagery on 15-minute intervals. | Cache weather data locally; retrain forecast models weekly using latest actuals vs. predictions. Open Climate Fix provides open-source solar nowcasting models. [S2][S8] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Demand forecast accuracy | Mean absolute percentage error (MAPE) on 15-minute-ahead forecasts, measured on 30 days of holdout data. | MAPE < 8% for day-ahead; < 5% for 1-hour-ahead. [S2][S8] |
| Solar/wind forecast accuracy | Normalized RMSE against actual generation, evaluated across clear-sky and cloudy conditions separately. | nRMSE < 15% for solar (all-weather); < 20% for wind. [S2][S8] |
| Dispatch optimality | Revenue achieved vs. theoretical maximum (computed post-hoc with perfect foresight). Measured over 30-day rolling window. | Revenue capture ratio > 85% of perfect-foresight benchmark. [S1][S4] |
| Contingency response latency | Time from frequency deviation detection to first MW injected, measured on synthetic grid events in test environment. | < 200 ms for 90th percentile events. [S1][S5] |
| DER command delivery rate | Percentage of setpoint commands acknowledged by end devices within 30 seconds. | > 95% acknowledgment rate. [S3] |
| Market bid compliance | Percentage of submitted bids that pass ISO/RTO format validation without rejection. | > 99.5% acceptance rate. |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with a single BESS site in one FCAS market (Phase 2). Run the AI optimizer in shadow mode for 4 weeks, comparing its recommendations against actual operator decisions, before enabling automated dispatch. Expand to DER aggregation (Phase 3) and full VPP (Phase 4) only after the single-site pilot meets all evaluation gates. |
| **Fallback path** | Every asset has a deterministic safe-state mode: batteries hold current SOC, DERs return to baseline setpoints, market positions are closed at current clearing price. If the AI platform is unreachable for > 60 seconds, SCADA-level automation takes over. The pre-AI manual dispatch process remains available as a full fallback. |
| **Observability** | Trace every dispatch decision with: timestamp, portfolio state snapshot, forecast inputs, optimizer solution, commands sent, market bids submitted, and actual asset responses. Store in TimescaleDB with 90-day hot retention and 7-year cold archive for regulatory compliance. Alert on: forecast MAPE drift > 2× baseline, bid rejection rate > 1%, communication loss to any asset, and optimizer infeasibility. |
| **Operations ownership** | Grid operations team owns production support. Data science team owns forecast model retraining and performance. Market operations team owns bidding strategy and settlement reconciliation. Platform engineering owns infrastructure, Kafka cluster, and Kubernetes. |
