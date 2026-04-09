# UC-042: Autonomous RFP and Proposal Response Generation — Implementation Guide

## Prerequisites

| Prerequisite | Detail |
|---|---|
| **Azure Subscription** | Azure OpenAI (GPT-4o, text-embedding-3-large deployed), Azure AI Search (S1+), Azure AI Document Intelligence, Cosmos DB, Blob Storage |
| **API Keys / Access** | Azure OpenAI endpoint + deployment names; Azure AI Search endpoint + admin key; Document Intelligence endpoint |
| **Existing Systems** | SharePoint/OneDrive for source documents; Salesforce CRM API access (optional for bid/no-bid); Microsoft Teams webhook URL (optional for SME routing) |
| **Dev Environment** | Python 3.11+, `langgraph>=0.3`, `langchain-openai`, `azure-ai-formrecognizer`, `azure-search-documents`, `azure-cosmos`, `fastapi` |
| **Permissions** | Managed Identity with Cognitive Services OpenAI User, Search Index Data Contributor, Storage Blob Data Reader roles |

---

## Project Structure

```
rfp-agent/
├── src/
│   ├── agents/              # Agent definitions (one file per agent)
│   │   ├── classifier.py
│   │   ├── retriever.py
│   │   ├── drafter.py
│   │   ├── compliance.py
│   │   ├── reviewer.py
│   │   └── bid_scorer.py
│   ├── tools/               # Tool functions agents call
│   │   ├── search.py        # Azure AI Search integration
│   │   ├── document_parser.py  # Document Intelligence integration
│   │   └── crm.py           # Salesforce CRM integration
│   ├── prompts/             # System prompts per agent
│   │   ├── classifier.md
│   │   ├── drafter.md
│   │   └── compliance.md
│   ├── graph/               # LangGraph orchestration
│   │   ├── state.py         # Shared state definition
│   │   ├── workflow.py      # Graph definition + edges
│   │   └── checkpointer.py  # Cosmos DB persistence
│   ├── models/              # Pydantic data models
│   │   └── schemas.py
│   └── api/                 # FastAPI endpoints
│       └── routes.py
├── scripts/
│   ├── index_content.py     # Build Azure AI Search index from content library
│   └── evaluate.py          # Run evaluation suite
├── config/
│   └── settings.py          # Environment-based configuration
└── tests/
    ├── test_agents.py
    ├── test_tools.py
    └── test_evaluation.py
```

---

## Step-by-Step Implementation

### Phase 1: Foundation

#### Step 1.1: Content Library Indexing

The content library is the foundation — without well-indexed, current content, the AI has nothing to ground its responses in. This step creates the Azure AI Search index and populates it from source documents.

```python
# scripts/index_content.py
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
)
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

credential = DefaultAzureCredential()

# Define index schema with hybrid search support
index = SearchIndex(
    name="rfp-content-library",
    fields=[
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String,
                    searchable=True, analyzer_name="en.microsoft"),
        SearchField(name="content_vector", type=SearchFieldDataType.Collection(
                    SearchFieldDataType.Single), vector_search_dimensions=3072,
                    vector_search_profile_name="hnsw-profile"),
        SearchField(name="source_document", type=SearchFieldDataType.String,
                    filterable=True),
        SearchField(name="category", type=SearchFieldDataType.String,
                    filterable=True, facetable=True),
        SearchField(name="last_verified_date", type=SearchFieldDataType.DateTimeOffset,
                    filterable=True, sortable=True),
        SearchField(name="document_type", type=SearchFieldDataType.String,
                    filterable=True),  # "proposal", "product_doc", "certification"
    ],
    vector_search=VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
        profiles=[VectorSearchProfile(name="hnsw-profile",
                                       algorithm_configuration_name="hnsw-config")],
    ),
    semantic_search=SemanticSearch(
        configurations=[SemanticConfiguration(
            name="rfp-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                content_fields=[SemanticField(field_name="content")]
            ),
        )]
    ),
)

index_client = SearchIndexClient(
    endpoint="https://<search-service>.search.windows.net",
    credential=credential,
)
index_client.create_or_update_index(index)
```

**Verification:** Run `az search index show --name rfp-content-library` and confirm the index exists with vector and semantic configurations.

#### Step 1.2: Core Dependencies

```bash
pip install langgraph>=0.3 langchain-openai langchain-core \
    azure-search-documents azure-ai-formrecognizer azure-cosmos \
    azure-identity openai fastapi uvicorn pydantic
```

