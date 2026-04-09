---
layout: use-case
title: "Autonomous Incident Investigation with Agentic AI Site Reliability Engineers"
uc_id: "UC-300"
category: "Code & DevOps"
category_dir: "code-and-devops"
category_icon: "terminal"
industry: "Cross-Industry (SaaS, Internet Platforms, FinTech, Travel, E-Commerce)"
complexity: "High"
status: "research"
summary: "Modern software companies operate hundreds to thousands of microservices generating continuous alert streams. Site Reliability Engineers manually investigate each alert by correlating signals across logs, metrics, traces, and deployments — work that consumes 20–30% of senior engineer time and leaves 62% of alerts never properly investigated."
slug: "UC-300-incident-investigation-sre"
has_solution_design: false
has_implementation_guide: false
has_evaluation: false
has_references: false
permalink: /use-cases/UC-300-incident-investigation-sre/
---

## Problem Statement

Modern software companies operate hundreds to thousands of microservices on Kubernetes, service meshes, and multi-cloud infrastructure, generating a continuous stream of alerts from observability tools like Datadog, Prometheus, Grafana, New Relic, and CloudWatch. When an alert fires — a latency spike, an "Upstream Retry Limit Exceeded" error, a database CPU saturation — a human Site Reliability Engineer (SRE) or on-call engineer must drop what they are doing, page into the alert, and begin a manual investigation that involves correlating signals across logs, metrics, traces, recent deployments, and dependency graphs spread across many tools and dashboards.

The structural problem is that this investigation work is repetitive, judgment-heavy, and disproportionately consumes the most experienced engineers. BlaBlaCar — the world's leading community-based travel platform with millions of members across 21 countries — runs a fully containerized service architecture on Kubernetes with Istio service mesh, supports more than 200 CI/CD deployments per day, and serves 200+ engineers across 40+ teams, all backed by a lean five-person SRE team embedded in a 40-person Foundations group. That ratio (one SRE per 40 engineers) is typical for high-velocity SaaS teams and is structurally unable to scale linearly with alert volume.

Investigation work also dominates the lifecycle of an incident. Industry research from Gartner, IBM, and PagerDuty puts the average cost of a major (P1/P2) IT incident in the $500K–$5M range when direct revenue loss, SLA penalties, and reputation damage are included; even moderate incidents commonly land between $15K and $35K each. Datadog reports that its Bits AI SRE agent has been tested across 2,000+ customer environments running tens of thousands of investigations, with the underlying observation that a large share of on-call work is "look at the dashboard, correlate, form a hypothesis, check the next dashboard" — exactly the type of multi-step tool-use loop that an LLM agent with read-only access to observability tools can perform autonomously.

The result is widespread alert fatigue, slow Mean Time to Resolution (MTTR), and senior engineers spending 20–30% of their week on triage instead of building reliability into the systems themselves. Cleric AI, an AI SRE startup that has raised $9.8M in seed funding led by Vertex Ventures US and was named a Gartner® Cool Vendor 2025 in AI for SRE and Observability, reports that early customers reclaimed 20–30% of total engineering capacity after deploying its agent into Slack alerting channels.

## Business Impact

