# UC-025: Autonomous Multi-Jurisdiction Tax Compliance and Filing with Agentic AI — Implementation Guide

## Prerequisites

| Prerequisite | Detail |
|-------------|--------|
| **Azure Subscription** | Azure OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-large deployments), Azure Document Intelligence (S0 tier), Azure AI Search (S1), Azure Container Apps, Azure Cosmos DB, Azure Service Bus, Azure Key Vault |
| **API Keys / Access** | Avalara AvaTax API key (sandbox + production) or Vertex O Series credentials; Azure OpenAI endpoint and deployment names; state tax authority portal credentials for filing agent |
| **Existing Systems** | ERP system with REST API access (SAP S/4HANA, Oracle Cloud, NetSuite, or Dynamics 365); e-commerce platform APIs if applicable |
| **Dev Environment** | Python 3.11+, LangGraph 0.4+, Azure SDK for Python, Playwright for browser automation |
| **Permissions** | Azure RBAC: Cognitive Services OpenAI User, Document Intelligence User; ERP API service account with read access to transactions and write access to tax fields |

---

## Project Structure

```
tax-compliance-agent/
├── src/
│   ├── agents/
│   │   ├── orchestrator.py         # Main orchestrator agent (Avi pattern)
│   │   ├── document_extraction.py  # Unstructured document → structured data
│   │   ├── certificate_agent.py    # Exemption certificate validation
│   │   ├── jurisdiction_agent.py   # Nexus analysis and filing obligations
│   │   ├── return_prep_agent.py    # Return assembly and validation
│   │   ├── filing_agent.py         # Portal automation and e-filing
│   │   └── notice_agent.py         # Tax authority notice triage
│   ├── tools/
│   │   ├── tax_engine.py           # Avalara AvaTax / Vertex API wrapper
│   │   ├── doc_intelligence.py     # Azure Document Intelligence client
│   │   ├── erp_connector.py        # ERP data extraction (SAP/Oracle/NetSuite)
│   │   ├── registry_lookup.py      # State exemption registry validation
│   │   ├── portal_filer.py         # Playwright-based portal filing
│   │   └── search_client.py        # Azure AI Search for tax rules RAG
│   ├── prompts/
│   │   ├── extraction.py           # Document extraction system prompts
│   │   ├── classification.py       # Notice and document classification prompts
│   │   ├── jurisdiction.py         # Nexus analysis prompts
│   │   └── validation.py           # Return validation prompts
│   ├── models/
│   │   ├── transaction.py          # Transaction data models
│   │   ├── tax_return.py           # Return and filing models
│   │   ├── certificate.py          # Exemption certificate models
│   │   └── notice.py               # Tax authority notice models
│   └── api/
│       └── endpoints.py            # FastAPI endpoints for ERP integration
├── config/
│   ├── jurisdictions.yaml          # Filing calendars, form mappings, thresholds
│   └── settings.py                 # Environment-specific configuration
├── tests/
│   ├── unit/                       # Tool function tests, prompt output validation
│   ├── integration/                # End-to-end agent flow tests
│   └── evaluation/                 # LLM output quality evaluation
└── docs/
```

---

## Step-by-Step Implementation

### Phase 1: Foundation — Tax Engine Integration

#### Step 1.1: Tax Engine API Connection

The deterministic tax engine is the foundation. All tax calculations flow through this API — the LLM never computes tax amounts. Avalara AvaTax provides the most comprehensive coverage (190+ countries), while Vertex O Series covers 20,000+ jurisdictions with 1 billion+ governed rules.

```python
# src/tools/tax_engine.py
from dataclasses import dataclass
from datetime import date
import httpx


@dataclass
class TaxLineItem:
    item_code: str
    description: str
    amount: float
    quantity: int
    tax_code: str  # Product taxability code (e.g., "PS081282" for software)


@dataclass
class TaxCalculationRequest:
    company_code: str
    transaction_type: str  # "SalesInvoice", "PurchaseInvoice", "ReturnInvoice"
    customer_code: str
    date: date
    ship_from_address: dict  # {line1, city, region, postal_code, country}
    ship_to_address: dict
    lines: list[TaxLineItem]
    currency_code: str = "USD"
    exemption_no: str | None = None


@dataclass
class TaxCalculationResult:
    total_tax: float
    total_taxable: float
    total_exempt: float
    lines: list[dict]  # Per-line tax breakdown by jurisdiction
    jurisdiction_details: list[dict]  # Tax by jurisdiction (state, county, city, district)


class AvalaraTaxEngine:
    """Deterministic tax calculation via Avalara AvaTax REST API v2.
    
    This is the authoritative source for all tax rates and rules.
    The LLM never performs tax calculations — only this engine does.
    """
    
    BASE_URL = "https://rest.avatax.com/api/v2"  # Production
    SANDBOX_URL = "https://sandbox-rest.avatax.com/api/v2"  # Sandbox
    
    def __init__(self, account_id: str, license_key: str, sandbox: bool = False):
        self.base_url = self.SANDBOX_URL if sandbox else self.BASE_URL
        self.auth = (account_id, license_key)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=self.auth,
            timeout=30.0,
        )
    
    async def calculate_tax(self, request: TaxCalculationRequest) -> TaxCalculationResult:
        """Calculate tax for a transaction. Returns deterministic, auditable results."""
        payload = {
            "type": request.transaction_type,
            "companyCode": request.company_code,
            "date": request.date.isoformat(),
            "customerCode": request.customer_code,
            "exemptionNo": request.exemption_no,
            "addresses": {
                "shipFrom": request.ship_from_address,
                "shipTo": request.ship_to_address,
            },
            "lines": [
                {
                    "number": str(i + 1),
                    "quantity": line.quantity,
                    "amount": line.amount,
                    "taxCode": line.tax_code,
                    "itemCode": line.item_code,
                    "description": line.description,
                }
                for i, line in enumerate(request.lines)
            ],
            "currencyCode": request.currency_code,
            "commit": False,  # Don't commit until filing
        }
        
        response = await self.client.post(
            "/transactions/create", json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return TaxCalculationResult(
            total_tax=data["totalTax"],
            total_taxable=data["totalTaxable"],
            total_exempt=data["totalExempt"],
            lines=data["lines"],
            jurisdiction_details=data.get("summary", []),
        )
    
    async def validate_address(self, address: dict) -> dict:
        """Validate and normalize address for accurate jurisdiction determination."""
        response = await self.client.post(
            "/addresses/resolve", json={"textCase": "Upper", **address}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_nexus_by_company(self, company_code: str) -> list[dict]:
        """Retrieve current nexus declarations for a company."""
        response = await self.client.get(
            f"/companies/{company_code}/nexus"
        )
        response.raise_for_status()
        return response.json()["value"]
```