---

### Phase 2: Core AI Integration

#### Step 2.1: LLM Connection & Configuration

Two model deployments serve different roles: GPT-4o for reasoning-heavy tasks (drafting, compliance), GPT-4o-mini for high-volume classification.

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    azure_openai_endpoint: str
    azure_openai_api_version: str = "2025-12-01-preview"

    # Model deployments
    model_reasoning: str = "gpt-4o"          # Draft generation, compliance, review
    model_classification: str = "gpt-4o-mini" # Question classification, dedup
    model_embedding: str = "text-embedding-3-large"

    # Temperatures per agent role
    temp_classifier: float = 0.0
    temp_drafter: float = 0.3
    temp_compliance: float = 0.0
    temp_reviewer: float = 0.1

    # Search
    search_endpoint: str
    search_index: str = "rfp-content-library"
    search_top_k: int = 8
    search_semantic_config: str = "rfp-semantic-config"

    # Thresholds
    confidence_threshold: float = 0.7  # Below this → flag for human review
    staleness_days: int = 365          # Content older than this → flag as stale

    class Config:
        env_prefix = "RFP_"
```

```python
# src/agents/_llm.py
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from config.settings import Settings

settings = Settings()
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

def get_llm(role: str) -> AzureChatOpenAI:
    """Return a configured LLM for the given agent role."""
    model_map = {
        "classifier": (settings.model_classification, settings.temp_classifier),
        "drafter": (settings.model_reasoning, settings.temp_drafter),
        "compliance": (settings.model_reasoning, settings.temp_compliance),
        "reviewer": (settings.model_reasoning, settings.temp_reviewer),
        "bid_scorer": (settings.model_reasoning, settings.temp_classifier),
    }
    model, temperature = model_map[role]
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=settings.azure_openai_api_version,
        azure_deployment=model,
        temperature=temperature,
    )
```

#### Step 2.2: Shared State Definition

LangGraph's `TypedDict` state flows through every node. This is the central data structure that accumulates results as the RFP moves through the pipeline.

```python
# src/graph/state.py
from typing import TypedDict, Annotated
from operator import add

class RFPQuestion(TypedDict):
    id: str
    text: str
    category: str | None
    is_duplicate: bool
    duplicate_of: str | None

class RetrievedPassage(TypedDict):
    content: str
    source_document: str
    relevance_score: float
    last_verified_date: str

class DraftResponse(TypedDict):
    question_id: str
    response_text: str
    citations: list[str]
    confidence: float
    flagged_stale: bool

class ComplianceResult(TypedDict):
    requirement_id: str
    addressed: bool
    section_ref: str | None
    gap_description: str | None

class RFPState(TypedDict):
    # Input
    rfp_document_url: str
    rfp_raw_markdown: str
    company_name: str

    # Parsed questions
    questions: list[RFPQuestion]

    # Retrieval results (keyed by question_id)
    retrieved_passages: dict[str, list[RetrievedPassage]]

    # Generated drafts
    drafts: list[DraftResponse]

    # Compliance
    compliance_results: list[ComplianceResult]
    compliance_gaps: list[str]

    # Quality
    quality_score: float
    quality_issues: list[str]

    # Bid/no-bid
    bid_score: float
    bid_recommendation: str  # "bid" | "no-bid" | "conditional"

    # Workflow control
    needs_human_review: bool
    sme_escalations: list[dict]
    current_phase: str
```

#### Step 2.3: Agent Definitions

Each agent is a LangGraph node function that reads from and writes to `RFPState`. Here are the three most critical agents:

**Question Classifier Agent:**

```python
# src/agents/classifier.py
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents._llm import get_llm
from src.graph.state import RFPState, RFPQuestion
import json

CLASSIFIER_PROMPT = """You are an RFP question classifier. Categorize each question
into exactly one of these categories:

- security: Data security, access controls, encryption, vulnerability management
- compliance: Regulatory requirements, certifications, audit, privacy (GDPR, SOC2, HIPAA)
- technical: Architecture, integrations, APIs, performance, scalability
- company_info: Company background, financials, team, references, case studies
- support: SLAs, support tiers, maintenance, incident response
- pricing: Cost structure, licensing, payment terms (flag for manual handling)
- project: Implementation timeline, methodology, project management, training

For each question, also determine if it is semantically equivalent to a previously
seen question. If it is, mark is_duplicate=true and reference the original question ID.

Return a JSON array of objects with fields:
{id, text, category, is_duplicate, duplicate_of}"""

