# UC-041: Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI — Implementation Guide

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

### Phase 1: Foundation

#### Step 1.1: Core Dependencies

```bash
pip install langgraph langchain-openai azure-search-documents azure-identity \
    azure-servicebus pydantic httpx fastapi uvicorn
```

#### Step 1.2: Data Models

The obligation model is the central data contract. Every agent reads or writes obligations in this schema.

```python
# src/models/obligation.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date

class DeonticType(str, Enum):
    MUST = "must"
    SHALL = "shall"
    MAY = "may"
    MUST_NOT = "must_not"
    SHOULD = "should"

class Obligation(BaseModel):
    """A discrete regulatory obligation extracted from regulatory text."""
    id: str = Field(description="Unique obligation identifier")
    obligation_text: str = Field(description="Verbatim text of the obligation")
    deontic_type: DeonticType = Field(description="Modal type: must/shall/may/must_not/should")
    addressee: str = Field(description="Who the obligation applies to")
    predicate: str = Field(description="What the addressee must do or not do")
    conditions: list[str] = Field(default_factory=list, description="Conditions under which the obligation applies")
    effective_date: date | None = Field(default=None, description="When the obligation takes effect")
    cross_references: list[str] = Field(default_factory=list, description="Referenced articles/regulations")
    article_reference: str = Field(description="Source article/section number")
    source_regulation: str = Field(description="Title and identifier of the source regulation")
    jurisdiction: str = Field(description="Jurisdiction that issued the regulation")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score")
    ambiguity_flag: bool = Field(default=False, description="True if deontic classification is uncertain")

class ApplicabilityResult(BaseModel):
    """Result of assessing whether an obligation applies to the firm."""
    obligation_id: str
    applicable: str = Field(description="yes | no | partial | requires_review")
    reasoning: str = Field(description="Explanation of the assessment")
    affected_entities: list[str] = Field(default_factory=list)
    affected_jurisdictions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    similar_past_assessments: list[str] = Field(default_factory=list)

class GapFinding(BaseModel):
    """A gap identified between a regulatory obligation and existing controls."""
    obligation_id: str
    obligation_summary: str
    existing_control: str | None = Field(description="Current control that partially covers this obligation, or None")
    gap_description: str
    severity: str = Field(description="high | medium | low")
    recommended_action: str
    affected_policies: list[str] = Field(default_factory=list)
```

#### Step 1.3: Pipeline State Definition

LangGraph's `TypedDict` state drives the entire pipeline. Every agent reads from and writes to this shared state.

```python
# src/models/pipeline_state.py
from typing import Annotated, TypedDict
from langgraph.graph import add_messages
from src.models.obligation import Obligation, ApplicabilityResult, GapFinding

def merge_lists(left: list, right: list) -> list:
    """Reducer that appends new items to existing list."""
    return left + right

class RegulatoryChangeState(TypedDict):
    """Pipeline state for processing a single regulatory change."""
    # Input
    document_id: str
    document_title: str
    document_text: str
    source_jurisdiction: str
    source_issuing_body: str
    document_type: str  # legislation | guidance | enforcement | consultation
    publication_date: str
    urgency: str  # routine | elevated | urgent

    # Extraction stage
    obligations: Annotated[list[Obligation], merge_lists]

    # Assessment stage
    assessments: Annotated[list[ApplicabilityResult], merge_lists]
    applicable_obligations: Annotated[list[Obligation], merge_lists]

    # Gap analysis stage
    gap_findings: Annotated[list[GapFinding], merge_lists]

    # Policy drafting stage
    policy_redlines: Annotated[list[dict], merge_lists]

    # Human review
    requires_human_review: bool
    human_review_reason: str

    # Audit trail
    messages: Annotated[list, add_messages]
```

---

### Phase 2: Core AI Integration

#### Step 2.1: LLM Connection & Configuration

```python
# src/agents/base.py
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential
import os

def get_extraction_llm() -> AzureChatOpenAI:
    """GPT-4o for obligation extraction and assessment — needs strong reasoning."""
    return AzureChatOpenAI(
        azure_deployment=os.environ["AZURE_OPENAI_GPT4O_DEPLOYMENT"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version="2024-12-01-preview",
        temperature=0.0,  # Deterministic extraction
        max_tokens=4096,
        azure_ad_token_provider=DefaultAzureCredential().get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
    )

def get_classification_llm() -> AzureChatOpenAI:
    """GPT-4o-mini for document classification — cost-effective for high volume."""
    return AzureChatOpenAI(
        azure_deployment=os.environ["AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version="2024-12-01-preview",
        temperature=0.0,
        max_tokens=1024,
        azure_ad_token_provider=DefaultAzureCredential().get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
    )
```

