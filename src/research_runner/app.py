from __future__ import annotations

import shutil
import time
from difflib import unified_diff
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from subprocess import run

from .config import AppConfig
from .console import banner, error, info, warn
from .git_ops import (
    apply_patch_to_index,
    GitError,
    commit,
    current_branch,
    dirty_paths,
    ensure_repo_root,
    has_path_changes,
    push,
    restore_staged_from_head,
    restore_worktree_from_head,
    stage_paths,
    show_head_file,
    upstream_ref,
)
from .models import AgentRunResult, Phase, RunState, WorkflowMode
from .state import default_state, load_state, save_state
from .topic_inference import extract_topic_ids
from .verification import find_next_topic_needing_detail, find_use_case_dirs, verify_research_complete, verify_research_new


class RunnerError(RuntimeError):
    pass


INDEX_FILES = ("README.md", "docs/use-cases/README.md")


def _load_or_create_state(config: AppConfig) -> tuple[RunState, bool]:
    state = load_state(config.state_path)
    if state and state.current_phase not in {Phase.COMPLETED, Phase.STOPPED, Phase.FAILED}:
        if Path(state.root).resolve() != config.root.resolve():
            raise RunnerError(f"State file root {state.root} does not match requested root {config.root}")
        if state.workflow_mode != config.workflow_mode:
            raise RunnerError(
                f"State file workflow_mode {state.workflow_mode.value} does not match requested mode {config.workflow_mode.value}"
            )
        info(f"Resuming workflow from {config.state_path}")
        state.sleep_hours = config.sleep_hours
        return state, True

    shutil.rmtree(config.state_path.parent, ignore_errors=True)
    return default_state(config.root, config.session_name, config.sleep_hours, config.workflow_mode), False


def _phase_log_path(config: AppConfig, state: RunState, phase_name: str) -> Path:
    return config.logs_dir / f"{phase_name}.ndjson"


def _recover_session_id_from_log(config: AppConfig, log_path: Path) -> str | None:
    return config.backend.recover_session_id(log_path)


def _infer_topic_id_from_log(config: AppConfig, log_path: Path, root: Path, excluded_ids: set[str] | None = None) -> str:
    texts = config.backend.extract_log_texts(log_path)
    if not texts:
        raise RunnerError(f"Log file does not exist or is empty: {log_path}")

    candidates = extract_topic_ids("\n".join(texts))
    if not candidates:
        raise RunnerError("Could not infer a topic ID from agent output")

    if excluded_ids:
        new_candidates = [
            candidate
            for candidate in candidates
            if candidate not in excluded_ids and find_use_case_dirs(root, candidate)
        ]
        if len(new_candidates) == 1:
            return new_candidates[0]

    valid = [candidate for candidate in candidates if find_use_case_dirs(root, candidate)]
    if len(valid) == 1:
        return valid[0]
    if len(candidates) == 1:
        return candidates[0]
    raise RunnerError(f"Could not disambiguate inferred topic IDs: {', '.join(candidates)}")


def _mark_failed(config: AppConfig, state: RunState, message: str) -> int:
    error(message)
    state.current_phase = Phase.FAILED
    state.failure_message = message
    save_state(config.state_path, state)
    return 1


def _fresh_preflight(config: AppConfig, state: RunState) -> None:
    config.backend.preflight(config.root)
    ensure_repo_root(config.root)

    branch = current_branch(config.root)
    upstream = upstream_ref(config.root)
    if not config.no_push and not (config.git_remote or upstream):
        raise RunnerError("Current branch has no upstream and no --git-remote was provided")

    state.git.branch = branch
    state.git.upstream = upstream
    state.git.push_remote = config.git_remote or (upstream.split("/", 1)[0] if upstream else None)
    state.artifacts.logs_dir = str(config.logs_dir)

    if config.workflow_mode == WorkflowMode.DETAIL_NEXT:
        next_topic = find_next_topic_needing_detail(config.root)
        if next_topic is None:
            state.current_phase = Phase.STOPPED
            state.stop_reason = "No use cases remain that are not detailed"
            save_state(config.state_path, state)
            return
        state.topic_id = next_topic.topic_id
        state.artifacts.research_new_folder = next_topic.use_case_dir
        state.current_phase = Phase.RESEARCH_COMPLETE_RUNNING
        info(f"Selected {state.topic_id} as the next use case to detail")
    else:
        state.topic_id = None
        state.artifacts.research_new_folder = None
        state.current_phase = Phase.RESEARCH_NEW_RUNNING

    _prepare_index_files_for_run(config)
    _snapshot_existing_use_case_dirs(config)
    _snapshot_index_baselines(config)
    save_state(config.state_path, state)


