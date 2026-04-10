# Research Runner

`research_runner` is a Python CLI that drives coding agent CLIs through the `research-new` and `research-complete` workflow for this repository.

It supports multiple agent backends. Each backend shells out to a local agent binary, persists workflow state, and commits/pushes generated use-case files after each phase.

## Supported Backends

| Backend | Binary | Session Resume | Notes |
|---------|--------|---------------|-------|
| `claude` (default) | `claude` | Yes | Claude Code CLI with `--dangerously-skip-permissions` |
| `codex` | `codex` | No | OpenAI Codex CLI with `--full-auto` |

## What It Does

The tool will:

1. verify the agent binary is installed and authenticated (backend-specific)
2. start or resume an agent session
3. run one of these recursive workflows:
   - `new-and-complete`: `/research-new`, then `/research-complete <topicId>`
   - `detail-next`: find the next lowest-numbered use case that is not `detailed`, then run `/research-complete <topicId>`
4. infer the `topicId` from agent output and the new use-case directory when needed
5. verify the generated files, markdown links, and placeholder URLs
6. commit and optionally push:
   - repository index files such as `README.md` and `docs/use-cases/README.md`
   - the generated or updated `docs/use-cases/.../UC-...` directory
7. if the agent hits a resettable usage limit, wait and retry the unfinished phase
8. after a successful cycle, start the next cycle in the selected workflow mode
9. stop only when:
   - you stop the process
   - the agent hits a weekly/terminal limit
   - `detail-next` has no remaining use cases to detail
   - the configured max runtime is reached

## Prerequisites

- Python 3.11+
- An agent CLI installed locally and available on `PATH`:
  - **Claude**: `claude` (requires Claude account login)
  - **Codex**: `codex` (requires OpenAI authentication)
- Git repository with a configured upstream branch, unless you pass `--git-remote` or `--no-push`
- Run from this repository root, not a subdirectory

## Install

From the repository root:

```bash
python -m pip install -e .
```

That installs the console script:

```bash
research-runner
```

You can also run it without installing the script:

```bash
PYTHONPATH=src python -m research_runner run
```

## Quick Start

From the repository root:

```bash
# Default: Claude backend
research-runner run --root .

# With Codex backend
research-runner run --root . --backend codex

# Typical production run
research-runner run --root . --sleep-hours 4 --max-runtime-hours 24
```

## Common Commands

Run with default settings (Claude):

```bash
research-runner run --root .
```

Run with Codex:

```bash
research-runner run --root . --backend codex
```

Recursively detail the next existing non-`detailed` use case:

```bash
research-runner run --root . --workflow-mode detail-next
```

Commit locally but do not push:

```bash
research-runner run --root . --no-push
```

Use an explicit remote:

```bash
research-runner run --root . --git-remote origin
```

Resume from an alternate state file:

```bash
research-runner run --root . --resume-state /path/to/state.json
```

Use a non-default agent binary:

```bash
research-runner run --root . --agent-bin /path/to/claude
research-runner run --root . --backend codex --agent-bin /path/to/codex
```

Run for 8 hours instead of the default 24:

```bash
research-runner run --root . --max-runtime-hours 8
```

Verify repository markdown links:

```bash
research-runner verify-links --root .
```

Verify repository markdown links and issue HTTP checks for external URLs:

```bash
research-runner verify-links --root . --check-remote
```

## CLI Arguments

`research-runner run` supports:

- `--root`
  Repository root. Defaults to the current directory.
- `--backend`
  Agent backend to use: `claude` (default) or `codex`.
- `--agent-bin`
  Agent binary to execute. Defaults based on `--backend`.
- `--sleep-hours`
  Hours to wait before retrying after an agent limit hit. Defaults to `4`.
- `--max-runtime-hours`
  Maximum total runtime for the looping app before it stops cleanly. Defaults to `24`.
- `--session-name`
  Optional explicit session name.
- `--git-remote`
  Remote to push to. If omitted, the tracked upstream remote is used.
- `--no-push`
  Commit locally without pushing.
- `--workflow-mode`
  `new-and-complete` to create and complete new use cases, or `detail-next` to recursively complete the next existing use case that is not yet `detailed`.
