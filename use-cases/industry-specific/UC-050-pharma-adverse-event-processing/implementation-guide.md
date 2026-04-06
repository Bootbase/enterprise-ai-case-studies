# UC-050: Autonomous Adverse Event Report Processing in Pharmacovigilance — Implementation Guide

## Prerequisites

| Prerequisite | Detail |
|--------------|--------|
| **Azure subscription** | Azure OpenAI deployment that supports structured outputs, plus a queue and container runtime. [TD1] |
| **Safety system sandbox** | Veeva Vault Safety sandbox with API access, intake inbox configuration, and non-production E2B transmission profile. [INT1][INT2][INT3][INT4] |
| **Terminology access** | Licensed MedDRA and WHO Drug Dictionary services exposed through internal APIs. [UC] |
| **Dev environment** | Python 3.11+, `openai`, `langgraph`, `pydantic`, `requests`, `tenacity`, `lxml`, `rapidfuzz`. |
| **Permissions** | Access to source channels, safety sandbox, prompt/evaluation store, and audit log sink. [UC][INT1] |

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

That split is what makes the system auditable. [UC][TD1][TD2]

---

## Step-by-Step Implementation

### Phase 1: Foundation

#### Step 1.1: Install the AI and connector dependencies

```bash
uv init pv-icsr-agent
uv add openai langgraph pydantic requests tenacity lxml rapidfuzz
```

Use `langgraph` for orchestration, `openai` for Azure OpenAI structured outputs, `requests` for the safety-system seam, and `lxml` for local XSD prechecks. LangGraph is the main runtime because it gives you checkpointed state and interrupts, which are the two features a regulated HITL workflow needs most. [TD1][TD2][TD3]

**Verification:** `uv run python -c "import openai, langgraph, pydantic, requests, lxml"` exits successfully.

#### Step 1.2: Define the case-state and extraction contracts first

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

**Verification:** invalid extra fields or missing required fields fail in unit tests before any live model call.

---

### Phase 2: Core AI Integration

#### Step 2.1: Connect Azure OpenAI with strict structured outputs

This node is the foundation of the entire workflow. If you do not lock extraction to a schema, downstream validation gets noisy fast. Azure's structured outputs are designed for exactly this pattern. [TD1]

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

**Why this matters:** the model's job is now "fill this contract," not "write something useful." That change removes most downstream parsing code and makes reviewer diffing practical. [TD1]

#### Step 2.2: Define the graph, not just a chat loop

Graph orchestration is the right fit because the case has state, approval pauses, retries, and branch points. LangGraph's `StateGraph`, checkpointing, and interrupts are the critical APIs here. [TD2][TD3]

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


def coding_node(state: CaseState) -> CaseState:
    return {"coding_result": run_coding_worker(state["intake"])}


def duplicate_node(state: CaseState) -> CaseState:
    return {"duplicate_result": run_duplicate_worker(state)}


def narrative_node(state: CaseState) -> CaseState:
    return {"narrative_result": run_narrative_worker(state)}


def qc_node(state: CaseState) -> CaseState:
    return {"qc_result": run_qc_worker(state)}


def route_after_qc(state: CaseState) -> Literal["write_case", "human_review"]:
    if state["qc_result"]["requires_human_review"]:
        return "human_review"
    return "write_case"


def human_review_node(state: CaseState) -> Command[Literal["write_case", END]]:
    decision = interrupt(
        {
            "case_id": state.get("case_id"),
            "review_reason": state.get("review_reason", "Regulatory review required"),
            "draft": {
                "intake": state.get("intake"),
                "coding": state.get("coding_result"),
                "duplicate": state.get("duplicate_result"),
                "narrative": state.get("narrative_result"),
                "qc": state.get("qc_result"),
            },
        }
    )
    if not decision["approved"]:
        return Command(update={"review_decision": decision}, goto=END)
    return Command(update={"review_decision": decision}, goto="write_case")


builder = StateGraph(CaseState)
builder.add_node("extract", extract_node)
builder.add_node("coding", coding_node)
builder.add_node("duplicate", duplicate_node)
builder.add_node("narrative", narrative_node)
builder.add_node("qc", qc_node)
builder.add_node("human_review", human_review_node)
builder.add_node("write_case", lambda state: state)

builder.add_edge(START, "extract")
builder.add_conditional_edges("extract", route_after_extract)
builder.add_edge("coding", "duplicate")
builder.add_edge("duplicate", "narrative")
builder.add_edge("narrative", "qc")
builder.add_conditional_edges("qc", route_after_qc)
builder.add_edge("write_case", END)

graph = builder.compile(checkpointer=MemorySaver())
```

This is the core design point: the graph decides control flow; the model only decides within a narrowly scoped node.

#### Step 2.3: Bind domain tools where the model genuinely needs lookup

Do not expose the safety database as a giant generic toolset. Give each worker only the tools it needs.

```python
import json
import os

from openai import AzureOpenAI


client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
)