#### Step 2.2: Obligation Extraction Agent

The extraction agent is the highest-leverage component — it turns unstructured regulatory text into machine-readable obligations. This is the task that took 1,800 hours manually at ING/CommBank.

```python
# src/agents/extractor.py
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.base import get_extraction_llm
from src.models.obligation import Obligation
from src.models.pipeline_state import RegulatoryChangeState
import json

EXTRACTION_SYSTEM_PROMPT = """You are the Obligation Extraction Agent for a regulatory change management platform.
Your job is to extract discrete regulatory obligations from regulatory text.

Rules:
1. Extract only obligations explicitly stated in the regulatory text.
   An obligation is a statement that imposes a duty, prohibition, or permission
   on a specified addressee (e.g., "firms must", "institutions shall",
   "the competent authority may require").
2. For each obligation, identify:
   - obligation_text: The exact text of the obligation (verbatim quote)
   - deontic_type: must | shall | may | must_not | should
   - addressee: Who the obligation applies to
   - predicate: What the addressee must do or not do
   - conditions: Under what circumstances the obligation applies
   - effective_date: When the obligation takes effect (if stated)
   - cross_references: Other articles, sections, or regulations referenced
   - article_reference: The article/section number where the obligation appears
3. Do NOT infer obligations that are not explicitly stated.
4. Do NOT merge multiple obligations into one — each discrete duty is a separate entry.
5. If a provision is ambiguous between obligation and recommendation,
   set deontic_type based on the modal verb used and add ambiguity_flag=true.
6. Return a JSON array of obligations matching the provided schema."""

def chunk_regulatory_text(text: str, chunk_size: int = 3000, overlap: int = 500) -> list[str]:
    """Split regulatory text into overlapping chunks, respecting article boundaries."""
    # Split on article/section boundaries first
    import re
    sections = re.split(r'(?=\nArticle\s+\d+|\nSection\s+\d+|\n\d+\.\s)', text)

    chunks = []
    current_chunk = ""
    for section in sections:
        if len(current_chunk) + len(section) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            # Keep overlap from end of previous chunk
            current_chunk = current_chunk[-overlap:] + section
        else:
            current_chunk += section
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

async def extract_obligations(state: RegulatoryChangeState) -> dict:
    """Extract obligations from regulatory text using GPT-4o structured outputs."""
    llm = get_extraction_llm()
    all_obligations: list[Obligation] = []

    chunks = chunk_regulatory_text(state["document_text"])

    for i, chunk in enumerate(chunks):
        response = await llm.ainvoke(
            [
                SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
                HumanMessage(content=(
                    f"Regulation: {state['document_title']}\n"
                    f"Jurisdiction: {state['source_jurisdiction']}\n"
                    f"Section chunk {i+1}/{len(chunks)}:\n\n{chunk}\n\n"
                    "Extract all obligations from this section."
                )),
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "obligations",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "obligations": {
                                "type": "array",
                                "items": Obligation.model_json_schema(),
                            }
                        },
                        "required": ["obligations"],
                    },
                },
            },
        )

        parsed = json.loads(response.content)
        for ob_data in parsed.get("obligations", []):
            ob_data["id"] = f"{state['document_id']}-{len(all_obligations):04d}"
            ob_data["source_regulation"] = state["document_title"]
            ob_data["jurisdiction"] = state["source_jurisdiction"]
            all_obligations.append(Obligation(**ob_data))

    # Deduplicate obligations that span chunk boundaries
    seen_texts = set()
    unique_obligations = []
    for ob in all_obligations:
        normalized = ob.obligation_text.strip().lower()[:200]
        if normalized not in seen_texts:
            seen_texts.add(normalized)
            unique_obligations.append(ob)

    return {"obligations": unique_obligations}
```

#### Step 2.3: Applicability Assessment Agent

