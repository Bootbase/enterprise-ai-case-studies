---
layout: use-case-detail
title: "Implementation Guide — Autonomous Mortgage Loan Document Processing"
uc_id: "UC-002"
uc_title: "Autonomous Mortgage Loan Document Processing and Underwriting with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Document Processing"
category_icon: "file-text"
industry: "Financial Services (Mortgage Lending)"
complexity: "High"
status: "detailed"
slug: "UC-002-mortgage-loan-processing"
permalink: /use-cases/UC-002-mortgage-loan-processing/implementation-guide/
---

## Build Goal

Build a document processing pipeline that classifies incoming mortgage documents, extracts key fields into structured data, cross-references values across the full loan file, and generates underwriting conditions — integrated bidirectionally with the lender's Loan Origination System. The first production release targets conventional conforming loans (Fannie/Freddie eligible) with the 20 highest-volume document types (W-2, pay stub, bank statement, tax return, 1003, credit report, appraisal, title commitment, and similar). Non-QM products, construction loans, and commercial lending are outside the first release.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python service on Azure Container Apps or AWS ECS | Python dominates ML/AI tooling; container runtime scales horizontally for refi volume spikes |
| **Model access** | Azure OpenAI GPT-4o (structured outputs) | Strong document understanding; structured output mode enforces extraction schemas; Azure satisfies US data residency |
| **OCR / layout** | Azure Document Intelligence (prebuilt mortgage models) | Purpose-built extractors for Form 1003, 1004, 1005, 1008, Closing Disclosure; handles photos, faxes, handwriting |
| **Orchestration runtime** | LangGraph | Graph-based workflow with conditional edges fits the classify → extract → cross-reference → condition pipeline |
| **Core connectors** | Encompass Partner API, Microsoft Graph API | Encompass covers 45%+ of US originations; Graph handles email/fax intake channels |
| **Evaluation / tracing** | LangSmith | Traces every LLM call with inputs, outputs, and latency; supports evaluation datasets for regression testing |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Intake and OCR pipeline operational | Document intake service (portal webhook + email listener); OCR extraction with Azure Document Intelligence; document storage with audit metadata |
| 2 | Classification and extraction accurate on core document types | LLM classification agent for top 20 document types; structured extraction schemas for income, asset, and property documents; confidence scoring and human review routing |
| 3 | Cross-referencing and condition generation functional | Cross-reference engine validating income consistency, asset sufficiency, DTI/LTV calculations; condition generator mapped to Fannie Mae Selling Guide sections; LOS writeback adapter for Encompass |
| 4 | Measured pilot with one production team | Shadow-mode deployment alongside manual processing; accuracy measurement against human underwriter baseline; threshold tuning; phased cutover for routine loan files |

## Core Contracts

### State And Output Schemas

The extraction agent returns structured JSON for each classified document. Every field carries a confidence score so downstream systems can route low-confidence values to human review without rejecting the entire document.

```python
from pydantic import BaseModel, Field
from enum import Enum

class DocumentType(str, Enum):
    W2 = "w2"
    PAY_STUB = "pay_stub"
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN_1040 = "tax_return_1040"
    FORM_1003 = "form_1003"
    APPRAISAL_1004 = "appraisal_1004"
    CREDIT_REPORT = "credit_report"
    TITLE_COMMITMENT = "title_commitment"

class ExtractedField(BaseModel):
    value: str | float | None
    confidence: float = Field(ge=0.0, le=1.0)
    source_page: int
    bounding_region: str | None = None

class DocumentExtractionResult(BaseModel):
    document_type: DocumentType
    classification_confidence: float
    borrower_name: ExtractedField | None = None
    employer_name: ExtractedField | None = None
    income_annual: ExtractedField | None = None
    income_ytd: ExtractedField | None = None
    asset_balance: ExtractedField | None = None
    property_value: ExtractedField | None = None
    document_date: ExtractedField | None = None
    tax_year: ExtractedField | None = None
```

### Tool Interface Pattern

LOS operations are wrapped in typed adapters with narrow scopes. The model never gets direct API access — each tool performs one business operation and validates inputs before execution.

```python
from langchain_core.tools import tool

@tool
def fetch_loan_context(loan_number: str) -> dict:
    """Retrieve current loan data from LOS for cross-referencing.
    Returns borrower info, existing conditions, and document index."""
    client = EncompassClient()
    loan = client.get_loan(loan_number)
    return {
        "borrower": loan.borrower_summary,
        "conditions": loan.open_conditions,
        "documents_on_file": loan.document_index,
        "loan_program": loan.program_type,
        "du_findings": loan.du_findings_summary,
    }

@tool
def write_extraction_results(
    loan_number: str,
    document_id: str,
    extraction: dict,
) -> dict:
    """Write extracted document data back to LOS. Only updates
    AI-designated fields — never overwrites underwriter entries."""
    client = EncompassClient()
    result = client.update_document_data(
        loan_number, document_id, extraction, source="ai_extraction"
    )
    return {"status": result.status, "fields_written": result.field_count}
```

## Orchestration Outline

The pipeline runs as a LangGraph workflow with conditional routing based on classification confidence and cross-reference results.

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(LoanDocumentState)