**Verification:** Run `calculate_tax` against Avalara sandbox with a known transaction. Verify tax amount matches manual lookup for the same jurisdiction/product combination.

#### Step 1.2: ERP Data Connector

```python
# src/tools/erp_connector.py
from dataclasses import dataclass
from datetime import date, datetime
import httpx


@dataclass
class ERPTransaction:
    transaction_id: str
    transaction_date: date
    customer_code: str
    customer_name: str
    ship_from: dict
    ship_to: dict
    line_items: list[dict]
    currency: str
    total_amount: float
    source_system: str  # "SAP", "Oracle", "NetSuite", "Dynamics365"


class ERPConnector:
    """Extracts transaction data from ERP systems.
    
    Supports SAP S/4HANA, Oracle Cloud, NetSuite, and Dynamics 365.
    Each ERP has its own API contract — this connector normalizes
    to a common ERPTransaction format for downstream processing.
    """
    
    def __init__(self, erp_type: str, base_url: str, credentials: dict):
        self.erp_type = erp_type
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=self._build_auth_headers(credentials),
            timeout=60.0,
        )
    
    async def fetch_transactions(
        self, start_date: date, end_date: date, company_code: str
    ) -> list[ERPTransaction]:
        """Fetch transactions for a date range from the ERP."""
        if self.erp_type == "SAP":
            return await self._fetch_sap_transactions(start_date, end_date, company_code)
        elif self.erp_type == "NetSuite":
            return await self._fetch_netsuite_transactions(start_date, end_date, company_code)
        elif self.erp_type == "Dynamics365":
            return await self._fetch_dynamics_transactions(start_date, end_date, company_code)
        else:
            raise ValueError(f"Unsupported ERP: {self.erp_type}")
    
    async def _fetch_netsuite_transactions(
        self, start_date: date, end_date: date, company_code: str
    ) -> list[ERPTransaction]:
        """NetSuite SuiteTalk REST API integration."""
        response = await self.client.get(
            "/services/rest/record/v1/invoice",
            params={
                "q": f'tranDate AFTER "{start_date}" AND tranDate BEFORE "{end_date}" '
                     f'AND subsidiary.name IS "{company_code}"',
                "limit": 1000,
                "fields": "tranId,tranDate,entity,shipAddress,lineItems,currency,total",
            },
        )
        response.raise_for_status()
        records = response.json()["items"]
        
        return [
            ERPTransaction(
                transaction_id=r["tranId"],
                transaction_date=datetime.fromisoformat(r["tranDate"]).date(),
                customer_code=r["entity"]["id"],
                customer_name=r["entity"]["refName"],
                ship_from=self._parse_netsuite_address(r.get("shipFrom", {})),
                ship_to=self._parse_netsuite_address(r.get("shipAddress", {})),
                line_items=r.get("lineItems", []),
                currency=r.get("currency", {}).get("refName", "USD"),
                total_amount=float(r.get("total", 0)),
                source_system="NetSuite",
            )
            for r in records
        ]
    
    def _build_auth_headers(self, credentials: dict) -> dict:
        """Build authentication headers based on ERP type."""
        # OAuth 2.0 token-based auth for all modern ERPs
        return {"Authorization": f"Bearer {credentials['access_token']}"}
    
    def _parse_netsuite_address(self, addr: dict) -> dict:
        return {
            "line1": addr.get("addr1", ""),
            "city": addr.get("city", ""),
            "region": addr.get("state", ""),
            "postalCode": addr.get("zip", ""),
            "country": addr.get("country", "US"),
        }
```

---

### Phase 2: Core AI Integration — Document Processing and Classification

#### Step 2.1: LLM Connection and Configuration

```python
# src/agents/base.py
from openai import AsyncAzureOpenAI

# Two model tiers: GPT-4o for complex reasoning, GPT-4o-mini for high-volume classification
llm_primary = AsyncAzureOpenAI(
    azure_endpoint="https://<your-resource>.openai.azure.com/",
    api_version="2025-03-01-preview",
    azure_deployment="gpt-4o",
    # Authentication via DefaultAzureCredential (Managed Identity in production)
)

llm_fast = AsyncAzureOpenAI(
    azure_endpoint="https://<your-resource>.openai.azure.com/",
    api_version="2025-03-01-preview",
    azure_deployment="gpt-4o-mini",
)

# Configuration: temperature=0 for deterministic extraction and classification
MODEL_CONFIG = {
    "extraction": {"model": "gpt-4o", "temperature": 0, "max_tokens": 4096},
    "classification": {"model": "gpt-4o-mini", "temperature": 0, "max_tokens": 1024},
    "validation": {"model": "gpt-4o", "temperature": 0, "max_tokens": 2048},
    "response_drafting": {"model": "gpt-4o", "temperature": 0.3, "max_tokens": 4096},
}
```

#### Step 2.2: Document Extraction Agent

This agent handles unstructured inputs — invoices, purchase orders, receipts — that arrive outside the ERP's structured transaction feed. Azure Document Intelligence provides OCR and prebuilt tax form models; Azure OpenAI provides structured extraction for non-standard documents.

