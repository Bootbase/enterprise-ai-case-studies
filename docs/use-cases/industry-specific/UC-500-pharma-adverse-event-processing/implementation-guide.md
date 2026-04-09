---
layout: use-case-detail
title: "Implementation Guide — UC-500: Autonomous Adverse Event Report Processing"
uc_id: "UC-500"
uc_title: "Autonomous Adverse Event Report Processing in Pharmacovigilance"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
status: "detailed"
slug: "UC-500-pharma-adverse-event-processing"
permalink: /use-cases/UC-500-pharma-adverse-event-processing/implementation-guide/
---

# UC-500: Autonomous Adverse Event Report Processing in Pharmacovigilance — Implementation Guide

## Prerequisites

| Prerequisite | Detail |
|--------------|--------|
| **Azure subscription** | Azure OpenAI deployment that supports structured outputs, plus a queue and container runtime. |
| **Safety system sandbox** | Veeva Vault Safety sandbox with API access, intake inbox configuration, and non-production E2B transmission profile. |
| **Terminology access** | Licensed MedDRA and WHO Drug Dictionary services exposed through internal APIs. |
| **Dev environment** | Python 3.11+, `openai`, `langgraph`, `pydantic`, `requests`, `tenacity`, `lxml`, `rapidfuzz`. |
| **Permissions** | Access to source channels, safety sandbox, prompt/evaluation store, and audit log sink. |

---

## Project Structure

```text
pv-icsr-agent/
├── src/
│   ├── agents/
│   │   ├── graph.py                # LangGraph workflow
│   │   ├── extract.py              # Structured extraction worker
│   │   ├── coding.py               # MedDRA / WHO Drug worker
│   │   ├── duplicate.py            # Duplicate comparison worker
│   │   └── narrative.py            # Narrative drafting + QC
│   ├── tools/
│   │   ├── veeva.py                # Safety DB connector
│   │   ├── meddra.py               # Terminology lookup wrappers
│   │   ├── who_drug.py             # Product dictionary wrappers
│   │   └── xsd.py                  # E2B schema validation
│   ├── prompts/
│   │   ├── extract_system.txt
│   │   ├── coding_system.txt
│   │   ├── duplicate_system.txt
│   │   ├── narrative_system.txt
│   │   └── qc_system.txt
│   ├── models/
│   │   ├── intake.py               # Pydantic schemas
│   │   └── case_state.py           # Graph state types
│   └── eval/
│       ├── score_extraction.py
│       ├── score_duplicates.py
│       └── score_narratives.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
└── README.md
```

The important boundary is not the folder tree. It is the contract line between:

- LLM workers that read, compare, or draft
- deterministic tools that search, validate, write, or transmit

That split is what makes the system auditable.

---

## Step-by-Step Implementation

### Phase 1: Foundation

#### Step 1.1: Install dependencies

```bash
uv init pv-icsr-agent
uv add openai langgraph pydantic requests tenacity lxml rapidfuzz
```

Use `langgraph` for orchestration, `openai` for Azure OpenAI structured outputs, `requests` for the safety-system seam, and `lxml` for local XSD prechecks. LangGraph is the main runtime because it gives you checkpointed state and interrupts, which are the two features a regulated HITL workflow needs most.

#### Step 1.2: Define the case-state and extraction contracts

Do this before writing any prompt. The extraction schema is the real API between the LLM and the rest of the system.

```python
from typing import Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

class EvidenceSpan(BaseModel):
    quote: str = Field(min_length=1)
    source_id: str
    start_char: int
    end_char: int

class MinimumCriteria(BaseModel):
    identifiable_patient: bool
    identifiable_reporter: bool
    suspect_product: bool
    adverse_event: bool

class IntakePacket(BaseModel):
    source_language: str | None = None
    seriousness: Literal["serious", "non_serious", "unknown"]
    minimum_criteria: MinimumCriteria
    suspect_products: list[str]
    adverse_events: list[str]
    patient_age: str | None = None
    patient_sex: str | None = None
    reporter_type: str | None = None
    narrative_summary: str
    evidence: list[EvidenceSpan]
    confidence: float = Field(ge=0.0, le=1.0)

class CaseState(TypedDict, total=False):
    case_id: str
    source_bundle: str
    intake: IntakePacket
    coding_result: dict
    duplicate_result: dict
    narrative_result: dict
    qc_result: dict
    review_reason: str
    review_decision: dict
    veeva_record_id: str
```