def classify_questions(state: RFPState) -> dict:
    llm = get_llm("classifier")
    response = llm.invoke([
        SystemMessage(content=CLASSIFIER_PROMPT),
        HumanMessage(content=f"Questions to classify:\n{json.dumps(
            [{'id': q['id'], 'text': q['text']} for q in state['questions']],
            indent=2
        )}"),
    ])
    classified = json.loads(response.content)
    return {
        "questions": [RFPQuestion(**q) for q in classified],
        "current_phase": "classified",
    }
```

**Retrieval Agent (Agentic RAG):**

```python
# src/agents/retriever.py
from src.tools.search import hybrid_search
from src.agents._llm import get_llm
from src.graph.state import RFPState
from langchain_core.messages import SystemMessage, HumanMessage

QUERY_REWRITE_PROMPT = """Given an RFP question, generate 2-3 optimized search queries
to find the best matching content in our proposal knowledge base.

Focus on:
1. The core capability or feature being asked about
2. Relevant compliance standards or certifications mentioned
3. Technical specifics (integrations, protocols, standards)

Return a JSON array of search query strings."""

def retrieve_for_questions(state: RFPState) -> dict:
    llm = get_llm("classifier")  # Low temp for query generation
    retrieved = {}

    for question in state["questions"]:
        if question.get("is_duplicate"):
            # Reuse retrieval from the original question
            retrieved[question["id"]] = retrieved.get(question["duplicate_of"], [])
            continue

        # Step 1: LLM generates optimized search queries
        response = llm.invoke([
            SystemMessage(content=QUERY_REWRITE_PROMPT),
            HumanMessage(content=question["text"]),
        ])
        queries = json.loads(response.content)

        # Step 2: Execute hybrid search for each query, merge and deduplicate
        all_passages = []
        seen_ids = set()
        for query in queries:
            results = hybrid_search(
                query_text=query,
                category_filter=question.get("category"),
                top_k=5,
            )
            for r in results:
                if r["id"] not in seen_ids:
                    all_passages.append(r)
                    seen_ids.add(r["id"])

        # Keep top-k by relevance score
        all_passages.sort(key=lambda x: x["relevance_score"], reverse=True)
        retrieved[question["id"]] = all_passages[:8]

    return {
        "retrieved_passages": retrieved,
        "current_phase": "retrieved",
    }
```

**Draft Generator Agent:**

```python
# src/agents/drafter.py
from src.agents._llm import get_llm
from src.graph.state import RFPState, DraftResponse
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import Settings
from datetime import datetime, timedelta
import json

settings = Settings()

DRAFTER_PROMPT = """You are an expert proposal writer for {company_name}.
Draft an RFP response based EXCLUSIVELY on the retrieved source passages below.

RULES:
1. Every factual claim MUST be supported by a retrieved passage.
2. If no passage supports a claim, do NOT include it — output GAP instead.
3. Cite sources inline as [Source: {{document_id}}].
4. Match the tone: professional, specific, confident but not arrogant.
5. Never fabricate statistics, customer names, or certifications.
6. If retrieved content was last verified over {staleness_days} days ago, set
   flagged_stale=true.

Return JSON:
{{
  "response_text": "...",
  "citations": ["doc_id_1", "doc_id_2"],
  "confidence": 0.0-1.0,
  "flagged_stale": true/false
}}"""

def generate_drafts(state: RFPState) -> dict:
    llm = get_llm("drafter")
    drafts = []
    stale_cutoff = datetime.utcnow() - timedelta(days=settings.staleness_days)

    for question in state["questions"]:
        if question.get("is_duplicate"):
            continue  # Will copy from original in post-processing

        passages = state["retrieved_passages"].get(question["id"], [])
        passages_text = "\n\n".join([
            f"[Source: {p['source_document']}] (verified: {p['last_verified_date']})\n"
            f"{p['content']}"
            for p in passages
        ])

        prompt = DRAFTER_PROMPT.format(
            company_name=state["company_name"],
            staleness_days=settings.staleness_days,
        )

        response = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=(
                f"RETRIEVED PASSAGES:\n{passages_text}\n\n"
                f"RFP QUESTION:\n{question['text']}"
            )),
        ])

        draft_data = json.loads(response.content)
        drafts.append(DraftResponse(
            question_id=question["id"],
            response_text=draft_data["response_text"],
            citations=draft_data["citations"],
            confidence=draft_data["confidence"],
            flagged_stale=draft_data.get("flagged_stale", False),
        ))

    return {
        "drafts": drafts,
        "current_phase": "drafted",
    }
