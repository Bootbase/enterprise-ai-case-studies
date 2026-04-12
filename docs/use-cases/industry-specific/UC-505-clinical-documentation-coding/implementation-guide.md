---
layout: use-case-detail
title: "Implementation Guide — Autonomous Clinical Documentation and Medical Coding"
uc_id: "UC-505"
uc_title: "Autonomous Clinical Documentation and Medical Coding with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Healthcare"
complexity: "High"
status: "detailed"
slug: "UC-505-clinical-documentation-coding"
permalink: /use-cases/UC-505-clinical-documentation-coding/implementation-guide/
---

## Build Goal

Build a production pilot that captures ambulatory encounter audio, generates structured clinical notes for physician review, assigns ICD-10-CM and CPT codes, and routes high-confidence encounters directly to billing. The first release covers established-patient office visits (CPT 99211–99215) in 2–3 specialties (primary care, internal medicine, and one surgical specialty). New patient visits, procedures, inpatient encounters, and multi-provider visits remain outside the first release. The pilot targets 50–100 physicians over 12 weeks, with success defined as under 1 minute average physician review time and 90%+ zero-touch coding rate at 98%+ accuracy. [S2][S7]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python (FastAPI) behind the health system's API gateway, deployed in a HIPAA-compliant cloud environment (AWS GovCloud, Azure for Healthcare, or GCP with HIPAA BAA) | Python dominates the ML/NLP ecosystem. FastAPI handles async encounter processing. HIPAA-compliant hosting is non-negotiable. |
| **Model access** | Anthropic Claude API (with BAA) for note generation; Fathom or CodaMetrix for autonomous coding | LLM generates high-quality clinical notes from transcripts. Purpose-built coding engines provide validated accuracy and Epic Toolbox integration. [S7][S8] |
| **Orchestration runtime** | Event-driven pipeline: EHR webhook (note signed) triggers coding engine; confidence gate routes to billing or coder queue | Documentation and coding are sequential but loosely coupled. Event-driven design allows independent scaling and failure isolation. |
| **Core connectors** | Epic FHIR R4 APIs (SMART on FHIR), medical ASR engine (Dragon or Deepgram), CMS code databases (ICD-10-CM, CPT, NCCI edits) | These are the actual systems in the processing chain. The pilot must prove FHIR read/write, ASR accuracy, and code validation work end-to-end. [S11] |
| **Evaluation / tracing** | OpenTelemetry for distributed traces per encounter; structured quality logs for note accuracy and coding metrics; compliance dashboard | Every encounter needs a traceable path from audio to billed claim. HTI-1 requires algorithm transparency documentation. [S9] |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Audio capture and note generation baseline | HIPAA-compliant audio streaming pipeline, ASR integration, note generation prompt suite with specialty templates (primary care, internal medicine), FHIR adapter for patient context read, evaluation dataset of 200+ labeled encounter-note pairs |
| 2 | Physician review workflow and EHR writeback | Mobile and desktop review interface (embedded in EHR or standalone), FHIR DocumentReference write for signed notes, physician feedback capture (accept/edit/reject per section), review time tracking |
| 3 | Autonomous coding pipeline | Coding engine integration (Fathom or CodaMetrix), NCCI edit validator, confidence scoring and routing logic, coder workqueue UI with AI-suggested codes and rationale, charge posting adapter to PMS |
| 4 | Measured pilot with 50–100 physicians | Shadow-mode deployment (AI processes in parallel with existing workflow), KPI dashboard, physician and coder feedback loops, compliance audit sampling, go/no-go for production rollout |

## Core Contracts

### State And Output Schemas

The encounter state flows through the documentation and coding pipelines. Each stage enriches it; the final state drives either zero-touch billing or coder review.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class EncounterStatus(str, Enum):
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    NOTE_DRAFTING = "note_drafting"
    PHYSICIAN_REVIEW = "physician_review"
    NOTE_SIGNED = "note_signed"
    CODING = "coding"
    CODER_REVIEW = "coder_review"
    BILLED = "billed"

class ClinicalNote(BaseModel):
    chief_complaint: str
    hpi: str  # history of present illness
    ros: str | None = None  # review of systems
    physical_exam: str | None = None
    assessment: list[str]  # list of diagnoses/impressions
    plan: list[str]
    confidence_per_section: dict[str, float]