workflow.add_node("ocr_extract", run_ocr_extraction)
workflow.add_node("classify_and_extract", run_llm_classification)
workflow.add_node("human_review", route_to_human_queue)
workflow.add_node("cross_reference", run_cross_reference_checks)
workflow.add_node("generate_conditions", generate_underwriting_conditions)
workflow.add_node("writeback", write_results_to_los)
workflow.add_node("escalate", route_to_underwriter)

workflow.set_entry_point("ocr_extract")
workflow.add_edge("ocr_extract", "classify_and_extract")

workflow.add_conditional_edges(
    "classify_and_extract",
    lambda state: "cross_reference"
        if state.classification_confidence >= 0.90
        else "human_review",
)

workflow.add_conditional_edges(
    "cross_reference",
    lambda state: "escalate"
        if state.has_material_discrepancy
        else "generate_conditions",
)

workflow.add_edge("generate_conditions", "writeback")
workflow.add_edge("writeback", END)
```

## Prompt And Guardrail Pattern

The extraction prompt operates like a document analyst — extract what is present, report what is missing, never fabricate values. The system prompt enforces structured output and escalation rules.

```text
You are a mortgage document analyst. Your job is to classify the document
and extract specific data fields.

RULES:
- Return ONLY values that are explicitly printed on the document.
- If a field is not visible or is illegible, set its value to null
  and confidence to 0.0.
- Do NOT infer, calculate, or estimate any value.
- Flag any document that appears altered, inconsistent, or incomplete
  by setting needs_review to true with a specific reason.
- For income documents: extract gross figures, not net.
- For bank statements: extract ending balance for the statement period.

OUTPUT: Return valid JSON matching the DocumentExtractionResult schema.
No additional text, explanation, or commentary.
```

A separate cross-reference prompt handles multi-document validation:

```text
You are reviewing extracted data across multiple documents for a single
mortgage loan file. Compare the following data points and identify
discrepancies:

1. W-2 wages vs. tax return gross income vs. pay stub YTD totals
2. Bank statement deposits vs. reported income sources
3. Large deposits (>$500) not attributable to regular income
4. Employment dates across documents

For each discrepancy, state the specific values, source documents,
and whether the discrepancy exceeds 5% of the reported value.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Encompass document events | Webhook listener on document upload events via Encompass Partner API | Register for `document.added` and `document.updated` events; filter by loan pipeline to avoid processing closed loans |
| OCR extraction | Azure Document Intelligence client using prebuilt mortgage models | Use `prebuilt-mortgage.us.1003` for URLA, `prebuilt-mortgage.us.1004` for appraisals; fall back to `prebuilt-document` for unrecognized formats |
| LOS writeback | Encompass custom field mapping for AI-extracted values | Map extraction fields to Encompass canonical field IDs; use `custom_fields` namespace to avoid overwriting underwriter-entered standard fields |
| Email/fax intake | Microsoft Graph API with mailbox monitoring or fax gateway webhook | Parse email attachments; handle inline images and forwarded document chains; assign to correct loan by subject line parsing or borrower email matching |
| GSE guideline rules | Deterministic rule engine for DTI/LTV/reserve calculations | Encode Fannie Mae Selling Guide B3-3 (income), B3-4 (assets), B3-6 (liabilities) requirements as versioned rules; update when GSE guidelines change quarterly |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Document classification accuracy | Gold-labeled test set of 500+ documents across top 20 types; measure precision and recall per document type | ≥ 95% overall accuracy; no type below 85% |
| Field extraction accuracy | Compare extracted values against underwriter-verified data for 200+ loan files; measure exact-match and within-tolerance rates | ≥ 97% exact match for income and asset fields; ≥ 95% for dates and identifiers |
| Cross-reference discrepancy detection | Inject known discrepancies into test loan files; measure detection rate and false positive rate | ≥ 90% detection rate; < 10% false positive rate |
| Condition generation quality | Underwriter panel reviews AI-generated conditions for 100+ files; rates each as correct, unnecessary, or missing | ≥ 85% underwriter agreement with AI-generated conditions |
| LOS writeback safety | Verify no underwriter-entered fields are overwritten; confirm all writes use AI-designated field namespaces | Zero overwrites of underwriter data; 100% namespace compliance |
| Processing latency | Measure end-to-end time from document upload to LOS writeback | < 30 seconds per document for classification and extraction; < 5 minutes for full file cross-reference |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode: AI processes every document but findings are only visible in a review dashboard, not written to LOS. After 2–4 weeks of accuracy validation, enable writeback for high-confidence classifications on conventional conforming loans. Expand document types and loan products incrementally |
| **Fallback path** | Disable LOS writeback with a configuration flag; documents route to standard manual processing queue. AI extraction results are preserved in the review dashboard for debugging but do not affect loan workflow |
| **Observability** | Trace every document through the pipeline: OCR result, classification decision with confidence, extraction fields, cross-reference findings, condition output. Alert on classification confidence distribution shifts (model degradation), processing queue depth (capacity), and writeback failures (integration health) |
| **Operations ownership** | Mortgage technology team owns LOS integration and document pipeline operations. Data science team owns model accuracy monitoring, evaluation dataset maintenance, and confidence threshold tuning. Underwriting management owns condition template review and escalation policy configuration |
