---
layout: use-case
title: "Autonomous Knowledge Synthesis and Research Copilot for Management Consultants with Agentic AI"
uc_id: "UC-400"
category: "Knowledge Management"
category_dir: "knowledge-management"
category_icon: "book-open"
industry: "Professional Services (Management Consulting, Strategy, Audit & Advisory)"
complexity: "High"
status: "research"
summary: "The product of a management consulting firm is its knowledge — hundreds of thousands of past engagement decks and research accumulated over decades. Yet junior consultants spend 30-50% of billable time on manual research, slide reformatting, and 'rediscovery' of work that already exists. McKinsey Lilli demonstrates that an agentic system can reclaim ~30% of research time, saving $12M/month across the firm."
slug: "UC-400-knowledge-synthesis-consulting"
has_solution_design: false
has_implementation_guide: false
has_evaluation: false
has_references: false
permalink: /use-cases/UC-400-knowledge-synthesis-consulting/
---

## Problem Statement

The product of a management consulting firm is its knowledge: hundreds of thousands of past engagement decks, expert-interview transcripts, proprietary research, market models, industry primers, and benchmarking data accumulated over decades. Yet on any given Monday, a freshly staffed consultant on a new engagement begins by emailing partners asking "has anyone done work on X?", searching a stale internal knowledge base with keyword matching, and re-creating analyses that already exist somewhere in the firm. Industry studies put the share of a junior consultant's time spent on manual research, slide reformatting, and "rediscovery" at 30-50% of billable hours — labor that produces no incremental client value and burns out the firm's talent pipeline. The Big Three (McKinsey, BCG, Bain) and Big Four (Deloitte, EY, PwC, KPMG) employ between 30,000 and 460,000 knowledge workers each whose productivity is bottlenecked by exactly this problem. McKinsey's response — Lilli, launched firmwide in July 2023 and now used by 75% of its ~43,000 employees monthly — has demonstrated that an agentic system layered over the firm's curated knowledge corpus can reclaim ~30% of research time, save 50,000+ hours/month across the firm, and redeploy approximately $12M/month of consultant labor toward higher-value work. BCG's GENE platform, Bain's Sage, and Deloitte's PairD/Zora pursue the same outcome but with weaker public metrics and documented hallucination incidents that have surfaced as far as senior-partner review. The use case sits at the intersection of enterprise RAG, multi-agent orchestration over proprietary knowledge corpora, and the most tightly-confidential information environment in business — where a single leaked client document is a career-ending event.

## Business Impact

| Dimension       | Description                               |
|-----------------|-------------------------------------------|
| **Cost**        | Junior consultant fully-loaded cost is $200-400/hour (US/EU); a single 8-week engagement team of 4-6 consultants represents $1.5-3M of labor. McKinsey reports Lilli has shifted ~$12M of monthly labor from research to higher-value synthesis. Across the global consulting industry (~$300B market in 2024 per Statista), even a 10% productivity gain on knowledge work represents $15-30B/year of redeployable capacity. |
| **Time**        | Building a project scoping deck used to take ~2 days at McKinsey and now takes under 3 hours with Lilli. Average Lilli session saves ~6 minutes versus manual lookup; 17 prompts/week/user across 32,000 active users compounds to 50,000+ hours reclaimed per month. The Harvard-BCG randomized field experiment with 758 consultants found AI users completed 12.2% more tasks, 25.1% faster, with 40%+ higher quality on the tasks AI was suited to. |
| **Error Rate**  | Manual research is prone to citation errors, missed prior work, and stale market data. At the same time, generative AI in consulting has documented failure modes: BCG and other firms have publicly acknowledged "plausible-but-wrong" market-sizing outputs reaching senior-partner review, and Deloitte reports up to 25% of project budgets now going to prompt engineering and validation overhead. Hallucination rates on long-tail proprietary knowledge questions remain a critical risk. |
| **Scale**       | McKinsey Lilli: 100,000+ proprietary documents indexed, 40+ curated knowledge sources, 500,000+ prompts per month, ~32,000 monthly active users (75% of ~43,000 employees). BCG: 18,000+ custom GPTs across ~32,000 employees. Bain: 19,000+ custom GPTs across ~19,000 employees. Deloitte PairD: rolled out to 75,000+ UK employees and expanding firmwide (~460,000 globally). |
| **Risk**        | Client confidentiality breach is the highest-severity risk in professional services — a single leaked NDA-covered document can terminate a multi-year client relationship and trigger litigation. M&A advisory teams operate under information-barrier ("Chinese wall") regimes that make any cross-engagement knowledge sharing legally hazardous. AI hallucinations in client deliverables are career-ending for individual consultants and reputation-damaging for the firm. EU AI Act and US sector regulations add documentation and explainability obligations for any system shaping client recommendations. |

