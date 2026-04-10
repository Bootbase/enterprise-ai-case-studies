# Enterprise AI Case Studies

A catalog of real-world enterprise AI case studies, each researched, designed, and documented end-to-end.

## Canonical Index

The maintained case-study index lives in [docs/use-cases/README.md](docs/use-cases/README.md). Use that file as the source of truth for IDs, folders, and lifecycle state.

## Workflow

- Add a new use case with [.agents/skills/research-new/SKILL.md](.agents/skills/research-new/SKILL.md).
- Detail an existing `research` entry with [.agents/skills/research-complete/SKILL.md](.agents/skills/research-complete/SKILL.md).
- Reuse the documented prompts in [docs/PROMPT.md](docs/PROMPT.md).
- Use the shared markdown templates in [.agents/templates/](.agents/templates/).

## Verification

- Run `research-runner verify-links --root .` to verify repository markdown links and reject placeholder URLs.
- Add `--check-remote` when you want the verifier to issue HTTP checks for external source links.
- The verifier is wired into the `research-new` and `research-complete` workflow checks for generated artifacts.
