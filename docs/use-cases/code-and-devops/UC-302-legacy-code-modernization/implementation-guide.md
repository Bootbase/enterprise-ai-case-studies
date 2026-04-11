---
layout: use-case-detail
title: "Implementation Guide — Autonomous Legacy Code Modernization and Migration with Agentic AI"
uc_id: "UC-302"
uc_title: "Autonomous Legacy Code Modernization and Migration with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Code & DevOps"
category_icon: "terminal"
industry: "Cross-Industry (Banking, Financial Services, Government, Insurance, Logistics, Telecommunications)"
complexity: "High"
status: "detailed"
slug: "UC-302-legacy-code-modernization"
permalink: /use-cases/UC-302-legacy-code-modernization/implementation-guide/
---

## Build Goal

The delivery team is building a modernization workbench that assembles one bounded legacy domain, generates modernization candidates, and emits reviewable pull-request artifacts with deterministic validation evidence. The first production boundary should cover one domain and its acceptance suite, not a whole-estate exit. Database platform replacement, enterprise-wide scheduler replacement, and autonomous cutover stay outside the first release. [S1][S5][S7][S10]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12 service with FastAPI for orchestration APIs and background workers for batch transformation jobs | Python keeps the AI, parsing, and validation ecosystem close together while letting teams expose modernization jobs through a controlled service boundary. |
| **Model access** | Azure OpenAI chat completion through Semantic Kernel | This matches Microsoft's published agentic modernization pattern and supports tenant-scoped deployment, tool calling, and plugin-based orchestration. [S7][S11][S12] |
| **Orchestration runtime** | Semantic Kernel agents plus native plugins for inventory lookup, validation, and repository output | The plugin model cleanly separates AI reasoning from deterministic side effects and keeps tool exposure explicit. [S11][S12] |
| **Core connectors** | Mainframe artifact export, graph-backed dependency store, Git repository adapter, Java build runner, and equivalence-test harness | These connectors correspond to the real integration seams called out by IBM, AWS, and Microsoft rather than generic chat tools. [S2][S3][S5][S7] |
| **Evaluation / tracing** | OpenTelemetry traces, structured run records, and versioned prompts plus validation evidence stored with each modernization unit | The workbench must explain what was generated, which tools were used, and why a unit was accepted or rejected. [S5][S13] |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Artifact-ready pilot scope | Selected business domain, source inventory, dependency export, schema and scheduler metadata capture, sanitized sample data, and artifact completeness checks. |
| 2 | Reliable understanding pipeline | Code graph store, generated documentation, domain clustering, ambiguity register, and retained-vs-migrate decisions for each modernization unit. |
| 3 | Controlled transformation loop | Agent prompts, plugin interfaces, candidate Java or .NET output, compile checks, regression suites, and pull-request artifact packaging. |
| 4 | Pilot validation and rollout | Dual-run harness, KPI dashboard, SME review workflow, rollback plan, and release criteria for pilot traffic or pilot batch execution. |

## Core Contracts

### State And Output Schemas

The core contract is the modernization unit. It gives the model enough context to work on one slice of the estate and carries the evidence needed for release decisions.

```python
from pydantic import BaseModel, Field
from typing import Literal


class ModernizationUnit(BaseModel):
    unit_id: str
    domain: str
    source_artifacts: list[str]
    source_dependencies: list[str]
    target_pattern: Literal["retain", "refactor", "replatform", "redesign"]
    target_runtime: Literal["java_quarkus", "java_spring", "dotnet"]
    acceptance_suite: list[str]
    risk_flags: list[str] = []


class TransformationResult(BaseModel):
    unit_id: str
    generated_files: list[str]
    unresolved_questions: list[str]
    compile_passed: bool
    regression_pass_rate: float = Field(ge=0.0, le=1.0)
    dual_run_match_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    needs_human_review: bool
```

### Tool Interface Pattern

Expose tools as narrow, deterministic plugins. The model should never talk directly to a shell, source-control server, or mainframe export without a typed interface. Semantic Kernel fits because it advertises only the functions needed for the current phase. [S11][S12]