```python
# src/agents/assessor.py
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.base import get_extraction_llm
from src.tools.knowledge_base import search_similar_assessments
from src.models.obligation import Obligation, ApplicabilityResult
from src.models.pipeline_state import RegulatoryChangeState
import json

ASSESSMENT_SYSTEM_PROMPT = """You are the Applicability Assessment Agent. You determine whether
extracted regulatory obligations apply to a specific financial institution.

Firm's Regulatory Perimeter:
{regulatory_perimeter}

Rules:
1. Assess each obligation against the firm's regulatory perimeter.
2. An obligation is "applicable" if the firm matches the addressee definition
   AND operates in the specified jurisdiction AND conducts the relevant activity.
3. An obligation is "partially_applicable" if it applies to some entities
   or jurisdictions but not all.
4. Provide reasoning that traces your assessment to specific elements
   of the firm's regulatory perimeter.
5. Include confidence_score (0.0-1.0). Below 0.80, the assessment will be
   routed to a human compliance officer for review.
6. Reference any similar past assessments provided.
7. Never assume applicability — if the addressee definition does not clearly
   match the firm's entity type, mark as "requires_review"."""

async def assess_applicability(state: RegulatoryChangeState) -> dict:
    """Assess which extracted obligations apply to the firm."""
    llm = get_extraction_llm()
    assessments: list[ApplicabilityResult] = []
    applicable: list[Obligation] = []
    needs_review = False
    review_reasons = []

    # Load firm's regulatory perimeter from config
    from src.config import REGULATORY_PERIMETER
    system_prompt = ASSESSMENT_SYSTEM_PROMPT.format(
        regulatory_perimeter=json.dumps(REGULATORY_PERIMETER, indent=2)
    )

    for obligation in state["obligations"]:
        # RAG: retrieve similar past assessments
        similar = await search_similar_assessments(obligation.obligation_text)
        similar_context = "\n".join(
            f"- Past assessment: {s['obligation_summary']} → {s['result']} ({s['reasoning'][:200]})"
            for s in similar[:3]
        )

        response = await llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=(
                    f"Obligation to assess:\n"
                    f"- Text: {obligation.obligation_text}\n"
                    f"- Addressee: {obligation.addressee}\n"
                    f"- Jurisdiction: {obligation.jurisdiction}\n"
                    f"- Deontic type: {obligation.deontic_type}\n\n"
                    f"Similar past assessments:\n{similar_context or 'None found.'}\n\n"
                    "Assess applicability."
                )),
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "applicability",
                    "schema": ApplicabilityResult.model_json_schema(),
                },
            },
        )

        result = ApplicabilityResult(**json.loads(response.content))
        result.obligation_id = obligation.id
        assessments.append(result)

        if result.applicable in ("yes", "partial"):
            applicable.append(obligation)
        if result.confidence < 0.80 or result.applicable == "requires_review":
            needs_review = True
            review_reasons.append(
                f"Obligation {obligation.id}: confidence={result.confidence:.2f}, "
                f"result={result.applicable}"
            )

    return {
        "assessments": assessments,
        "applicable_obligations": applicable,
        "requires_human_review": needs_review,
        "human_review_reason": "; ".join(review_reasons) if review_reasons else "",
    }
```

#### Step 2.4: Tool Definitions — Knowledge Base (RAG)

```python
# src/tools/knowledge_base.py
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.identity.aio import DefaultAzureCredential
import os

_credential = DefaultAzureCredential()

async def search_similar_assessments(obligation_text: str, top_k: int = 5) -> list[dict]:
    """Search for similar past applicability assessments using hybrid search."""
    async with SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name="regulatory-assessments",
        credential=_credential,
    ) as client:
        results = await client.search(
            search_text=obligation_text[:500],
            vector_queries=[
                VectorizableTextQuery(
                    text=obligation_text[:500],
                    k_nearest_neighbors=top_k,
                    fields="obligation_embedding",
                )
            ],
            select=["obligation_summary", "result", "reasoning", "assessment_date"],
            top=top_k,
        )
        return [doc async for doc in results]

async def search_regulatory_corpus(query: str, jurisdiction: str | None = None, top_k: int = 10) -> list[dict]:
    """Search the regulatory document corpus for relevant provisions."""
    filter_expr = f"jurisdiction eq '{jurisdiction}'" if jurisdiction else None

    async with SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name="regulatory-corpus",
        credential=_credential,
    ) as client:
        results = await client.search(
            search_text=query,
            vector_queries=[
                VectorizableTextQuery(
                    text=query,
                    k_nearest_neighbors=top_k,
                    fields="content_embedding",
                )
            ],
            filter=filter_expr,
            select=["regulation_title", "article_reference", "content", "jurisdiction"],
            top=top_k,
        )
        return [doc async for doc in results]

async def search_controls(obligation_text: str, top_k: int = 5) -> list[dict]:
    """Search existing controls that may cover a given obligation."""
    async with SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name="control-framework",
        credential=_credential,
    ) as client:
        results = await client.search(
            search_text=obligation_text[:500],
            vector_queries=[
                VectorizableTextQuery(
                    text=obligation_text[:500],
                    k_nearest_neighbors=top_k,
                    fields="control_embedding",
                )
            ],
            select=["control_id", "control_description", "linked_policies", "linked_obligations"],
            top=top_k,
        )
        return [doc async for doc in results]
```

