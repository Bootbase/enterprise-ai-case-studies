---
layout: use-case-detail
title: "Implementation Guide — Autonomous Freight Logistics Orchestration"
uc_id: "UC-200"
uc_title: "Autonomous Freight Logistics Orchestration with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Workflow Automation"
status: "detailed"
slug: "UC-200-freight-logistics-orchestration"
permalink: /use-cases/UC-200-freight-logistics-orchestration/implementation-guide/
---

## Prerequisites

| Prerequisite | Detail |
|--------------|--------|
| **Azure Subscription** | Azure OpenAI deployment with GPT-4o (structured outputs), Azure Service Bus, Azure Container Apps or AKS. |
| **TMS Access** | API credentials for target TMS (Navisphere, MercuryGate, BluJay) with read/write permissions. |
| **NMFC Classification Data** | Licensed access to National Motor Freight Classification tariff via internal lookup API. |
| **Email Access** | Microsoft Graph API or IMAP credentials for inbound logistics email inbox. |
| **Dev Environment** | Python 3.11+, openai, langgraph, pydantic, aiohttp, tenacity, azure-servicebus. |

## Project Structure

```text
freight-agents/
├── src/
│   ├── agents/
│   │   ├── email_classifier.py
│   │   ├── quote_extractor.py
│   │   ├── order_parser.py
│   │   ├── freight_classifier.py
│   │   ├── carrier_matcher.py
│   │   ├── tracking_agent.py
│   │   └── missed_pickup.py
│   ├── tools/
│   │   ├── tms.py
│   │   ├── nmfc.py
│   │   ├── pricing.py
│   │   ├── carrier_capacity.py
│   │   └── voice.py
│   ├── prompts/
│   ├── models/
│   ├── workers/
│   └── eval/
├── tests/
└── README.md
```

## Phase 1: Foundation

### Step 1: Define Extraction Schemas

Define Pydantic models for QuoteRequest, OrderTender, FreightClassification, and TrackingUpdate before writing prompts. The schema is the contract between the LLM and the rest of the system.

### Step 2: Install Dependencies

```bash
uv init freight-agents
uv add openai langgraph pydantic aiohttp tenacity azure-servicebus azure-identity
```

Use langgraph for multi-step tool-calling loops (freight classification, missed pickup resolution). Use azure-servicebus for event-driven coordination.

## Phase 2: Core AI Integration

### Step 1: Azure OpenAI Setup

Configure Azure OpenAI with structured outputs enforcing JSON schema compliance. Set temperature=0 for all extraction agents.

### Step 2: Email Classification Agent

Build the ingestion router that classifies emails by transaction type (quote, order, tracking, capacity). C.H. Robinson's classifier handles 11,000+ emails daily.

### Step 3: Freight Classification Agent

Implement tool-calling pattern where agent queries NMFC lookup service before selecting codes. Never allow hallucinated NMFC codes.

### Step 4: Quote and Order Extraction Agents

Build schema-first extraction agents. C.H. Robinson's order agent processes 5,500 truckload orders/day in 90 seconds each.

## Phase 3: Integration & Orchestration

### Step 1: TMS Connector

Build REST API client for target TMS (Navisphere, MercuryGate, BluJay). Implement bidirectional read/write for shipments, orders, tracking, appointments.

### Step 2: Event-Driven Coordination

Deploy Azure Service Bus topics for email classification, quote requests, order tenders, and exceptions. Each agent subscribes to its trigger event and publishes results to downstream topics.

### Step 3: Pricing & Carrier Matching

Implement deterministic pricing engine that evaluates rate cards, market factors, carrier performance. Integrate carrier matching optimization algorithm.

### Step 4: Voice AI for Tracking & Missed Pickups

Connect Azure Communication Services for outbound voice calls. Train voice agent to extract tracking status, handle carrier objections, determine missed pickup resolutions.

## Phase 4: Evaluation & Monitoring

### Step 1: Build Evaluation Set

Create labeled dataset of 500+ emails per transaction type with correct extractions, classifications, and NMFC codes.

### Step 2: Accuracy Metrics

- Quote extraction accuracy vs. manual baseline
- NMFC classification accuracy on labeled set
- Order processing time and error rate
- Quote response time and coverage

### Step 3: Observability

Deploy LangSmith for agent tracing, tool call monitoring, and decision pathway visibility. Configure Application Insights for latency, throughput, and error rate tracking.

## Deployment Strategy

C.H. Robinson's phased approach:

1. Start with highest-volume, most-structured customer cohort (quote extraction)
2. Validate extraction accuracy on real email diversity
3. Add order processing agent for top 100 customers
4. Deploy NMFC classification agent for LTL shipments
5. Roll out voice AI for tracking and missed pickup resolution
6. Expand to broader customer base once agents prove reliable

## Key Technical Decisions

- **Schema-first extraction**: Non-negotiable for reliable production operation at scale
- **Tool-first classification**: NMFC lookup tool prevents hallucinated codes
- **Event-driven coordination**: Parallel workflows (quoting, booking, tracking) operate independently on shared TMS state
- **TMS as system of record**: Agents augment, not replace, existing platform
- **Confidence-based escalation**: Human reviewers handle ambiguous extractions, high-value accounts, novel exceptions