```python
# src/agents/document_extraction.py
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.identity.aio import DefaultAzureCredential
from pydantic import BaseModel, Field


class ExtractedTransaction(BaseModel):
    """Structured output schema for transaction extraction from documents."""
    vendor_name: str = Field(description="Name of the vendor/supplier")
    vendor_address: dict = Field(description="Vendor address with line1, city, region, postalCode, country")
    customer_name: str = Field(description="Name of the customer/buyer")
    customer_address: dict = Field(description="Customer address with line1, city, region, postalCode, country")
    invoice_number: str = Field(description="Invoice or document reference number")
    invoice_date: str = Field(description="Invoice date in YYYY-MM-DD format")
    line_items: list[dict] = Field(
        description="List of line items, each with: description, quantity, unit_price, amount, product_code"
    )
    total_amount: float = Field(description="Total invoice amount before tax")
    currency: str = Field(description="Three-letter currency code (e.g., USD, EUR)")
    confidence: float = Field(description="Confidence score 0.0-1.0 for overall extraction quality")


EXTRACTION_SYSTEM_PROMPT = """You are a tax compliance document extraction agent. Your role is to extract
structured transaction data from invoices, purchase orders, and receipts for tax calculation purposes.

CRITICAL RULES:
- Extract ONLY what is explicitly present in the document. Never infer or fabricate data.
- If a field is not visible in the document, set it to null or empty string.
- Addresses MUST include enough detail for jurisdiction determination (city, state/region, postal code, country).
- Product descriptions should be detailed enough for tax code classification.
- Set confidence to a value between 0.0 and 1.0 reflecting extraction reliability.
  Use < 0.7 if the document is blurry, handwritten, or has missing critical fields.
- Dates must be in YYYY-MM-DD format. Convert all date formats to this standard.
- Amounts must be numeric (no currency symbols). Use the document's stated currency."""


class DocumentExtractionAgent:
    """Extracts structured transaction data from unstructured documents.
    
    Two-stage pipeline:
    1. Azure Document Intelligence: OCR + layout analysis for text extraction
    2. Azure OpenAI: Structured extraction from OCR text into transaction schema
    """
    
    def __init__(self, doc_intel_endpoint: str, openai_client):
        self.doc_client = DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint,
            credential=DefaultAzureCredential(),
        )
        self.openai = openai_client
    
    async def extract_from_document(self, document_bytes: bytes, filename: str) -> ExtractedTransaction:
        """Extract structured transaction data from a document image or PDF."""
        
        # Stage 1: OCR via Azure Document Intelligence
        # Use prebuilt tax models for known formats, general model for others
        model_id = self._select_model(filename)
        poller = await self.doc_client.begin_analyze_document(
            model_id=model_id,
            body=document_bytes,
            content_type="application/octet-stream",
        )
        result = await poller.result()
        ocr_text = result.content
        
        # Stage 2: Structured extraction via Azure OpenAI
        response = await self.openai.beta.chat.completions.parse(
            model="gpt-4o",
            temperature=0,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract transaction data from this document:\n\n{ocr_text}"},
            ],
            response_format=ExtractedTransaction,
        )
        
        return response.choices[0].message.parsed
    
    def _select_model(self, filename: str) -> str:
        """Select the appropriate Document Intelligence model based on document type."""
        lower = filename.lower()
        if any(x in lower for x in ["w2", "w-2"]):
            return "prebuilt-tax.us.w2"
        elif any(x in lower for x in ["1099", "1098"]):
            return "prebuilt-tax.us.1099NEC"  # or other 1099 variants
        elif "invoice" in lower:
            return "prebuilt-invoice"
        else:
            return "prebuilt-layout"  # General OCR + layout for unknown formats
```

#### Step 2.3: Exemption Certificate Validation Agent

```python
# src/agents/certificate_agent.py
from pydantic import BaseModel, Field
from enum import Enum


class CertificateType(str, Enum):
    RESALE = "resale"
    EXEMPT_ORG = "exempt_organization"
    GOVERNMENT = "government"
    MANUFACTURING = "manufacturing"
    AGRICULTURAL = "agricultural"
    OTHER = "other"


class ExtractedCertificate(BaseModel):
    """Structured output for exemption certificate extraction."""
    certificate_type: CertificateType
    issuing_state: str = Field(description="Two-letter state code (e.g., CA, TX, NY)")
    purchaser_name: str
    purchaser_address: dict
    purchaser_tax_id: str = Field(description="State tax ID or EIN of the purchaser")
    seller_name: str | None = None
    exemption_reason: str
    effective_date: str | None = Field(description="Date in YYYY-MM-DD format")
    expiration_date: str | None = Field(description="Date in YYYY-MM-DD format, null if no expiration")
    signature_present: bool
    signature_date: str | None = None
    confidence: float


CERTIFICATE_SYSTEM_PROMPT = """You are a tax compliance agent specialized in exemption certificate validation.
Extract all fields from the exemption certificate image/text provided.

CRITICAL RULES:
- Extract ONLY what is present on the certificate. Never infer missing data.
- Verify that signature_present is true ONLY if you can see an actual signature (not just a signature line).
- If the certificate has an expiration date, extract it. Many states issue certificates without expiration.
- The issuing_state is the state whose exemption is being claimed, not necessarily the purchaser's state.
- Set confidence < 0.7 if: signature is missing, critical fields are illegible, or form appears incomplete.
- Tax IDs should be extracted exactly as printed (include hyphens, spaces as shown)."""


class CertificateValidationAgent:
    """Validates exemption certificates through OCR extraction and registry verification.
    
    Pipeline:
    1. OCR extraction of certificate fields
    2. Structural validation (required fields present, dates valid)
    3. Registry cross-verification (tax ID lookup against state databases)
    4. Expiry tracking and renewal notification scheduling
    """
    
    def __init__(self, doc_intel_endpoint: str, openai_client, registry_client):
        self.doc_client = DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint,
            credential=DefaultAzureCredential(),
        )
        self.openai = openai_client
        self.registry = registry_client
    
    async def validate_certificate(self, cert_bytes: bytes) -> dict:
        """Full validation pipeline for an exemption certificate."""
        
        # Step 1: OCR + structured extraction
        poller = await self.doc_client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=cert_bytes,
            content_type="application/octet-stream",
        )
        result = await poller.result()
        
        response = await self.openai.beta.chat.completions.parse(
            model="gpt-4o",
            temperature=0,
            messages=[
                {"role": "system", "content": CERTIFICATE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract certificate data:\n\n{result.content}"},
            ],
            response_format=ExtractedCertificate,
        )
        cert = response.choices[0].message.parsed
        
        # Step 2: Structural validation (deterministic — no LLM)
        issues = self._validate_structure(cert)
        
        # Step 3: Registry cross-verification (deterministic API call)
        registry_valid = await self.registry.verify_tax_id(
            state=cert.issuing_state,
            tax_id=cert.purchaser_tax_id,
        )
        if not registry_valid:
            issues.append(f"Tax ID {cert.purchaser_tax_id} not found in {cert.issuing_state} registry")
        
        return {
            "certificate": cert.model_dump(),
            "validation_issues": issues,
            "registry_verified": registry_valid,
            "status": "valid" if not issues and registry_valid else "requires_review",
        }
    
    def _validate_structure(self, cert: ExtractedCertificate) -> list[str]:
        """Deterministic validation rules — no LLM needed."""
        issues = []
        if not cert.signature_present:
            issues.append("Certificate is missing a signature")
        if not cert.purchaser_tax_id:
            issues.append("Purchaser tax ID is missing")
        if cert.expiration_date:
            from datetime import date, datetime
            exp = datetime.strptime(cert.expiration_date, "%Y-%m-%d").date()
            if exp < date.today():
                issues.append(f"Certificate expired on {cert.expiration_date}")
        if cert.confidence < 0.7:
            issues.append(f"Low extraction confidence ({cert.confidence:.2f}) — manual review recommended")
        return issues
```

#### Step 2.4: Notice Triage Agent

