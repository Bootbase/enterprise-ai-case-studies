from __future__ import annotations

import argparse
from pathlib import Path

from .app import run_workflow
from .backends import BACKENDS, get_backend
from .config import build_config
from .models import WorkflowMode
from .verification import verify_repository_documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run or resume the research workflow.")
    run_parser.add_argument("--root", default=".", help="Repository root. Defaults to the current directory.")
    run_parser.add_argument(
        "--backend",
        choices=sorted(BACKENDS),
        default="claude",
        help="Agent backend to use. Defaults to 'claude'.",
    )
    run_parser.add_argument("--agent-bin", default=None, help="Agent binary to execute. Defaults based on --backend.")
    run_parser.add_argument("--sleep-hours", type=int, default=4, help="Hours to wait before retrying after a limit hit.")
    run_parser.add_argument(
        "--max-runtime-hours",
        type=float,
        default=24,
        help="Maximum total runtime for the looping app before it stops cleanly. Defaults to 24 hours.",
    )
    run_parser.add_argument("--session-name", help="Explicit session name. Defaults to a generated name.")
    run_parser.add_argument("--git-remote", help="Explicit Git remote to push to. Defaults to the tracked upstream remote.")
    run_parser.add_argument("--no-push", action="store_true", help="Commit locally without pushing.")
    run_parser.add_argument(
        "--workflow-mode",
        choices=[mode.value for mode in WorkflowMode],
        default=WorkflowMode.NEW_AND_COMPLETE.value,
        help=(
            "Choose whether to create and complete new use cases (`new-and-complete`) "
            "or recursively detail the next existing non-detailed use case (`detail-next`)."
        ),
    )
    run_parser.add_argument(
        "--resume-state",
        help="Alternate state-file path. Defaults to .research-runner/state.json under the repo root.",
    )

    verify_parser = subparsers.add_parser("verify-links", help="Verify markdown links and placeholder URLs.")
    verify_parser.add_argument("--root", default=".", help="Repository root. Defaults to the current directory.")
    verify_parser.add_argument(
        "--check-remote",
        action="store_true",
        help="Also issue HTTP checks for external URLs. Requires network access.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        backend = get_backend(args.backend, args.agent_bin)
        config = build_config(
            root=args.root,
            backend=backend,
            sleep_hours=args.sleep_hours,
            max_runtime_hours=args.max_runtime_hours,
            session_name=args.session_name,
            git_remote=args.git_remote,
            no_push=args.no_push,
            state_path=args.resume_state,
            workflow_mode=args.workflow_mode,
        )
        return run_workflow(config)

    if args.command == "verify-links":
        verified = verify_repository_documents(Path(args.root).resolve(), check_remote=args.check_remote)
        print(f"Verified markdown links in {verified} files")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