| Dimension       | Description                               |
|-----------------|-------------------------------------------|
| **Cost**        | Average P1/P2 incident cost: $500K–$5M (Gartner/IBM/PagerDuty), with most teams modeling $15K–$35K per major incident. On-call tooling for a 100-engineer team runs ~$54K–$58K/year (incident.io, PagerDuty Business + AIOps) on top of the much larger labor cost of senior SRE time. Cleric reports early customers reclaiming 20–30% of total engineering capacity previously lost to repetitive troubleshooting. |
| **Time**        | Cleric investigations average under 2 minutes from alert to root-cause hypothesis at BlaBlaCar. Datadog Bits AI SRE produces audit-ready root-cause analyses in minutes versus the hours typical of manual investigation. Customers of self-healing AI SRE platforms report up to 90% reduction in MTTR for the investigation phase. |
| **Error Rate**  | Manual investigations vary widely by engineer experience, time of day (night-shift fatigue), and tool familiarity. Junior on-call engineers frequently escalate alerts that a senior would resolve directly, multiplying interruption cost. Inconsistent runbook adherence creates investigation gaps that surface later as recurring incidents. |
| **Scale**       | BlaBlaCar: 200+ deployments/day, 200+ engineers, 40+ teams, 5-person SRE team. Datadog Bits AI SRE: 2,000+ customer environments tested, tens of thousands of investigations executed across global enterprises and startups. Azure SRE Agent and AWS DevOps Agent ship as managed services across the entire Azure and AWS customer base respectively. Alert volumes for a mid-sized SaaS commonly exceed 10,000–100,000 alerts per month per cluster. |
| **Risk**        | Slow MTTR translates directly into customer-visible downtime, SLA credit payouts, and revenue loss for transaction-driven businesses. Alert fatigue causes real incidents to be acknowledged late or missed. Senior SRE burnout creates retention risk in a labor market where SRE compensation routinely exceeds $200K. For regulated industries (FinTech, healthcare SaaS), failure to investigate and document an incident creates audit and compliance exposure. |

## Current Process (Before AI)

1. **Alert Fires**: A monitoring tool (Datadog, Prometheus/Alertmanager, New Relic, CloudWatch, Dynatrace) raises an alert based on a SLO breach, error-rate threshold, or anomaly detector. The alert is routed to a Slack/Teams channel and to the on-call rotation in PagerDuty, Opsgenie, or incident.io.
2. **On-Call Acknowledgment**: The on-call engineer acknowledges the page (often interrupted from focused work or sleep), opens the alert payload, and begins to triage. Severity is provisionally assigned based on the alert metadata.
3. **Context Gathering**: The engineer opens the relevant Datadog/Grafana/Kibana dashboard, scans recent logs, checks Prometheus query results, reviews distributed traces in Jaeger/Tempo/Honeycomb, and inspects Kubernetes pod state via `kubectl` or Lens. Each tool requires its own login, query language, and mental model.
4. **Recent-Change Correlation**: The engineer checks the deployment system (ArgoCD, Spinnaker, GitHub Actions, Jenkins) for recent releases, feature flag toggles in LaunchDarkly/Unleash, and infrastructure changes in Terraform Cloud — looking for a temporal correlation between the change and the alert.
5. **Dependency Investigation**: If the failing service depends on databases (PostgreSQL, MySQL, MongoDB, DynamoDB), caches (Redis, Memcached), queues (Kafka, RabbitMQ, SQS), or downstream services, the engineer walks the dependency graph through the service mesh (Istio, Linkerd) or APM tool, checking each one for upstream issues.
6. **Hypothesis & Mitigation**: The engineer forms a root-cause hypothesis (e.g., "the new release introduced a slow query that saturates the database connection pool"), takes a mitigation action (rollback, scale up, feature flag off, restart), and observes whether the alert clears.
7. **Escalation**: If the on-call engineer cannot resolve the issue within an SLA window, the incident is escalated to a domain expert, a senior SRE, or an incident commander, often pulling multiple engineers into a war-room call.
8. **Postmortem & Documentation**: After resolution, the on-call writes a postmortem in Confluence/Notion/Jira, captures timeline and remediation actions, and the team meets to review systemic causes.

### Bottlenecks & Pain Points

- **Tool sprawl**: Investigation requires jumping between 5–10 different tools (metrics, logs, traces, deployment system, runbooks, source code, dependency graph, ticketing). The engineer is the manual integration layer between observability silos.
- **Alert fatigue**: High alert volume relative to true incident volume desensitizes on-call engineers. Real critical incidents get acknowledged late because they look like every other alert.
- **Knowledge concentration**: Effective investigation depends on tribal knowledge of how a specific service has failed in the past — knowledge that lives in the heads of senior engineers and is lost when they leave or rotate off on-call.
- **Out-of-hours impact**: Night and weekend pages cause sleep disruption, fatigue-driven errors, and burnout. Companies pay on-call premiums but cannot eliminate the human cost.
- **Slow correlation across team boundaries**: An alert in service A may be caused by a deployment in service B owned by a different team. Cross-team correlation requires a human to recognize the connection and reach out, often taking hours.
- **Investigations don't scale linearly**: Adding more on-call engineers does not linearly reduce MTTR because the bottleneck is the cognitive work of correlation and hypothesis formation, not the headcount available to look at dashboards.
- **Postmortem learnings don't reach the next investigation**: Lessons captured in postmortems rarely change how the next similar incident is investigated, because runbook updates lag and engineers don't read runbooks under pressure.

