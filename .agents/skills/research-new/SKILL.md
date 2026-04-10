---
name: research-new
description: >-
  Discovers and documents a new enterprise AI use case from real-world
  evidence, then creates the research-stage `index.md` brief. Use when the
  user wants to add a new use case, find a new AI use case, research a new
  enterprise AI scenario, or says 'new use case', 'add use case', 'discover
  use case', 'find another use case'. Do NOT use for detailing an existing use
  case — use `research-complete` instead.
---

# Discover And Document A New Use Case

## Goal

Produce a concise research-stage `index.md` that works as a business brief:

- grounded in named deployments and real metrics
- short enough to scan quickly
- specific enough to justify why the use case deserves a full detailed write-up later

The output is not a whitepaper. It is the decision-ready brief that the rest of the workflow builds on.

## Required Inputs

Read:

- `docs/use-cases/README.md`
- `.agents/templates/use-case.md`

Follow the section order in the template exactly. Do not invent extra top-level sections.

## Workflow

### Step 1 — Inventory

Parse the Use Case Index table in `docs/use-cases/README.md`.

- List the existing use cases by ID, title, category, and industry.
- Identify categories and industries that are already crowded.
- Avoid adding a use case that materially overlaps with an existing problem statement.

### Step 2 — Discover

Search for a distinct enterprise AI use case with real deployment evidence.

Prioritize:

- named companies or public-sector organizations
- production deployments or clearly documented pilots
- concrete metrics, operating constraints, and system details
- use cases that fit the repository goal: end-to-end enterprise workflows, not generic chatbot ideas

Avoid:

- speculative future use cases
- vendor feature pages with no customer evidence
- categories already covered unless the operational problem is clearly different

### Step 3 — Assign ID And Category

Pick the correct category from the README table and use the lowest available ID in that range:

- `001–099` Document Processing
- `100–199` Customer Service
- `200–299` Workflow Automation
- `300–399` Code & DevOps
- `400–499` Knowledge Management
- `500–999` Industry-Specific

Create:

`docs/use-cases/{category-dir}/UC-{NNN}-{slug}/index.md`

### Step 4 — Write `index.md`

Use `.agents/templates/use-case.md`.

The brief must:

- stay within the template section order exactly
- be concise: target roughly `700–1,200` words excluding front matter and tables
- use direct business language, not hype, not generic AI phrasing
- include real source cues inline for quantitative claims where helpful
- include an `Evidence Base` table with `3–6` high-value sources or deployments
- keep numbered workflows to `4–6` steps unless the domain genuinely requires more
- keep friction lists and scope lists short and specific

### Step 5 — Update The Index

Add one row to `docs/use-cases/README.md`, matching the existing table format exactly.

### Step 6 — Verify Links Before Finishing

- If you include any URL in the generated markdown, it must be a clickable Markdown link. Do not leave bare URL text in the document.
- Only link to local repository artifacts that already exist at commit time. Do not add "coming soon" file links.
- Before you keep an external URL, open it and confirm it resolves to the content you are citing. Replace redirected or stale URLs with the final working page.
- If a section does not need a link, omit the link instead of guessing.

## Writing Rules

- Prefer short declarative sentences.
- Use concrete nouns: team names, systems, documents, regulators, transaction types.
- Do not write like a model explaining itself.
- Do not use rhetorical framing such as "the key insight is", "the market is telling us", or "this is not X, it is Y".
- Do not pad with exhaustive examples once the point is clear.
- If a number is estimated or directional, say so.
- Keep links sparse. Use them only where they help the reader reach a real supporting artifact or source.

## Output Contract

The generated `index.md` must include these top-level headings exactly:

- `## Problem Statement`
- `## Business Case`
- `## Current Workflow`
- `## Target State`
- `## Stakeholders`
- `## Constraints`
- `## Evidence Base`
- `## Scope Boundaries`

No `{placeholder}` text may remain.

## Gotchas

- Create only `index.md`. Do not create detailed artifacts.
- Use real company names, tools, and metrics. Never fabricate them.
- Keep the brief readable on the site. If a section feels like an appendix, cut it.
- The goal is a high-signal brief that earns a future `research-complete`, not a complete solution design.
- A dead link is worse than no link. If you cannot verify a URL or local artifact, do not link it.
