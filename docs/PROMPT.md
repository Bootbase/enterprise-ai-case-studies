# Reusable Prompts for Use Case Research

## Quick Reference

| Prompt | What it does |
|--------|-------------|
| [Research Next](#research-next-use-case) | Find and document a new use case (index.md only) |
| [Research Specific](#research-a-specific-use-case) | Document a specific use case you already have in mind |
| [Detail Existing](#detail-an-existing-use-case) | Fill in solution-design, implementation-guide, evaluation, and references for an existing `research` entry |

---

## Research Next Use Case

Discovers and documents a new use case automatically. Reads the index to avoid duplicates.

```
Read `docs/use-cases/README.md` and `.agents/templates/use-case.md`.

Step 1 — Inventory:
- Parse the Use Case Index table in README.md.
- List every existing use case by ID, title, category, and industry.
- Identify which categories and industries are already covered.

Step 2 — Discover:
- Search the web for real-world agentic AI use cases that are DISTINCTLY
  different from every existing entry — different problem domain, different
  industry, or a fundamentally different operational angle.
- Prioritize use cases with published production deployments, concrete
  metrics, and named companies.
- Avoid overlapping with any existing entry's problem space.

Step 3 — Assign ID & Category:
- Pick the correct category from README.md's category table.
- Use the LOWEST available ID in that category's range:
  001-099 (Document Processing), 100-199 (Customer Service),
  200-299 (Workflow Automation), 300-399 (Code & DevOps),
  400-499 (Knowledge Management), 500-999 (Industry-Specific).
- Create the folder: docs/use-cases/UC-{NNN}-{slug}/

Step 4 — Write index.md:
- Use the template in `.agents/templates/use-case.md`.
- Keep the section order exactly as written in the template.
- Write a concise business brief, not a whitepaper.
- Target roughly 700–1,200 words excluding front matter and tables.
- Fill in every section with concrete, researched content:
  real companies, real numbers, real pains, real systems.
- Set status to `research`.
- No {placeholder} text may remain.

Step 5 — Update index:
- Add a row to the Use Case Index table in docs/use-cases/README.md,
  matching the existing table format exactly.

Step 6 — Do NOT create solution-design.md, implementation-guide.md,
evaluation.md, or references.md. Only index.md.

Rules:
- Use real company names, products, tools, and metrics — not made-up ones.
- Keep the tone direct and business-oriented; avoid hype and generic AI phrasing.
- Cite the source for quantitative claims inline where helpful.
- Include `3–6` rows in the `Evidence Base` section.
- If real-world data is scarce, say so directly and use the best available estimate.
- Every template placeholder must be replaced.
- If you include any URL, make it a clickable Markdown link.
- Verify each external URL by opening it before you keep it in the document.
- Never link to a local artifact that does not exist yet.
```

---

## Research a Specific Use Case

Use this when you already know what use case you want. Replace `{DESCRIPTION}` with a short description.

```
Read `docs/use-cases/README.md` and `.agents/templates/use-case.md`.

Research and document the following agentic AI use case:

"{DESCRIPTION}"

Step 1 — Verify uniqueness:
- Parse the Use Case Index table in README.md.
- Confirm this use case does not substantially overlap with any existing entry.
- If it does overlap, stop and explain the conflict.

Step 2 — Research:
- Search the web for real-world implementations. Find companies that have
  done this, the tools they used, and the results they achieved.

Step 3 — Assign ID & Category:
- Pick the correct category from README.md's category table.
- Use the LOWEST available ID in that category's range:
  001-099 (Document Processing), 100-199 (Customer Service),
  200-299 (Workflow Automation), 300-399 (Code & DevOps),
  400-499 (Knowledge Management), 500-999 (Industry-Specific).
- Create the folder: docs/use-cases/UC-{NNN}-{slug}/

Step 4 — Write index.md:
- Use the template in `.agents/templates/use-case.md`.
- Keep the section order exactly as written in the template.
- Write a concise business brief, not a whitepaper.
- Fill in every section with concrete, researched content.
- Set status to `research`.
- No {placeholder} text may remain.

Step 5 — Update index:
- Add a row to the Use Case Index table in docs/use-cases/README.md.

Step 6 — Do NOT create solution-design.md, implementation-guide.md,
evaluation.md, or references.md. Only index.md.

Rules:
- Use real company names, products, tools, and metrics — not made-up ones.
- Keep the tone direct and business-oriented; avoid hype and generic AI phrasing.
- Cite the source for quantitative claims inline.
- Every template placeholder must be replaced.
- If you include any URL, make it a clickable Markdown link.
- Verify each external URL by opening it before you keep it in the document.
- Never link to a local artifact that does not exist yet.
```

---

## Detail an Existing Use Case

Picks up an existing `research` entry and fills in the remaining files.

```
Read `docs/use-cases/README.md`.

Step 1 — Select:
- Find the FIRST row in the Use Case Index table with status `research`.
- Read its index.md to understand the problem.

Step 2 — Research deeper:
- Search the web for real implementations, framework choices, integration seams,
  official technical documentation, and reported metrics for this use case.
- Prioritize primary sources and official documentation.
- Prefer Azure-compatible and open-source solutions when the evidence supports them.

Step 3 — Populate remaining files using templates in `.agents/templates/`:
- `solution-design.md` — Operating model, architecture, AI boundaries,
  integration seams, control model, and key design decisions.
- `implementation-guide.md` — Delivery blueprint, stack choices, core contracts,
  orchestration pattern, prompt/guardrail pattern, integration notes,
  evaluation harness, and rollout notes. Use real framework APIs, not pseudocode.
- `evaluation.md` — Published evidence, explicit assumptions, scenario economics,
  risks, rollout KPIs, and open questions. Label `published` vs `estimated`.
- `references.md` — Annotated source register plus claim map. Every meaningful
  claim should be traceable.

Step 4 — Update status:
- In index.md, change status from `research` to `detailed`.
- In index.md front matter, set has_solution_design, has_implementation_guide,
  has_evaluation, and has_references to true.
- In docs/use-cases/README.md, update the same row's status to `detailed`.

Rules:
- Use real tools, APIs, and frameworks — not made-up names.
- Keep the split between files clean. Do not repeat the same content across tabs.
- Include only focused code snippets from real SDKs or frameworks.
- Cite sources for all claims about deployments and metrics.
- If real-world examples are scarce, say so explicitly and narrow the recommendation.
- Keep the tone direct and business-oriented; avoid generic AI phrasing.
- Focus on Azure-first but include open-source alternatives where useful.
- Every template placeholder must be replaced.
- All detail files must be in `docs/use-cases/{category-dir}/UC-NNN-slug/`.
- Each file must include Jekyll front matter.
- Every URL shown in markdown must be a clickable Markdown link, not raw URL text.
- Verify each cited external URL by opening it before you keep it.
- Never publish a link to a local file unless that file already exists.
```

---

## Variations

Append any of these to the prompts above.

### Specific Industry Focus

```
Focus specifically on the {INDUSTRY} industry. Find implementations from
{INDUSTRY} companies and address {INDUSTRY}-specific regulations and constraints.
```

### Compare Multiple Approaches

```
In solution-design.md, design TWO alternative architectures and compare them
in the "Alternatives Considered" section. Recommend one with clear reasoning.
```

### Specific Tech Stack

```
The solution MUST use: {list specific tools, e.g., "Semantic Kernel, Azure OpenAI,
Azure AI Search, AKS"}. Design the architecture around this stack.
```