def _resume_wait(config: AppConfig, state: RunState) -> None:
    target = None
    if state.waiting_until:
        target = datetime.fromisoformat(state.waiting_until)
    if target is None:
        target = datetime.now().astimezone() + timedelta(hours=state.sleep_hours)
    remaining = (target - datetime.now().astimezone()).total_seconds()
    if remaining > 0:
        sleep_for = remaining
        runtime_remaining = _runtime_remaining_seconds(config, state)
        if runtime_remaining is not None:
            sleep_for = min(sleep_for, max(runtime_remaining, 0))
        if sleep_for > 0:
            info(f"Sleeping for {sleep_for:.0f}s before retrying {state.resume_phase.value if state.resume_phase else 'workflow'}")
            time.sleep(sleep_for)
    state.waiting_until = None
    if state.resume_phase is None:
        raise RunnerError("State is waiting for a retry but no resume_phase is recorded")
    state.current_phase = state.resume_phase
    state.resume_phase = None
    save_state(config.state_path, state)


def _schedule_retry(config: AppConfig, state: RunState, phase: Phase, message: str) -> None:
    warn(message)
    state.current_phase = Phase.WAITING_FOR_LIMIT_RESET
    state.resume_phase = phase
    state.limit_retries += 1
    state.waiting_until = (datetime.now().astimezone() + timedelta(hours=state.sleep_hours)).isoformat()
    save_state(config.state_path, state)


def _runtime_deadline(config: AppConfig, state: RunState) -> datetime | None:
    if state.timestamps.started_at is None:
        return None
    return datetime.fromisoformat(state.timestamps.started_at) + timedelta(hours=config.max_runtime_hours)


def _runtime_limit_reached(config: AppConfig, state: RunState) -> bool:
    deadline = _runtime_deadline(config, state)
    if deadline is None:
        return False
    return datetime.now().astimezone() >= deadline


def _runtime_remaining_seconds(config: AppConfig, state: RunState) -> float | None:
    deadline = _runtime_deadline(config, state)
    if deadline is None:
        return None
    return (deadline - datetime.now().astimezone()).total_seconds()


def _next_cycle_state(config: AppConfig, previous_state: RunState) -> RunState:
    started_at = previous_state.timestamps.started_at
    shutil.rmtree(config.state_path.parent, ignore_errors=True)
    state = default_state(config.root, config.session_name, config.sleep_hours, config.workflow_mode)
    if started_at is not None:
        state.timestamps.started_at = started_at
    state.timestamps.updated_at = state.timestamps.started_at
    return state


def _recover_session_id_for_phase(config: AppConfig, state: RunState, phase_name: str) -> str | None:
    if not config.backend.supports_sessions:
        return None

    candidate_phase_names = [phase_name]
    if phase_name != "research-complete":
        candidate_phase_names.append("research-complete")
    if phase_name != "research-new":
        candidate_phase_names.append("research-new")

    seen: set[str] = set()
    for candidate_phase_name in candidate_phase_names:
        if candidate_phase_name in seen:
            continue
        seen.add(candidate_phase_name)
        recovered = _recover_session_id_from_log(config, _phase_log_path(config, state, candidate_phase_name))
        if recovered:
            return recovered
    return None


def _stop_run(config: AppConfig, state: RunState, reason: str, *, exit_code: int = 0, warning: bool = False) -> int:
    if warning:
        warn(reason)
    else:
        info(reason)
    state.current_phase = Phase.STOPPED
    state.stop_reason = reason
    save_state(config.state_path, state)
    return exit_code


def _index_snapshot_slug(relative_path: str) -> str:
    return relative_path.replace("/", "__")


def _index_baseline_path(config: AppConfig, relative_path: str) -> Path:
    return config.baselines_dir / "index-files" / f"{_index_snapshot_slug(relative_path)}.baseline"


def _existing_use_case_dirs_path(config: AppConfig) -> Path:
    return config.baselines_dir / "existing-use-case-dirs.txt"


def _user_index_snapshot_path(config: AppConfig, relative_path: str) -> Path:
    return config.baselines_dir / "index-files" / f"{_index_snapshot_slug(relative_path)}.user"