---

### Phase 3: Integration Layer

#### Step 3.1: GRC Platform Connector

```python
# src/tools/grc_connector.py
import httpx
import os

class GRCConnector:
    """Connector for enterprise GRC platform (ServiceNow GRC example)."""

    def __init__(self):
        self.base_url = os.environ["GRC_API_BASE_URL"]
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {os.environ['GRC_API_TOKEN']}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def get_obligation_register(self, jurisdiction: str | None = None) -> list[dict]:
        """Retrieve current obligation register entries from GRC platform."""
        params = {"sysparm_limit": 500}
        if jurisdiction:
            params["sysparm_query"] = f"jurisdiction={jurisdiction}"

        resp = await self.client.get(
            f"{self.base_url}/api/now/table/sn_compliance_obligation",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()["result"]

    async def create_assessment_record(self, assessment: dict) -> str:
        """Write a regulatory change assessment to the GRC platform."""
        resp = await self.client.post(
            f"{self.base_url}/api/now/table/sn_compliance_assessment",
            json=assessment,
        )
        resp.raise_for_status()
        return resp.json()["result"]["sys_id"]

    async def create_change_task(self, task: dict) -> str:
        """Create a regulatory change implementation task."""
        resp = await self.client.post(
            f"{self.base_url}/api/now/table/sn_compliance_task",
            json=task,
        )
        resp.raise_for_status()
        return resp.json()["result"]["sys_id"]

    async def update_obligation(self, obligation_id: str, updates: dict) -> None:
        """Update an existing obligation in the register."""
        resp = await self.client.patch(
            f"{self.base_url}/api/now/table/sn_compliance_obligation/{obligation_id}",
            json=updates,
        )
        resp.raise_for_status()
```

#### Step 3.2: Regulatory Feed Connector

```python
# src/tools/regulatory_feed.py
import httpx
import feedparser
from datetime import datetime, timedelta
import os

class RegulatoryFeedConnector:
    """Monitor regulatory publication feeds for new documents."""

    def __init__(self):
        self.feeds: list[dict] = [
            # Example: EU Official Journal RSS
            {"name": "EU Official Journal", "type": "rss",
             "url": "https://eur-lex.europa.eu/rss/rss.xml",
             "jurisdiction": "EU"},
            # Example: FCA regulatory publications
            {"name": "FCA Publications", "type": "rss",
             "url": "https://www.fca.org.uk/rss/publications.xml",
             "jurisdiction": "UK"},
        ]
        # Commercial feeds (CUBE, Wolters Kluwer) via API
        self.commercial_api_url = os.environ.get("REGULATORY_FEED_API_URL")
        self.commercial_api_key = os.environ.get("REGULATORY_FEED_API_KEY")

    async def poll_rss_feeds(self, since: datetime | None = None) -> list[dict]:
        """Poll RSS feeds for new regulatory publications."""
        since = since or datetime.utcnow() - timedelta(hours=24)
        new_documents = []

        for feed_config in self.feeds:
            feed = feedparser.parse(feed_config["url"])
            for entry in feed.entries:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date > since:
                    new_documents.append({
                        "source": feed_config["name"],
                        "jurisdiction": feed_config["jurisdiction"],
                        "title": entry.title,
                        "summary": entry.get("summary", ""),
                        "url": entry.link,
                        "publication_date": pub_date.isoformat(),
                    })
        return new_documents

    async def poll_commercial_feed(self, since: datetime | None = None) -> list[dict]:
        """Poll commercial regulatory intelligence feed (CUBE/Wolters Kluwer API)."""
        if not self.commercial_api_url:
            return []

        since_str = (since or datetime.utcnow() - timedelta(hours=24)).isoformat()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.commercial_api_url}/publications",
                params={"since": since_str, "limit": 100},
                headers={"Authorization": f"Bearer {self.commercial_api_key}"},
            )
            resp.raise_for_status()
            return resp.json()["publications"]
```

---

### Phase 4: Orchestration & Flow

#### Step 4.1: LangGraph Pipeline Orchestration

The pipeline uses LangGraph's `StateGraph` with conditional routing and human-in-the-loop interrupts.

