# AI Agent Instructions

## Scope

This repo is a catalog of real-world enterprise AI use cases — each researched, designed, and documented end-to-end. Use cases follow a lifecycle: `research` → `detailed`.

## Navigation

| I need to...                              | Action                                                                          |
| ----------------------------------------- | ------------------------------------------------------------------------------- |
| Add a new use case                        | `/research-new`                                                                 |
| Detail an existing `research` use case    | `/research-complete`                                                            |
| Browse the use case index                 | Read [use-cases/README.md](use-cases/README.md)                                 |
| Understand the file structure             | Read [use-cases/_templates/](use-cases/_templates/)                             |
| See reusable prompts (copy-paste format)  | Read [use-cases/PROMPT.md](use-cases/PROMPT.md)                                 |

## Use Case Lifecycle

```
/research-new                    /research-complete
      │                                │
      ▼                                ▼
┌──────────┐                   ┌──────────────┐
│ research │ ─────────────────▸│   detailed   │
│          │                   │              │
│ Files:   │                   │ Files:       │
│ • use-case.md                │ • use-case.md (status updated)
│          │                   │ • solution-design.md
│          │                   │ • implementation-guide.md
│          │                   │ • evaluation.md
│          │                   │ • references.md
└──────────┘                   └──────────────┘
```

## Loading Priority

1. Load this file at session start.
2. Check the navigation table before starting work — invoke the matching skill.
3. Load templates and PROMPT.md on demand.
