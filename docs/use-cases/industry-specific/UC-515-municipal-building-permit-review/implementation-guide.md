---
layout: use-case-detail
title: "Implementation Guide — Autonomous Municipal Building Permit Review"
uc_id: "UC-515"
uc_title: "Autonomous Municipal Building Permit Review"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "building"
industry: "Government / Public Sector"
complexity: "High"
status: "detailed"
slug: "UC-515-municipal-building-permit-review"
permalink: /use-cases/UC-515-municipal-building-permit-review/implementation-guide/
---

## Build Goal

Deliver an AI pre-screening service that accepts building plan submissions from the permitting platform, evaluates them against digitized code rules, and returns a structured compliance report with marked-up plan sheets and code citations — all within one business day of submission. The first release targets standard single-family residential permits (the highest volume, most rule-based category). Commercial, multi-family, and complex structural categories remain in the human-only queue until the rule base and parser accuracy are validated for those project types.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python service on containerized infrastructure (Docker / Kubernetes) | Python dominates the CV/ML ecosystem; containers allow municipal IT to deploy on-premises or in government cloud (Azure Gov, GovCloud) |
| **Model access** | Custom vision model (fine-tuned object detection) + deterministic rule engine | Building plan analysis requires spatial parsing that general-purpose LLMs cannot do reliably; rule engine ensures reproducibility |
| **Orchestration runtime** | Event-driven pipeline: webhook listener → task queue → worker pool | Applications arrive asynchronously; task queue handles volume spikes (e.g., post-disaster surges) without blocking |
| **Core connectors** | REST adapters for Accela Civic Platform API or Tyler EnerGov API; OGC-compliant GIS client for parcel data | These are the two dominant permitting platforms in U.S. municipalities; GIS integration needed for parcel-specific zoning checks |
| **Evaluation / tracing** | Structured JSON logs with per-application trace ID; monthly accuracy review against examiner overrides | Audit trail is a legal requirement for public agencies; override rate is the primary quality metric |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Code digitization (8–12 weeks) | Local zoning and building codes encoded as machine-readable rules with test cases | Rule repository with version tracking; validation suite covering 50+ common residential code provisions; GIS parcel data integration |
| 2 — Document parser (8–10 weeks) | Vision pipeline extracts spatial data from residential plan PDFs at target accuracy | Fine-tuned object detection model for floor plans; OCR pipeline for dimension labels and annotations; parser accuracy benchmark on 200+ historical plans |
| 3 — Compliance engine + report (6–8 weeks) | End-to-end pipeline: plan in → compliance report out | Rule evaluation engine; report generator with marked-up PDF and structured JSON output; examiner review dashboard prototype |
| 4 — Pilot (10–12 weeks) | Pre-screening live on a subset of residential applications with examiner shadow review | Permitting platform integration; applicant-facing report delivery; examiner override tracking; accuracy and throughput dashboards |

## Core Contracts

### State And Output Schemas

The compliance report is the primary contract between the AI service and downstream consumers (examiners, applicants, permitting platform). Each finding maps to a specific code section, includes the extracted measurement or observation, and carries a confidence score.

```python
from pydantic import BaseModel
from enum import Enum

class FindingStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"  # confidence below threshold

class ComplianceFinding(BaseModel):
    discipline: str          # "zoning", "building", "fire", "accessibility"
    code_section: str        # "IRC R305.1" or "Denver Zoning 3.2.4.1"
    rule_description: str    # "Minimum ceiling height in habitable rooms"
    extracted_value: str     # "7 ft 2 in" — what the parser read from the plan
    required_value: str      # "7 ft 0 in minimum"
    status: FindingStatus
    confidence: float        # 0.0–1.0; below 0.85 → NEEDS_REVIEW
    sheet_reference: str     # "A-2" — which plan sheet
    markup_coords: list[float] | None  # bounding box on the sheet for visual markup

class ComplianceReport(BaseModel):
    application_id: str
    jurisdiction: str
    project_type: str        # "single_family_new", "commercial_remodel", etc.
    findings: list[ComplianceFinding]
    summary_pass: int
    summary_fail: int
    summary_needs_review: int
    report_pdf_url: str      # link to marked-up plan PDF
    generated_at: str        # ISO 8601 timestamp
```

### Tool Interface Pattern

The AI service exposes two capabilities to the permitting platform: submitting an application for pre-screening and retrieving the compliance report. The permitting platform triggers pre-screening via webhook; the service processes asynchronously and writes the report back.

```python
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/prescreen")
async def submit_for_prescreen(
    application_id: str,
    plan_files: list[str],  # URLs to uploaded plan PDFs
    parcel_id: str,
    project_type: str,
    background_tasks: BackgroundTasks,
):
    """Called by permitting platform webhook when a new application is submitted."""
    background_tasks.add_task(
        run_prescreen_pipeline,
        application_id=application_id,
        plan_files=plan_files,
        parcel_id=parcel_id,
        project_type=project_type,
    )
    return JSONResponse({"status": "accepted", "application_id": application_id})

@app.get("/report/{application_id}")
async def get_report(application_id: str):
    """Returns the compliance report once processing completes."""
    report = await fetch_report(application_id)
    if not report:
        return JSONResponse({"status": "processing"}, status_code=202)
    return report.model_dump()
```

