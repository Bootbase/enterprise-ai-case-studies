---
layout: use-case-detail
title: "Solution Design — Autonomous Customs Declaration and Trade Document Processing"
uc_id: "UC-003"
uc_title: "Autonomous Customs Declaration and Trade Document Processing"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "Document Processing"
category_icon: "file-text"
industry: "Logistics / Global Trade"
complexity: "High"
status: "detailed"
slug: "UC-003-customs-trade-document-processing"
permalink: /use-cases/UC-003-customs-trade-document-processing/solution-design/
---

## What This Design Covers

This design covers the declaration-preparation layer of customs brokerage: ingesting trade documents, extracting shipment facts, recommending tariff classifications, assembling filing-ready declarations, and routing exceptions to a licensed broker. AI handles document interpretation and candidate generation. Deterministic validation, filing adapters, and human review stay in charge of legal submission and edge-case decisions.

## Recommended Operating Model

| Decision Area | Recommendation |
|---------------|----------------|
| **Autonomy Model** | Semi-autonomous. Auto-draft repeat traffic, but require broker review for new SKUs, missing origin evidence, sanctions hits, quota or trade-remedy exposure, and low-confidence cases |
| **System of Record** | Existing customs operating platform remains authoritative for shipment context, item master, broker overrides, and filing history. Government systems remain authoritative for filing status |
| **Human Decision Points** | Final sign-off on low-confidence entries, legal classification overrides, origin disputes, denied-party escalations, and filings with material duty impact |
| **Primary Value Driver** | Reduce repetitive document comparison and tariff lookup work while recovering avoidable duty leakage and shortening clearance preparation time |

## Architecture

### System Diagram

