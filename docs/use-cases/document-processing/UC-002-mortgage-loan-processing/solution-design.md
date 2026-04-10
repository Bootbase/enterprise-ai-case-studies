---
layout: use-case-detail
title: "Solution Design — Autonomous Mortgage Loan Document Processing"
uc_id: "UC-002"
uc_title: "Autonomous Mortgage Loan Document Processing and Underwriting with Agentic AI"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "Document Processing"
category_icon: "file-text"
industry: "Financial Services (Mortgage Lending)"
complexity: "High"
status: "detailed"
slug: "UC-002-mortgage-loan-processing"
permalink: /use-cases/UC-002-mortgage-loan-processing/solution-design/
---

## What This Design Covers

This design addresses the document-intensive middle of mortgage loan origination: classifying incoming borrower documents, extracting structured data, cross-referencing fields across the full loan file, generating underwriting conditions, and clearing those conditions when satisfactory documentation arrives. The system operates as a semi-autonomous digital loan processor that handles high-volume rules-based work while routing complex credit judgments, exception cases, and regulatory-mandated decisions to human underwriters. The design boundary starts at document receipt and ends at the clear-to-close recommendation — it does not cover final credit approval, adverse action notices, property valuation, or fraud investigation.

## Recommended Operating Model

| Decision Area | Recommendation |
|---------------|----------------|
| **Autonomy Model** | Semi-autonomous: documents classified and extracted without human touch; cross-referencing and condition generation automated; human underwriter reviews AI-prepared findings and retains approval authority |
| **System of Record** | Loan Origination System (ICE Encompass, Black Knight Empower, or Blend) remains authoritative for loan data, status, and audit trail |
| **Human Decision Points** | Final credit approval or denial; adverse action notices (ECOA requirement); exception cases flagged by the AI; loans with material discrepancies exceeding configurable thresholds; fair lending review samples |
| **Primary Value Driver** | Eliminating documentation ping-pong and manual data entry — converting 48–72 hour initial file reviews into sub-24-hour automated pre-reviews, freeing underwriters from administrative overhead |

## Architecture

### System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      Document Sources                            │
│   Portal Upload  │  Email/Fax  │  Third-Party (VOE, Credit)     │
└────────┬─────────┴──────┬──────┴───────────┬────────────────────┘
         │                │                  │
         ▼                ▼                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Intake Service                                │
│  Normalize formats (PDF/JPEG/TIFF/photo) │ Split multi-doc PDFs │
│  Register in document queue              │ Assign tracking ID   │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│              OCR & Layout Extraction                             │
│  Azure Document Intelligence / Amazon Textract                   │
│  Preserves tables, forms, handwriting  │  Outputs structured    │
│  text with bounding boxes              │  page-level content    │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│           Classification & Data Extraction (LLM)                 │
│  Classifies into 700+ document types with confidence score       │
│  Extracts key fields (income, assets, dates, identifiers)        │
│  Returns structured JSON with per-field confidence               │
└────────┬───────────────────────────────────────┬─────────────────┘
         │ ≥ threshold                           │ < threshold
         ▼                                       ▼
┌─────────────────────────┐       ┌──────────────────────────────┐
│  Cross-Reference Engine │       │  Human Classification Queue  │
│  Validates consistency  │       │  Processor reviews low-conf  │
│  across loan file docs  │       │  documents and corrects      │
│  (W-2 vs tax vs paystub)│       └──────────────────────────────┘
│  Checks GSE guideline   │
│  requirements (DU/LPA)  │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│              Condition Generator                                 │
│  Identifies missing documents, data gaps, discrepancies          │
│  Generates specific conditions with borrower-facing language     │
│  Maps conditions to GSE guideline references                     │
└────────┬───────────────────────────────────────┬─────────────────┘
         │ routine                               │ complex / exception
         ▼                                       ▼
