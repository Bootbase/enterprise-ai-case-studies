# UC-050: Autonomous Adverse Event Report Processing in Pharmacovigilance — Evaluation

## Evaluation Overview

The public evidence base for AI in pharmacovigilance is uneven. The strongest implementation detail comes from three kinds of sources:

- peer-reviewed feasibility work, especially Pfizer's pilot on AI-assisted case intake [CS1]
- vendor case studies with operational metrics, especially Tech Mahindra and ArisGlobal [CS2][CS3]
- product releases that reveal which sub-problems vendors isolated into separate agents or services, such as intake, translation, and multi-agent orchestration [CS4][CS5]

That means the right evaluation posture is two-layered:

1. use published metrics to understand where AI is already working in production or near-production
2. treat every ROI number for this use case as scenario-based unless the source publishes audited operating data

This document does both. Published metrics stay clearly labeled as published. Financial projections derived from the research brief are marked `estimated`. [UC]

---

## Baseline (Before AI)

The baseline below uses the existing research brief as the operating assumption set for a sponsor or CRO processing 2,000 ICSRs per month. Where the brief gives a range, the table uses a midpoint and labels the calculation as `estimated`. [UC]

| Metric | Value | Source |
|--------|-------|--------|
| **Processing Time** | `2-4 hours/case` | Research brief. [UC] |
| **Triage Deadline** | `24 hours from awareness` | Research brief. [UC] |
| **Cost per Case** | `~$132.60 estimated` | `3.0 hours x $44.20/hr` median staff cost from the brief. [UC] |
| **Monthly Labor Cost at 2,000 Cases** | `~$265,200 estimated` | `2,000 x $132.60`. [UC] |
| **Human FTE Capacity Needed** | `25-50 FTE-months estimated` | `2,000 cases x 2-4 hours`, divided by `160` productive hours/FTE/month. [UC] |

---

## Published Results (After AI)

The table below does not pretend these numbers came from one common benchmark. They come from different public deployments and pilots, so they should be read as directional evidence for what the market is already achieving.

| Metric | Before AI | Published AI Result | Change |
|--------|-----------|---------------------|--------|
| **Intake data accuracy** | Manual entry with known inconsistency | `90%` data extraction accuracy and quality reported by ArisGlobal Advanced Intake | Major improvement in standardized intake. [CS3] |
| **Cost reduction** | Full manual case intake process | `30-50%` cost reduction reported by Tech Mahindra's multi-agent intake system | Material operating leverage if validated locally. [CS2] |
| **Turnaround** | Hours per case | "Hours to minutes" reported by Tech Mahindra | Large cycle-time compression. [CS2] |
| **Valid-case rate** | Manual review required for all | `>95%` valid case rate reported by Tech Mahindra | Better early routing and intake precision. [CS2] |
| **Compliance timeliness** | Manual queues at risk during surges | `98%` compliance timeliness reported by Tech Mahindra | Strong indicator for deadline-sensitive PV operations. [CS2] |
| **Operational capacity** | Roughly `2-4` cases/day per specialist based on the brief | `150-200` cases/day reported by Tech Mahindra's solution | Shows why queue-based AI cells are attractive for spikes. [CS2][UC] |
| **Case extraction feasibility** | Not automated | Overall extraction F1 of `0.72-0.74` for the top vendors in Pfizer's pilot | Confirms technical feasibility, but not autonomy. [CS1] |
| **Case validity classification** | Manual intake review | `81%` correct validity prediction after two training cycles for the best vendor in Pfizer's pilot | Good enough to assist routing, not enough to skip review everywhere. [CS1] |

---

## Quality Assessment

### What the AI already does well