```python
# src/agents/notice_agent.py
from pydantic import BaseModel, Field
from enum import Enum


class NoticeUrgency(str, Enum):
    CRITICAL = "critical"   # Assessment, lien, levy — requires immediate action
    HIGH = "high"           # Audit notice, information request with < 30 day deadline
    MEDIUM = "medium"       # Discrepancy notice, rate change notification
    LOW = "low"             # Informational, general correspondence


class NoticeType(str, Enum):
    ASSESSMENT = "assessment"
    AUDIT_NOTICE = "audit_notice"
    INFORMATION_REQUEST = "information_request"
    DISCREPANCY = "discrepancy"
    RATE_CHANGE = "rate_change"
    REGISTRATION = "registration"
    PENALTY = "penalty"
    REFUND = "refund"
    GENERAL = "general"


class ClassifiedNotice(BaseModel):
    notice_type: NoticeType
    urgency: NoticeUrgency
    issuing_authority: str = Field(description="Tax authority name (e.g., 'California Franchise Tax Board')")
    jurisdiction: str = Field(description="State/country code")
    reference_number: str | None = Field(description="Notice or case reference number")
    response_deadline: str | None = Field(description="Response due date in YYYY-MM-DD format")
    amount_at_issue: float | None = Field(description="Dollar amount referenced in notice, if any")
    summary: str = Field(description="2-3 sentence summary of what the notice requires")
    key_dates: list[str] = Field(description="All dates mentioned in the notice")
    required_actions: list[str] = Field(description="Specific actions the taxpayer must take")


NOTICE_SYSTEM_PROMPT = """You are a tax compliance agent specialized in classifying and triaging
tax authority notices. You receive OCR text from scanned or digitized notices.

CRITICAL RULES:
- Classify the notice type and urgency based on the content, not assumptions.
- Extract ALL dates mentioned — response deadlines are the most critical field.
- If a dollar amount is at issue (assessment, penalty, adjustment), extract it precisely.
- For required_actions, list the specific steps the taxpayer must take to respond.
- Urgency classification:
  * CRITICAL: Assessment, lien, levy, garnishment — threatens immediate financial impact
  * HIGH: Audit notice, information request with deadline < 30 days
  * MEDIUM: Discrepancy notice, proposed adjustment with > 30 day response window
  * LOW: Informational, rate change notification, general correspondence
- Never fabricate a deadline. If no deadline is stated, set response_deadline to null."""


RESPONSE_DRAFT_PROMPT = """You are a tax compliance agent drafting an initial response to a tax authority notice.

Notice summary: {notice_summary}
Required actions: {required_actions}
Issuing authority: {issuing_authority}

Draft a professional response letter that:
1. Acknowledges receipt of the notice and references the notice number
2. Addresses each required action
3. Requests additional time if the deadline is within 14 days
4. Uses formal, respectful language appropriate for tax authority correspondence
5. Includes placeholders for: [COMPANY_NAME], [TAX_ID], [CONTACT_NAME], [CONTACT_PHONE]

IMPORTANT: This is a DRAFT for human review. Include a header noting "DRAFT — FOR REVIEW" and
flag any areas where the tax professional should add specific factual responses."""


class NoticeTirageAgent:
    """Classifies and triages tax authority notices, generating draft responses.
    
    Two-step process:
    1. Classification: Determine notice type, urgency, deadlines, and required actions
    2. Response drafting: Generate initial response draft for human review
    """
    
    def __init__(self, openai_client, doc_intel_endpoint: str):
        self.openai = openai_client
        self.doc_client = DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint,
            credential=DefaultAzureCredential(),
        )
    
    async def triage_notice(self, notice_bytes: bytes) -> dict:
        """Full notice triage pipeline: OCR → classify → draft response."""
        
        # Step 1: OCR extraction
        poller = await self.doc_client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=notice_bytes,
            content_type="application/octet-stream",
        )
        result = await poller.result()
        
        # Step 2: Classification (GPT-4o-mini — high volume, lower cost)
        classification = await self.openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": NOTICE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this tax authority notice:\n\n{result.content}"},
            ],
            response_format=ClassifiedNotice,
        )
        notice = classification.choices[0].message.parsed
        
        # Step 3: Draft response (GPT-4o — needs higher quality for correspondence)
        draft = await self.openai.chat.completions.create(
            model="gpt-4o",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": RESPONSE_DRAFT_PROMPT.format(
                        notice_summary=notice.summary,
                        required_actions="\n".join(f"- {a}" for a in notice.required_actions),
                        issuing_authority=notice.issuing_authority,
                    ),
                },
                {"role": "user", "content": "Draft the response letter."},
            ],
        )
        
        return {
            "classification": notice.model_dump(),
            "draft_response": draft.choices[0].message.content,
            "ocr_text": result.content,
        }
```

---

### Phase 3: Integration Layer — Tax Rules RAG and Jurisdiction Analysis

#### Step 3.1: Tax Rules Knowledge Base

```python
# src/tools/search_client.py
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.identity.aio import DefaultAzureCredential


class TaxRulesSearchClient:
    """Hybrid search over tax rules, regulations, and jurisdiction guidance.
    
    The vector index contains:
    - State/country tax codes and regulations
    - Exemption rules by jurisdiction and product category
    - Nexus threshold rules (economic nexus, physical presence)
    - Filing frequency requirements and deadlines
    - Recent rate changes and effective dates
    
    This supports RAG for the Jurisdiction Analyzer Agent, providing
    grounded context for nexus and filing obligation determination.
    """
    
    def __init__(self, endpoint: str, index_name: str, embedding_client):
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=DefaultAzureCredential(),
        )
        self.embedding_client = embedding_client
    
    async def search_tax_rules(self, query: str, jurisdiction: str | None = None, top_k: int = 5) -> list[dict]:
        """Hybrid search: vector similarity + keyword + optional jurisdiction filter."""
        
        # Generate embedding for semantic search
        embedding_response = await self.embedding_client.embeddings.create(
            model="text-embedding-3-large",
            input=query,
        )
        query_vector = embedding_response.data[0].embedding
        
        # Build filter for jurisdiction scoping
        filter_expr = f"jurisdiction eq '{jurisdiction}'" if jurisdiction else None
        
        results = await self.search_client.search(
            search_text=query,  # Keyword component
            vector_queries=[
                VectorizedQuery(
                    vector=query_vector,
                    k_nearest_neighbors=top_k,
                    fields="content_vector",
                )
            ],
            filter=filter_expr,
            top=top_k,
            select=["jurisdiction", "rule_type", "content", "effective_date", "source_url"],
        )
        
        docs = []
        async for result in results:
            docs.append({
                "jurisdiction": result["jurisdiction"],
                "rule_type": result["rule_type"],
                "content": result["content"],
                "effective_date": result["effective_date"],
                "source_url": result["source_url"],
                "score": result["@search.score"],
            })
        return docs
```