## Current Process (Before AI)

1. New engagement starts: a partner staffs a team of 4-6 consultants from the firm's bench
2. The engagement manager defines the scoping question (e.g., "growth strategy for a mid-cap industrial chemicals company in Southeast Asia")
3. Each consultant individually starts a research workstream: market sizing, competitor mapping, regulatory landscape, customer dynamics
4. For each workstream, the consultant searches the internal knowledge management system (typically a SharePoint/Documentum/proprietary KB) using keyword search
5. The consultant emails 3-10 partners and senior associates asking "has anyone done work on adjacent topics?" and waits 24-72 hours for responses
6. The consultant downloads and skims dozens of prior project decks, identifying reusable frames, charts, and benchmarks (with names and client identifiers redacted to honor confidentiality)
7. The consultant pulls market data from licensed third-party sources (Capital IQ, Gartner, IBISWorld, Euromonitor, EIU, expert networks like GLG)
8. The consultant synthesizes findings into draft slides, manually re-formatting charts to firm visual standards
9. The engagement manager reviews drafts, identifies gaps, and sends the consultant back for additional research
10. The partner reviews the synthesized deliverable, often demanding additional benchmarks or rephrasings 24 hours before the client meeting
11. Final deck is locked, watermarked, and delivered; the underlying research becomes part of the firm's KB if (and only if) someone manually files it post-engagement

### Bottlenecks & Pain Points

- **Rediscovery tax**: Consultants routinely re-create analyses that already exist somewhere in the firm because keyword search cannot match conceptual queries to past work, and tacit knowledge of "who did what" lives in partner heads
- **Asymmetric expertise access**: Senior partners are the firm's index — junior consultants depend on getting partner attention to find relevant precedent work, creating a hierarchical bottleneck
- **Slide reformatting drudgery**: Industry estimates put 20-30% of consultant time on PowerPoint mechanics rather than analysis
- **Stale knowledge base**: Internal KBs decay as engagement teams fail to file final artifacts; what is filed is poorly tagged
- **Information barriers vs. knowledge sharing tension**: Compliance walls exist for legitimate reasons but suppress legitimate cross-engagement learning even where no conflict exists
- **Talent attrition**: 20-30% annual attrition at top consulting firms means tribal knowledge walks out the door constantly; the firm's IP is increasingly trapped in former employees' memories
- **Non-billable overhead**: Travel booking, expense management, calendar coordination, and meeting note-taking consume 5-10 hours/week per consultant of non-billable time
- **Onboarding velocity**: New hires take 6-12 months to become productive because they must learn the firm's tacit knowledge networks rather than its explicit ones

## Desired Outcome (After AI)