```

---

### Phase 3: Integration Layer

#### Step 3.1: Azure AI Search — Hybrid Search Tool

This is the core retrieval tool that agents call. It combines keyword matching, vector similarity, and semantic reranking in a single query.

```python
# src/tools/search.py
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from config.settings import Settings

settings = Settings()
credential = DefaultAzureCredential()

search_client = SearchClient(
    endpoint=settings.search_endpoint,
    index_name=settings.search_index,
    credential=credential,
)

openai_client = AzureOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    azure_ad_token_provider=credential,
    api_version=settings.azure_openai_api_version,
)

def hybrid_search(
    query_text: str,
    category_filter: str | None = None,
    top_k: int = 8,
) -> list[dict]:
    """Execute hybrid search: keyword + vector + semantic reranking."""

    # Generate embedding for vector search component
    embedding = openai_client.embeddings.create(
        model=settings.model_embedding,
        input=query_text,
    ).data[0].embedding

    # Build filter expression
    filter_expr = None
    if category_filter:
        filter_expr = f"category eq '{category_filter}'"

    # Execute hybrid query with semantic reranking
    results = search_client.search(
        search_text=query_text,                        # Keyword component
        vector_queries=[VectorizableTextQuery(
            text=query_text,
            k_nearest_neighbors=top_k * 2,
            fields="content_vector",
        )],                                            # Vector component
        query_type="semantic",                         # Semantic reranking
        semantic_configuration_name=settings.search_semantic_config,
        filter=filter_expr,
        top=top_k,
        select=["id", "content", "source_document", "last_verified_date",
                "category", "document_type"],
    )

    return [
        {
            "id": r["id"],
            "content": r["content"],
            "source_document": r["source_document"],
            "relevance_score": r["@search.reranker_score"] or r["@search.score"],
            "last_verified_date": r["last_verified_date"],
        }
        for r in results
    ]
```

#### Step 3.2: Document Intelligence — RFP Parser Tool

Converts uploaded RFP documents into structured Markdown that the Question Classifier can process.

```python
# src/tools/document_parser.py
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.identity import DefaultAzureCredential
from config.settings import Settings

settings = Settings()
credential = DefaultAzureCredential()

doc_client = DocumentAnalysisClient(
    endpoint=settings.doc_intelligence_endpoint,
    credential=credential,
)

def parse_rfp_document(document_url: str) -> str:
    """Parse an RFP document into structured Markdown using Azure Document Intelligence."""
    poller = doc_client.begin_analyze_document_from_url(
        model_id="prebuilt-layout",
        document_url=document_url,
        output_content_format="markdown",
    )
    result = poller.result()
    return result.content


def extract_questions_from_markdown(markdown: str) -> list[dict]:
    """Use LLM to extract individual questions from parsed RFP Markdown.

    This handles the variety of RFP formats: numbered lists, tables,
    nested sections, spreadsheet-style questionnaires.
    """
    from src.agents._llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    import json

    llm = get_llm("classifier")
    response = llm.invoke([
        SystemMessage(content=(
            "Extract every question or requirement from this RFP document. "
            "Assign each a sequential ID (Q-001, Q-002, ...). "
            "Include the section context (e.g., 'Section 3.2 - Security'). "
            "Return JSON array: [{id, text, section}]"
        )),
        HumanMessage(content=markdown),
    ])
    return json.loads(response.content)
```

---

### Phase 4: Orchestration & Flow

#### Step 4.1: LangGraph Workflow Definition

The graph encodes the full RFP processing pipeline with conditional edges for re-generation loops and human review gates.

```python
# src/graph/workflow.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.graph.state import RFPState
from src.agents.classifier import classify_questions
from src.agents.retriever import retrieve_for_questions
from src.agents.drafter import generate_drafts
from src.agents.compliance import check_compliance
from src.agents.reviewer import review_quality
from src.agents.bid_scorer import score_bid
from src.tools.document_parser import parse_rfp_document, extract_questions_from_markdown