- `--resume-state`
  Alternate path for the persisted state file.

`research-runner verify-links` supports:

- `--root`
  Repository root. Defaults to the current directory.
- `--check-remote`
  Also issue HTTP checks for external URLs. This requires network access.

## How Backends Work

Each backend implements the `AgentBackend` interface:

- **`preflight()`** — verifies the agent binary is installed and authenticated
- **`build_prompt()`** — translates a skill name into an agent-specific command
  - Claude: uses `/skill-name` invocation syntax
  - Codex: reads the full SKILL.md content from `.agents/skills/` and passes it as the prompt
- **`run()`** — executes the command, streams output, detects limits
- **`extract_log_texts()`** — parses backend-specific log format for topic ID inference

### Adding a New Backend

Create a new module in `src/research_runner/backends/` implementing `AgentBackend`, then register it in `backends/__init__.py`:

```python
BACKENDS: dict[str, type[AgentBackend]] = {
    "claude": ClaudeBackend,
    "codex": CodexBackend,
    "your-agent": YourAgentBackend,
}
```

## How Resume Works

The runner persists state in:

```text
.research-runner/state.json
```

If a run stops partway through because of an interruption or a resettable limit, rerun the same command. The runner will load the saved phase and continue from there.

For Claude, the runner recovers the session UUID from logs and uses `--resume`. For backends without session support (Codex), each phase is a fresh invocation.

After a fully successful cycle, the runner resets its internal phase state and starts the next cycle for the same workflow mode until one of the stop conditions is hit.

## Logs And Artifacts

The runner writes under:

```text
.research-runner/
```

Important files:

- `.research-runner/state.json`
  Current workflow state
- `.research-runner/logs/research-new.ndjson`
  Streamed agent output for `research-new`
- `.research-runner/logs/research-complete.ndjson`
  Streamed agent output for `research-complete`
- `.research-runner/baselines/`
  Internal snapshots used to safely handle pre-existing index-file edits and detect pre-existing use-case directories

## Git Behavior

In `new-and-complete` mode, after a successful `research-new`, the runner commits and pushes:

- the generated `UC-...` directory under `docs/use-cases/`
- any generated delta in `README.md`
- any generated delta in `docs/use-cases/README.md`

After a successful `research-complete`, it does the same again.

Commit messages are:

- `chore(research): add UC-XXX via research runner`
- `chore(research): complete UC-XXX via research runner`

In `detail-next` mode, each cycle skips `research-new`, selects the next lowest-numbered existing use case that is not `detailed`, and runs `research-complete` for that topic. When no such use case remains, the runner stops cleanly.

## Dirty Index Files

If `README.md` or `docs/use-cases/README.md` is already dirty before a fresh run:

- the runner snapshots your current version
- temporarily restores the worktree copy to `HEAD`
- runs the agent and stages only the generated delta for the automated commit
- restores your original local edits afterward

If your local edits overlap heavily with the agent's generated delta, restoration can still produce merge conflicts.

## Troubleshooting

`Claude binary not found` / `Codex binary not found`

- Verify the agent binary is installed and on `PATH`, or pass `--agent-bin`.

`Unsupported Claude auth mode`

- Run `claude auth status --text` and make sure you are logged in with a Claude account.

`Current branch has no upstream`

- Set an upstream branch or pass `--git-remote`.

`Could not infer a topic ID from agent output`

- The agent may not have completed its task. Check the logs in `.research-runner/logs/`.

Run marked `waiting_for_limit_reset`

- Rerun the same command and let the runner sleep until the saved retry time, or adjust `--sleep-hours` for future runs.

Run stops after a successful cycle even though you expected it to continue

- Check `--max-runtime-hours`. The app stops cleanly once that total runtime budget is exhausted.

## Typical Real Run

```bash
# Claude
research-runner run --root . --sleep-hours 4 --max-runtime-hours 24

# Codex
research-runner run --root . --backend codex --max-runtime-hours 24
```

Then monitor:

- console output for live agent progress
- `.research-runner/state.json` for phase/status
- `.research-runner/logs/*.ndjson` for raw streamed output
