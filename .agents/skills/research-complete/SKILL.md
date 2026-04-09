---
name: research-complete
description: >-
  Takes an existing use case at 'research' status and produces the full
  solution-design.md, implementation-guide.md, evaluation.md, and
  references.md with real-world AI architecture patterns, code, and metrics.
  Use when the user wants to detail a use case, complete research, fill in
  the remaining files, expand a use case, or says 'detail next', 'complete
  research', 'fill in solution design', 'expand use case'. Also trigger when
  the user references a specific UC-NNN and asks for the full write-up. Do
  NOT use for creating new use cases — use the `research-new` skill instead.
---

# Detail an Existing Use Case

## Quick Reference

| Step | Action | Output |
|------|--------|--------|
| 1. Find target | First `research` row in README.md index | Use case folder path |
| 2. Read brief | Read use-case.md | Problem understanding |
| 3. Read templates | Read all 4 templates in `_templates/` | Structure reference |
| 4. Research | Extensive web search for real implementations | Sources and patterns |
| 5. Write files | Populate 4 files with AI-focused content | Completed deliverables |
| 6. Update status | Change `research` → `detailed` in README.md + use-case.md | Updated index |

## File Emphasis

| File | Focus | The reader wants to understand... |
|------|-------|-----------------------------------|
| solution-design.md | HOW the AI solves the problem | Agent pattern, LLM role, tools, prompts, human-in-the-loop |
| implementation-guide.md | The AI integration code | Agent definition, tool implementations, orchestration, evaluation |
| evaluation.md | What worked and what didn't | Real metrics, failure modes, lessons learned, ROI |
| references.md | Every source cited | Case studies, vendor docs, repos, talks |

---

## Workflow

### Step 1 — Find the next target

Read `docs/use-cases/README.md` and find the FIRST row in the Use Case Index table with status `research`. If no rows have status `research`, report "No use cases pending research completion" and stop.

### Step 2 — Read the research brief

Navigate to that use case's folder (e.g., `docs/use-cases/{category-dir}/UC-NNN-slug/`) and read `index.md`. Understand the problem, domain, constraints, and success criteria. This is the research brief.

### Step 3 — Read the templates

Read all 4 templates in `.agents/templates/` for structure reference:
- `solution-design.md`
- `implementation-guide.md`
- `evaluation.md`
- `references.md`

### Step 4 — Research

Search the web extensively for:
- How real companies actually solved this problem with AI
- Which agent patterns they chose and WHY (single-agent, multi-agent, RAG, hybrid)
- Which LLM frameworks they used (Semantic Kernel, LangGraph, CrewAI, Azure AI Foundry, etc.) and why
- How the AI connects to the domain-specific systems (the integration seam)
- Prompt engineering approaches and tool definitions that made it work
- What failed, what surprised them, what they'd do differently
- Published metrics and ROI from real deployments
- Case studies, blog posts, conference talks, GitHub repos

### Step 5 — Populate the 4 files

Use the templates for structure but shift the emphasis per the File Emphasis table above. Replace every placeholder — no `{curly brace}` placeholders may remain.

#### solution-design.md

Place file at `docs/use-cases/{category-dir}/UC-NNN-slug/solution-design.md`. Emphasize:
- **Agent pattern** — Which pattern (ReAct, plan-and-execute, multi-agent orchestrator-worker, RAG pipeline, hybrid) and WHY it fits this problem. Most important section.
- **LLM role** — What the LLM does at each step: extraction, reasoning, classification, generation, decision-making. Be specific about which steps need AI and which don't.
- **Tool/function design** — What tools the agent calls, what they return, how they connect to domain systems. This is where AI meets the real world.
- **Prompt strategy** — System prompts, few-shot examples, chain-of-thought, structured output schemas. Include actual prompt snippets where possible.
- **Human-in-the-loop** — Where humans stay in the loop, what triggers escalation, how confidence thresholds are set.
- **Data flow through the AI** — Clear diagram showing what data enters the LLM, what comes out, what happens next.
- Keep infra sections minimal — just name the services, don't elaborate.
- Include Jekyll front matter at the top (layout: use-case-detail, etc.)

#### implementation-guide.md

Place file at `docs/use-cases/{category-dir}/UC-NNN-slug/implementation-guide.md`. Emphasize:
- **LLM connection and configuration** — Model selection, temperature, token limits, structured output setup.
- **Agent definition** — Actual agent code: system prompt, tool bindings, orchestration logic. Use real framework APIs (e.g., `ChatCompletionAgent()`, `StateGraph()`, `kernel.add_plugin()`).
- **Tool implementations** — Functions the agent calls to interact with domain systems. Show the AI-to-real-world interface.
- **Prompt templates** — Real prompt text showing domain knowledge injection, output format enforcement, edge case handling.
- **Orchestration flow** — How multiple steps/agents coordinate: state management, handoffs, retry logic.
- **Evaluation and testing of AI quality** — How to measure if AI output is correct (AI-specific, not generic unit tests).
- Skip or minimize: Dockerfiles, CI/CD, monitoring dashboards, project scaffolding, infra setup.
- Include Jekyll front matter at the top (layout: use-case-detail, etc.)

#### evaluation.md

Place file at `docs/use-cases/{category-dir}/UC-NNN-slug/evaluation.md`. Emphasize:
- Real metrics from published case studies (with citations)
- Where the AI excels vs. where it still struggles
- Failure modes specific to the AI approach (hallucination, edge cases, confidence calibration)
- Lessons learned about prompt engineering, model selection, agent patterns
- ROI calculation grounded in numbers from index.md
- What surprised teams during implementation
- Include Jekyll front matter at the top (layout: use-case-detail, etc.)

#### references.md

Place file at `docs/use-cases/{category-dir}/UC-NNN-slug/references.md`. Contents:
- Every claim in the other 3 files must be traceable here
- Prioritize: case studies, vendor docs for the AI tools used, GitHub repos with working code, conference talks
- Verify URLs are real (do not fabricate)
- Include Jekyll front matter at the top (layout: use-case-detail, etc.)

### Step 6 — Update status

In `docs/use-cases/README.md`, change the status from `research` to `detailed`. Also update the status field in `index.md` front matter and the `has_*` flags to `true` for each file you created.

---

## Gotchas

- **Focus on the AI, not the plumbing** — every section should teach how AI integration works for this problem. Infrastructure is context, not content.
- **Use REAL tools, APIs, frameworks** — nothing made up. Code snippets must use real SDK methods.
- **Prioritize Azure-first** but always mention open-source alternatives.
- **Every metric must cite a source** in references.md. If real data isn't available, say "estimated" and explain the basis.
- **Do not modify index.md content** beyond updating the status field and has_* flags in front matter.
- **All detail files go in the same folder as index.md** (e.g., `docs/use-cases/{category-dir}/UC-NNN-slug/`). Each must have Jekyll front matter.
- **Only edit README.md status** (except for creating the detail files).
- **No `{curly brace}` placeholders may remain** in any output file.