SEARCH_MEDDRA_TOOL = {
    "type": "function",
    "function": {
        "name": "search_meddra",
        "description": "Search licensed MedDRA terms and return ranked LLT/PT candidates.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


SEARCH_WHO_DRUG_TOOL = {
    "type": "function",
    "function": {
        "name": "search_who_drug",
        "description": "Resolve suspect products against the licensed WHO Drug Dictionary.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


TOOL_REGISTRY = {
    "search_meddra": lambda args: meddra_client.search(**args),
    "search_who_drug": lambda args: who_drug_client.search(**args),
}


def run_coding_worker(intake: IntakePacket) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are the coding worker for pharmacovigilance. "
                "Use tools before selecting any code. "
                "Never invent a term or code. "
                "Return JSON with event_codes, product_codes, confidence, and requires_human_review."
            ),
        },
        {"role": "user", "content": intake.model_dump_json()},
    ]

    while True:
        response = client.chat.completions.create(
            model=os.environ["AZURE_OPENAI_TOOL_MODEL"],
            temperature=0,
            parallel_tool_calls=False,
            tools=[SEARCH_MEDDRA_TOOL, SEARCH_WHO_DRUG_TOOL],
            messages=messages,
        )

        message = response.choices[0].message
        if not getattr(message, "tool_calls", None):
            return json.loads(message.content)

        messages.append(message.model_dump())

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = TOOL_REGISTRY[tool_call.function.name](args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps(result),
                }
            )
```

This worker is allowed two tools only because its job is narrow: resolve event and product terminology. That is easier to validate than exposing duplicate search, writeback, and review actions in the same loop. [TD1][TD4]

---

### Phase 3: Integration Layer

#### Step 3.1: Connect to the safety database through an explicit connector layer

For the reference seam, use the documented Veeva object and attachment APIs. Keep those calls in one file so every model write path goes through auditable mapping code. [INT1]

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

    def get_object_record(self, object_name: str, record_id: str) -> dict:
        response = requests.get(
            f"{self.base_url}/api/{self.api_version}/vobjects/{object_name}/{record_id}",
            headers=self._headers(),
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

    def run_lifecycle_action(
        self,
        object_name: str,
        record_id: str,
        action_name: str,
        payload: dict[str, Any] | None = None,
    ) -> dict:
        response = requests.post(
            f"{self.base_url}/api/{self.api_version}/vobjects/{object_name}/{record_id}/actions/{action_name}",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=payload or {},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
```

This is the integration seam. The model never gets direct URL-building privileges.

#### Step 3.2: Map AI output to safety-system fields explicitly

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

Persisting evidence and coding JSON with the case is worth the extra storage. It makes reviewer replay, deviation analysis, and validation much easier later.

---

### Phase 4: Orchestration & Flow

#### Step 4.1: Add retries around LLM calls, not around business decisions

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

The wrong retry boundary is a common failure mode. Retrying a network call is good. Retrying a business classification until you "like the answer" is not.

#### Step 4.2: Pause for regulated review with `interrupt()`

LangGraph interrupts are a clean fit for PV review because they persist state and resume with a reviewer decision instead of inventing side-channel state. [TD3]

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

Reviewer comments become part of the case state, not a separate undocumented channel.

---

### Phase 5: Evaluation and Minimal Deployment Notes

#### Step 5.1: Treat the gold set as a first-class artifact

Your first production-quality deliverable is not the API. It is the evaluation set.

Build at least:

- 300-500 routine non-serious cases
- 100-150 serious cases
- 50-100 duplicate or near-duplicate pairs
- 50 multilingual cases
- 50 known hard cases: handwritten scans, literature reports, poor chronology, missing minimum criteria

The public evidence base shows exactly why this matters: Pfizer's pilot found materially different performance by entity type and case class, not one universal score. [CS1]

#### Step 5.2: Keep packaging and deployment boring

Run the graph worker behind a queue, persist checkpoints in a durable store, and send traces to your standard observability platform. The deployment mechanics are intentionally uninteresting here; the correctness hinges on the contracts, prompts, tools, and evaluation set.

---

## Key Code Patterns

### Pattern: Schema-first extraction

```python
def extract_and_validate(bundle_text: str) -> IntakePacket:
    intake = safe_extract(bundle_text)
    assert intake.evidence, "Every extracted packet must carry evidence spans"
    return intake
```

This is the single highest-leverage pattern in the whole design. If extraction is not schema-first, every later node becomes fragile.

### Pattern: Tool-grounded terminology selection

```python
def must_have_single_high_confidence_term(result: dict) -> None:
    if result["requires_human_review"]:
        raise ValueError("Ambiguous terminology result must be reviewed by a human")
```

The point is not just "use a tool." The point is that the model is only allowed to choose among controlled candidates.

### Pattern: Reviewer interrupt with resumable state

```python
def requires_review(state: CaseState) -> bool:
    return (
        state["intake"].seriousness == "serious"
        or state["intake"].confidence < 0.90
        or state["duplicate_result"]["requires_human_review"]
        or state["qc_result"]["requires_human_review"]
    )
```