def _head_index_snapshot_path(config: AppConfig, relative_path: str) -> Path:
    return config.baselines_dir / "index-files" / f"{_index_snapshot_slug(relative_path)}.head"


def _prepare_index_files_for_run(config: AppConfig) -> None:
    for relative_path in INDEX_FILES:
        file_path = config.root / relative_path
        if not file_path.exists():
            continue
        if not dirty_paths(config.root, relative_path):
            continue

        config.baselines_dir.mkdir(parents=True, exist_ok=True)
        user_snapshot_path = _user_index_snapshot_path(config, relative_path)
        head_snapshot_path = _head_index_snapshot_path(config, relative_path)
        user_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        user_snapshot_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
        head_snapshot_path.write_text(show_head_file(config.root, relative_path), encoding="utf-8")
        restore_worktree_from_head(config.root, relative_path)
        warn(f"{relative_path} is already dirty; local edits were snapshotted and temporarily hidden during the run")


def _snapshot_existing_use_case_dirs(config: AppConfig) -> None:
    existing = sorted(
        str(path.relative_to(config.root))
        for path in config.root.glob("docs/use-cases/*/UC-*")
        if path.is_dir()
    )
    target = _existing_use_case_dirs_path(config)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(existing) + ("\n" if existing else ""), encoding="utf-8")


def _existing_use_case_dirs(config: AppConfig) -> set[str]:
    path = _existing_use_case_dirs_path(config)
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _existing_topic_ids(config: AppConfig) -> set[str]:
    topic_ids: set[str] = set()
    for relative_dir in _existing_use_case_dirs(config):
        name = Path(relative_dir).name
        if name.startswith("UC-"):
            topic_ids.add(name.split("-", 2)[0] + "-" + name.split("-", 2)[1])
    return topic_ids