#### Step 3.2: Jurisdiction Analyzer Agent

```python
# src/agents/jurisdiction_agent.py
from pydantic import BaseModel, Field


class NexusAssessment(BaseModel):
    """Structured output for nexus and filing obligation analysis."""
    jurisdiction: str = Field(description="State/country code")
    jurisdiction_name: str = Field(description="Full jurisdiction name")
    has_nexus: bool = Field(description="Whether the company has nexus in this jurisdiction")
    nexus_type: str = Field(description="physical, economic, click-through, affiliate, marketplace, or none")
    nexus_basis: str = Field(description="Explanation of why nexus exists or does not exist")
    filing_required: bool
    filing_frequency: str = Field(description="monthly, quarterly, annually, or not_applicable")
    next_filing_deadline: str | None = Field(description="Next filing due date in YYYY-MM-DD format")
    estimated_liability: float | None = Field(description="Estimated tax liability for current period")
    economic_threshold: dict | None = Field(
        description="Economic nexus thresholds: {sales_amount, transaction_count, period}"
    )
    current_activity: dict | None = Field(
        description="Company's current activity: {total_sales, transaction_count, period}"
    )


JURISDICTION_SYSTEM_PROMPT = """You are a tax compliance agent analyzing nexus obligations and filing
requirements. You have access to retrieved tax rules and the company's transaction data.

ANALYSIS FRAMEWORK:
1. Check physical nexus: Does the company have employees, offices, warehouses, or property in this jurisdiction?
2. Check economic nexus: Does the company exceed the jurisdiction's economic nexus thresholds?
   - Most US states adopted Wayfair thresholds after South Dakota v. Wayfair (2018)
   - Common threshold: $100,000 in sales OR 200 transactions in the prior/current calendar year
   - Some states have different thresholds (e.g., CA: $500,000 sales only)
3. Check other nexus types: click-through, affiliate, marketplace facilitator rules
4. Determine filing frequency based on estimated liability (most states have tiered frequencies)

CRITICAL RULES:
- Base your analysis ONLY on the tax rules retrieved and the transaction data provided.
- Do NOT guess economic nexus thresholds — use the retrieved rules.
- If you don't have sufficient data to determine nexus, set has_nexus to false and explain in nexus_basis.
- Filing deadlines must come from the retrieved filing calendar data, not from general knowledge.
- Economic nexus thresholds vary significantly by state — always use the specific state's rules."""


class JurisdictionAnalyzerAgent:
    """Determines nexus obligations and filing requirements per jurisdiction.
    
    Uses RAG over the tax rules knowledge base to ground analysis in
    current, jurisdiction-specific rules rather than LLM general knowledge.
    """
    
    def __init__(self, openai_client, search_client, tax_engine):
        self.openai = openai_client
        self.search = search_client
        self.tax_engine = tax_engine
    
    async def analyze_jurisdiction(
        self,
        jurisdiction: str,
        company_code: str,
        transaction_summary: dict,
    ) -> NexusAssessment:
        """Analyze nexus and filing obligations for a single jurisdiction."""
        
        # Retrieve jurisdiction-specific rules via RAG
        nexus_rules = await self.search.search_tax_rules(
            query=f"economic nexus threshold filing requirements {jurisdiction}",
            jurisdiction=jurisdiction,
            top_k=5,
        )
        
        filing_rules = await self.search.search_tax_rules(
            query=f"filing frequency deadlines return due dates {jurisdiction}",
            jurisdiction=jurisdiction,
            top_k=3,
        )
        
        # Get current nexus declarations from tax engine
        current_nexus = await self.tax_engine.get_nexus_by_company(company_code)
        has_declared_nexus = any(n["region"] == jurisdiction for n in current_nexus)
        
        # Build context for LLM analysis
        rules_context = "\n\n".join(
            f"[Rule: {r['rule_type']}] (effective {r['effective_date']})\n{r['content']}"
            for r in nexus_rules + filing_rules
        )
        
        response = await self.openai.beta.chat.completions.parse(
            model="gpt-4o",
            temperature=0,
            messages=[
                {"role": "system", "content": JURISDICTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Analyze nexus for jurisdiction: {jurisdiction}\n\n"
                        f"Company transaction summary for this jurisdiction:\n"
                        f"- Total sales: ${transaction_summary.get('total_sales', 0):,.2f}\n"
                        f"- Transaction count: {transaction_summary.get('transaction_count', 0)}\n"
                        f"- Period: {transaction_summary.get('period', 'current year')}\n"
                        f"- Has physical presence: {transaction_summary.get('physical_presence', 'unknown')}\n"
                        f"- Currently declared nexus: {has_declared_nexus}\n\n"
                        f"Retrieved tax rules:\n{rules_context}"
                    ),
                },
            ],
            response_format=NexusAssessment,
        )
        
        return response.choices[0].message.parsed
```

---

### Phase 4: Orchestration and Flow

#### Step 4.1: Workflow Orchestration with LangGraph

The orchestrator coordinates all agents through a state graph with conditional routing and human-in-the-loop approval gates.