This keeps review policy explicit and testable.

---

## Prompt Templates

### Extraction Worker

```text
System:
You extract pharmacovigilance intake facts from raw case material.

Output contract:
- Return only the IntakePacket schema.
- Every non-null field must have supporting evidence.
- If the source is contradictory, surface the contradiction in narrative_summary and lower confidence.
- If one of the four minimum criteria is missing, return the best partial extraction anyway.
```

### Duplicate Review Worker

```text
System:
You compare a candidate case against possible duplicates returned by the safety database.

Rules:
1. Compare patient, product, event, reporter, and timeline.
2. Explain mismatches explicitly.
3. If evidence is insufficient to merge automatically, set requires_human_review=true.
4. Never claim "not a duplicate" unless the differences are material.
```

### Narrative Worker

```text
System:
Draft a pharmacovigilance case narrative in English.

Rules:
1. Preserve dates, products, and event chronology exactly as provided.
2. Use the sponsor template order.
3. Do not add causality conclusions unless supplied in the structured case.
4. If information is missing, state that it is unavailable rather than filling it in.
```

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `AZURE_OPENAI_EXTRACT_MODEL` | none | Deployment used for schema-first extraction. |
| `AZURE_OPENAI_TOOL_MODEL` | none | Deployment used for tool-calling workers. |
| `AZURE_OPENAI_NARRATIVE_MODEL` | none | Deployment used for narrative drafting. |
| `EXTRACTION_TEMPERATURE` | `0.0` | Keep extraction deterministic. |
| `NARRATIVE_TEMPERATURE` | `0.2` | Allow slight linguistic flexibility without drifting facts. |
| `AUTO_ROUTE_CONFIDENCE` | `0.90` | Minimum extraction confidence for touchless routing. |
| `DUPLICATE_REVIEW_FLOOR` | `0.60` | Lower bound for human duplicate review. |
| `MAX_SOURCE_CHARS` | `24000` | Upper bound passed into a single worker call before chunking. |
| `VEEVA_API_VERSION` | `v15.0` | Veeva Vault API version. |
| `CHECKPOINT_BACKEND` | `sqlite` | Replace in-memory examples with durable storage in production. |

---

## Testing Strategy

### Unit Tests

Test deterministic logic aggressively:

- minimum-criteria rules
- field mapping to the safety database
- escalation policy
- XSD validation wrappers
- tool result parsing

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

Use a real Azure OpenAI deployment and a safety sandbox:

- live extraction against canned reports
- live terminology lookup
- record creation and attachment upload in the sandbox
- outbound XML validation without transmission

```python
def test_veeva_record_round_trip(vault_client: VaultClient):
    created = vault_client.create_object_record("custom_case_stub__c", {"name__v": "AI-TEST-001"})
    record_id = created["data"][0]["id"]
    fetched = vault_client.get_object_record("custom_case_stub__c", record_id)
    assert fetched["data"]["id"] == record_id
```

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

Track at least:

- field-level extraction accuracy
- case-validity classification accuracy
- MedDRA coding top-1 / top-3 match rate
- duplicate detection precision and recall
- narrative reviewer edit distance
- percentage of cases auto-routed vs escalated

Those are the quality measures that matter in this use case, not generic chatbot satisfaction.

---

## Monitoring & Observability

| What to Monitor | Tool / Method | Alert Threshold |
|-----------------|---------------|-----------------|
| **Extraction schema failures** | Structured logging on parse exceptions | `>1%` of cases in 15 minutes |
| **Escalation rate** | Graph-state metrics | Sudden rise above calibrated baseline |
| **Duplicate-review uncertainty** | Custom worker metric | `>25%` of routine cases |
| **Safety writeback failures** | Connector logs | Any sustained non-zero error rate |
| **E2B validation failures** | XML validation queue | Immediate alert for any production case |
| **Token usage per case** | Azure/OpenAI usage logs | Deviation from pilot baseline |

---

## Common Pitfalls & Mitigations

| Pitfall | Mitigation |
|---------|------------|
| Letting the model decide submission rules | Keep regulatory gating in deterministic code. |
| Exposing too many tools to one worker | Give each worker only the tools it needs. [TD4] |
| Writing model output straight into the safety system | Use an explicit mapping layer and sandbox first. |
| Using one prompt for extraction, coding, and narrative | Split workers by task and validate each separately. [CS2][CS4] |
| Ignoring evidence provenance | Persist evidence spans with every extracted field. |
| Treating validation as a one-time project | Re-run the gold set whenever prompts, tools, or models change. |

---

## Rollback Plan

If quality drops or a validation issue appears:

1. Disable the touchless route flag so every case pauses after extraction.
2. Keep AI in suggestion-only mode for coding and narrative generation.
3. Continue using the safety inbox and manual case processing as the system of record.
4. Preserve all prompts, traces, and reviewer corrections from the failed batch for root-cause analysis.