---

### Phase 2: Core AI Integration

#### Step 2.1: Connect Azure OpenAI with structured outputs

This node is the foundation of the entire workflow. If you do not lock extraction to a schema, downstream validation gets noisy fast.

```python
import os
from openai import AzureOpenAI
from models.intake import IntakePacket

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
)

EXTRACTION_SYSTEM_PROMPT = """
You are the intake extraction worker for a pharmacovigilance system.
Populate the IntakePacket schema from the source bundle.

Rules:
1. Only extract facts supported by quoted evidence.
2. If a field is not explicit, return null or an empty list.
3. Do not infer causality.
4. Do not invent MedDRA or WHO Drug codes.
5. Return only schema-valid output.
""".strip()

def run_extraction(bundle_text: str) -> IntakePacket:
    completion = client.beta.chat.completions.parse(
        model=os.environ["AZURE_OPENAI_EXTRACT_MODEL"],
        temperature=0,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": bundle_text},
        ],
        response_format=IntakePacket,
    )
    return completion.choices[0].message.parsed
```

#### Step 2.2: Define the graph

```python
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from models.case_state import CaseState
from agents.extract import run_extraction
from agents.coding import run_coding_worker
from agents.duplicate import run_duplicate_worker
from agents.narrative import run_narrative_worker, run_qc_worker

def extract_node(state: CaseState) -> CaseState:
    return {"intake": run_extraction(state["source_bundle"])}

def route_after_extract(state: CaseState) -> Literal["coding", "human_review"]:
    intake = state["intake"]
    if intake.seriousness == "serious" or intake.confidence < 0.90:
        return "human_review"
    return "coding"

def human_review_node(state: CaseState) -> Command[Literal["write_case", END]]:
    decision = interrupt({
        "case_id": state.get("case_id"),
        "review_reason": state.get("review_reason", "Regulatory review required"),
        "draft": {
            "intake": state.get("intake"),
            "coding": state.get("coding_result"),
            "duplicate": state.get("duplicate_result"),
            "narrative": state.get("narrative_result"),
            "qc": state.get("qc_result"),
        },
    })
    if not decision["approved"]:
        return Command(update={"review_decision": decision}, goto=END)
    return Command(update={"review_decision": decision}, goto="write_case")

builder = StateGraph(CaseState)
builder.add_node("extract", extract_node)
builder.add_node("coding", lambda state: {"coding_result": run_coding_worker(state["intake"])})
builder.add_node("duplicate", lambda state: {"duplicate_result": run_duplicate_worker(state)})
builder.add_node("narrative", lambda state: {"narrative_result": run_narrative_worker(state)})
builder.add_node("qc", lambda state: {"qc_result": run_qc_worker(state)})
builder.add_node("human_review", human_review_node)
builder.add_node("write_case", lambda state: state)

builder.add_edge(START, "extract")
builder.add_conditional_edges("extract", route_after_extract)
builder.add_edge("coding", "duplicate")
builder.add_edge("duplicate", "narrative")
builder.add_edge("narrative", "qc")
builder.add_conditional_edges("qc", lambda state: "human_review" if state["qc_result"]["requires_human_review"] else "write_case")
builder.add_edge("write_case", END)

graph = builder.compile(checkpointer=MemorySaver())
```

---

### Phase 3: Integration Layer

#### Step 3.1: Connect to the safety database

For the reference seam, use the documented Veeva object and attachment APIs. Keep those calls in one file so every model write path goes through auditable mapping code.

```python
import os
from typing import Any
import requests

class VaultClient:
    def __init__(self, base_url: str, api_version: str, access_token: str):
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.access_token = access_token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def create_object_record(self, object_name: str, fields: dict[str, Any]) -> dict:
        response = requests.post(
            f"{self.base_url}/api/{self.api_version}/vobjects/{object_name}",
            headers={**self._headers(), "Content-Type": "application/json"},
            json={"data": [fields]},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def add_attachment(
        self,
        object_name: str,
        record_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> dict:
        response = requests.post(
            f"{self.base_url}/api/{self.api_version}/vobjects/{object_name}/{record_id}/attachments",
            headers=self._headers(),
            files={"file": (filename, content, content_type)},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
```