```python
# src/agents/orchestrator.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    CALCULATING = "calculating"
    ANALYZING = "analyzing"
    PREPARING = "preparing"
    AWAITING_APPROVAL = "awaiting_approval"
    FILING = "filing"
    COMPLETED = "completed"
    EXCEPTION = "exception"


@dataclass
class ComplianceState:
    """Persistent state for the tax compliance workflow."""
    # Input
    company_code: str = ""
    filing_period: str = ""  # e.g., "2026-03"
    jurisdictions: list[str] = field(default_factory=list)
    
    # Processing state
    status: WorkflowStatus = WorkflowStatus.PENDING
    transactions: list[dict] = field(default_factory=list)
    tax_calculations: list[dict] = field(default_factory=list)
    nexus_assessments: list[dict] = field(default_factory=list)
    prepared_returns: list[dict] = field(default_factory=list)
    
    # Approval state
    returns_pending_approval: list[dict] = field(default_factory=list)
    approved_returns: list[dict] = field(default_factory=list)
    rejected_returns: list[dict] = field(default_factory=list)
    
    # Results
    filed_returns: list[dict] = field(default_factory=list)
    exceptions: list[dict] = field(default_factory=list)
    audit_trail: list[dict] = field(default_factory=list)
    
    # Messages for agent communication
    messages: Annotated[list, add_messages] = field(default_factory=list)


def build_compliance_workflow(
    erp_connector,
    tax_engine,
    jurisdiction_agent,
    return_prep_agent,
    filing_agent,
) -> StateGraph:
    """Build the LangGraph workflow for end-to-end tax compliance."""
    
    graph = StateGraph(ComplianceState)
    
    # Node: Extract transactions from ERP
    async def extract_transactions(state: ComplianceState) -> dict:
        """Pull transaction data from ERP for the filing period."""
        from datetime import datetime
        year, month = state.filing_period.split("-")
        start_date = datetime(int(year), int(month), 1).date()
        # Calculate end of month
        if int(month) == 12:
            end_date = datetime(int(year) + 1, 1, 1).date()
        else:
            end_date = datetime(int(year), int(month) + 1, 1).date()
        
        transactions = await erp_connector.fetch_transactions(
            start_date=start_date,
            end_date=end_date,
            company_code=state.company_code,
        )
        return {
            "transactions": [t.__dict__ for t in transactions],
            "status": WorkflowStatus.CALCULATING,
            "audit_trail": state.audit_trail + [{
                "step": "extract_transactions",
                "count": len(transactions),
                "period": state.filing_period,
            }],
        }
    
    # Node: Calculate tax via deterministic engine
    async def calculate_taxes(state: ComplianceState) -> dict:
        """Run all transactions through the deterministic tax engine."""
        calculations = []
        for txn in state.transactions:
            result = await tax_engine.calculate_tax(
                TaxCalculationRequest(
                    company_code=state.company_code,
                    transaction_type="SalesInvoice",
                    customer_code=txn["customer_code"],
                    date=txn["transaction_date"],
                    ship_from_address=txn["ship_from"],
                    ship_to_address=txn["ship_to"],
                    lines=[
                        TaxLineItem(**item) for item in txn["line_items"]
                    ],
                    currency_code=txn.get("currency", "USD"),
                )
            )
            calculations.append({
                "transaction_id": txn["transaction_id"],
                "result": result.__dict__,
            })
        return {
            "tax_calculations": calculations,
            "status": WorkflowStatus.ANALYZING,
        }
    
    # Node: Analyze jurisdiction obligations
    async def analyze_jurisdictions(state: ComplianceState) -> dict:
        """Determine filing obligations per jurisdiction using LLM + RAG."""
        # Aggregate transactions by jurisdiction
        jurisdiction_totals = {}
        for calc in state.tax_calculations:
            for detail in calc["result"].get("jurisdiction_details", []):
                jur = detail.get("region", "unknown")
                if jur not in jurisdiction_totals:
                    jurisdiction_totals[jur] = {"total_sales": 0, "transaction_count": 0, "period": state.filing_period}
                jurisdiction_totals[jur]["total_sales"] += detail.get("taxable", 0)
                jurisdiction_totals[jur]["transaction_count"] += 1
        
        assessments = []
        for jurisdiction, summary in jurisdiction_totals.items():
            assessment = await jurisdiction_agent.analyze_jurisdiction(
                jurisdiction=jurisdiction,
                company_code=state.company_code,
                transaction_summary=summary,
            )
            assessments.append(assessment.model_dump())
        
        filing_jurisdictions = [a["jurisdiction"] for a in assessments if a["filing_required"]]
        return {
            "nexus_assessments": assessments,
            "jurisdictions": filing_jurisdictions,
            "status": WorkflowStatus.PREPARING,
        }
    
    # Node: Prepare returns
    async def prepare_returns(state: ComplianceState) -> dict:
        """Assemble returns for each jurisdiction requiring filing."""
        returns = []
        for jurisdiction in state.jurisdictions:
            # Filter calculations for this jurisdiction
            jur_calcs = [
                c for c in state.tax_calculations
                if any(d.get("region") == jurisdiction for d in c["result"].get("jurisdiction_details", []))
            ]
            prepared = await return_prep_agent.prepare_return(
                jurisdiction=jurisdiction,
                period=state.filing_period,
                calculations=jur_calcs,
                company_code=state.company_code,
            )
            returns.append(prepared)
        
        return {
            "prepared_returns": returns,
            "returns_pending_approval": returns,
            "status": WorkflowStatus.AWAITING_APPROVAL,
        }
    
    # Node: Human approval gate (interrupt-resume pattern)
    async def human_approval(state: ComplianceState) -> dict:
        """Present returns for human review. Workflow pauses here until approved."""
        # LangGraph interrupt: pauses execution and waits for external resume
        approval_decisions = interrupt({
            "message": f"Review {len(state.returns_pending_approval)} tax returns for {state.filing_period}",
            "returns": state.returns_pending_approval,
            "action_required": "Approve or reject each return",
        })
        
        # Process approval decisions (provided when workflow is resumed)
        approved = []
        rejected = []
        for decision in approval_decisions:
            if decision["approved"]:
                approved.append(decision["return"])
            else:
                rejected.append({**decision["return"], "rejection_reason": decision.get("reason", "")})
        
        return {
            "approved_returns": approved,
            "rejected_returns": rejected,
            "returns_pending_approval": [],
            "status": WorkflowStatus.FILING if approved else WorkflowStatus.EXCEPTION,
        }
    
    # Node: File approved returns
    async def file_returns(state: ComplianceState) -> dict:
        """Submit approved returns via e-filing APIs or portal automation."""
        filed = []
        exceptions = []
        for ret in state.approved_returns:
            try:
                confirmation = await filing_agent.file_return(
                    jurisdiction=ret["jurisdiction"],
                    return_data=ret,
                )
                filed.append({**ret, "confirmation": confirmation})
            except Exception as e:
                exceptions.append({**ret, "error": str(e)})
        
        return {
            "filed_returns": filed,
            "exceptions": state.exceptions + exceptions,
            "status": WorkflowStatus.COMPLETED,
        }
    
    # Conditional routing
    def route_after_approval(state: ComplianceState) -> str:
        if state.approved_returns:
            return "file_returns"
        return END  # All rejected — nothing to file
    
    # Build the graph
    graph.add_node("extract_transactions", extract_transactions)
    graph.add_node("calculate_taxes", calculate_taxes)
    graph.add_node("analyze_jurisdictions", analyze_jurisdictions)
    graph.add_node("prepare_returns", prepare_returns)
    graph.add_node("human_approval", human_approval)
    graph.add_node("file_returns", file_returns)
    
    graph.add_edge(START, "extract_transactions")
    graph.add_edge("extract_transactions", "calculate_taxes")
    graph.add_edge("calculate_taxes", "analyze_jurisdictions")
    graph.add_edge("analyze_jurisdictions", "prepare_returns")
    graph.add_edge("prepare_returns", "human_approval")
    graph.add_conditional_edges("human_approval", route_after_approval)
    graph.add_edge("file_returns", END)
    
    return graph.compile(checkpointer=MemorySaver())
```