def parse_rfp(state: RFPState) -> dict:
    """Node 1: Parse the RFP document into questions."""
    markdown = parse_rfp_document(state["rfp_document_url"])
    questions = extract_questions_from_markdown(markdown)
    return {
        "rfp_raw_markdown": markdown,
        "questions": [{"id": q["id"], "text": q["text"],
                       "category": None, "is_duplicate": False,
                       "duplicate_of": None} for q in questions],
        "current_phase": "parsed",
    }

def should_regenerate(state: RFPState) -> str:
    """Conditional edge: re-draft low-confidence answers or proceed."""
    low_confidence = [d for d in state["drafts"]
                      if d["confidence"] < 0.5]
    if low_confidence and state.get("regeneration_count", 0) < 2:
        return "regenerate"
    return "compliance"

def needs_human_gate(state: RFPState) -> str:
    """Conditional edge: route to human review if gaps exist."""
    if state["compliance_gaps"] or state.get("quality_score", 1.0) < 0.7:
        return "human_review"
    return "assemble"

def human_review_node(state: RFPState) -> dict:
    """Human-in-the-loop gate. LangGraph interrupts here for human input."""
    return {"needs_human_review": True}

def assemble_final(state: RFPState) -> dict:
    """Assemble the final submission-ready document."""
    return {"current_phase": "complete"}

# Build the graph
builder = StateGraph(RFPState)

# Add nodes
builder.add_node("parse", parse_rfp)
builder.add_node("classify", classify_questions)
builder.add_node("bid_score", score_bid)
builder.add_node("retrieve", retrieve_for_questions)
builder.add_node("draft", generate_drafts)
builder.add_node("compliance", check_compliance)
builder.add_node("review", review_quality)
builder.add_node("human_review", human_review_node)
builder.add_node("assemble", assemble_final)

# Define edges
builder.set_entry_point("parse")
builder.add_edge("parse", "classify")
builder.add_edge("classify", "bid_score")
builder.add_edge("bid_score", "retrieve")
builder.add_edge("retrieve", "draft")
builder.add_conditional_edges("draft", should_regenerate, {
    "regenerate": "retrieve",   # Loop back for low-confidence answers
    "compliance": "compliance",
})
builder.add_edge("compliance", "review")
builder.add_conditional_edges("review", needs_human_gate, {
    "human_review": "human_review",
    "assemble": "assemble",
})
builder.add_edge("human_review", "assemble")
builder.add_edge("assemble", END)

# Compile with checkpointing for long-running workflows
memory = MemorySaver()  # Replace with CosmosDBSaver in production
graph = builder.compile(checkpointer=memory, interrupt_before=["human_review"])
```

#### Step 4.2: Running the Workflow

```python
# src/api/routes.py
from fastapi import FastAPI, BackgroundTasks
from src.graph.workflow import graph

app = FastAPI()

@app.post("/rfp/process")
async def process_rfp(
    document_url: str,
    company_name: str,
    background_tasks: BackgroundTasks,
):
    """Kick off RFP processing. Returns a thread_id for status tracking."""
    thread_id = f"rfp-{uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "rfp_document_url": document_url,
        "company_name": company_name,
        "questions": [],
        "retrieved_passages": {},
        "drafts": [],
        "compliance_results": [],
        "compliance_gaps": [],
        "quality_score": 0.0,
        "quality_issues": [],
        "bid_score": 0.0,
        "bid_recommendation": "",
        "needs_human_review": False,
        "sme_escalations": [],
        "current_phase": "started",
    }

    # Run asynchronously — graph will checkpoint at each node
    background_tasks.add_task(graph.ainvoke, initial_state, config)
    return {"thread_id": thread_id, "status": "processing"}

@app.get("/rfp/{thread_id}/status")
async def get_status(thread_id: str):
    """Check current phase and retrieve results."""
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    return {
        "phase": state.values.get("current_phase"),
        "needs_human_review": state.values.get("needs_human_review"),
        "bid_recommendation": state.values.get("bid_recommendation"),
        "draft_count": len(state.values.get("drafts", [])),
        "compliance_gaps": state.values.get("compliance_gaps", []),
    }