## Orchestration Outline

The pre-screening pipeline runs as an async task triggered by the permitting platform. It follows a strict sequence: parse plans, look up parcel context, evaluate rules, generate report, write back.

```python
async def run_prescreen_pipeline(
    application_id: str,
    plan_files: list[str],
    parcel_id: str,
    project_type: str,
):
    # 1. Parse plan documents — extract spatial data, dimensions, annotations
    parsed_plans = await document_parser.extract(plan_files)

    # 2. Retrieve parcel context from GIS — zoning designation, setback lines,
    #    overlay districts, flood zone
    parcel_context = await gis_client.get_parcel_context(parcel_id)

    # 3. Load applicable code rules for this jurisdiction + project type
    rules = await rule_repository.get_rules(
        jurisdiction=parcel_context.jurisdiction,
        project_type=project_type,
    )

    # 4. Evaluate each rule against parsed plan data
    findings = compliance_engine.evaluate(parsed_plans, parcel_context, rules)

    # 5. Generate compliance report with marked-up PDF
    report = report_generator.build(application_id, findings, parsed_plans)

    # 6. Write report back to permitting platform
    await permitting_client.attach_report(application_id, report)
    await permitting_client.notify_applicant(application_id, report.summary_fail)
```

## Prompt And Guardrail Pattern

This system primarily uses computer vision and deterministic rules, not LLM prompts. However, the report generator uses a language model to produce plain-language correction guidance for applicants. The prompt is tightly constrained to prevent hallucination.

```text
You are a building code compliance assistant. Given a list of code compliance
findings, write a short correction notice for the applicant.

Rules:
- Reference the specific code section for each finding (provided in the data).
- State what was found and what is required. Do not speculate about intent.
- Use plain language. The reader may not be a licensed professional.
- Do not suggest that the applicant can ignore a finding.
- Do not provide legal advice or interpret variances.
- If a finding has status "needs_review", state that this item requires
  examiner review and cannot be resolved through resubmission alone.

Output format: numbered list, one item per finding, max 3 sentences each.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| **Permitting platform (Accela / Tyler)** | Webhook receiver for new-application events; API client for attaching reports and updating application status | Accela's Civic Platform exposes REST APIs for record events and document attachment. Tyler's EnerGov has a similar API catalog. Build an adapter layer so the same pipeline supports either platform. |
| **GIS / parcel data** | REST client for the municipality's ArcGIS or open GIS endpoint | Parcel boundaries, zoning designations, and overlay districts change with rezoning actions. Cache parcel data with a short TTL (24 hours) and refresh on each pre-screen request. |
| **Electronic plan review (Avolve / e-PlanSoft)** | Markup overlay that renders AI annotations alongside examiner annotations in the existing plan viewer | Departments that already use electronic plan review will reject a second viewer. AI annotations should appear as a layer in the existing tool, not a separate interface. |
| **Code rule updates** | Manual review + import workflow triggered by ICC code cycle or local amendment | Code updates are infrequent (every 1–3 years for ICC; ad-hoc for local) but high-impact. Each update must be tested against historical applications before going live. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| **Parser accuracy** (extracting dimensions, room types, annotations from plan PDFs) | Compare extracted values against manually labeled ground truth on 200+ historical plans; measure precision and recall per element type | ≥ 90% precision, ≥ 85% recall on residential floor plans |
| **Rule evaluation correctness** (does the engine produce the right pass/fail for a known plan + code combination) | Run each digitized rule against a test suite of plan data with known outcomes; track pass/fail agreement rate | ≥ 95% agreement with examiner findings on test suite |
| **Examiner override rate** (how often examiners disagree with an AI finding in production) | Track overrides per finding during pilot; classify overrides as AI-wrong vs. examiner-discretion | AI-wrong override rate < 10% within 90 days of pilot start |
| **Applicant correction cycle reduction** (do pre-screened applications require fewer resubmissions) | Compare average correction cycles for pre-screened vs. non-pre-screened applications during pilot | ≥ 30% reduction in average correction cycles |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with standard single-family residential new construction — the highest-volume, most rule-based category. Shadow mode first (AI reports generated but not sent to applicants; examiners compare AI findings to their own). Graduate to applicant-facing reports after 60 days if override rate meets gate. Expand to commercial and multi-family after residential is stable. |
| **Fallback path** | If the AI service is unavailable, the permitting platform routes applications directly to the human review queue with no pre-screen report. Examiners are never blocked by the AI layer. |
| **Observability** | Per-application trace ID linking webhook receipt, parser output, rule evaluation results, and report delivery. Dashboard showing daily volume, median processing time, pass/fail distribution, and examiner override rate. Alert on processing time exceeding 4 hours or error rate exceeding 5%. |
| **Operations ownership** | Municipal IT owns infrastructure and uptime. The AI vendor (or internal ML team) owns model accuracy and rule updates. A joint review board meets monthly during pilot to review override data and approve rule changes. |
