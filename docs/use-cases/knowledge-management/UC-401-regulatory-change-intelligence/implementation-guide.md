---
layout: use-case-detail
title: "Implementation Guide — Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
uc_id: "UC-401"
uc_title: "Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Knowledge Management"
status: "detailed"
slug: "UC-401-regulatory-change-intelligence"
permalink: /use-cases/UC-401-regulatory-change-intelligence/implementation-guide/
---

## Prerequisites

| Prerequisite | Detail |
|--------------|--------|
| **Azure Subscription** | Azure OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-large), Azure AI Search (S1+), Azure Service Bus, Azure Blob Storage, Azure SQL Database, Azure Container Apps or AKS |
| **API Keys / Access** | Azure OpenAI endpoint with GPT-4o and GPT-4o-mini deployments; Azure AI Search admin key; regulatory feed API keys (CUBE, Wolters Kluwer, or equivalent) |
| **Existing Systems** | GRC platform (ServiceNow GRC, RSA Archer, or MetricStream) with REST API access; policy management system (SharePoint or equivalent) |
| **Dev Environment** | Python 3.11+, `langgraph`, `langchain-openai`, `azure-search-documents`, `pydantic`, `httpx` |
| **Permissions** | Managed Identity with Cognitive Services OpenAI User role; Azure AI Search contributor; Service Bus sender/receiver; GRC platform API credentials (service account with read/write to obligation register) |

---

## Project Structure

```
reg-change-intelligence/
├── src/
│   ├── agents/              # Agent definitions and orchestration
│   │   ├── scanner.py       # Horizon Scanner Agent
│   │   ├── extractor.py     # Obligation Extraction Agent
│   │   ├── assessor.py      # Applicability Assessment Agent
│   │   ├── gap_analyzer.py  # Gap Analysis Agent
│   │   ├── policy_drafter.py # Policy Drafting Agent
│   │   └── pipeline.py      # LangGraph pipeline orchestration
│   ├── tools/               # Tool/function definitions for agents
│   │   ├── regulatory_feed.py    # Regulatory source connectors
│   │   ├── obligation_store.py   # Obligation register CRUD
│   │   ├── knowledge_base.py     # Azure AI Search RAG tools
│   │   ├── grc_connector.py      # GRC platform integration
│   │   └── policy_store.py       # Policy document retrieval
│   ├── prompts/             # System prompts and prompt templates
│   │   ├── extraction.py    # Obligation extraction prompts
│   │   ├── assessment.py    # Applicability assessment prompts
│   │   └── drafting.py      # Policy drafting prompts
│   ├── models/              # Data models and schemas
│   │   ├── obligation.py    # Obligation Pydantic models
│   │   ├── assessment.py    # Assessment result models
│   │   └── pipeline_state.py # LangGraph state definition
│   └── api/                 # API endpoints
│       └── routes.py        # FastAPI endpoints for human review
├── config/
│   └── settings.py          # Configuration (env vars, thresholds)
├── tests/
│   ├── test_extraction.py   # Extraction accuracy tests
│   ├── test_assessment.py   # Applicability assessment tests
│   └── eval/                # Gold-set evaluation suites
│       └── obligations_gold.json
└── pyproject.toml
```

---

## Step-by-Step Implementation

### Phase 1: Foundation (Weeks 1-2)

#### Step 1.1: Environment Setup

```bash
pip install langgraph langchain-openai azure-search-documents azure-identity \
    azure-servicebus pydantic httpx fastapi uvicorn python-dotenv
```

Create `.env`:

```
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_AI_SEARCH_ENDPOINT=https://<resource>.search.windows.net/
AZURE_AI_SEARCH_KEY=<key>
GRC_PLATFORM_BASE_URL=https://<grc-instance>.service-now.com
GRC_API_KEY=<service-account-key>
AZURE_SERVICE_BUS_CONN_STRING=<conn-string>
```

#### Step 1.2: Define Core Data Models

Create `src/models/obligation.py` with Pydantic schemas for `Obligation`, `ApplicabilityResult`, `GapAssessment`, `PolicyRedline`, and `PipelineState`.

#### Step 1.3: Set Up Azure Infrastructure

