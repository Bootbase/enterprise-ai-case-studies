---
name: research-complete
description: >-
  Takes an existing use case at `research` status and produces the full
  detailed write-up: `solution-design.md`, `implementation-guide.md`,
  `evaluation.md`, and `references.md`. Use when the user wants to detail an
  existing use case, complete research, fill in the remaining files, or expand
  a research-stage entry. Do NOT use for creating a new use case — use
  `research-new` instead.
---

# Detail An Existing Use Case

## Goal

Turn a research-stage brief into a publishable case study that readers can learn from quickly.

The detailed output must be:

- correct enough to trust, with source traceability
- explicit about what is published fact versus design recommendation versus estimate
- business-oriented in tone
- split cleanly across files, with minimal duplication

## Required Inputs

Read:

- `docs/use-cases/README.md`
- the target `index.md`
- all four templates in `.agents/templates/`

Follow the section order in each template exactly. Do not invent extra top-level sections.

## File Responsibilities

Use the files for different jobs:

- `solution-design.md`
  Operating model, architecture, AI boundaries, integration seams, control model, and design decisions.
- `implementation-guide.md`
  Practical delivery blueprint: stack, contracts, orchestration pattern, prompts, evaluation harness, rollout notes.
- `evaluation.md`
  Published evidence, assumptions, economics, risks, rollout KPIs, and open questions.
- `references.md`
  Annotated source register plus claim map. Every meaningful claim in the other three files must be traceable here.

## Workflow

### Step 1 — Select The Target

Find the first use case in `docs/use-cases/README.md` with status `research`, unless a specific `UC-XXX` is provided as an argument.

### Step 2 — Read The Research Brief

Read that use case's `index.md` and extract:

- the business problem
- the incumbent systems
- the operating constraints
- the success metrics already implied by the brief

Do not rewrite the body of `index.md`. Later, only update the status and `has_*` flags in front matter.

### Step 3 — Research Deeply

Search for primary and high-value secondary sources covering:

- real deployments and published metrics
- specific architecture choices and integration seams
- official documentation for the AI stack and incumbent systems
- domain-specific standards, regulations, or data contracts

Prioritize:

- customer stories, case studies, official docs, public technical write-ups, standards documentation

Be cautious with:

- analyst summaries
- vendor marketing pages with no named deployment
- claims that do not distinguish pilot from production

### Step 4 — Write The Detailed Files

Use the templates exactly.

Keep the files compact enough to read on the site:

- `solution-design.md`: target `900–1,400` words
- `implementation-guide.md`: target `900–1,400` words
- `evaluation.md`: target `700–1,200` words
- `references.md`: as short as possible while still making claims traceable

#### Additional Rules For Each File

`solution-design.md`

- emphasize the business operating model, not infrastructure inventory
- explain where AI is appropriate and where deterministic logic or human review stays in charge
- include one clear system diagram

`implementation-guide.md`

- show only the code or configuration patterns that materially teach the reader something
- use real SDKs or framework APIs
- keep code snippets focused; prefer `2–3` strong snippets over many shallow ones
- do not turn this file into a scaffold dump, CI/CD guide, or Docker tutorial

`evaluation.md`

- clearly label `published` versus `estimated`
- do not invent user quotes or survey data
- do not present one company's result as if it were a universal benchmark

`references.md`

- include a source register with stable IDs such as `S1`, `S2`, `S3`
- include a claim map that points major claims or sections back to those IDs
- omit low-value source lists that are not used anywhere
- make every external source a clickable Markdown link, not a bare URL
- open every cited external URL before you keep it, and make sure it resolves to the source you are claiming
- never link to a local artifact unless that file already exists in the use-case directory

### Step 5 — Update Status

Update:

- `docs/use-cases/README.md`: `research` -> `detailed`
- target `index.md` front matter:
  - `status: detailed`
  - `has_solution_design: true`
  - `has_implementation_guide: true`
  - `has_evaluation: true`
  - `has_references: true`

## Writing Rules

- Write like an operator or architect explaining a real system to another operator or architect.
- Prefer short declarative sentences over grand framing.
- Keep claims specific and qualified.
- Separate three things clearly:
  - what a source explicitly says
  - what the case study recommends
  - what is estimated
- Avoid generic "AI writing" language, especially:
  - hype
  - repetitive scene-setting
  - abstract management phrasing with no systems or process detail
- Prefer no link over a speculative link. Every link must be real, reachable, and relevant.

## Output Contract

The generated files must include these exact top-level headings:

`solution-design.md`

- `## What This Design Covers`
- `## Recommended Operating Model`
- `## Architecture`
- `## End-to-End Flow`
- `## AI Responsibilities and Boundaries`
- `## Integration Seams`
- `## Control Model`
- `## Reference Technology Stack`
- `## Key Design Decisions`

`implementation-guide.md`

- `## Build Goal`
- `## Reference Stack`
- `## Delivery Plan`
- `## Core Contracts`
- `## Orchestration Outline`
- `## Prompt And Guardrail Pattern`
- `## Integration Notes`
- `## Evaluation Harness`
- `## Deployment Notes`

`evaluation.md`

- `## Decision Summary`
- `## Published Evidence`
- `## Assumptions And Scenario Model`
- `## Expected Economics`
- `## Quality, Risk, And Failure Modes`
- `## Rollout KPI Set`
- `## Open Questions`

`references.md`

- `## Source Quality Notes`
- `## Source Register`
- `## Claim Map`

No `{placeholder}` text may remain.

## Gotchas

- Keep the split between files clean. Do not repeat the same table in multiple places.
- If the evidence base is thin, say that directly and narrow the recommendation.
- Focus on one strong reference architecture instead of listing every possible tool in the market.
- The site publishes detailed case studies. Write for readers, not for the agent runtime.
- Do not leave raw URL text in markdown. Use clickable Markdown links everywhere a URL is shown.
- Do not leave "coming soon" links to files that do not exist yet.