```python
# src/agents/pipeline.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.models.pipeline_state import RegulatoryChangeState
from src.agents.scanner import classify_document
from src.agents.extractor import extract_obligations
from src.agents.assessor import assess_applicability
from src.agents.gap_analyzer import analyze_gaps
from src.agents.policy_drafter import draft_policy_updates

def should_extract(state: RegulatoryChangeState) -> str:
    """Route: only extract obligations from potentially applicable documents."""
    if state.get("document_type") in ("legislation", "guidance", "enforcement"):
        return "extract"
    return "archive"

def should_review(state: RegulatoryChangeState) -> str:
    """Route: human review for low-confidence assessments."""
    if state.get("requires_human_review"):
        return "human_review"
    if state.get("applicable_obligations"):
        return "gap_analysis"
    return "archive"

def has_gaps(state: RegulatoryChangeState) -> str:
    """Route: draft policies only if gaps were found."""
    if state.get("gap_findings"):
        return "draft_policies"
    return "confirm_compliance"

def build_pipeline() -> StateGraph:
    """Build the regulatory change processing pipeline."""
    builder = StateGraph(RegulatoryChangeState)

    # Add nodes
    builder.add_node("classify", classify_document)
    builder.add_node("extract", extract_obligations)
    builder.add_node("assess", assess_applicability)
    builder.add_node("human_review", lambda s: s)  # Interrupt point
    builder.add_node("gap_analysis", analyze_gaps)
    builder.add_node("draft_policies", draft_policy_updates)
    builder.add_node("confirm_compliance", log_compliance_confirmation)
    builder.add_node("archive", log_archive)

    # Add edges
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", should_extract,
                                  {"extract": "extract", "archive": "archive"})
    builder.add_edge("extract", "assess")
    builder.add_conditional_edges("assess", should_review,
                                  {"human_review": "human_review",
                                   "gap_analysis": "gap_analysis",
                                   "archive": "archive"})
    builder.add_edge("human_review", "gap_analysis")
    builder.add_conditional_edges("gap_analysis", has_gaps,
                                  {"draft_policies": "draft_policies",
                                   "confirm_compliance": "confirm_compliance"})
    builder.add_edge("draft_policies", END)
    builder.add_edge("confirm_compliance", END)
    builder.add_edge("archive", END)

    return builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["human_review"],  # Pause for human review
    )

async def log_compliance_confirmation(state: RegulatoryChangeState) -> dict:
    """Log that all applicable obligations are already covered by existing controls."""
    from src.tools.grc_connector import GRCConnector
    grc = GRCConnector()
    await grc.create_assessment_record({
        "document_id": state["document_id"],
        "result": "no_gaps",
        "summary": f"All {len(state['applicable_obligations'])} applicable obligations "
                   f"are covered by existing controls.",
    })
    return {}

async def log_archive(state: RegulatoryChangeState) -> dict:
    """Archive non-applicable document with classification rationale."""
    return {}
```

#### Step 4.2: Human-in-the-Loop Review

LangGraph's `interrupt_before` pauses the pipeline at the `human_review` node. A FastAPI endpoint allows compliance officers to resume processing after review.

```python
# src/api/routes.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agents.pipeline import build_pipeline

app = FastAPI(title="Regulatory Change Intelligence API")
pipeline = build_pipeline()

class HumanReviewDecision(BaseModel):
    thread_id: str
    approved_obligations: list[str]  # IDs of confirmed-applicable obligations
    rejected_obligations: list[str]  # IDs of confirmed-not-applicable obligations
    reviewer_id: str
    review_notes: str

@app.get("/reviews/pending")
async def list_pending_reviews():
    """List regulatory changes awaiting human review."""
    # Query checkpointer for interrupted threads
    # Implementation depends on checkpointer backend (memory, postgres, etc.)
    ...

@app.post("/reviews/submit")
async def submit_review(decision: HumanReviewDecision):
    """Submit human review decision and resume pipeline processing."""
    from src.models.pipeline_state import RegulatoryChangeState

    # Filter applicable_obligations based on human decision
    config = {"configurable": {"thread_id": decision.thread_id}}
    state = await pipeline.aget_state(config)

    if not state or not state.values:
        raise HTTPException(404, "Thread not found or not awaiting review")

    current = state.values
    confirmed = [
        ob for ob in current.get("applicable_obligations", [])
        if ob.id in decision.approved_obligations
    ]

    # Resume pipeline with human-validated obligations
    await pipeline.ainvoke(
        {
            "applicable_obligations": confirmed,
            "requires_human_review": False,
            "human_review_reason": f"Reviewed by {decision.reviewer_id}: {decision.review_notes}",
        },
        config=config,
    )
    return {"status": "resumed", "thread_id": decision.thread_id}
```

#### Step 4.3: Scheduled Scanner Trigger