#### Step 4.2: Running the Workflow

```python
# Example: Trigger monthly filing workflow
import asyncio
from langgraph.types import Command


async def run_monthly_filing(company_code: str, period: str):
    """Execute the monthly tax compliance filing workflow."""
    
    workflow = build_compliance_workflow(
        erp_connector=erp_connector,
        tax_engine=tax_engine,
        jurisdiction_agent=jurisdiction_agent,
        return_prep_agent=return_prep_agent,
        filing_agent=filing_agent,
    )
    
    config = {"configurable": {"thread_id": f"filing-{company_code}-{period}"}}
    
    initial_state = ComplianceState(
        company_code=company_code,
        filing_period=period,
    )
    
    # Run until human approval interrupt
    result = await workflow.ainvoke(initial_state, config=config)
    
    # At this point, workflow is paused at human_approval node
    # Tax manager reviews in UI, then resumes:
    approval_decisions = [
        {"return": ret, "approved": True}
        for ret in result["returns_pending_approval"]
    ]
    
    # Resume workflow with approval decisions
    final = await workflow.ainvoke(
        Command(resume=approval_decisions), config=config
    )
    
    return final
```

---

## Key Code Patterns

### Pattern: Deterministic Validation Over LLM Trust

Tax amounts, rates, and filing positions must be verifiable. Never trust the LLM for these — always validate against the deterministic tax engine.

```python
async def validate_return_amounts(prepared_return: dict, tax_engine) -> list[str]:
    """Cross-validate LLM-prepared return against deterministic tax engine totals.
    
    The return preparation agent assembles data, but the tax engine is the
    authoritative source for amounts. Any discrepancy triggers manual review.
    """
    issues = []
    engine_total = sum(
        calc["result"]["total_tax"]
        for calc in prepared_return["calculations"]
    )
    prepared_total = prepared_return.get("total_tax_due", 0)
    
    if abs(engine_total - prepared_total) > 0.01:  # Penny-level tolerance
        issues.append(
            f"Amount mismatch: engine={engine_total:.2f}, "
            f"prepared={prepared_total:.2f}, diff={abs(engine_total - prepared_total):.2f}"
        )
    
    return issues
```

### Pattern: Structured Output Enforcement

All LLM outputs use Pydantic models via Azure OpenAI's structured output mode, preventing hallucinated fields and ensuring downstream systems receive valid data.

```python
# Every agent uses response_format=PydanticModel to enforce schema
response = await openai_client.beta.chat.completions.parse(
    model="gpt-4o",
    temperature=0,
    messages=[...],
    response_format=ExtractedTransaction,  # Pydantic model enforces JSON schema
)
# response.choices[0].message.parsed is guaranteed to match the schema
# No need for try/except JSON parsing — Azure OpenAI handles validation
```

### Pattern: Confidence-Based Routing

```python
def route_by_confidence(extraction_result: dict, threshold: float = 0.85) -> str:
    """Route extractions below confidence threshold to human review.
    
    Confidence thresholds calibrated per task:
    - Document extraction: 0.85 (high — financial data must be accurate)
    - Certificate validation: 0.80 (medium — registry check provides second verification)
    - Notice classification: 0.75 (lower — human reviews all responses anyway)
    """
    if extraction_result.get("confidence", 0) >= threshold:
        return "automated_pipeline"
    else:
        return "human_review_queue"
```

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | (required) | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_PRIMARY_DEPLOYMENT` | `gpt-4o` | Model for complex reasoning tasks |
| `AZURE_OPENAI_FAST_DEPLOYMENT` | `gpt-4o-mini` | Model for high-volume classification |
| `EXTRACTION_TEMPERATURE` | `0` | Temperature for document extraction (deterministic) |
| `DRAFTING_TEMPERATURE` | `0.3` | Temperature for notice response drafting (slight creativity) |
| `AVALARA_ACCOUNT_ID` | (required) | Avalara AvaTax account identifier |
| `AVALARA_LICENSE_KEY` | (required) | Avalara AvaTax API license key |
| `AVALARA_SANDBOX` | `true` | Use sandbox environment for testing |
| `DOC_INTELLIGENCE_ENDPOINT` | (required) | Azure Document Intelligence endpoint |
| `AI_SEARCH_ENDPOINT` | (required) | Azure AI Search endpoint for tax rules RAG |
| `AI_SEARCH_INDEX` | `tax-rules` | Index name for tax rules knowledge base |
| `CONFIDENCE_THRESHOLD_EXTRACTION` | `0.85` | Minimum confidence for automated document processing |
| `CONFIDENCE_THRESHOLD_CERTIFICATE` | `0.80` | Minimum confidence for certificate auto-validation |
| `CONFIDENCE_THRESHOLD_NOTICE` | `0.75` | Minimum confidence for notice auto-classification |
| `FILING_APPROVAL_REQUIRED` | `true` | Require human approval before filing (should always be true in production) |
| `MAX_RETRIES_TAX_ENGINE` | `3` | Max retries for Avalara/Vertex API failures |
| `MAX_RETRIES_LLM` | `3` | Max retries for Azure OpenAI API failures |

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_certificate_validation.py
import pytest
from src.agents.certificate_agent import CertificateValidationAgent, ExtractedCertificate


def test_expired_certificate_flagged():
    """Structural validation catches expired certificates without LLM."""
    agent = CertificateValidationAgent.__new__(CertificateValidationAgent)
    cert = ExtractedCertificate(
        certificate_type="resale",
        issuing_state="CA",
        purchaser_name="Test Corp",
        purchaser_address={"line1": "123 Main St", "city": "LA", "region": "CA", "postalCode": "90001", "country": "US"},
        purchaser_tax_id="123-456-789",
        exemption_reason="Resale",
        effective_date="2023-01-01",
        expiration_date="2024-12-31",  # Expired
        signature_present=True,
        confidence=0.95,
    )
    issues = agent._validate_structure(cert)
    assert any("expired" in issue.lower() for issue in issues)


def test_missing_signature_flagged():
    """Missing signature triggers review regardless of confidence."""
    agent = CertificateValidationAgent.__new__(CertificateValidationAgent)
    cert = ExtractedCertificate(
        certificate_type="resale",
        issuing_state="TX",
        purchaser_name="Test Corp",
        purchaser_address={"line1": "456 Oak Ave", "city": "Austin", "region": "TX", "postalCode": "78701", "country": "US"},
        purchaser_tax_id="32-123456789",
        exemption_reason="Resale",
        effective_date="2025-01-01",
        expiration_date=None,
        signature_present=False,  # Missing
        confidence=0.95,
    )
    issues = agent._validate_structure(cert)
    assert any("signature" in issue.lower() for issue in issues)
```

