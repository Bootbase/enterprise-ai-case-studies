from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from ..console import info
from ..models import AgentRunResult, LimitHit
from ..skill_resolver import resolve_skill_prompt
from .base import AgentBackend


RATE_LIMIT_RE = re.compile(r"rate.limit|429|too.many.requests|quota.exceeded", re.IGNORECASE)


def _detect_codex_limit(text: str) -> LimitHit | None:
    if RATE_LIMIT_RE.search(text):
        return LimitHit(kind="usage", matched_text=text.strip()[:120], reset_at=None)
    return None


def _reader(stream: Any, stream_name: str, target_queue: queue.Queue[tuple[str, str]]) -> None:
    try:
        for line in iter(stream.readline, ""):
            target_queue.put((stream_name, line))
    finally:
        target_queue.put((stream_name, ""))


def _log_event(log_path: Path, stream_name: str, raw_line: str) -> None:
    event = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "stream": stream_name,
        "text": raw_line.rstrip("\n"),
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    return env


class CodexBackend(AgentBackend):
    """Backend that drives the OpenAI Codex CLI (``codex``)."""

    default_bin: str = "codex"

    @property
    def name(self) -> str:
        return "codex"

    @property
    def supports_sessions(self) -> bool:
        return False

    def preflight(self, root: Path) -> None:
        if shutil.which(self.agent_bin) is None and not Path(self.agent_bin).exists():
            raise RuntimeError(f"Codex binary not found: {self.agent_bin}")

    def build_prompt(self, root: Path, skill_name: str, args: str | None = None) -> str:
        return resolve_skill_prompt(root, skill_name, args)

    def run(
        self,
        *,
        root: Path,
        command: str,
        log_path: Path,
        session_name: str,
        session_id: str | None = None,
        resume: bool = False,
    ) -> AgentRunResult:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        args = [
            self.agent_bin,
            "exec",
            "--full-auto",
            command,
        ]

        info(f"Executing: {self.agent_bin} exec --full-auto <prompt>")
        process = subprocess.Popen(
            args,
            cwd=root,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            env=_child_env(),
        )

        assert process.stdout is not None
        assert process.stderr is not None

        q: queue.Queue[tuple[str, str]] = queue.Queue()
        threads = [
            threading.Thread(target=_reader, args=(process.stdout, "stdout", q), daemon=True),
            threading.Thread(target=_reader, args=(process.stderr, "stderr", q), daemon=True),
        ]
        for thread in threads:
            thread.start()

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        closed = {"stdout": False, "stderr": False}
        limit_hit: LimitHit | None = None

        while not all(closed.values()):
            stream_name, line = q.get()
            if line == "":
                closed[stream_name] = True
                continue
            _log_event(log_path, stream_name, line)

            if stream_name == "stdout":
                stdout_lines.append(line.rstrip("\n"))
                stripped = line.strip()
                if stripped:
                    print(stripped)
            else:
                stderr_lines.append(line.rstrip("\n"))
                print(line.rstrip("\n"))

            if not limit_hit:
                limit_hit = _detect_codex_limit(line)

        return_code = process.wait()
        rendered = "\n".join(stdout_lines)
        return AgentRunResult(
            exit_code=return_code,
            rendered_text=rendered,
            raw_output=rendered,
            stderr_text="\n".join(stderr_lines),
            session_id=None,
            limit_hit=limit_hit,
        )

    def extract_log_texts(self, log_path: Path) -> list[str]:
        if not log_path.exists():
            return []
        texts: list[str] = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception:
                texts.append(line)
                continue
            text = payload.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text)
        return texts
