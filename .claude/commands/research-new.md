---
description: >-
  Discovers and documents a new agentic AI use case by researching real-world
  deployments, then creates use-case.md with concrete companies, metrics, and
  systems. Use when the user wants to add a new use case, find a new AI use
  case, research a new enterprise AI scenario, or says 'new use case', 'add
  use case', 'discover use case', 'find another use case'. Also trigger when
  the user provides a topic and wants it turned into a use case entry. Do NOT
  use for detailing an existing use case — use /research-complete instead.
---

# Discover & Document a New Use Case

## Quick Reference

| Step | Action | Output |
|------|--------|--------|
| 1. Inventory | Parse README.md index | List of existing use cases |
| 2. Discover | Web search for distinct real-world AI deployments | Candidate use case |
| 3. Assign ID | Pick category + lowest available ID | Folder path |
| 4. Write | Populate use-case.md from template | Completed use-case.md |
| 5. Index | Add row to README.md table | Updated index |

## Workflow

### Step 1 — Inventory

Read `use-cases/README.md` and `use-cases/_templates/use-case.md`.

Parse the Use Case Index table. List every existing use case by ID, title, category, and industry. Identify which categories and industries are already covered.

### Step 2 — Discover

Search the web for real-world agentic AI use cases that are DISTINCTLY different from every existing entry — different problem domain, different industry, or a fundamentally different operational angle.

Prioritize use cases with published production deployments, concrete metrics, and named companies. Avoid overlapping with any existing entry's problem space.

### Step 3 — Assign ID & Category

Pick the correct category from README.md's category table. Use the LOWEST available ID in that category's range. Create the folder: `use-cases/{category}/UC-{NNN}-{slug}/`

### Step 4 — Write use-case.md

Use the template in `use-cases/_templates/use-case.md`. Fill in EVERY section with concrete, researched content: real companies, real numbers, real pain points, real systems. Set status to `research`. No `{placeholder}` text may remain.

### Step 5 — Update index

Add a row to the Use Case Index table in `use-cases/README.md`, matching the existing table format exactly.

## Gotchas

- **Do NOT create solution-design.md, implementation-guide.md, evaluation.md, or references.md** — only use-case.md. Use `/research-complete` later to populate those.
- **Use REAL company names, products, tools, and metrics** — not made-up ones. Cite sources inline (e.g., "700K reports/year (FDA FAERS)").
- **If solid real-world data is scarce**, state that explicitly and use the best available estimates.
- **Every template placeholder must be replaced** — no `{curly brace}` text may remain in the output.