An agentic AI platform — modeled on McKinsey Lilli's architecture and 2024-2025 "Agents-at-Scale" framework — that serves as the firm's knowledge operating system. Consultants converse with the platform in natural language to: discover relevant prior work across the firm's full corpus (subject to information-barrier permissions), synthesize multi-source research with citations, draft scoping decks and benchmarking analyses, generate client-ready chart suggestions, summarize expert interviews, and offload non-billable admin tasks (calendar coordination, expense reports, meeting notes) to specialized sub-agents. Beyond a single chat interface, the platform exposes an internal "agent marketplace" where partners and practice areas publish vertical agents (industry-specific research agents, deal-comparison agents, regulatory-tracker agents, tone-of-voice review agents) built on a shared Agent Factory pipeline. Every output is fully cited to source documents, every interaction is logged for audit, and information-barrier permissions are enforced at the retrieval layer so a consultant on Engagement A literally cannot retrieve documents from Engagement B if compliance flags them as walled. The system shifts consultants from "find and reformat" to "evaluate and synthesize," compresses scoping decks from 2 days to 3 hours, and reclaims a measurable share of every consultant's week for higher-value client work.

### Success Criteria

| Metric                              | Target                                  |
|-------------------------------------|-----------------------------------------|
| Monthly active users (% of consultant headcount) | >= 70% (McKinsey Lilli benchmark: 75%) |
| Average prompts per active user per week | >= 15 (McKinsey Lilli benchmark: 17)    |
| Time saved per session              | >= 5 minutes (McKinsey Lilli benchmark: ~6 min) |
| Scoping deck production time        | < 4 hours (down from 2 days; McKinsey Lilli reports < 3 hours) |
| Time-to-first-relevant-citation     | < 30 seconds for 95% of queries          |
| Citation accuracy (no hallucinated sources) | > 99% — every cited document must exist and contain the cited content |
| Information-barrier compliance      | 100% — zero retrievals across walled engagement boundaries |
| Cross-engagement knowledge reuse rate | Measurable increase in % of decks containing previously-filed assets |
| Consultant onboarding time-to-productivity | 30-50% reduction (proxy: time to first independent client-facing deliverable) |
| Specialized agents in marketplace   | 100+ within 12 months (McKinsey reportedly has 12,000+ internal agents across business functions) |
| Cost per query (LLM + retrieval)    | < $0.10 fully loaded                    |

## Stakeholders

| Role                              | Interest                                    |
|-----------------------------------|---------------------------------------------|
| Senior Partner / Engagement Director | Faster team mobilization, higher leverage per consultant, fewer escalations to partner attention for routine research |
| Practice Area Leader              | Codify the practice's intellectual property into reusable assets and specialized agents |
| Engagement Manager                | Compress scoping and benchmarking work; spend more cycles on synthesis and client interaction |
| Junior Consultant / Analyst       | Skip the grunt work (search, reformat, expense reports) and focus on analytical reasoning |
| Chief AI Officer / Head of Generative AI | Owns the platform, agent factory pipeline, and adoption KPIs |
| Knowledge Management Officer      | Curate and govern the underlying corpus, classify documents by sensitivity and information barriers |
| Risk & Compliance / General Counsel | Enforce client confidentiality, information barriers, regulatory disclosure obligations (EU AI Act, sector regs); audit every output that touches a client deliverable |
| IT / Platform Engineering         | Integrate with internal KBs, Azure (or equivalent), identity provider, Office/PowerPoint tooling, meeting platforms |
| CISO / Information Security       | Protect proprietary IP from model training leakage, enforce data residency, manage tenant isolation |
| CFO                               | Track ROI in billable-hour terms, justify enterprise LLM contracts |
| HR / People Function              | Reframe junior consultant role from "research drone" to "AI-augmented synthesizer"; manage change anxiety |

## Constraints