1. Deploy Azure OpenAI resources (GPT-4o, text-embedding-3-large)
2. Create Azure AI Search index with schema matching regulatory corpus
3. Set up Service Bus topic for event routing
4. Configure managed identities and RBAC roles

### Phase 2: Core Agents (Weeks 3-6)

#### Step 2.1: Horizon Scanner Agent

```python
# src/agents/scanner.py
from langgraph.graph import StateGraph
from langchain_openai import AzureChatOpenAI

def build_scanner():
    llm = AzureChatOpenAI(
        deployment_name="gpt-4o-mini",
        model_name="gpt-4o-mini",
        temperature=0
    )
    # Define classification prompt
    # Returns: document_type, jurisdiction, topic, urgency, confidence
    ...
```

Monitors regulatory feed APIs, classifies documents, routes to extraction.

#### Step 2.2: Obligation Extraction Agent

The highest-value agent. Uses structured output (JSON mode) to enforce schema compliance.

```python
# src/agents/extractor.py
# Input: regulatory text chunks (2K-4K tokens)
# Output: list of Obligation schema-compliant extractions
# Key prompt rules:
# - Never infer obligations not explicitly stated
# - Each deontic statement is a separate obligation
# - Include ambiguity_flag if modal verb is uncertain
```

Target: 90%+ precision on gold set before production.

#### Step 2.3: Applicability Assessment Agent

Maps extracted obligations to firm's regulatory perimeter.

```python
# src/agents/assessor.py
# Input: Obligation + firm's regulatory perimeter definition
# Output: ApplicabilityResult (applicable/partial/not-applicable + reasoning)
# Use RAG retrieval of past assessments for consistency
```

#### Step 2.4: Gap Analysis Agent

Hybrid approach: deterministic matching + LLM semantic similarity.

```python
# src/agents/gap_analyzer.py
# Input: Applicable obligation + existing obligation register + control framework
# Output: GapAssessment with identified gaps and severity
```

#### Step 2.5: Policy Drafting Agent

Generates redlines respecting firm style guide and regulatory citations.

```python
# src/agents/policy_drafter.py
# Input: Gap details + current policy text + regulatory context
# Output: PolicyRedline JSON with proposed insertions/modifications
```

### Phase 3: Orchestration & Integration (Weeks 7-10)

#### Step 3.1: LangGraph Pipeline

```python
# src/agents/pipeline.py
from langgraph.graph import StateGraph
from src.models.pipeline_state import PipelineState

def build_pipeline():
    graph = StateGraph(PipelineState)
    
    # Add nodes
    graph.add_node("scanner", scanner_node)
    graph.add_node("extraction", extraction_node)
    graph.add_node("assessment", assessment_node)
    graph.add_node("gap_analysis", gap_analysis_node)
    graph.add_node("policy_draft", policy_draft_node)
    graph.add_node("human_review", human_review_node)
    
    # Add conditional edges
    graph.add_conditional_edges(
        "assessment",
        lambda state: "human_review" if state.confidence < 0.80 else "gap_analysis"
    )
    
    # Set entry and compile
    graph.set_entry_point("scanner")
    return graph.compile(interrupt_before=["human_review", "gap_analysis"])
```

#### Step 3.2: GRC Platform Connector

```python
# src/tools/grc_connector.py
class GRCConnector:
    def __init__(self, base_url: str, api_key: str):
        self.client = httpx.Client(headers={"Authorization": f"Bearer {api_key}"})
    
    def read_obligation_register(self) -> list[dict]:
        """Fetch all obligations from GRC system."""
        ...
    
    def write_assessment(self, assessment: GapAssessment):
        """Record assessment in GRC."""
        ...
```

#### Step 3.3: Knowledge Base (RAG)

```python
# src/tools/knowledge_base.py
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

class RegulatoryKB:
    def __init__(self, search_client: SearchClient, embedding_client):
        self.search = search_client
        self.embeddings = embedding_client
    
    def retrieve_similar_obligations(self, obligation: str, top_k: int = 5):
        """Retrieve past assessments of similar obligations via semantic search."""
        ...
```

#### Step 3.4: FastAPI for Human Review