| Capability | Evidence | Interpretation |
|------------|----------|----------------|
| **Structured intake from messy source text** | ArisGlobal reports `90%` extraction accuracy; Pfizer's top vendors reached `0.72-0.74` composite extraction F1. [CS1][CS3] | Extraction is mature enough to automate the first pass on routine cases. |
| **Case intake routing and prioritization** | Tech Mahindra reports `>95%` valid-case rates and `98%` compliance timeliness. [CS2] | AI is strongest when paired with explicit routing criteria and queueing logic. |
| **Scaling routine volume** | Tech Mahindra reports `150-200` cases/day. [CS2] | The clearest value is capacity expansion without linear headcount growth. |
| **Translation as a separable workflow** | ArisGlobal productized translation as its own NavaX service with TransPerfect. [CS5] | Teams discovered translation is a clean specialization boundary, not just another prompt instruction. |

### Where the AI still struggles

| Capability | Evidence | Why It Matters |
|------------|----------|----------------|
| **Edge-case extraction** | Pfizer notes AE verbatim was among the lowest-scoring entity types, and only `31-34%` of cases reached `80-100%` completion in the top vendor runs. [CS1] | The difficult cases are exactly the ones reviewers care about most. |
| **Autonomous case validity** | Best vendor reached `81%` correct valid/invalid case prediction, not a near-perfect level. [CS1] | That is good for pre-triage, not for removing controlled review. |
| **End-to-end autonomy claims** | Public vendors publish intake, translation, and throughput metrics, but much less on fully autonomous causality assessment or submission release. [CS2][CS3][CS4][CS5] | The market is telling you where confidence is high enough to automate and where it is not. |
| **Cross-case duplicate ambiguity** | Vendors emphasize duplicate matching as a feature, but public quality metrics are still sparse. [CS2][UC] | Duplicate handling should stay behind a review threshold until sponsor data proves otherwise. |

---

## Failure Analysis

| Failure Mode | Evidence | Impact | Practical Mitigation |
|--------------|----------|--------|----------------------|
| **Hallucinated or over-inferred fields** | Structured outputs and evidence grounding are now explicit recommendations because unconstrained generation was too brittle. [TD1] | High | Force schema-valid extraction and require evidence spans for every non-null field. |
| **Weak performance on specific entities** | Pfizer's pilot found uneven entity performance, with AE verbatim lagging the best fields. [CS1] | High | Keep extraction scores by field, not just one composite number. |
| **Over-automation of regulated decisions** | Public metrics are strongest for intake and translation, not for final submission autonomy. [CS2][CS5] | High | Put seriousness, causality, and final submission behind human approval gates. |
| **Tool sprawl degrades decision quality** | Semantic Kernel warns that too many tools reduce selection quality. [TD4] | Medium | Keep tools scoped per worker and avoid giant universal toolboxes. |
| **Validation drift after prompt changes** | This is implicit in every regulated AI deployment: prompt changes change behavior. [UC] | High | Re-run the gold set on every prompt, model, or tool change. |

---

## Cost Analysis

### Operational Costs

The operating envelope below is `estimated`. Public sources publish percentage gains, not platform invoices, so the numbers are derived from the research brief's 2,000-case monthly scenario. [UC]

| Cost Component | Monthly Cost | Notes |
|----------------|-------------|-------|
| **Residual specialist review** | `$90k-$130k estimated` | Assumes the AI removes roughly `50-65%` of routine effort but serious and ambiguous cases still route to humans. [UC][CS3] |
| **LLM and AI platform** | `$10k-$20k estimated` | Structured extraction, coding, duplicate review, and narrative generation across the monthly case load. |
| **Queue, storage, tracing, retrieval** | `$5k-$12k estimated` | Connectors, search, state persistence, and audit retention. |
| **Total Operational** | **`$105k-$162k estimated`** | Consistent with the labor envelope and published efficiency claims. [UC][CS2][CS3] |

### ROI Calculation

This is a scenario model, not a vendor promise.

| Factor | Value |
|--------|-------|
| **Previous Cost (monthly)** | `$265,200 estimated` from the brief's median labor assumptions. [UC] |
| **AI Solution Cost (monthly)** | `$105k-$162k estimated`. |
| **Net Savings (monthly)** | `$103k-$160k estimated`. |
| **Implementation Cost** | `$500k-$750k estimated` for integration, validation package, gold-set creation, and rollout. |
| **Payback Period** | `~3-7 months estimated`. |

