---
layout: use-case-detail
title: "Implementation Guide — Autonomous Construction Progress Monitoring and Delay Prediction"
uc_id: "UC-512"
uc_title: "Autonomous Construction Progress Monitoring and Delay Prediction"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Construction"
complexity: "High"
status: "detailed"
slug: "UC-512-construction-progress-monitoring"
permalink: /use-cases/UC-512-construction-progress-monitoring/implementation-guide/
---

## Build Goal

Build a production pilot that covers one active project site, processes daily 360-degree captures, compares them against the project's IFC model, measures progress at the activity level, and surfaces deviation alerts in the team's existing PM platform. The first release should demonstrate measurable improvement in deviation detection lead time and superintendent documentation effort. Multi-site rollout, predictive delay forecasting, and automated payment application support stay outside the first release. [S1][S2]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python (FastAPI) for the processing API; containerized workers for CV inference | Python dominates the CV and ML ecosystem. FastAPI handles the webhook-based upload flow and dashboard API. GPU workers run inference in parallel per floor. |
| **Model access** | Custom YOLO v8+ models for element detection; IfcOpenShell for BIM model parsing [S10] | YOLO provides the throughput needed for processing thousands of image frames daily. IfcOpenShell reads IFC geometry and properties without requiring Autodesk licensing. |
| **Orchestration runtime** | Celery with Redis broker for task distribution | Daily processing is a batch pipeline with per-floor parallelism. Celery handles retry on failed frames and priority queuing for critical-path zones. |
| **Core connectors** | Autodesk Platform Services (Model Derivative API) for BIM access; Procore REST API for issue creation; XER/XML import for P6 schedules [S8][S9] | These are the systems the pilot site already uses. The connectors must work before the AI adds value. |
| **Evaluation / tracing** | MLflow for model versioning and accuracy tracking; OpenTelemetry for pipeline traces; Grafana for operational dashboards | CV model accuracy must be tracked per element type over time. Pipeline failures on individual frames need traceability. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Capture pipeline and BIM integration baseline | Upload service with auto-geolocation, IFC model parser, element extraction from BIM, floor-plan alignment, test dataset of 2,000+ labeled frames from the pilot site |
| 2 | CV detection and BIM comparison engine | Trained element detection models (MEP, framing, finishes), voxel-based or element-level BIM comparison, deviation scoring with confidence levels, accuracy evaluation against ground truth |
| 3 | Progress engine and PM integration | Activity-level progress calculation mapped to CPM schedule, Procore integration for deviation issues and daily logs, dashboard with progress heatmap and deviation list |
| 4 | Measured pilot on one active project | 30-day parallel run alongside manual tracking, KPI comparison (detection lead time, coverage, documentation time), superintendent and PM feedback, go/no-go for multi-site rollout |

## Core Contracts

### State And Output Schemas

The capture session is the core state object. Each daily capture produces a session that flows through processing, comparison, and alerting. The deviation report is the primary output consumed by human teams.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ProcessingStatus(str, Enum):
    UPLOADING = "uploading"
    GEOLOCATING = "geolocating"
    DETECTING = "detecting"
    COMPARING = "comparing"
    COMPLETE = "complete"
    FAILED = "failed"

class DetectedElement(BaseModel):
    element_type: str  # e.g., "duct", "sprinkler_head", "drywall"
    bim_guid: str | None  # IFC GlobalId if matched
    confidence: float = Field(ge=0.0, le=1.0)
    location: dict  # floor, zone, coordinates
    installation_state: str  # "installed", "partial", "missing", "defective"

class Deviation(BaseModel):
    deviation_id: str
    element: DetectedElement
    deviation_type: str  # "missing", "out_of_sequence", "quality_defect"
    severity: str  # "critical", "major", "minor"
    confidence: float = Field(ge=0.0, le=1.0)
    bim_reference: str  # IFC element path
    recommended_action: str

class CaptureSession(BaseModel):
    session_id: str
    project_id: str
    capture_date: datetime
    status: ProcessingStatus
    floor: str
    zone: str | None
    frame_count: int
    coverage_pct: float = Field(ge=0.0, le=100.0)
    detected_elements: list[DetectedElement]
    deviations: list[Deviation]
    activity_progress: dict[str, float]  # activity_id -> percent_complete
```

### Tool Interface Pattern

The BIM comparison engine exposes a tool interface for querying the IFC model. This keeps BIM access scoped and testable independently of the CV pipeline.

```python
import ifcopenshell

class BIMModelTool:
    """Reads IFC model elements for comparison against detected site state."""

    def __init__(self, ifc_path: str):
        self.model = ifcopenshell.open(ifc_path)

    def get_elements_by_floor(self, floor_name: str) -> list[dict]:
        """Return all building elements assigned to a given floor."""
        storey = next(
            (s for s in self.model.by_type("IfcBuildingStorey")
             if s.Name == floor_name),
            None,
        )
        if not storey:
            return []
        elements = ifcopenshell.util.element.get_decomposition(storey)
        return [
            {
                "guid": e.GlobalId,
                "type": e.is_a(),
                "name": getattr(e, "Name", None),
                "geometry": self._extract_bbox(e),
            }
            for e in elements
            if e.is_a("IfcBuildingElement")
        ]

    def _extract_bbox(self, element) -> dict | None:
        """Extract bounding box from element geometry."""
        # Simplified — production uses ifcopenshell.geom for full mesh
        settings = ifcopenshell.geom.settings()
        try:
            shape = ifcopenshell.geom.create_shape(settings, element)
            verts = shape.geometry.verts
            xs = verts[0::3]
            return {"min_x": min(xs), "max_x": max(xs)}
        except Exception:
            return None