```python
# src/api/routes.py
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/assessments/{assessment_id}/approve")
async def approve_assessment(assessment_id: str, feedback: dict):
    """Compliance officer approves/rejects an assessment."""
    ...

@app.post("/assessments/{assessment_id}/escalate")
async def escalate_assessment(assessment_id: str, reason: str):
    """Escalate to senior compliance officer."""
    ...
```

### Phase 4: Testing & Calibration (Weeks 11-14)

#### Step 4.1: Build Gold Set

Label 20-30 regulations from multiple jurisdictions with:
- Ground-truth obligations
- Applicability assessments
- Policy gap identifications

#### Step 4.2: Evaluation Metrics

```python
# src/eval/metrics.py
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix

def evaluate_extraction(predictions, gold_set):
    """Precision, recall, F1 on obligation extraction."""
    ...

def evaluate_applicability(predictions, gold_set):
    """Accuracy on applicability classification."""
    ...
```

#### Step 4.3: Prompt Tuning

Use gold set results to refine prompts:
- Add more few-shot examples
- Tighten deontic classification rules
- Improve applicability reasoning

Target: 90%+ precision, 85%+ recall on extraction before production.

### Phase 5: Deployment (Weeks 15-16)

#### Step 5.1: Container Image

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "src.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 5.2: Deploy to AKS

```bash
kubectl create namespace compliance-ai
kubectl apply -f k8s/deployment.yaml -n compliance-ai
kubectl apply -f k8s/service.yaml -n compliance-ai
```

#### Step 5.3: Configure Monitoring

Set up Application Insights dashboards:
- Agent decision traces (confidence scores, tool calls)
- End-to-end latencies (detection → assessment → draft)
- Escalation rates and human review queue depth
- GRC system sync health

---

## Prompt Strategy

### Obligation Extraction Prompt

```
System:
You are the Obligation Extraction Agent for a regulatory change management platform.

Rules:
1. Extract only obligations explicitly stated in the regulatory text.
2. For each obligation, identify:
   - obligation_text: Exact verbatim quote
   - deontic_type: must | shall | may | must_not | should
   - addressee: Who the obligation applies to
   - predicate: What the addressee must do
   - conditions: Under what circumstances
   - effective_date: When it takes effect (if stated)
   - cross_references: Other articles referenced
   - article_reference: Source article/section number
3. Do NOT infer obligations not explicitly stated.
4. Do NOT merge multiple obligations into one.
5. If ambiguous, set ambiguity_flag=true.
6. Return only valid JSON array.
```

### Applicability Assessment Prompt

```
System:
You are the Applicability Assessment Agent.

You have:
- The firm's regulatory perimeter (licensed activities, entity types, jurisdictions)
- Historical applicability assessments for similar obligations

Rules:
1. Assess each obligation against the firm's regulatory perimeter.
2. An obligation is "applicable" if:
   - The firm matches the addressee definition
   - AND operates in the specified jurisdiction
   - AND conducts the relevant activity
3. Provide reasoning tracing to specific elements of regulatory perimeter.
4. Include confidence_score (0.0-1.0). Below 0.80 → human review.
5. Never assume applicability—if addressee definition unclear, mark "requires_review".
```

---

## Integration Checklist

- [ ] Azure OpenAI deployments (GPT-4o, GPT-4o-mini, text-embedding-3-large)
- [ ] Azure AI Search index created and initial corpus indexed
- [ ] Regulatory feed API access (CUBE, Wolters Kluwer, or equivalent)
- [ ] GRC platform API connectivity tested (ServiceNow/Archer/MetricStream)
- [ ] Policy management system integration (SharePoint read access)
- [ ] Service Bus topic/queue topology configured
- [ ] Managed Identity and RBAC roles assigned
- [ ] Environment variables and secrets stored in Key Vault
- [ ] Gold set (20-30 regulations) labeled for evaluation
- [ ] Extraction agent achieves 90%+ precision on gold set
- [ ] Applicability assessment reaches 95%+ accuracy
- [ ] End-to-end pipeline tested with sample regulatory change
- [ ] Human review workflow (FastAPI endpoints) functional
- [ ] Application Insights monitoring configured
- [ ] Container image built and published to ACR
- [ ] AKS deployment manifests prepared
- [ ] Stakeholder onboarding materials prepared