```

---

### Phase 5: Deployment

#### Step 5.1: Configuration & Secrets Management

All secrets via Azure Key Vault; configuration via environment variables. No secrets in code.

```yaml
# config/deployment.yaml (AKS manifest snippet)
env:
  - name: RFP_AZURE_OPENAI_ENDPOINT
    valueFrom:
      secretKeyRef:
        name: rfp-agent-secrets
        key: azure-openai-endpoint
  - name: RFP_SEARCH_ENDPOINT
    valueFrom:
      secretKeyRef:
        name: rfp-agent-secrets
        key: search-endpoint
  - name: AZURE_CLIENT_ID  # Workload Identity
    valueFrom:
      fieldRef:
        fieldPath: metadata.labels['azure.workload.identity/client-id']
```

---

## Key Code Patterns

### Pattern: Grounded Generation with Source Attribution

The most critical pattern for RFP responses — preventing hallucination while maintaining fluency.

```python
def validate_draft_grounding(draft: DraftResponse,
                              passages: list[RetrievedPassage]) -> dict:
    """Post-generation validation: ensure every citation references
    a real retrieved passage."""
    available_sources = {p["source_document"] for p in passages}
    invalid_citations = [c for c in draft["citations"]
                         if c not in available_sources]

    if invalid_citations:
        return {
            "valid": False,
            "issue": f"Citations reference unknown sources: {invalid_citations}",
            "action": "regenerate",
        }

    # Check confidence threshold
    if draft["confidence"] < 0.7:
        return {
            "valid": True,
            "issue": "Low confidence — flagged for human review",
            "action": "flag",
        }

    return {"valid": True, "issue": None, "action": "accept"}
```

### Pattern: Semantic Caching for Repeated Questions

60-70% of RFP questions are substantially similar across proposals. Cache responses by question embedding similarity.

```python
import hashlib
import numpy as np

def get_semantic_cache_key(question_embedding: list[float],
                            threshold: float = 0.95) -> str | None:
    """Check if a semantically similar question was recently answered.
    Returns cached response key if similarity > threshold."""
    # In production, this queries a dedicated cache index in Azure AI Search
    # with a vector similarity filter
    query_vector = np.array(question_embedding)
    # ... search cache index for nearest neighbor
    # Returns cache key if cosine similarity > threshold, else None
    return None  # Placeholder — implement with Azure AI Search vector query
```

### Pattern: Structured Output Enforcement

Use Pydantic models with `response_format` to ensure agents return machine-parseable output.

```python
from pydantic import BaseModel, Field

class ClassificationOutput(BaseModel):
    id: str
    text: str
    category: str = Field(description="One of: security, compliance, technical, "
                          "company_info, support, pricing, project")
    is_duplicate: bool
    duplicate_of: str | None = None

# With Azure OpenAI structured outputs
response = llm.invoke(
    messages,
    response_format=ClassificationOutput,  # Enforced JSON schema
)
```

---

## Configuration Reference

| Parameter | Default | Description |
|---|---|---|
| `RFP_AZURE_OPENAI_ENDPOINT` | (required) | Azure OpenAI service endpoint |
| `RFP_MODEL_REASONING` | `gpt-4o` | Model for drafting, compliance, review |
| `RFP_MODEL_CLASSIFICATION` | `gpt-4o-mini` | Model for classification tasks |
| `RFP_MODEL_EMBEDDING` | `text-embedding-3-large` | Embedding model for search |
| `RFP_TEMP_DRAFTER` | `0.3` | Temperature for draft generation |
| `RFP_TEMP_CLASSIFIER` | `0.0` | Temperature for classification |
| `RFP_SEARCH_TOP_K` | `8` | Number of passages to retrieve per question |
| `RFP_CONFIDENCE_THRESHOLD` | `0.7` | Below this, flag for human review |
| `RFP_STALENESS_DAYS` | `365` | Content older than this flagged as stale |
| `RFP_MAX_REGENERATION_LOOPS` | `2` | Maximum re-draft attempts for low-confidence answers |

---

## Testing Strategy

### Unit Tests

Test agent logic in isolation with mocked LLM responses and search results.

```python
# tests/test_agents.py
def test_classifier_categorizes_security_question():
    """Verify the classifier correctly categorizes security questions."""
    mock_state = {
        "questions": [
            {"id": "Q-001", "text": "Describe your data encryption at rest and in transit."}
        ]
    }
    # Mock the LLM to return expected classification
    with patch("src.agents.classifier.get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value.content = json.dumps([{
            "id": "Q-001",
            "text": "Describe your data encryption at rest and in transit.",
            "category": "security",
            "is_duplicate": False,
            "duplicate_of": None,
        }])
        result = classify_questions(mock_state)
        assert result["questions"][0]["category"] == "security"