```text
┌───────────────────────────────────────────────────────────────────────┐
│ Sources                                                               │
│ Portal / EDI / Email / Forwarder feed / ERP shipment event            │
└──────────────┬────────────────────────────────────────────────────────┘
               ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Intake and normalization                                              │
│ Split document bundles, OCR/layout extraction, shipment correlation   │
└──────────────┬────────────────────────────────────────────────────────┘
               ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Trade reasoning layer                                                 │
│ LLM extraction + candidate HS ranking + origin evidence synthesis     │
│ bounded by retrieved tariff data, prior rulings, item master history  │
└──────────────┬───────────────────────────────┬────────────────────────┘
               │                               │
               │ high confidence               │ exception / low confidence
               ▼                               ▼
┌──────────────────────────────┐   ┌───────────────────────────────────┐
│ Deterministic validation     │   │ Broker review workbench           │
│ Required fields, duty math,  │   │ Review evidence, override codes,  │
│ schema checks, screening,    │   │ request documents, approve draft  │
│ country adapter rules        │   └───────────────────────────────────┘
└──────────────┬───────────────┘
               ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Filing adapters and audit trail                                       │
│ Customs platform writeback -> CDS / ICS2 / local adapter -> responses │
└───────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Role | Notes |
|-----------|------|-------|
| Intake and normalization service | Registers documents, correlates them to shipments, runs OCR and layout extraction | Keeps source documents and extracted text versioned for audit |
| Trade reasoning layer | Extracts declaration fields and ranks HS and origin candidates from retrieved sources | It only works against a bounded candidate set. Published accuracy ranges from 80% (LLMs at 6-digit) to 95% (domain-trained at 11-digit) |
| Tariff and compliance knowledge service | Serves tariff measures, origin rules, screening lists, and prior broker decisions | Versioning matters because tariff and filing rules change |
| Deterministic validation engine | Enforces country schema rules, validates duty math, checks required fields, and blocks unsafe submissions | It rejects incomplete or contradictory drafts before transmission |
| Broker review workbench | Presents evidence, confidence, candidate codes, and exceptions for approval or override | Human corrections become reusable memory for repeat SKUs |
| Filing adapter layer | Translates approved drafts into country-specific messages and records acknowledgements or rejects | Country interfaces differ enough to justify separate adapters |

## End-to-End Flow

| Step | What Happens | Owner |
|------|--------------|-------|
| 1 | Shipment context and source documents arrive; the intake service normalizes the bundle and assigns a declaration case ID | Integration service |
| 2 | OCR and layout extraction produce structured text; the reasoning layer extracts invoice, packing, transport, and origin facts with evidence spans | Document pipeline |
| 3 | Tariff candidates, origin rules, item history, and sanctions lists are retrieved; AI ranks candidates and drafts the declaration | Retrieval + AI |
| 4 | Deterministic validators check required elements, duty math, document completeness, screening results, and adapter rules | Rules engine |
| 5 | High-confidence drafts are staged for filing; exceptions route to a broker who approves, overrides, or requests more evidence | Filing adapter + broker |

## AI Responsibilities and Boundaries

| Workflow Area | AI Does | Deterministic System Does | Human Owns |
|---------------|---------|---------------------------|------------|
| Document extraction | Extracts product descriptions, quantities, values, packaging, origin clues, and document references | Enforces field schemas, required-document checks, and evidence linkage | Resolves unreadable or contradictory source documents |
| HS classification support | Ranks candidate commodity codes and explains fit against retrieved evidence | Restricts candidate sets by jurisdiction, validates code format, and recalculates duty impact | Makes final decisions on new products, ambiguous goods, and material overrides |
| Origin and FTA preparation | Summarizes origin evidence and flags missing proof | Checks whether required proof types are present for the claimed preference | Decides whether origin proof is sufficient and whether to claim preference |
| Screening and filing prep | Prepares screening context and declaration narratives | Executes screening, validates filing payloads, and controls transmission rights | Adjudicates screening matches and authorizes filing where policy requires review |

## Integration Seams

| System | Integration Method | Why It Matters |
|--------|--------------------|----------------|
| Customs operating platform | REST API or event-driven adapter into CargoWise, Descartes, broker OMS, or importer compliance platform | This is where broker work already happens |
| Country filing interfaces | Country-specific API or message adapter for US ACE (via ABI), UK CDS (via HMRC API), EU ICS2 (via STI), and other certified customs channels | Filing contracts are formal and jurisdiction-specific. ABI is the only approved US filing method; CDS replaced CHIEF for UK declarations; ICS2 became mandatory across all EU transport modes in September 2025 |
| Tariff and origin data services | Official tariff datasets or licensed tariff content, plus internal item master and ruling store | Classification quality depends on bounded retrieval and versioned data |
| Screening and compliance services | Enterprise sanctions screening API plus case-management callback | Screening must stay deterministic and auditable |

## Control Model

| Risk | Control |
|------|---------|
| Incorrect tariff classification due to vague product descriptions | Retrieve a bounded set of candidate codes, require evidence spans, and route low-confidence or high-duty-impact outcomes to broker review |
| Filing invalidation because country schemas drift or message versions change | Keep adapter validation separate from AI, pin adapter versions, and test against country sandboxes before rollout |
| Unsupported FTA claim or wrong origin statement | Separate origin proof detection from origin decisioning; block preference claims when required proof is absent or stale |
| False negative or false positive sanctions handling | Use deterministic screening outside the model and require human adjudication before release on matched parties |

## Reference Technology Stack

| Layer | Default Choice | Reason | Viable Alternative |
|-------|----------------|--------|--------------------|
| **Model layer** | OpenAI Responses API with structured outputs, deployed directly or through Azure OpenAI where residency demands it | Produces typed drafts instead of brittle free-form text | Anthropic Claude on Amazon Bedrock |
| **Document understanding** | Azure AI Document Intelligence | Strong OCR and layout extraction for mixed PDFs, scans, and image-based shipping documents | Amazon Textract |
| **Orchestration** | LangGraph | Explicit state transitions fit the intake -> retrieval -> draft -> validate -> file or escalate workflow | Temporal or custom state machine |
| **Retrieval / memory** | Postgres plus pgvector for case memory, with a versioned tariff and rulings store | Keeps broker corrections, product history, and tariff snapshots queryable and auditable | Elasticsearch plus object storage |

## Key Design Decisions

| Decision | Choice | Why It Fits This Use Case |
|----------|--------|---------------------------|
| Country rollout strategy | Start with one customs regime and one lane before expanding | Customs adapters, origin rules, and message contracts vary too much for a multi-country first release |
| Classification pattern | Retrieve candidate codes first, then let the model rank and justify them | Retrieval bounds the search space and reduces hallucination risk |
| Submission authority | Keep filing credentials and transmission rights outside the model | Filing is a regulated act. The model should prepare drafts, not hold authority to transmit |
| Learning loop | Use broker overrides and post-entry outcomes as controlled memory | Customs teams need explainable reuse of prior decisions by SKU, supplier, and jurisdiction |