### Conservative Interpretation

If an organization realizes only the lower end of the published savings early, or if validation overhead delays the touchless rate, payback moves right. Even so, the use case still fits the brief's requirement to show ROI inside `12-18 months` on conservative assumptions. [UC][CS2][CS3]

---

## Lessons Learned

### What Worked Well

- Specialized workers beat broad prompts. The public market signal is clear: Tech Mahindra describes a multi-agent architecture, and ArisGlobal is productizing separate intake, translation, and orchestration agents rather than one general-purpose assistant. [CS2][CS4][CS5]
- Translation is a strong automation boundary. ArisGlobal's translation release suggests teams found this task clean enough to isolate as a dedicated service tied directly into PV workflows. [CS5]
- Schema-first extraction is the stabilizer. Azure's structured outputs map exactly to the need for repeatable intake packets and QC checklists. [TD1]
- Human review remains a feature, not a fallback. LangGraph's interrupts are a good technical match for the way PV reviewers already work: pause, inspect, annotate, resume. [TD3]

### What Didn't Work

- One score does not describe PV quality. Pfizer's pilot shows why: good composite F1 still hid weaker performance on specific entities and only partial case completeness on many samples. [CS1]
- "Autonomous end-to-end PV" is usually overstated in public materials. The published numbers focus on intake throughput, translation, and efficiency, not on autonomous causality sign-off or ungated submission release. [CS2][CS3][CS4][CS5]
- Over-broad tool access is counterproductive. The more the model can do in one loop, the harder the system becomes to validate and the worse tool selection tends to get. [TD4]

### What Surprised Teams

- Translation and intake moved into productized AI faster than many expected, while duplicate review and medical judgment remain more guarded. [CS3][CS5]
- Public vendors are now emphasizing orchestration and agent suites, which implies the integration problem is no longer just "pick a model" but "control a regulated workflow." [CS4]
- The peer-reviewed pilot was good enough to justify automation investment even without near-human perfection, because the value came first from routing and effort reduction, not from replacing every reviewer. [CS1]

---

## Limitations Discovered

| Limitation | Severity | Workaround / Plan |
|------------|----------|-------------------|
| Vendor case studies publish uneven metrics | Medium | Use them to choose architecture, then validate on a sponsor-owned gold set. |
| Public evidence on duplicate quality is thin | High | Keep duplicate merge decisions behind review thresholds. |
| Public data on causality and final submission autonomy is scarce | High | Keep those steps human-approved. |
| Regulatory validation effort is not optional | High | Budget for prompt/version control, test packs, and trace retention from day one. |

---

## What We'd Do Differently

- Start with routine non-serious cases only. The public evidence is strongest there, and it creates the cleanest path to validated ROI. [CS1][CS2][CS3]
- Build the evaluation set before expanding the tool surface. Too many teams start with orchestration and only later discover they cannot prove quality. [UC]
- Treat translation, duplicate review, and narrative drafting as separate workers from day one instead of one "safety copilot" prompt. The market already learned that lesson. [CS2][CS4][CS5]

---

## Next Steps

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| High | Run a sponsor-owned pilot on `500-1,000` routine cases with full gold-set scoring | Validates touchless rate and extraction quality on real portfolio data. |
| High | Implement serious-case interrupt and reviewer resume flow first | Makes the system safe enough to trial in a regulated environment. |
| Medium | Add dedicated translation and duplicate-review workers | Improves multilingual handling and reviewer efficiency. |
| Medium | Capture reviewer edits and feed them back into evaluation sets | Improves calibration without promising unsupervised learning in production. |
| Low | Expand from one safety platform seam to additional connectors | Reuse the same AI core across Veeva, ArisGlobal, or Argus estates. |