## Desired Outcome (After AI)

An autonomous AI SRE agent that monitors alerting channels (Slack, Teams, PagerDuty webhooks), automatically begins investigating the moment an alert fires, executes a multi-step diagnostic loop using read-only access to the same observability tools a human SRE would use (Datadog, Prometheus, Grafana, Kubernetes API, deployment systems, source repos), correlates signals across all of them, forms and tests hypotheses, posts a structured root-cause analysis back into the alerting channel within 2–5 minutes, and learns continuously from engineer feedback so future investigations of similar alerts improve over time. Humans retain final decision authority on remediation actions in production.

Cleric AI's deployment at BlaBlaCar demonstrates the target state: introduced into the SRE helpdesk in August 2024 against the Chaos engineering app, expanded to the Database Reliability team's alerting channels in October 2024 acting as level-one incident response, and added to the Identity and Access Management team's Slack alerting channel in late January 2025. Within three weeks of being added to the IAM channel, with no prior domain-specific configuration, Cleric earned a perfect score from a senior IAM engineer for correctly diagnosing an "Upstream Retry Limit Exceeded" alert. Investigation time averaged under 2 minutes. Datadog's Bits AI SRE, Azure SRE Agent, AWS DevOps Agent, Neubird, incident.io's AI SRE, and Observe's AI SRE/o11y.ai agents all converge on the same operating model: agentic investigation with explainable RCA and policy-bounded auto-remediation.

### Success Criteria

| Metric                              | Target                                            |
|-------------------------------------|---------------------------------------------------|
| Investigation time per alert        | < 2 minutes from alert fire to RCA hypothesis (Cleric/BlaBlaCar baseline) |
| RCA quality                         | Senior-engineer rating ≥ 4/5 on a sampled basis   |
| Engineering capacity reclaimed      | 20–30% of SRE/on-call capacity returned to higher-value work (Cleric customer baseline) |
| MTTR reduction                      | Up to 90% reduction in investigation phase (industry benchmark) |
| Coverage of alert types             | ≥ 80% of recurring alert types handled without human investigation |
| Cross-team correlation              | Agent automatically links alerts in service A to recent deployments in service B |
| Continuous learning                 | Investigation success rate improves measurably after engineer feedback (LangSmith-tracked at Cleric) |
| Remediation authority               | 100% human-approved for production write actions; agent may execute read-only diagnostics autonomously |
| Audit trail                         | Every investigation produces an audit-ready trace of tool calls, evidence, and reasoning (Datadog Bits AI SRE design) |
| Onboarding time per new domain      | ≤ 3 weeks from agent introduction to first perfect-score investigation (Cleric/IAM team baseline) |

## Stakeholders

| Role                              | Interest                                          |
|-----------------------------------|---------------------------------------------------|
| Head of SRE / Reliability         | Reduce on-call burden, improve MTTR, retain senior engineers |
| On-Call Engineers                 | Fewer middle-of-the-night pages, faster context when paged   |
| Engineering Managers              | Reclaim engineering capacity for feature work, reduce burnout |
| Incident Commander                | Faster initial RCA, better-prepared war rooms, consistent investigation quality |
| Platform Engineering              | Integration with existing observability stack (Datadog/Prometheus/Grafana), Kubernetes, service mesh |
| Security & Compliance             | Read-only access controls, audit trail of all agent actions, no production write without approval |
| CTO / VP Engineering              | ROI on AI investment, demonstrable MTTR/capacity improvement, scalable reliability without linear headcount growth |
| Finance / Procurement             | Justifiable cost vs. displaced labor and avoided incident impact |
| Product / Customer Success        | Faster resolution of customer-visible issues, fewer SLA credit payouts |