def _restore_user_index_overlays(config: AppConfig) -> None:
    for relative_path in INDEX_FILES:
        user_snapshot = _user_index_snapshot_path(config, relative_path)
        head_snapshot = _head_index_snapshot_path(config, relative_path)
        file_path = config.root / relative_path
        if not user_snapshot.exists() or not head_snapshot.exists() or not file_path.exists():
            continue

        with NamedTemporaryFile("w+", encoding="utf-8", delete=False) as current_file:
            current_file.write(file_path.read_text(encoding="utf-8"))
            current_file.flush()
            current_path = current_file.name

        try:
            completed = run(
                ["git", "merge-file", "-p", current_path, str(head_snapshot), str(user_snapshot)],
                cwd=config.root,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            if completed.returncode not in (0, 1):
                raise RunnerError(
                    f"Failed to restore pre-existing {relative_path} edits after the run: "
                    f"{completed.stderr.strip() or completed.stdout.strip()}"
                )
            file_path.write_text(completed.stdout, encoding="utf-8")
            if completed.returncode == 1:
                warn(f"{relative_path} was restored with merge conflicts against pre-existing local edits")
        finally:
            Path(current_path).unlink(missing_ok=True)


def _snapshot_index_baselines(config: AppConfig) -> None:
    for relative_path in INDEX_FILES:
        baseline_path = _index_baseline_path(config, relative_path)
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        source = config.root / relative_path
        if source.exists():
            baseline_path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _stage_index_delta(config: AppConfig, relative_path: str) -> None:
    file_path = config.root / relative_path
    baseline_path = _index_baseline_path(config, relative_path)
    if not file_path.exists():
        return
    if not baseline_path.exists():
        stage_paths(config.root, [relative_path])
        return

    baseline_text = baseline_path.read_text(encoding="utf-8")
    current_text = file_path.read_text(encoding="utf-8")
    if baseline_text == current_text:
        restore_staged_from_head(config.root, relative_path)
        return

    patch_text = "".join(
        unified_diff(
            baseline_text.splitlines(keepends=True),
            current_text.splitlines(keepends=True),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
        )
    )
    if not patch_text:
        restore_staged_from_head(config.root, relative_path)
        return

    restore_staged_from_head(config.root, relative_path)
    try:
        apply_patch_to_index(config.root, patch_text)
    except GitError as exc:
        raise RunnerError(
            f"Could not isolate {relative_path} changes from pre-existing edits; "
            f"the generated delta overlaps with earlier uncommitted changes: {exc}"
        ) from exc


def _run_phase(config: AppConfig, state: RunState, phase: Phase, skill_name: str, skill_args: str | None = None) -> bool | None:
    phase_name = "research-new" if phase == Phase.RESEARCH_NEW_RUNNING else "research-complete"
    resume_session = state.session_started and config.backend.supports_sessions
    if not state.session_started:
        state.session_started = True
    if resume_session and state.session_id is None:
        state.session_id = _recover_session_id_for_phase(config, state, phase_name)
        if state.session_id is None:
            resume_session = False

    command_text = config.backend.build_prompt(config.root, skill_name, skill_args)
    state.current_phase = phase
    state.last_command = command_text
    save_state(config.state_path, state)

    log_path = _phase_log_path(config, state, phase_name)
    result = config.backend.run(
        root=config.root,
        command=command_text,
        log_path=log_path,
        session_name=state.session_name,
        session_id=state.session_id,
        resume=resume_session,
    )
    if result.session_id:
        state.session_id = result.session_id

    if result.limit_hit is not None:
        if result.limit_hit.kind == "weekly":
            state.current_phase = Phase.STOPPED
            state.resume_phase = phase
            state.stop_reason = f"Agent weekly limit hit: {result.limit_hit.matched_text}"
            save_state(config.state_path, state)
            return None
        _schedule_retry(config, state, phase, f"Agent usage limit hit: {result.limit_hit.matched_text}")
        return False
    if result.exit_code != 0:
        raise RunnerError(f"Agent exited with code {result.exit_code}: {result.stderr_text or result.raw_output}")

    state.current_phase = (
        Phase.RESEARCH_NEW_VERIFYING if phase == Phase.RESEARCH_NEW_RUNNING else Phase.RESEARCH_COMPLETE_VERIFYING
    )
    save_state(config.state_path, state)
    return True


def _commit_phase(config: AppConfig, state: RunState, *, message: str, paths: list[str]) -> None:
    stage_targets = [path for path in paths if path not in INDEX_FILES]
    for relative_path in paths:
        if relative_path in INDEX_FILES:
            _stage_index_delta(config, relative_path)
    if stage_targets:
        stage_paths(config.root, stage_targets)
    commit_sha = commit(config.root, message)
    if commit_sha:
        info(f"Created commit {commit_sha}")
        state.git.last_commit = commit_sha
    elif has_path_changes(config.root, paths):
        info("Relevant paths remain dirty but no new commit was created; assuming commit step is already satisfied")
    else:
        info("No changes to commit for this phase")

    if not config.no_push and state.git.push_remote and state.git.branch and commit_sha:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                push(config.root, state.git.push_remote, state.git.branch)
                info(f"Pushed {state.git.branch} to {state.git.push_remote}")
                last_error = None
                break
            except GitError as exc:
                last_error = exc
                warn(f"Push attempt {attempt}/3 failed: {exc}")
                if attempt < 3:
                    time.sleep(attempt)
        if last_error is not None:
            raise last_error
    _snapshot_index_baselines(config)
    save_state(config.state_path, state)


def run_workflow(config: AppConfig) -> int:
    state, _ = _load_or_create_state(config)
    save_state(config.state_path, state)

    try:
        while True:
            if _runtime_limit_reached(config, state):
                try:
                    _restore_user_index_overlays(config)
                except RunnerError as restore_exc:
                    warn(str(restore_exc))
                return _stop_run(
                    config,
                    state,
                    f"Stopped after reaching the max runtime of {config.max_runtime_hours:g} hours",
                )

            if state.current_phase == Phase.PREFLIGHT:
                banner("Preflight")
                _fresh_preflight(config, state)
                continue

            if state.current_phase == Phase.WAITING_FOR_LIMIT_RESET:
                banner("Waiting For Limit Reset")
                _resume_wait(config, state)
                continue

            if state.current_phase == Phase.RESEARCH_NEW_RUNNING:
                banner("Research New")
                phase_result = _run_phase(config, state, Phase.RESEARCH_NEW_RUNNING, "research-new")
                if phase_result is None:
                    try:
                        _restore_user_index_overlays(config)
                    except RunnerError as restore_exc:
                        warn(str(restore_exc))
                    return _stop_run(config, state, state.stop_reason or "Agent stopped the workflow")
                if not phase_result:
                    continue
                continue

            if state.current_phase == Phase.RESEARCH_NEW_VERIFYING:
                banner("Verify Research New")
                if state.topic_id is None:
                    state.topic_id = _infer_topic_id_from_log(
                        config,
                        _phase_log_path(config, state, "research-new"),
                        config.root,
                        excluded_ids=_existing_topic_ids(config),
                    )
                verification = verify_research_new(config.root, state.topic_id)
                if verification.use_case_dir in _existing_use_case_dirs(config):
                    raise RunnerError(
                        f"{verification.use_case_dir} already existed before the run; "
                        "refusing to commit a pre-existing use-case directory"
                    )
                state.artifacts.research_new_folder = verification.use_case_dir
                state.current_phase = Phase.RESEARCH_NEW_GIT
                save_state(config.state_path, state)
                continue

            if state.current_phase == Phase.RESEARCH_NEW_GIT:
                banner("Git Commit Research New")
                if not state.topic_id or not state.artifacts.research_new_folder:
                    raise RunnerError("Missing topic_id or use case folder before research-new Git step")
                _commit_phase(
                    config,
                    state,
                    message=f"chore(research): add {state.topic_id} via research runner",
                    paths=["README.md", "docs/use-cases/README.md", state.artifacts.research_new_folder],
                )
                state.current_phase = Phase.RESEARCH_COMPLETE_RUNNING
                save_state(config.state_path, state)
                continue

            if state.current_phase == Phase.RESEARCH_COMPLETE_RUNNING:
                banner("Research Complete")
                if not state.topic_id:
                    raise RunnerError("Cannot run research-complete without a topic_id")
                phase_result = _run_phase(
                    config,
                    state,
                    Phase.RESEARCH_COMPLETE_RUNNING,
                    "research-complete",
                    state.topic_id,
                )
                if phase_result is None:
                    try:
                        _restore_user_index_overlays(config)
                    except RunnerError as restore_exc:
                        warn(str(restore_exc))
                    return _stop_run(config, state, state.stop_reason or "Agent stopped the workflow")
                if not phase_result:
                    continue
                continue

            if state.current_phase == Phase.RESEARCH_COMPLETE_VERIFYING:
                banner("Verify Research Complete")
                if not state.topic_id:
                    raise RunnerError("Cannot verify research-complete without a topic_id")
                verification = verify_research_complete(config.root, state.topic_id)
                state.artifacts.research_new_folder = verification.use_case_dir
                state.current_phase = Phase.RESEARCH_COMPLETE_GIT
                save_state(config.state_path, state)
                continue

            if state.current_phase == Phase.RESEARCH_COMPLETE_GIT:
                banner("Git Commit Research Complete")
                if not state.topic_id or not state.artifacts.research_new_folder:
                    raise RunnerError("Missing topic_id or use case folder before research-complete Git step")
                _commit_phase(
                    config,
                    state,
                    message=f"chore(research): complete {state.topic_id} via research runner",
                    paths=["README.md", "docs/use-cases/README.md", state.artifacts.research_new_folder],
                )
                state.current_phase = Phase.COMPLETED
                save_state(config.state_path, state)
                _restore_user_index_overlays(config)
                info(f"Workflow cycle completed successfully. State saved to {config.state_path}")
                continue

            if state.current_phase == Phase.COMPLETED:
                if _runtime_limit_reached(config, state):
                    return _stop_run(
                        config,
                        state,
                        f"Stopped after reaching the max runtime of {config.max_runtime_hours:g} hours",
                    )
                if state.workflow_mode == WorkflowMode.DETAIL_NEXT:
                    info("Starting the next detail-next cycle")
                else:
                    info("Starting the next workflow cycle")
                state = _next_cycle_state(config, state)
                save_state(config.state_path, state)
                continue

            if state.current_phase == Phase.STOPPED:
                info(state.stop_reason or f"Workflow stopped. State saved to {config.state_path}")
                return 0

            if state.current_phase == Phase.FAILED:
                return _mark_failed(config, state, state.failure_message or "Workflow is already marked failed")

            raise RunnerError(f"Unhandled phase: {state.current_phase}")

    except KeyboardInterrupt:
        try:
            _restore_user_index_overlays(config)
        except RunnerError as restore_exc:
            warn(str(restore_exc))
        return _stop_run(config, state, "Stopped by user", exit_code=130, warning=True)

    except (RunnerError, GitError) as exc:
        if state.current_phase != Phase.WAITING_FOR_LIMIT_RESET:
            try:
                _restore_user_index_overlays(config)
            except RunnerError as restore_exc:
                warn(str(restore_exc))
        return _mark_failed(config, state, str(exc))