### Integration Tests

```python
# tests/integration/test_tax_calculation.py
import pytest
from src.tools.tax_engine import AvalaraTaxEngine, TaxCalculationRequest, TaxLineItem


@pytest.mark.asyncio
async def test_avalara_sandbox_calculation():
    """Verify tax calculation against Avalara sandbox with known jurisdiction."""
    engine = AvalaraTaxEngine(
        account_id="test_account",
        license_key="test_key",
        sandbox=True,
    )
    
    result = await engine.calculate_tax(
        TaxCalculationRequest(
            company_code="TEST",
            transaction_type="SalesInvoice",
            customer_code="CUST001",
            date=date(2026, 3, 15),
            ship_from_address={
                "line1": "100 Ravine Ln NE", "city": "Bainbridge Island",
                "region": "WA", "postalCode": "98110", "country": "US",
            },
            ship_to_address={
                "line1": "123 Main St", "city": "Irvine",
                "region": "CA", "postalCode": "92615", "country": "US",
            },
            lines=[TaxLineItem(
                item_code="SW001", description="Software License",
                amount=100.00, quantity=1, tax_code="SW054000",
            )],
        )
    )
    
    assert result.total_tax >= 0  # CA has sales tax on tangible goods
    assert result.total_taxable == 100.00
    assert len(result.jurisdiction_details) > 0  # Should have state + local breakdown
```

### Evaluation Tests

```python
# tests/evaluation/test_extraction_quality.py
import json
import pytest


EXTRACTION_TEST_CASES = [
    {
        "input_file": "tests/fixtures/invoice_standard.pdf",
        "expected": {
            "vendor_name": "Acme Corp",
            "invoice_number": "INV-2026-001",
            "total_amount": 5250.00,
            "line_items_count": 3,
        },
    },
    {
        "input_file": "tests/fixtures/invoice_handwritten.pdf",
        "expected": {
            "vendor_name": "Bob's Hardware",
            "min_confidence": 0.5,  # Expect lower confidence on handwritten
        },
    },
]


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", EXTRACTION_TEST_CASES)
async def test_document_extraction_accuracy(test_case, extraction_agent):
    """Evaluate extraction accuracy against labeled test documents."""
    with open(test_case["input_file"], "rb") as f:
        result = await extraction_agent.extract_from_document(f.read(), test_case["input_file"])
    
    expected = test_case["expected"]
    if "vendor_name" in expected:
        assert result.vendor_name == expected["vendor_name"], f"Vendor mismatch: {result.vendor_name}"
    if "total_amount" in expected:
        assert abs(result.total_amount - expected["total_amount"]) < 0.01
    if "line_items_count" in expected:
        assert len(result.line_items) == expected["line_items_count"]
    if "min_confidence" in expected:
        assert result.confidence >= expected["min_confidence"]


@pytest.mark.asyncio
async def test_notice_classification_accuracy(notice_agent):
    """Evaluate notice classification against labeled test set."""
    test_notices = json.load(open("tests/fixtures/notice_test_set.json"))
    
    correct = 0
    for case in test_notices:
        with open(case["file"], "rb") as f:
            result = await notice_agent.triage_notice(f.read())
        
        if result["classification"]["notice_type"] == case["expected_type"]:
            correct += 1
        if result["classification"]["urgency"] == case["expected_urgency"]:
            correct += 1
    
    accuracy = correct / (len(test_notices) * 2)  # 2 checks per notice
    assert accuracy >= 0.85, f"Notice classification accuracy {accuracy:.1%} below 85% threshold"
```

---

## Monitoring & Observability

| What to Monitor | Tool / Method | Alert Threshold |
|-----------------|--------------|-----------------|
| **Tax engine API latency** | Application Insights dependency tracking | p95 > 500ms (Avalara benchmark: 15ms avg) |
| **LLM extraction accuracy** | Custom metric: human override rate on auto-processed documents | Override rate > 15% in 24h window |
| **Filing deadline proximity** | Azure Logic Apps scheduled check against filing calendar | Any jurisdiction with < 3 days to deadline and unfiled return |
| **Token usage** | Azure OpenAI usage metrics | Daily spend > 2x 30-day average |
| **Certificate expiry** | Scheduled scan of certificate store | Any certificate expiring within 30 days |
| **Notice response SLA** | Custom metric: time from receipt to classification | Classification > 4 hours after receipt |

---

## Common Pitfalls & Mitigations

| Pitfall | Mitigation |
|---------|------------|
| LLM hallucinating tax rates or amounts | Never use LLM for calculation — all math goes through deterministic tax engine (Avalara/Vertex). LLM only handles language tasks. |
| Stale tax rates in cached lookups | Cache invalidation keyed on jurisdiction + effective date. Subscribe to Avalara/Vertex rate change notifications. |
| OCR errors on poor-quality certificate scans | Low confidence triggers human review. Require minimum DPI/resolution on uploads. Fallback to manual entry for sub-threshold quality. |
| Prompt injection via uploaded documents | Input sanitization on all document text before LLM processing. Azure OpenAI content filters enabled. System prompts instruct extraction-only behavior. |
| Filing portal changes breaking automation | Playwright selectors isolated per jurisdiction in config. Automated screenshot comparison detects portal UI changes. Fallback to e-filing API where available. |
| Rate limit exhaustion during month-end filing burst | Azure OpenAI PTU provisioning for predictable peak capacity. Queue-based processing with backpressure. Tier classification tasks to GPT-4o-mini. |

---

## Rollback Plan

1. **Disable automated filing**: Set `FILING_APPROVAL_REQUIRED=true` (should already be true) and pause the Filing Agent. Returns continue to be prepared but not submitted.
2. **Revert to manual preparation**: Disable the Return Preparation Agent. Tax team uses ERP-exported data with traditional tax software for return preparation.
3. **Preserve tax engine integration**: The deterministic tax calculation layer (Avalara/Vertex) operates independently of the LLM agents and can continue serving real-time transaction tax without disruption.
4. **Export audit trail**: All agent decisions, calculations, and filings are logged in Cosmos DB with full provenance. Export for manual audit if needed.
5. **Gradual re-enablement**: Re-enable agents one at a time (document extraction first, then certificate validation, then return preparation) with increased confidence thresholds during ramp-up.