```python
from typing import Annotated
from semantic_kernel.functions import kernel_function


class ModernizationPlugin:
    def __init__(self, catalog, validator):
        self.catalog = catalog
        self.validator = validator

    @kernel_function(description="Return the normalized artifact bundle for one modernization unit.")
    def load_unit(
        self, unit_id: Annotated[str, "Unique modernization unit identifier"]
    ) -> dict:
        return self.catalog.load_unit(unit_id)

    @kernel_function(description="Run compile and regression checks for generated output.")
    def validate_candidate(
        self, unit_id: Annotated[str, "Modernization unit identifier"]
    ) -> dict:
        return self.validator.run(unit_id)
```

## Orchestration Outline

Keep the control flow simple. Start with an approved modernization unit, let the agent retrieve only that unit's artifacts, and route every result through validation before any repository writeback. AWS and Microsoft both emphasize objective-driven reruns rather than whole-pipeline restarts. [S3][S4][S7]

```python
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.functions import KernelArguments


kernel = Kernel()
kernel.add_service(AzureChatCompletion(service_id="modernizer"))
kernel.add_plugin(ModernizationPlugin(catalog, validator), plugin_name="modernization")

settings = AzureChatPromptExecutionSettings(service_id="modernizer")
settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

agent = ChatCompletionAgent(
    kernel=kernel,
    name="cobol_modernizer",
    instructions=PLANNER_AND_CONVERTER_PROMPT,
    arguments=KernelArguments(settings=settings),
)

response = await agent.get_response(
    messages=(
        "Load modernization unit PAYMENTS_BATCH_042. "
        "Produce a target-language conversion plan, unresolved questions, "
        "and only then draft code for the unit."
    )
)
```

## Prompt And Guardrail Pattern

The system prompt should force the model to declare uncertainty, cite source artifacts, and refuse to invent missing scheduler or data semantics.

```text
You are a legacy modernization agent working on one approved modernization unit.

Rules:
- Use only the artifacts returned by tools for this unit.
- Quote source file names, paragraph names, copybooks, and JCL steps when you
  explain a decision.
- If transaction order, scheduler flow, record layout, or error handling is
  unclear, emit `needs_human_review=true` and list the ambiguity.
- Do not claim semantic equivalence. Equivalence is decided only by validation.
- Do not write directly to production branches. Output reviewable artifacts only.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Mainframe artifact ingestion | Export pipeline for COBOL, copybooks, JCL, screen maps, schemas, and historical docs into the modernization catalog | Do not start from source files alone. Missing JCL, scheduler, or schema context is a predictable failure mode. [S3][S5][S7] |
| Dependency and call-graph store | Graph model linking programs, copybooks, data stores, batch jobs, and target services | Microsoft's published learnings show call-chain depth and chunking as the main orchestration challenge. [S7] |
| Validation harness | Compiler, regression suite runner, dual-run comparator, and evidence packager | Testing is not optional cleanup. It is the confidence mechanism. [S5] |
| Repository writeback | PR generator that writes candidate code, design notes, and validation results into a review branch | Keep write actions small and auditable. |
| Data handling | Sanitized test-data capture and lineage tracking for comparison datasets | AWS keeps data collection under system-programmer control. [S5] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Domain decomposition quality | Sample approved modernization units and measure whether all required source dependencies were present before generation | 100% of pilot units have complete dependency manifests before transformation starts |
| Translation and compile quality | Track compile success and static-analysis violations for generated units | 100% compile success for pilot-bound units after the review cycle; no critical static-analysis violations |
| Functional equivalence | Execute curated golden tests and dual-run comparison for the pilot scenario set | 100% pass rate on high-criticality scenarios and no unexplained output mismatches |
| Ambiguity handling | Review how often the system escalates missing business rules instead of guessing | 0 silent failures on known ambiguous cases; every ambiguity recorded in the evidence bundle |
| Human review efficiency | Measure SME review time per unit and number of rework cycles | Review effort should trend downward by the second or third wave |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one business domain and run the workbench in shadow mode against completed legacy outputs before letting it generate pilot-ready PRs for active work. |
| **Fallback path** | Preserve the existing release path and keep the legacy runtime authoritative until dual-run exit criteria are met. A failed pilot should leave the source estate untouched. |
| **Observability** | Log prompts, tool calls, source artifact IDs, validation results, and human overrides per modernization unit. |
| **Operations ownership** | Put the platform team in charge of the workbench, with explicit named approvers from architecture, QA, and the mainframe SME group for each wave. |
| **Change scope** | Separate code transformation from database platform replacement and core scheduler replacement in the first release. Combining all three at once hides root causes when validation fails. |