```python
# src/agents/scanner.py
from src.tools.regulatory_feed import RegulatoryFeedConnector
from src.agents.base import get_classification_llm
from src.models.pipeline_state import RegulatoryChangeState
from langchain_core.messages import SystemMessage, HumanMessage
import json

CLASSIFICATION_PROMPT = """You are the Regulatory Document Classifier. Given a regulatory
publication title and summary, classify it.

Return JSON with:
- document_type: legislation | guidance | enforcement | consultation | other
- topic_areas: list of regulatory topics (e.g., ["capital requirements", "AML", "data protection"])
- urgency: routine | elevated | urgent
- relevance_score: 0.0-1.0 (how likely this is relevant to a regulated financial institution)
- classification_reasoning: brief explanation"""

async def classify_document(state: RegulatoryChangeState) -> dict:
    """Classify a regulatory document by type, topic, and urgency."""
    llm = get_classification_llm()

    response = await llm.ainvoke(
        [
            SystemMessage(content=CLASSIFICATION_PROMPT),
            HumanMessage(content=(
                f"Title: {state['document_title']}\n"
                f"Jurisdiction: {state['source_jurisdiction']}\n"
                f"Issuing Body: {state['source_issuing_body']}\n"
                f"Publication Date: {state['publication_date']}\n"
                f"Summary: {state['document_text'][:2000]}"
            )),
        ],
    )

    classification = json.loads(response.content)
    return {
        "document_type": classification["document_type"],
        "urgency": classification.get("urgency", "routine"),
    }

async def run_scan_cycle():
    """Scheduled function: poll feeds and trigger pipeline for new publications."""
    from src.agents.pipeline import build_pipeline
    import uuid

    feed = RegulatoryFeedConnector()
    new_docs = await feed.poll_rss_feeds()
    new_docs.extend(await feed.poll_commercial_feed())

    pipeline = build_pipeline()

    for doc in new_docs:
        initial_state: RegulatoryChangeState = {
            "document_id": str(uuid.uuid4()),
            "document_title": doc["title"],
            "document_text": doc.get("full_text", doc.get("summary", "")),
            "source_jurisdiction": doc["jurisdiction"],
            "source_issuing_body": doc["source"],
            "document_type": "",
            "publication_date": doc["publication_date"],
            "urgency": "",
            "obligations": [],
            "assessments": [],
            "applicable_obligations": [],
            "gap_findings": [],
            "policy_redlines": [],
            "requires_human_review": False,
            "human_review_reason": "",
            "messages": [],
        }
        config = {"configurable": {"thread_id": initial_state["document_id"]}}
        await pipeline.ainvoke(initial_state, config=config)
```

---

### Phase 5: Gap Analysis & Policy Drafting

#### Step 5.1: Gap Analysis Agent

```python
# src/agents/gap_analyzer.py
from src.agents.base import get_extraction_llm
from src.tools.knowledge_base import search_controls
from src.models.obligation import GapFinding
from src.models.pipeline_state import RegulatoryChangeState
from langchain_core.messages import SystemMessage, HumanMessage
import json

GAP_ANALYSIS_PROMPT = """You are the Gap Analysis Agent. You compare regulatory obligations
against existing controls to identify compliance gaps.

For each obligation, you receive the obligation text and a list of existing controls
that may already cover it.

Rules:
1. If an existing control fully addresses the obligation, output gap_exists=false.
2. If no control addresses the obligation, or controls only partially cover it,
   describe the specific gap.
3. Rate severity: "high" if the gap creates direct regulatory risk,
   "medium" if partial coverage exists, "low" if the gap is procedural.
4. Recommend a specific action to close each gap.
5. List which existing policies would need updating."""

async def analyze_gaps(state: RegulatoryChangeState) -> dict:
    """Compare applicable obligations against existing controls."""
    llm = get_extraction_llm()
    findings: list[GapFinding] = []

    for obligation in state["applicable_obligations"]:
        # Retrieve existing controls that may cover this obligation
        existing_controls = await search_controls(obligation.obligation_text)
        controls_context = "\n".join(
            f"- Control {c['control_id']}: {c['control_description'][:300]}"
            for c in existing_controls[:5]
        )

        response = await llm.ainvoke(
            [
                SystemMessage(content=GAP_ANALYSIS_PROMPT),
                HumanMessage(content=(
                    f"Obligation:\n"
                    f"- ID: {obligation.id}\n"
                    f"- Text: {obligation.obligation_text}\n"
                    f"- Addressee: {obligation.addressee}\n"
                    f"- Deontic type: {obligation.deontic_type}\n\n"
                    f"Existing controls that may cover this obligation:\n"
                    f"{controls_context or 'No matching controls found.'}\n\n"
                    "Analyze gaps."
                )),
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "gap_analysis",
                    "schema": GapFinding.model_json_schema(),
                },
            },
        )

        finding = GapFinding(**json.loads(response.content))
        finding.obligation_id = obligation.id
        findings.append(finding)

    return {"gap_findings": [f for f in findings if f.gap_description]}
```

