# Enterprise AI Case Studies

A curated library of published case studies showing how agentic AI systems are framed, designed, implemented, and evaluated in real enterprise environments.

The goal is to answer a simple question for anyone evaluating agentic AI in the enterprise: **"Has someone already solved this, and what did it actually take?"**

Browse the library at **[enterprise-ai-case-studies.bootbase.be](https://enterprise-ai-case-studies.bootbase.be)**.

## What's in the library

Each case study is a self-contained deep-dive into one enterprise AI scenario — for example, autonomous customer service resolution, AP invoice processing, or SRE incident investigation. Case studies are grouped into six categories:

| Category | What it covers |
|---|---|
| **Document Processing** | Extracting, classifying, and acting on structured and unstructured documents (invoices, contracts, trade docs, mortgages). |
| **Customer Service** | Autonomous resolution of customer and IT service interactions. |
| **Workflow Automation** | Multi-step back-office processes — procurement, hiring, financial close, tax, audit, logistics. |
| **Code & DevOps** | Engineering and operations work — incident investigation, SOC triage, legacy modernization. |
| **Knowledge Management** | Synthesis over large knowledge bases — consulting research, regulatory intelligence. |
| **Industry-Specific** | Scenarios tied to a specific vertical — pharma, insurance, legal, banking, healthcare, energy, manufacturing, and others. |

A case study is either in **research** stage (a short brief establishing that the scenario is real and worth documenting) or **detailed** stage (a full five-document write-up). The [case study index](docs/use-cases/README.md) lists every entry with its current stage.

## How a case study is structured

When a case study reaches the **detailed** stage, it consists of five documents that each answer a different question. Read them in order if you want the full picture, or jump straight to the one that matches your role.

| Document | Question it answers | Who it's for |
|---|---|---|
| **`index.md`** — Problem brief | What is the business problem, who has it, what does "solved" look like, and what evidence exists that agentic AI can solve it? Includes the business case, current workflow, target state, success metrics, stakeholders, constraints, and scope. | Anyone — start here. Especially useful for executives, product leaders, and analysts deciding whether a scenario is worth pursuing. |
| **`solution-design.md`** — Solution design | At an architectural level, how should the system be built? Operating model, component architecture, end-to-end flow, AI responsibilities and boundaries, integration seams, control model, reference tech stack, and the key design decisions with their trade-offs. | Solution architects and technical leads shaping an approach. |
| **`implementation-guide.md`** — Implementation guide | What would you actually build? Delivery plan, core data contracts, orchestration outline, prompt and guardrail patterns, integration notes, evaluation harness, and deployment notes. | Engineers and delivery teams moving from design to code. |
| **`evaluation.md`** — Evaluation | Is this worth doing, and what happens if it goes wrong? Decision summary, published evidence, assumptions and scenario model, expected economics, quality and failure modes, rollout KPIs, and open questions. | Sponsors, finance, and risk owners pressure-testing the business case. |
| **`references.md`** — References | Where does every claim come from? A register of sources with quality notes, plus a claim map linking specific statements in the other documents back to their evidence. | Anyone verifying a specific number, quote, or assertion. |

Case studies at the **research** stage have only the `index.md` brief. The other four documents get added when the case study is promoted to detailed.

## How to use the site

- **Exploring what's possible.** Skim the category index, pick case studies close to your domain, and read their `index.md` briefs. Each brief is designed to be readable in a few minutes and to make the business case standalone.
- **Evaluating a specific scenario.** Open one case study and read it top to bottom — brief → solution design → implementation guide → evaluation. By the end you should have enough to decide whether to pursue it and to brief an internal team.
- **Building something similar.** Use the solution design as your architectural starting point and the implementation guide as a checklist of what needs to exist before you ship. Adapt; don't copy — every organization has its own constraints.
- **Verifying a claim.** Every detailed case study is source-backed. If a number looks surprising, open `references.md` and trace it through the claim map to the original source.

Case studies are documentation of what has been proven to work elsewhere, not prescriptive blueprints. Treat them as a starting point for your own thinking, not a shortcut around it.
