---
layout: use-case-detail
title: "Implementation Guide — Autonomous Accounts Payable Invoice Processing with Multi-Agent AI"
uc_id: "UC-001"
uc_title: "Autonomous Accounts Payable Invoice Processing with Multi-Agent AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Document Processing"
category_icon: "file-text"
industry: "Cross-Industry (Real Estate, Retail, Manufacturing, Professional Services, Hospitality)"
complexity: "High"
status: "detailed"
slug: "UC-001-ap-invoice-processing"
permalink: /use-cases/UC-001-ap-invoice-processing/implementation-guide/
---

## Build Goal

Build a production pilot that handles one AP inbox, one ERP, and a limited supplier cohort before expanding across entities. The first release should automate invoice extraction, normalization, PO matching, non-PO coding suggestions, and ERP writeback for low-risk invoices. It should not try to redesign treasury, supplier onboarding, or global tax handling on day one. [S1][S2][S16]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python service or Azure Container Apps worker | Good fit for document-heavy integrations and common AI SDKs. |
| **Model access** | Azure OpenAI structured outputs | Keeps the normalization layer schema-bound. [S9] |
| **Document extraction** | Azure Document Intelligence `prebuilt-invoice` | Purpose-built invoice extraction with AP-oriented fields. [S10] |
| **Orchestration runtime** | LangGraph | Good fit for deterministic routing with review branches. [S12] |
| **Core connectors** | Microsoft Graph, SAP Supplier Invoice API, ERP master-data APIs | Covers inbox intake and authoritative finance writeback. [S14][S16][S17] |
| **Evaluation / tracing** | Workflow traces plus application telemetry | Needed to review node outputs and exception reasons. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Stable intake and schema contracts | Inbox connector, source-file store, invoice packet schema, gold-set sample of real invoices |
| 2 | Reliable extraction and routing | Document extraction, structured normalization, duplicate screen, PO versus non-PO branching |
| 3 | ERP-safe automation | SAP posting adapter, approval-policy checks, exception queue, audit payload logging |
| 4 | Measured pilot | Supplier cohort rollout, KPI dashboard, human-review feedback loop, rollback path |

## Core Contracts

### State And Output Schemas

The contract that matters most is the normalized invoice packet. It is the handoff from AI to the finance rules layer. Keep it strict, typed, and narrow. Include only fields downstream systems actually use.

```python
from pydantic import BaseModel, ConfigDict
from openai import OpenAI
import os

class InvoicePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_name: str | None
    invoice_number: str | None
    invoice_date: str | None
    po_number: str | None
    currency: str | None
    gross_amount: float | None
    confidence: float

client = OpenAI(
    base_url=os.environ["AZURE_OPENAI_BASE_URL"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

completion = client.beta.chat.completions.parse(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    messages=[
        {"role": "system", "content": "Extract invoice data into the schema."},
        {"role": "user", "content": invoice_text},
    ],
    response_format=InvoicePacket,
)

packet = completion.choices[0].message.parsed
```

This pattern follows Microsoft's structured-output guidance and removes most of the brittle post-processing that otherwise accumulates in AP workflows. [S9]

### Tool Interface Pattern

Keep tools narrow. Do not expose raw ERP access to the model. Wrap each finance action in an adapter with one business purpose.

```python
from langchain_core.tools import tool
import requests

@tool
def fetch_po_context(po_number: str) -> dict:
    response = requests.get(
        f"{ERP_BASE_URL}/purchase-orders/{po_number}",
        headers={"Authorization": f"Bearer {ERP_TOKEN}"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()

@tool
def create_supplier_invoice(payload: dict) -> dict:
    response = requests.post(
        f"{SAP_BASE_URL}/sap/opu/odata/SAP/API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice",
        json=payload,
        headers={"Authorization": f"Bearer {SAP_TOKEN}"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()
```

The tool boundary should mirror the way finance systems already expose APIs: read PO context, validate master data, create invoice, release or reverse only through named operations. [S16][S17]

## Orchestration Outline

The workflow should branch early and avoid unnecessary model loops. Most AP failures are not "reasoning" failures. They are master-data, tolerance, or approval-policy failures.

```python
from typing_extensions import TypedDict
from langgraph.graph import START, END, StateGraph

class ApState(TypedDict, total=False):
    invoice_id: str
    packet: dict
    route: str
    review_reason: str

graph = StateGraph(ApState)
graph.add_node("extract", extract_invoice_packet)
graph.add_node("validate", run_policy_checks)
graph.add_node("code", suggest_non_po_coding)
graph.add_node("post", post_to_erp)
graph.add_node("review", send_to_exception_queue)

graph.add_edge(START, "extract")
graph.add_edge("extract", "validate")
graph.add_conditional_edges("validate", route_after_validation)
graph.add_edge("code", "post")
graph.add_edge("post", END)
graph.add_edge("review", END)
ap_workflow = graph.compile()
```

This is where LangGraph is useful: explicit node boundaries, clear branching, and observable state transitions. [S12]

## Prompt And Guardrail Pattern

The core extraction prompt should read like a finance control, not a chatbot instruction set.

```text
You are the invoice normalization worker for an AP automation system.

Rules:
1. Return only schema-valid output.
2. Use null when a field is not present.
3. Do not infer PO numbers, tax codes, or vendor IDs.
4. Flag low-confidence cases instead of guessing.
5. Preserve line-item totals exactly as written in the source.
```

Add a second prompt for non-PO coding that includes valid company-code, GL-account, and tax-code choices from the ERP. The model should select only from those choices, never invent them. [S2][S3][S9]

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Inbox ingestion | Shared mailbox listener using Graph message and attachment APIs | Handle attachment sizes and non-inline files explicitly. [S14] |
| Invoice extraction | Document Intelligence call plus packet normalization | Use the invoice model first; fall back to custom document logic for supplier-specific gaps. [S10][S11] |
| PO and master data lookup | ERP or procurement read adapters | Keep these read-only from the model's perspective. |
| ERP posting | Supplier invoice create, list, release, reverse adapters | Map AI output into SAP payloads only after deterministic checks pass. [S16][S17] |
| Eventing | Queue between intake, extraction, validation, and posting | Use queues for load leveling; use topics if you need separate subscribers for audit or analytics. [S15] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Extraction quality | Field-level precision and recall on a labeled invoice set | `>= 95%` on required header fields before autopilot pilot |
| Posting safety | Zero unauthorized or malformed ERP writes in staging | `0` invalid posts |
| Match and coding quality | Percentage of invoices that pass human review without edits | `>= 85%` on pilot cohort before wider release |
| Exception routing | Reviewer agreement that the right cases were escalated | `>= 90%` agreement on reviewed sample |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one entity, one inbox, and the most repetitive suppliers. HSB and Countsy both show the gains come quickly when the workflow is standardized. [S1][S2] |
| **Fallback path** | If extraction confidence, matching, or policy checks fail, the invoice goes to the normal AP queue with source files and model output attached. |
| **Observability** | Trace every model call, confidence score, policy failure, and ERP writeback result. That is the only reliable way to tune thresholds. |
| **Operations ownership** | Finance operations owns acceptance thresholds and exception policy; platform engineering owns runtime, connectors, and telemetry. |