---

## Key Code Patterns

### Pattern: Regulatory Text Chunking with Article Boundaries

Regulatory texts must be chunked at article/section boundaries to preserve obligation coherence. Chunking mid-obligation breaks extraction accuracy.

```python
import re

def chunk_by_articles(text: str, max_tokens: int = 3000) -> list[dict]:
    """Chunk regulatory text at article boundaries with metadata."""
    article_pattern = r'(Article\s+\d+[a-z]?|Section\s+\d+(?:\.\d+)*)'
    parts = re.split(f'(?={article_pattern})', text)

    chunks = []
    current = {"text": "", "articles": []}

    for part in parts:
        match = re.match(article_pattern, part)
        if match:
            if len(current["text"]) + len(part) > max_tokens and current["text"]:
                chunks.append(current)
                current = {"text": "", "articles": []}
            current["articles"].append(match.group())
        current["text"] += part

    if current["text"]:
        chunks.append(current)
    return chunks
```

### Pattern: Confidence-Based Routing

Every agent output includes a confidence score. The pipeline routes low-confidence results to human review.

```python
CONFIDENCE_THRESHOLDS = {
    "classification": 0.90,      # Auto-accept above
    "applicability": 0.80,       # Route to human below
    "gap_analysis": 0.85,        # Route to human below
    "auto_archive": 0.95,        # Auto-archive non-applicable above
}

def route_by_confidence(result: dict, task: str) -> str:
    threshold = CONFIDENCE_THRESHOLDS[task]
    if result.get("confidence", 0) < threshold:
        return "human_review"
    return "proceed"
```

### Pattern: Audit Trail Logging

Every agent decision is logged with full provenance for regulatory examination readiness.

```python
import logging
from datetime import datetime

audit_logger = logging.getLogger("audit_trail")

def log_agent_decision(
    agent_name: str,
    document_id: str,
    input_summary: str,
    output_summary: str,
    confidence: float,
    model_version: str,
    prompt_version: str,
):
    """Log an agent decision to the immutable audit trail."""
    audit_logger.info(
        "agent_decision",
        extra={
            "agent": agent_name,
            "document_id": document_id,
            "timestamp": datetime.utcnow().isoformat(),
            "input_summary": input_summary[:500],
            "output_summary": output_summary[:500],
            "confidence": confidence,
            "model_version": model_version,
            "prompt_version": prompt_version,
        },
    )
```

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `AZURE_OPENAI_GPT4O_DEPLOYMENT` | `gpt-4o` | GPT-4o deployment name for extraction and assessment |
| `AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT` | `gpt-4o-mini` | GPT-4o-mini deployment name for classification |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI endpoint URL |
| `AZURE_SEARCH_ENDPOINT` | — | Azure AI Search endpoint URL |
| `GRC_API_BASE_URL` | — | GRC platform REST API base URL |
| `EXTRACTION_TEMPERATURE` | `0.0` | Temperature for obligation extraction (deterministic) |
| `CLASSIFICATION_TEMPERATURE` | `0.0` | Temperature for document classification |
| `APPLICABILITY_CONFIDENCE_THRESHOLD` | `0.80` | Below this, route to human review |
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | `0.90` | Below this, require human classification |
| `CHUNK_SIZE` | `3000` | Regulatory text chunk size in characters |
| `CHUNK_OVERLAP` | `500` | Overlap between chunks to preserve article context |
| `SCAN_INTERVAL_HOURS` | `4` | How often the horizon scanner polls feeds |
| `MAX_OBLIGATIONS_PER_REGULATION` | `500` | Safety limit to prevent runaway extraction |

---

## Testing Strategy

### Unit Tests — Prompt Logic & Tool Functions

```python
# tests/test_extraction.py
import pytest
from src.models.obligation import Obligation, DeonticType

def test_obligation_model_validation():
    """Obligation model enforces required fields and valid deontic types."""
    ob = Obligation(
        id="REG-001-0001",
        obligation_text="Investment firms shall maintain adequate capital.",
        deontic_type=DeonticType.SHALL,
        addressee="investment firms",
        predicate="maintain adequate capital",
        article_reference="Article 11(1)",
        source_regulation="MiFID II",
        jurisdiction="EU",
        confidence=0.95,
    )
    assert ob.deontic_type == DeonticType.SHALL
    assert ob.ambiguity_flag is False

def test_chunk_respects_article_boundaries():
    """Chunking should never split an article across chunks."""
    from src.agents.extractor import chunk_regulatory_text
    text = "Article 1\nFirms shall do X.\n" * 50 + "Article 2\nFirms must do Y.\n" * 50
    chunks = chunk_regulatory_text(text, chunk_size=500)
    # Each chunk should start at an article boundary
    for chunk in chunks[1:]:  # Skip first chunk
        assert "Article" in chunk[:50]
```