┌─────────────────────────┐       ┌──────────────────────────────┐
│  LOS Writeback Service  │       │  Underwriter Review Queue    │
│  Posts findings, condi-  │       │  AI-prepared file summary    │
│  tions, extracted data   │       │  with flagged exceptions     │
│  to Encompass/Empower    │       │  and recommended conditions  │
└─────────────────────────┘       └──────────────────────────────┘
```

### Component Responsibilities

| Component | Role | Notes |
|-----------|------|-------|
| Intake Service | Normalizes document formats, splits compound PDFs, assigns tracking IDs | Handles format chaos: photos, faxes, multi-page uploads with mixed content |
| OCR & Layout Extraction | Converts images and scanned documents to structured text preserving tables and forms | Separate from LLM stage to allow independent optimization of each |
| Classification & Extraction Agent | Classifies document type and extracts key fields using LLM with structured outputs | Confidence scoring at document and field level drives routing |
| Cross-Reference Engine | Validates data consistency across all documents in the loan file | Deterministic rules for GSE guideline checks; AI-assisted for ambiguous cases |
| Condition Generator | Produces specific, actionable conditions for missing or inconsistent data | Maps to Fannie Mae Selling Guide and Freddie Mac Guide requirements |
| LOS Writeback Service | Posts extracted data, classifications, conditions, and findings back to LOS | Bidirectional integration; never overwrites underwriter-entered data |

## End-to-End Flow

| Step | What Happens | Owner |
|------|--------------|-------|
| 1 | Documents arrive via portal, email, fax, or third-party service; Intake Service normalizes and registers each document | Integration service |
| 2 | OCR extracts text, tables, and form fields; preserves spatial layout for downstream classification | OCR service |
| 3 | LLM classifies document type (W-2, bank statement, appraisal, etc.) and extracts key data fields with per-field confidence scores | Classification agent |
| 4 | Cross-Reference Engine validates extracted data across the full loan file — income consistency, asset sufficiency, DTI/LTV calculations — against GSE guidelines | Rules engine + AI |
| 5 | Condition Generator identifies gaps and discrepancies; produces specific conditions with guideline references | Condition agent |
| 6 | Routine findings and conditions written to LOS; complex or exception cases routed to underwriter review queue with AI-prepared summary | LOS adapter / routing |
| 7 | When new documents arrive to satisfy conditions, system re-runs extraction and cross-referencing; auto-clears conditions that now pass | Classification + rules |

## AI Responsibilities and Boundaries

| Workflow Area | AI Does | Deterministic System Does | Human Owns |
|---------------|---------|---------------------------|------------|
| Document classification | Identifies document type with confidence score across 700+ categories | Routes below-threshold documents to human queue | Resolves ambiguous or novel document types |
| Data extraction | Extracts income, asset, liability, and property fields from unstructured documents | Validates field formats, enforces schema constraints | Reviews low-confidence extractions flagged by system |
| Cross-referencing | Identifies discrepancies across documents (income mismatch, undisclosed debts) | Calculates DTI, LTV, reserves using extracted values against GSE formulas | Adjudicates material discrepancies; applies compensating factors |
| Condition generation | Drafts specific conditions with borrower-facing language | Enforces TRID timelines; maps conditions to guideline sections | Approves or modifies conditions before issuance; final credit decision |
| Condition clearing | Evaluates newly submitted documents against outstanding conditions | Confirms document completeness and format requirements | Reviews cleared conditions for complex cases |

## Integration Seams

| System | Integration Method | Why It Matters |
|--------|--------------------|----------------|
| ICE Encompass / Black Knight Empower | REST API (Encompass Partner API / Empower SDK) | 45%+ of US mortgage originations flow through Encompass; bidirectional read/write is essential for loan data and document indexing |
| Borrower portal / document upload | Event-driven (webhook or queue trigger on upload) | Documents must be processed within seconds of receipt to maintain near-real-time classification |
| GSE automated underwriting (DU/LPA) | API or findings import | Cross-referencing must align with DU/LPA documentation requirements and eligibility decisions |
| Email / fax channels | Microsoft Graph API or email gateway | Legacy channels still account for significant document volume; intake must handle these alongside portal uploads |
| Document storage | LOS-native document store or S3/Blob with LOS reference | Extracted text and metadata stored alongside source documents for audit trail |

## Control Model

| Risk | Control |
|------|---------|
| Extraction hallucination (LLM generates plausible but incorrect field values) | Per-field confidence scoring; dual-extraction with comparison for high-stakes fields (income, SSN); deterministic schema validation rejects out-of-range values |
| Incorrect condition generation (AI misses a required document or generates a spurious condition) | Conditions mapped to specific GSE guideline sections; underwriter reviews all conditions before borrower communication in initial rollout |
| Fair lending risk (inconsistent AI treatment across borrower demographics) | AI operates on document content only — no access to race, ethnicity, gender, or age fields; periodic fair lending audit comparing AI outcomes across demographic segments |
| TRID timeline violation (AI processing delay causes missed disclosure deadlines) | Deterministic timeline tracker independent of AI pipeline; alerts if document processing queue exceeds SLA thresholds |
| Data privacy breach (borrower PII exposed in logs or model context) | PII fields (SSN, DOB, account numbers) redacted from logs and traces; model context scoped to single loan file; SOC 2 Type II controls on all processing infrastructure |
| Over-automation (system auto-clears a condition that should require human review) | Configurable escalation thresholds by condition type; high-risk conditions (large deposits, employment gaps, income discrepancies above threshold) always route to underwriter |

## Reference Technology Stack

| Layer | Default Choice | Reason | Viable Alternative |
|-------|----------------|--------|--------------------|
| **Model layer** | Azure OpenAI GPT-4o with structured outputs | Strong performance on document understanding and structured extraction; Azure hosting satisfies data residency requirements | Anthropic Claude via Amazon Bedrock (proven at Rocket Close for mortgage documents) |
| **OCR / layout** | Azure Document Intelligence with prebuilt mortgage models | Purpose-built models for Form 1003, 1004, 1005, 1008, and Closing Disclosure; handles photos and faxes | Amazon Textract (proven at Rocket Close) |
| **Orchestration** | LangGraph (Python) | Graph-based workflow with conditional routing fits the branching classification → extraction → cross-reference → condition pipeline | Custom state machine; Temporal for long-running loan lifecycles |
| **Eventing** | Azure Service Bus or Amazon SQS | Decouples document intake from processing; handles volume spikes during refi booms | Apache Kafka for higher-throughput deployments |
| **Observability** | LangSmith or Azure Monitor | Trace every classification and extraction decision for audit; monitor confidence distributions and escalation rates | Datadog with custom instrumentation |

## Key Design Decisions

| Decision | Choice | Why It Fits This Use Case |
|----------|--------|---------------------------|
| Separate OCR and LLM stages | Two-stage pipeline: OCR first, then LLM classification/extraction | Allows independent optimization — OCR handles format chaos (photos, faxes, handwriting) while LLM handles semantic understanding. Proven architecture at Rocket Close |
| No AI credit decisions | AI prepares the file; human underwriter retains final approval authority | ECOA/Reg B requires explainable credit decisions with specific adverse action reasons. CFPB Circular 2022-03 explicitly prohibits "black box" defenses. Human-in-the-loop satisfies regulatory requirements |
| Confidence-based routing | Documents and fields below configurable confidence thresholds route to human review | Allows gradual trust calibration — start with conservative thresholds, widen as accuracy is validated. Mirrors Indecomm's approach of flagging fields below 90% confidence for review |
| LOS-native storage | All extracted data and AI findings written back to the LOS, not a parallel system | Underwriters work in their existing LOS; the AI system augments rather than replaces the workflow. Avoids dual-system complexity and maintains single audit trail |
| Per-loan context isolation | Each loan file processed in an isolated context; no cross-loan data leakage | Borrower privacy protection; prevents PII from one loan appearing in another's processing context. Aligns with GLBA requirements |