#### Step 3.2: Map AI output to safety-system fields

Do not write `model_dump()` directly into the safety system. Create a deterministic translation layer.

```python
def map_case_to_vault_fields(state: CaseState) -> dict:
    intake = state["intake"]
    coding = state["coding_result"]
    narrative = state["narrative_result"]

    return {
        "source_language__c": intake.source_language,
        "seriousness__c": intake.seriousness,
        "patient_age__c": intake.patient_age,
        "patient_sex__c": intake.patient_sex,
        "reporter_type__c": intake.reporter_type,
        "narrative__c": narrative["narrative_text"],
        "minimum_criteria_json__c": intake.minimum_criteria.model_dump_json(),
        "coding_json__c": json.dumps(coding),
        "evidence_json__c": json.dumps([item.model_dump() for item in intake.evidence]),
        "ai_confidence__c": intake.confidence,
    }
```

---

### Phase 4: Orchestration & Flow

#### Step 4.1: Add retries around LLM calls

Network errors and 429s should retry. Regulatory routing should not.

```python
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

@retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
)
def safe_extract(bundle_text: str) -> IntakePacket:
    return run_extraction(bundle_text)
```

#### Step 4.2: Pause for regulated review with `interrupt()`

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "case-2026-000123"}}

# First call pauses at the human_review node.
pending = graph.invoke(
    {"case_id": "case-2026-000123", "source_bundle": bundle_text},
    config=config,
)

# Reviewer decision later resumes the same case.
approved = graph.invoke(
    Command(
        resume={
            "approved": True,
            "reviewer": "pv_specialist_01",
            "notes": "Narrative accepted. Seriousness confirmed as non-serious.",
        }
    ),
    config=config,
)
```

---

## Testing Strategy

### Unit Tests

Test deterministic logic aggressively: minimum-criteria rules, field mapping, escalation policy, XSD validation, tool result parsing.

```python
def test_route_after_extract_serious_cases_always_pause():
    state = {"intake": IntakePacket(
        seriousness="serious",
        minimum_criteria={"identifiable_patient": True, "identifiable_reporter": True, "suspect_product": True, "adverse_event": True},
        suspect_products=["Drug A"],
        adverse_events=["Rash"],
        narrative_summary="Serious rash after Drug A",
        evidence=[],
        confidence=0.99,
    )}
    assert route_after_extract(state) == "human_review"
```

### Integration Tests

Use a real Azure OpenAI deployment and a safety sandbox: live extraction, terminology lookup, record creation, attachment upload, outbound XML validation.

### Evaluation Tests

Do not stop at "the call succeeded." Score the AI output against a labeled gold set.

```python
def score_extraction(packet: IntakePacket, gold: dict) -> dict[str, float]:
    field_hits = 0
    field_total = 0
    for field in ["suspect_products", "adverse_events", "patient_age", "patient_sex", "reporter_type"]:
        field_total += 1
        if getattr(packet, field) == gold[field]:
            field_hits += 1
    return {
        "field_accuracy": field_hits / field_total,
        "minimum_criteria_accuracy": (
            packet.minimum_criteria.model_dump() == gold["minimum_criteria"]
        ),
    }
```

Track: field-level extraction accuracy, case-validity classification accuracy, MedDRA coding top-1 / top-3 match rate, duplicate detection precision and recall, narrative reviewer edit distance, percentage of cases auto-routed vs escalated.

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `AZURE_OPENAI_EXTRACT_MODEL` | none | Deployment used for schema-first extraction. |
| `AZURE_OPENAI_TOOL_MODEL` | none | Deployment used for tool-calling workers. |
| `EXTRACTION_TEMPERATURE` | `0.0` | Keep extraction deterministic. |
| `AUTO_ROUTE_CONFIDENCE` | `0.90` | Minimum extraction confidence for touchless routing. |
| `DUPLICATE_REVIEW_FLOOR` | `0.60` | Lower bound for human duplicate review. |
| `VEEVA_API_VERSION` | `v15.0` | Veeva Vault API version. |