### Evaluation Tests — AI Output Quality

```python
# tests/eval/test_extraction_accuracy.py
import json
import pytest

GOLD_SET_PATH = "tests/eval/obligations_gold.json"

@pytest.mark.asyncio
async def test_extraction_precision_recall():
    """Measure obligation extraction against human-labeled gold set.

    Target: precision >= 0.90, recall >= 0.85.
    """
    from src.agents.extractor import extract_obligations

    with open(GOLD_SET_PATH) as f:
        gold_cases = json.load(f)

    total_precision_scores = []
    total_recall_scores = []

    for case in gold_cases:
        state = {
            "document_id": case["document_id"],
            "document_title": case["title"],
            "document_text": case["text"],
            "source_jurisdiction": case["jurisdiction"],
            "source_issuing_body": case["issuing_body"],
        }
        result = await extract_obligations(state)
        extracted = {ob.obligation_text[:100] for ob in result["obligations"]}
        expected = {ob["obligation_text"][:100] for ob in case["expected_obligations"]}

        if extracted:
            precision = len(extracted & expected) / len(extracted)
            total_precision_scores.append(precision)
        if expected:
            recall = len(extracted & expected) / len(expected)
            total_recall_scores.append(recall)

    avg_precision = sum(total_precision_scores) / len(total_precision_scores)
    avg_recall = sum(total_recall_scores) / len(total_recall_scores)

    assert avg_precision >= 0.90, f"Precision {avg_precision:.2f} below 0.90 threshold"
    assert avg_recall >= 0.85, f"Recall {avg_recall:.2f} below 0.85 threshold"
```

---

## Monitoring & Observability

| What to Monitor | Tool / Method | Alert Threshold |
|-----------------|---------------|-----------------|
| **Extraction latency** | Application Insights custom metric | p95 > 5 min per regulation |
| **Classification confidence drift** | Rolling average of confidence scores | Mean confidence drops below 0.85 |
| **Human review queue depth** | Custom metric from review API | Backlog > 50 pending reviews |
| **Obligation extraction volume** | Counter metric | Sudden drop to 0 (feed outage) |
| **Applicability assessment accuracy** | Periodic comparison vs. human reviewer decisions | Agreement rate drops below 90% |
| **Token usage / cost** | Azure OpenAI metrics | Daily budget exceeded |
| **Feed polling failures** | Health check on regulatory feed connectors | Any feed unresponsive > 24 hours |

---

## Common Pitfalls & Mitigations

| Pitfall | Mitigation |
|---------|------------|
| LLM hallucinating regulatory cross-references | Structured output schema with cross_reference validation against known regulation IDs; "never invent citations" prompt rule |
| Token limit exceeded on long regulations (100+ pages) | Article-boundary chunking with overlap; parallel extraction across chunks; deduplication on merge |
| False positives in applicability (alert fatigue) | Start with narrow regulatory perimeter definition; calibrate confidence thresholds on historical data; target < 15% false positive rate |
| Inconsistent obligation extraction across prompt versions | Version-lock prompts; run regression suite against gold set on every prompt change |
| Regulatory text in non-English languages | Use GPT-4o's multilingual capabilities; add language-specific few-shot examples; consider translation-then-extraction pipeline for low-resource languages |
| Conflicting obligations across jurisdictions | Detect and flag conflicts rather than resolving autonomously; always route cross-border conflicts to human review |
| GRC platform API rate limits | Queue-based writes with retry and backoff; batch obligation register updates |

---

## Rollback Plan

1. **Disable automated pipeline processing** — stop the scheduled scanner; new publications queue but are not processed
2. **Switch to manual monitoring** — compliance team resumes manual feed checking using existing RSS bookmarks and regulator websites
3. **Preserve all processed data** — all assessments, extracted obligations, and audit logs remain in the system; nothing is deleted
4. **Resume manual workflow** — use GRC platform's native workflow to route any in-flight assessments to human completion
5. **Post-mortem** — identify which agent failed, review the failure case against the gold set, fix the prompt or tool, and re-validate before re-enabling
