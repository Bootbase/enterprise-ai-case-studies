# Reusable Prompts for Use Case Research

## Quick Reference

| Prompt | What it does |
|--------|-------------|
| [Research Next](#research-next-use-case) | Find and document a new use case (use-case.md only) |
| [Research Specific](#research-a-specific-use-case) | Document a specific use case you already have in mind |
| [Detail Existing](#detail-an-existing-use-case) | Fill in solution-design, implementation-guide, evaluation, and references for an existing `research` entry |

---

## Research Next Use Case

Discovers and documents a new use case automatically. Reads the index to avoid duplicates.

```
Read use-cases/README.md and use-cases/_templates/use-case.md.

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
- Use the LOWEST available ID in that category's range.
- Create the folder: use-cases/{category}/UC-{NNN}-{slug}/

Step 4 — Write use-case.md:
- Use the template in use-cases/_templates/use-case.md.
- Fill in EVERY section with concrete, researched content:
  real companies, real numbers, real pain points, real systems.
- Set status to `research`.
- No {placeholder} text may remain.

Step 5 — Update index:
- Add a row to the Use Case Index table in use-cases/README.md,
  matching the existing table format exactly.

Step 6 — Do NOT create solution-design.md, implementation-guide.md,
evaluation.md, or references.md. Only use-case.md.

Rules:
- Use REAL company names, products, tools, and metrics — not made-up ones
- Cite the source for quantitative claims inline (e.g., "700K reports/year (FDA FAERS)")
- If solid real-world data is scarce, state that explicitly and use the best available estimates
- Every template placeholder must be replaced
```

---

## Research a Specific Use Case

Use this when you already know what use case you want. Replace `{DESCRIPTION}` with a short description.

```
Read use-cases/README.md and use-cases/_templates/use-case.md.

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
- Use the LOWEST available ID in that category's range.
- Create the folder: use-cases/{category}/UC-{NNN}-{slug}/

Step 4 — Write use-case.md:
- Use the template in use-cases/_templates/use-case.md.
- Fill in EVERY section with concrete, researched content.
- Set status to `research`.
- No {placeholder} text may remain.

Step 5 — Update index:
- Add a row to the Use Case Index table in use-cases/README.md.

Step 6 — Do NOT create solution-design.md, implementation-guide.md,
evaluation.md, or references.md. Only use-case.md.

Rules:
- Use REAL company names, products, tools, and metrics — not made-up ones
- Cite the source for quantitative claims inline
- Every template placeholder must be replaced
```

---

## Detail an Existing Use Case

Picks up an existing `research` entry and fills in the remaining files.

```
Read use-cases/README.md.

Step 1 — Select:
- Find the FIRST row in the Use Case Index table with status `research`.
- Read its use-case.md to understand the problem.

Step 2 — Research deeper:
- Search the web for architecture patterns, real implementations,
  framework choices, code examples, and reported metrics for this use case.
- Prioritize Azure-compatible and open-source solutions.

Step 3 — Populate remaining files using templates in use-cases/_templates/:
- solution-design.md — Architecture, component diagram, agent pattern
  selection with rationale, integration points, tool/framework choices
  with justification, security considerations, cost estimate.
- implementation-guide.md — Step-by-step build guide with real code
  snippets, project structure, configuration, testing strategy,
  monitoring setup. Use real framework APIs (not pseudocode).
- evaluation.md — Expected/reported metrics, ROI calculation, known
  limitations, lessons learned from real implementations.
- references.md — All case studies, documentation, repos, and talks
  found during research. Every claim should be traceable.

Step 4 — Update status:
- In use-case.md, change status from `research` to `detailed`.
- In use-cases/README.md, update the same row's status to `detailed`.

Rules:
- Use REAL tools, APIs, and frameworks — not made-up names
- Include actual code snippets from real framework SDKs
- Cite sources for all claims about company implementations
- If real-world examples are scarce, say so explicitly
- Focus on Azure-first but include open-source alternatives
- Every template placeholder must be replaced
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