class CodeAssignment(BaseModel):
    code: str  # e.g., "E11.9" or "99214"
    code_system: str  # "ICD-10-CM" or "CPT"
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_text: str  # excerpt from note justifying the code

class EncounterState(BaseModel):
    encounter_id: str
    patient_id: str
    provider_id: str
    status: EncounterStatus
    specialty: str
    transcript: str | None = None
    clinical_note: ClinicalNote | None = None
    assigned_codes: list[CodeAssignment] = []
    zero_touch_eligible: bool = False
    created_at: datetime
    updated_at: datetime
```

### Tool Interface Pattern

The Note Generation Agent receives patient context from the EHR before drafting. Tools are scoped: the agent can read patient data but cannot write to the EHR — only the physician's sign-off triggers writeback.

```python
from anthropic import Anthropic

client = Anthropic()

note_generation_tools = [
    {
        "name": "get_patient_context",
        "description": (
            "Retrieve the patient's active problem list, current medications, "
            "allergies, and recent visit notes from the EHR via FHIR."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string"},
                "fhir_resources": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "Condition", "MedicationRequest",
                            "AllergyIntolerance", "DocumentReference",
                        ],
                    },
                },
            },
            "required": ["patient_id"],
        },
    },
    {
        "name": "get_specialty_template",
        "description": (
            "Retrieve the note template for a given specialty. "
            "Templates define required sections and formatting."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string"},
                "visit_type": {
                    "type": "string",
                    "enum": ["new_patient", "established", "follow_up"],
                },
            },
            "required": ["specialty", "visit_type"],
        },
    },
]
```

## Orchestration Outline

The system runs two sequential pipelines connected by the physician sign-off event. The documentation pipeline is synchronous with the encounter; the coding pipeline is triggered asynchronously after the note is signed.

```python
# Documentation pipeline — runs during/after the encounter
async def documentation_pipeline(encounter_id: str, audio_stream):
    # 1. Transcribe audio with medical ASR
    transcript = await asr_engine.transcribe(audio_stream)

    # 2. Fetch patient context from EHR
    patient_ctx = await fhir_client.get_patient_context(
        patient_id=encounter.patient_id,
        resources=["Condition", "MedicationRequest", "AllergyIntolerance"],
    )

    # 3. Generate structured clinical note
    note = await note_agent.generate(
        transcript=transcript,
        patient_context=patient_ctx,
        specialty=encounter.specialty,
    )

    # 4. Present to physician for review — await sign-off
    await review_queue.submit(encounter_id, note)
    # Physician reviews, edits, signs → triggers EHR writeback


# Coding pipeline — triggered by note_signed event
async def coding_pipeline(encounter_id: str, signed_note: ClinicalNote):
    # 1. Coding engine assigns ICD-10-CM and CPT codes
    codes = await coding_engine.assign_codes(signed_note)

    # 2. Rules engine validates against NCCI edits and medical necessity
    validated = ncci_validator.validate(codes)

    # 3. Route by confidence
    if all(c.confidence >= CONFIDENCE_THRESHOLD for c in validated):
        await billing_system.submit_charges(encounter_id, validated)
    else:
        await coder_queue.submit(encounter_id, validated, signed_note)
```

## Prompt And Guardrail Pattern

The note generation prompt grounds the AI strictly in the transcript and patient context. It must not infer findings that were not discussed.

```text
You are a clinical documentation specialist. Generate a structured
clinical note from the encounter transcript and patient context below.

Rules:
1. Document ONLY what was explicitly discussed or observed in the
   transcript. Never infer symptoms, findings, or diagnoses not
   mentioned by the physician or patient.
2. Use the specialty template structure. Populate each section from
   the transcript. Mark sections "Not discussed" if the transcript
   contains no relevant content.
3. For the Assessment, list each diagnosis or impression the physician
   stated. Use the patient's active problem list for context but do
   not add diagnoses the physician did not address.
4. For the Plan, document each action the physician stated: orders,
   referrals, medication changes, follow-up timing.
5. Assign a confidence score (0.0–1.0) to each section based on
   transcript clarity. Flag sections below 0.7 for physician attention.
6. Never generate billing codes, compliance recommendations, or
   risk assessments. Your role is clinical documentation only.