```

### Integration Tests

Test the full pipeline with real Azure services against a known RFP document.

```python
def test_end_to_end_small_rfp():
    """Process a 10-question test RFP and verify output structure."""
    config = {"configurable": {"thread_id": "test-e2e"}}
    result = graph.invoke({
        "rfp_document_url": "https://storage.blob.core.windows.net/test/sample-rfp.pdf",
        "company_name": "TestCorp",
        # ... initial state
    }, config)

    assert len(result["drafts"]) >= 8  # At least 80% answered
    assert all(d["confidence"] > 0 for d in result["drafts"])
    assert result["current_phase"] == "complete"
```

### Evaluation Tests — AI Quality

The most important tests: measure whether the AI produces correct, grounded responses.

```python
# scripts/evaluate.py
def evaluate_grounding_accuracy(drafts: list, ground_truth: list) -> dict:
    """Compare AI drafts against human-verified gold-standard answers.

    Metrics:
    - Factual accuracy: % of claims supported by source docs
    - Completeness: % of required points addressed
    - Hallucination rate: % of claims not traceable to any source
    - Citation accuracy: % of citations pointing to correct source
    """
    results = {
        "factual_accuracy": 0.0,
        "completeness": 0.0,
        "hallucination_rate": 0.0,
        "citation_accuracy": 0.0,
    }

    for draft, truth in zip(drafts, ground_truth):
        # Use GPT-4o as judge to evaluate grounding
        judge_response = judge_llm.invoke([
            SystemMessage(content=GROUNDING_JUDGE_PROMPT),
            HumanMessage(content=f"DRAFT:\n{draft['response_text']}\n\n"
                         f"GROUND TRUTH:\n{truth['expected_answer']}\n\n"
                         f"SOURCES:\n{truth['valid_sources']}"),
        ])
        scores = json.loads(judge_response.content)
        for key in results:
            results[key] += scores[key]

    # Average across all questions
    n = len(drafts)
    return {k: v / n for k, v in results.items()}
```

---

## Monitoring & Observability

| What to Monitor | Tool / Method | Alert Threshold |
|---|---|---|
| **LLM Latency** | Application Insights custom metric | p95 > 15s per question |
| **LLM Error Rate** | Application Insights dependency tracking | > 3% in 5-min window |
| **Token Usage** | Custom metric (input + output tokens per RFP) | Daily spend > $100 |
| **Confidence Distribution** | Custom histogram metric | > 30% of answers below 0.7 confidence |
| **Hallucination Rate** | Weekly eval batch against gold set | > 5% hallucination rate |
| **Content Staleness** | Azure AI Search filter query on last_verified_date | > 20% of retrievals flagged stale |
| **Workflow Completion** | LangGraph state tracking | RFP stuck in single phase > 1 hour |

---

## Common Pitfalls & Mitigations

| Pitfall | Mitigation |
|---|---|
| LLM hallucinating capabilities not in knowledge base | Strict grounded generation prompt; post-generation citation validation; confidence scoring with human review below threshold |
| Stale content in knowledge base produces inaccurate answers | `last_verified_date` field on every document; automated staleness flagging; quarterly content refresh workflow |
| Token limit exceeded on large RFP documents (2000+ questions) | Process questions in parallel batches of 20-50; chunk long questions; use GPT-4o-mini for classification to reduce cost |
| Inconsistent tone across answers from different retrieval sources | Quality Review agent enforces tone consistency in post-processing pass; company style guide embedded in drafter system prompt |
| RFP format variety (PDF tables, XLSX questionnaires, web portals) | Document Intelligence handles PDF/DOCX/XLSX; portal questionnaires require custom adapters or manual CSV export |
| Prompt injection from adversarial RFP content | System prompts define strict output format; input sanitization removes suspicious instructions; LLM output validated against schema before storage |

---

## Rollback Plan

1. **Feature flag on AI pipeline**: Toggle between AI-generated and fully manual workflow without code deployment; AI drafts stored separately from human-edited versions
2. **Parallel run period**: During initial deployment, run AI pipeline alongside manual process for 2-4 weeks; proposal managers compare outputs before trusting AI drafts
3. **Manual fallback**: If AI pipeline fails or produces unacceptable quality, proposal managers revert to content library keyword search + manual drafting — the same process used before AI, with no data loss
4. **State preservation**: LangGraph checkpointing means a failed workflow can resume from the last successful node rather than restarting entirely