## Constraints

| Constraint              | Detail                          |
|-------------------------|---------------------------------|
| **Data Privacy**        | Logs and traces routinely contain customer PII, request payloads, and authentication tokens. Agent must operate within the customer's cloud boundary or via a dedicated tenant with strict data handling. GDPR, CCPA, HIPAA (for healthcare SaaS), and PCI-DSS (for FinTech) apply depending on industry. No telemetry data may be used for cross-customer model training without explicit opt-in. |
| **Latency**             | Investigation must complete within 2–5 minutes of alert fire to be useful during an active incident. Agent must operate continuously, 24/7, with no human prompting required. |
| **Budget**              | LLM inference cost per investigation must be a small fraction of the labor cost it displaces. For a $200K-loaded SRE, even 5 minutes of saved time per investigation justifies meaningful inference spend, but per-investigation cost must be metered and capped. Total tool cost should be measured against the on-call platform baseline (~$54K–$58K/year for a 100-engineer team on incident.io or PagerDuty Business). |
| **Existing Systems**    | Must integrate read-only with the incumbent observability stack: Datadog, Prometheus, Grafana, New Relic, CloudWatch, Dynatrace, Honeycomb, Tempo, Loki, Elastic. Must connect to deployment systems (ArgoCD, Spinnaker, GitHub Actions), service mesh (Istio, Linkerd), Kubernetes API, and source repos. Must post into Slack/Teams alerting channels and integrate with PagerDuty/Opsgenie/incident.io. Cannot replace the observability or alerting stack — agent augments them. |
| **Compliance**          | SOC 2 Type II is table stakes. Production write actions (rollback, scale, restart, feature flag toggle) require explicit human approval and a full audit trail. For regulated industries, change management policies (ITIL, SOX) must be respected — the agent cannot bypass change-approval boards. Read-only access by default; any escalation to write access must be policy-bounded and reviewed. |
| **Scale**               | Must handle thousands of alerts per day per environment. Must operate in parallel across hundreds of services and dozens of teams without cross-contamination of context. Must absorb alert storms during major outages without degrading investigation quality. |

## Scope Boundaries

### In Scope

- Autonomous investigation of production alerts originating from observability tools (Datadog, Prometheus, Grafana, New Relic, CloudWatch, etc.)
- Multi-tool correlation across logs, metrics, traces, deployments, and dependency graphs
- Read-only diagnostic access to Kubernetes, service mesh, databases, queues, and APM tools
- Hypothesis generation and root-cause analysis with structured, audit-ready output
- Cross-team correlation linking alerts to recent deployments or upstream service issues
- Slack/Teams posting of investigation results into alerting channels
- Integration with PagerDuty/Opsgenie/incident.io for alert ingestion
- Continuous learning from engineer feedback (thumbs up/down, RCA edits, follow-up questions)
- Audit trail of every tool call, query, and reasoning step the agent performed
- Optional, policy-bounded auto-remediation for low-risk, well-characterized alerts (e.g., restart a known-flaky pod, scale up under load) — only with explicit human approval gates
- Initial coverage of recurring infrastructure alerts (database saturation, pod crash loops, latency spikes, error-rate threshold breaches, mesh retry limit exceeded)
- Expansion path to application-level alerts and business-metric alerts

### Out of Scope

- Production write actions without human approval (no autonomous rollback, no autonomous traffic shifting in critical paths, no autonomous database modifications)
- Replacement of the observability stack itself
- Replacement of the alerting and incident management platform (PagerDuty, incident.io, etc.)
- Capacity planning, architecture review, and proactive reliability engineering (separate workstreams)
- Security incident response (SOC/SIEM workflows are a different domain and have stricter requirements)
- Code-level bug fixing and pull request generation (handled by separate code-assistant tools)
- Customer-facing status page updates and customer communication
- Postmortem authoring (agent provides timeline and evidence; humans write the postmortem narrative and assign action items)
- Cross-customer model training on private telemetry data
