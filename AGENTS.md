# AI Agent Instructions

## Scope

This repo is a catalog of real-world enterprise AI use cases — each researched, designed, and documented end-to-end. Use cases follow a lifecycle: `research` → `detailed`.

## Navigation

| I need to...                              | Action                                                                                         |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Add a new use case                        | Read [.agents/skills/research-new/SKILL.md](.agents/skills/research-new/SKILL.md)             |
| Detail an existing `research` use case    | Read [.agents/skills/research-complete/SKILL.md](.agents/skills/research-complete/SKILL.md)   |
| Browse the use case index                 | Read [docs/use-cases/README.md](docs/use-cases/README.md)                                      |
| Understand the file structure             | Read [.agents/templates/](.agents/templates/)                                                 |
| See reusable prompts (copy-paste format)  | Read [docs/PROMPT.md](docs/PROMPT.md)                                                         |

## Use Case Lifecycle

```
research-new                     research-complete
      │                                │
      ▼                                ▼
┌──────────┐                   ┌──────────────┐
│ research │ ─────────────────▸│   detailed   │
│          │                   │              │
│ Files:   │                   │ Files:       │
│ • docs/use-cases/{category}/  │ • docs/use-cases/{category}/
│   UC-NNN-slug/index.md        │   UC-NNN-slug/index.md (status updated)
│          │                   │ • solution-design.md
│          │                   │ • implementation-guide.md
│          │                   │ • evaluation.md
│          │                   │ • references.md
└──────────┘                   └──────────────┘
```

## Loading Priority

1. Load this file at session start.
2. Check the navigation table before starting work — load the matching skill from `.agents/skills/`.
3. `.claude/skills/` mirrors `.agents/skills/` via symlink.
4. Load templates and PROMPT.md on demand.