Output: JSON matching the ClinicalNote schema.
```

The coding engine uses its own purpose-built models (not a general LLM). The guardrail layer is the deterministic NCCI edit validator that rejects invalid code combinations before they reach billing.

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Epic FHIR R4 read/write | SMART on FHIR app registration; OAuth 2.0 client credentials flow for batch, authorization code flow for interactive; read Condition, MedicationRequest, AllergyIntolerance, DocumentReference; write DocumentReference for signed notes | Epic requires App Orchard (now Showroom) registration and security review. FHIR scopes must follow minimum necessary principle. Expect 4–8 weeks for Epic integration approval. [S11] |
| Medical ASR engine | Streaming audio adapter with speaker diarization; medical vocabulary model; real-time interim transcripts for physician display | Microsoft Dragon is the market leader (deployed at 600+ health systems). Deepgram offers a medical model with lower latency. BAA required. Audio retention policy must be configurable per site. [S12] |
| Coding engine (Fathom/CodaMetrix) | API adapter for code assignment; webhook for confidence scores; coder workqueue integration for flagged encounters | Both Fathom and CodaMetrix are available in Epic Toolbox. Prefer the vendor already approved by the health system's IT security team. Integration is typically REST API with HL7v2 fallback. [S7][S8] |
| NCCI edit validation | Rules engine that validates code pairs against CMS NCCI Procedure-to-Procedure and Medically Unlikely Edits tables; LCD/NCD medical necessity checks | NCCI tables update quarterly. Build an automated refresh from CMS downloads. This is deterministic validation — no AI involved. Critical for preventing claim denials. |
| Coder workqueue | Web interface showing AI-suggested codes, confidence scores, supporting note excerpts, and edit/accept actions; integrates with existing coding workflow tools | Must surface the rationale (which note text supports each code) so coders can review efficiently. Track coder override rate as a signal for model improvement. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Note clinical accuracy | Physician acceptance rate (percentage of notes signed without edits); section-level edit rate; random audio-vs-note audit by clinical quality team (5% sample) | >= 85% notes accepted without substantive edits; zero major hallucinations (fabricated findings) in audit sample [S6] |
| Note completeness | PDQI-9 score (validated documentation quality instrument) on a random sample of AI-generated vs. prior physician-authored notes | AI notes score >= physician baseline on PDQI-9 thoroughness and organization dimensions [S6] |
| Coding accuracy | Encounter-level accuracy: percentage of encounters where all assigned codes match expert coder review; code-level precision and recall | >= 98% encounter-level accuracy on established-patient E/M visits [S7][S8] |
| Zero-touch automation rate | Percentage of eligible encounters that pass the confidence gate and route directly to billing without coder intervention | >= 90% of established-patient E/M encounters in pilot specialties [S7] |
| Physician review time | Median time from note presentation to physician sign-off, measured from app telemetry | Median < 60 seconds for routine established-patient encounters [S2][S4] |
| Denial rate impact | Coding-related claim denial rate pre vs. post deployment, measured per specialty | >= 20% reduction in coding-related denials within 90 days of go-live [S8] |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode: AI generates notes and codes in parallel with the existing workflow, but does not replace it. Physicians see AI-drafted notes alongside their normal documentation. Coders see AI-suggested codes alongside manual coding. Measure accuracy for 4–6 weeks before enabling the AI path as primary. Expand from pilot specialties to additional departments in 3-month waves. [S2][S3] |
| **Fallback path** | If the AI pipeline fails (ASR outage, model error, FHIR unavailability), the physician documents normally in the EHR and coders code from the manual note. No encounter should be delayed or lost because of an AI system outage. The fallback is the pre-AI workflow, which remains fully functional throughout the rollout period. |
| **Observability** | Trace every encounter end-to-end: audio capture status, ASR latency and word error rate, note generation latency and confidence scores, physician review time and edit rate, coding confidence and code assignments, NCCI validation results, billing submission status. Alert on: ASR failure rate > 2%, note generation latency > 30 seconds, physician edit rate spike > 2 standard deviations, coding confidence distribution shift, denial rate increase. |
| **Operations ownership** | Clinical informatics owns note quality, specialty templates, and physician adoption. Revenue cycle owns coding accuracy, denial monitoring, and coder workflow. IT/platform team owns infrastructure, FHIR integration, and system reliability. Compliance owns audit sampling, HTI-1 documentation, and upcoding monitoring. [S9][S10] |