```

## Orchestration Outline

The daily pipeline runs as a batch job triggered by capture upload completion. Each floor is processed in parallel. The orchestrator coordinates detection, comparison, progress calculation, and alert routing.

```python
from celery import chain, group

def process_daily_capture(session_id: str):
    """Orchestrate daily capture processing for one session."""
    session = load_session(session_id)
    floor_tasks = []

    for floor in session.floors:
        floor_pipeline = chain(
            geolocate_frames.s(session_id, floor),
            detect_elements.s(),      # CV inference per frame
            compare_with_bim.s(),     # match against IFC model
            calculate_progress.s(),   # activity-level percent-complete
        )
        floor_tasks.append(floor_pipeline)

    # Process all floors in parallel, then aggregate
    workflow = (
        group(floor_tasks)
        | aggregate_session_results.s(session_id)
        | run_delay_predictor.s()
        | route_alerts.s()           # create issues in Procore / BCF
    )
    workflow.apply_async()
```

The `route_alerts` step checks each deviation against confidence thresholds and severity rules before creating issues. Deviations below the confidence threshold are logged but not routed, preventing alert fatigue.

## Prompt And Guardrail Pattern

The core pipeline uses CV models, not LLMs. The natural-language layer is a query assistant that lets project managers ask questions about progress status. This is the only LLM component.

```text
You are a construction progress assistant. You answer questions about
project progress using data from the capture and comparison pipeline.

Rules:
1. Answer only from the progress data provided in context. Never
   estimate, extrapolate, or speculate beyond the measured data.
2. When reporting percent-complete, state the capture date and
   confidence level alongside the number.
3. If a question asks about an area that was not captured, say so
   explicitly — do not guess.
4. Never make recommendations about schedule acceleration, crew
   changes, or subcontractor management. Those are human decisions.
5. When reporting deviations, include the BIM element reference and
   the confidence score so the user can verify.
6. If asked about cost or payment, respond that cost data is outside
   your scope and direct the user to the PM platform.

Output: concise, factual answers. Use bullet points for lists.
No opinions. No construction advice.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| BIM model ingestion | IFC file parser using IfcOpenShell; schedule sync with Autodesk APS Model Derivative API for teams using Revit/ACC [S8] | IFC is the interoperability format. Teams using Revit can export IFC or use the APS Data Exchange Cloud Connector. Update the local IFC copy when the model version changes. |
| Schedule import | XER parser for Primavera P6; XML parser for Microsoft Project; manual CSV fallback | The schedule defines activity definitions, baseline dates, and logic ties. The progress engine maps detected elements to activities using a configurable element-to-activity mapping table. |
| PM platform (Procore) | REST adapter that creates observations and issues via Procore API; attaches deviation images and BIM references [S9] | Use Procore's OAuth 2.0 flow. Map deviation severity to Procore issue priority. Include a deep link back to the progress dashboard for context. |
| BCF issue creation | BCF-API client for creating model-referenced issues in BIM tools [S7] | Each BCF issue includes the IFC element GUID, a viewpoint (camera position and direction), and a snapshot image. This lets the design team see exactly what the AI flagged in their BIM authoring tool. |
| Capture hardware | Vendor-specific upload SDK (Buildots, OpenSpace) or generic file-based upload for camera-agnostic setups | Prefer vendors with auto-geolocation (visual SLAM). If using a generic camera, the upload service must accept manual floor-plan alignment. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Element detection accuracy | Precision and recall per element type on labeled test set (2,000+ frames from pilot site); stratified by element category (MEP, structural, finishes) | Precision >= 85%, recall >= 80% across all tracked element types [S1] |
| BIM comparison correctness | Percentage of flagged deviations confirmed by superintendent spot check during 30-day pilot | >= 80% confirmation rate on deviations with confidence >= 0.7 |
| Progress measurement accuracy | Compare AI-calculated percent-complete against manual progress report for same activities over 4-week period | Mean absolute error <= 8 percentage points per activity [S2] |
| Coverage completeness | Percentage of total floor area captured per daily walk; tracked per floor and zone | >= 85% average coverage across all floors during pilot |
| Alert relevance | Percentage of routed alerts that the PM acted on (confirmed, assigned, or closed as resolved) vs. dismissed as noise | >= 70% action rate on routed alerts |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one active project in mid-construction (structural complete, MEP and finishes underway). Run AI monitoring in parallel with existing manual process for 30 days. Compare detection lead time and coverage before replacing manual tracking on that site. [S1][S3] |
| **Fallback path** | If the AI pipeline fails or produces low-confidence results, the superintendent reverts to manual photo documentation and weekly schedule updates. No progress data or payment application should depend solely on the AI system during the pilot. |
| **Observability** | Track per-session: frame count, processing time, coverage percentage, detection count, deviation count, and alert count. Alert on processing failures, coverage drops below threshold, and model accuracy degradation (measured via periodic ground-truth samples). |
| **Operations ownership** | VDC (Virtual Design and Construction) team owns BIM model currency and CV model calibration. Project management team owns alert triage and issue resolution workflow. IT owns infrastructure, connectivity, and data retention. |