| Constraint              | Detail                          |
|-------------------------|---------------------------------|
| **Data Privacy**        | All client engagement documents are NDA-covered; many are MNPI (material non-public information) under securities law; cross-border data residency requirements (EU client documents may not leave EU; financial-sector clients may require dedicated tenancy); AI must not be trained on client documents in ways that risk leakage to other tenants |
| **Latency**             | Sub-30-second response for retrieval queries during client meetings; sub-3-second response for autocomplete and quick lookups; long-running synthesis tasks (multi-source briefs) acceptable up to 5 minutes with progress indication |
| **Budget**              | At McKinsey scale (500K+ prompts/month), even $0.10/query is $50K/month in inference; multi-modal queries with document retrieval push higher; budget envelope must be justified against billable-hour productivity gains; enterprise LLM contracts (Azure OpenAI, Anthropic, Cohere) are typically negotiated at multi-million-dollar annual commitments |
| **Existing Systems**    | Must integrate with: internal SharePoint/Documentum knowledge bases; PowerPoint and Excel; Microsoft 365 / Google Workspace identity and calendar; CRM systems (Salesforce, MS Dynamics); third-party data sources (Capital IQ, Gartner, IBISWorld, Euromonitor, GLG, AlphaSense); meeting platforms (Zoom, Teams) for transcript ingestion |
| **Compliance**          | Information-barrier ("Chinese wall") enforcement at the retrieval layer — not at the chat layer — so the LLM never sees walled content; full audit trail of every prompt, retrieved document, and output; EU AI Act high-risk-system documentation; transparency obligations for any output reaching a client deliverable; sector-specific overlays (HIPAA for health clients, SEC for capital-markets work, GDPR for EU work) |
| **Scale**               | Tens of thousands of concurrent users at peak (McKinsey-scale: ~43K employees, ~32K monthly active); millions of indexed documents; thousands of new documents added per day from engagement teams; multi-region deployment for latency and residency |
| **Hallucination tolerance** | Effectively zero on factual claims that reach client deliverables — every citation must resolve to a real document containing the cited content; outputs that cannot be traced to a source must be visibly flagged as "ungrounded synthesis" |
| **IP protection**       | The corpus IS the firm's competitive advantage; embedding indices, fine-tunes, and prompt logs must be encrypted at rest and isolated from any vendor multi-tenant training pipeline |

## Scope Boundaries

### In Scope

- Conversational research assistant over the firm's curated proprietary knowledge corpus (past engagement decks, expert interview transcripts, proprietary research, market models, industry primers)
- Multi-source synthesis combining proprietary corpus with licensed third-party data (Capital IQ, Gartner, IBISWorld, Euromonitor, AlphaSense, GLG)
- Citation-backed answers with full source attribution at the paragraph level
- Multi-agent orchestration: a coordinator that decomposes complex research questions into sub-tasks routed to specialized agents (industry research, market sizing, regulatory tracking, deal comparison, tone-of-voice review)
- Internal "agent marketplace" / Agent Factory pipeline for practice areas to publish their own vertical agents
- Information-barrier-aware retrieval that enforces engagement-level access controls before any document reaches the LLM
- Audit logging of every prompt, retrieved document, model invocation, and final output
- Integration with PowerPoint/Excel for inline drafting and chart generation
- Non-billable admin offloading: meeting note generation, calendar coordination, expense report drafting (the McKinsey "Calendar Concierge" pattern, 120K bookings in six months)
- Tone-of-voice and house-style review agents for draft client deliverables
- Multi-LLM backend orchestration (mixing OpenAI, Anthropic Claude, Cohere, and open-weight models per task economics)

### Out of Scope

- Customer/client-facing chatbots (the system is internal-only; client-facing AI is a separate use case)
- Autonomous client deliverable production without human-in-the-loop partner review
- Trading, investment decision-making, or any system that takes irreversible financial actions on client capital (those are governed by separate use cases such as Bridgewater AIA Labs)
- Recruiting, performance management, and compensation decisions
- Replacement of subject-matter expertise — the system augments consultants but does not certify recommendations
- Unrestricted training of foundation models on the firm's proprietary corpus (retrieval-augmented use only; any fine-tuning is governed by separate IP-protection controls)
- Public-facing thought leadership generation without partner editorial review
- Automated client billing, contract execution, or legal document production (governed by separate use cases including UC-052 for legal due diligence)
