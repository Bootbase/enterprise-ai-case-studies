from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from .models import VerificationResult


FRONTMATTER_STATUS_RE = re.compile(r'^status:\s*["\']?(?P<status>[^"\']+?)["\']?\s*$', re.MULTILINE)
FRONTMATTER_LAYOUT_RE = re.compile(r'^layout:\s*["\']?(?P<layout>[^"\']+?)["\']?\s*$', re.MULTILINE)
FRONTMATTER_PERMALINK_RE = re.compile(r'^permalink:\s*["\']?(?P<permalink>[^"\']+?)["\']?\s*$', re.MULTILINE)
TOPIC_ID_RE = re.compile(r"^(?P<topic_id>UC-\d+)-")
README_STATUS_RE = re.compile(r"\|\s*(research|detailed)\s*\|", re.IGNORECASE)
INDEX_READMES = ("docs/use-cases/README.md", "README.md")
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
PLACEHOLDER_RE = re.compile(r"\{[A-Za-z][A-Za-z0-9 ,._/+():-]{1,120}\}")
MARKDOWN_LINK_RE = re.compile(r'(?<!!)\[[^\]]+\]\((?P<target><[^>]+>|[^)\s]+(?:\s+"[^"]*")?)\)')
RAW_URL_RE = re.compile(r"https?://[^\s<>)\"']+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(?P<heading>.+?)\s*$", re.MULTILINE)
PLACEHOLDER_URL_RE = re.compile(
    r"https?://[^\s\"')]*(YOUR-|localhost|127\.0\.0\.1|\{[^}]+\}|example\.(?:com|org|net))",
    re.IGNORECASE,
)
HTTP_TIMEOUT_SECONDS = 15
SKIP_DIR_NAMES = {".git", ".research-runner", ".venv", "__pycache__", ".pytest_cache"}

USE_CASE_GLOB = "docs/use-cases/*/UC-*"
USE_CASE_INDEX = "index.md"

REQUIRED_HEADINGS: dict[str, tuple[str, ...]] = {
    "index.md": (
        "## Problem Statement",
        "## Business Case",
        "## Current Workflow",
        "## Target State",
        "## Stakeholders",
        "## Constraints",
        "## Evidence Base",
        "## Scope Boundaries",
    ),
    "solution-design.md": (
        "## What This Design Covers",
        "## Recommended Operating Model",
        "## Architecture",
        "## End-to-End Flow",
        "## AI Responsibilities and Boundaries",
        "## Integration Seams",
        "## Control Model",
        "## Reference Technology Stack",
        "## Key Design Decisions",
    ),
    "implementation-guide.md": (
        "## Build Goal",
        "## Reference Stack",
        "## Delivery Plan",
        "## Core Contracts",
        "## Orchestration Outline",
        "## Prompt And Guardrail Pattern",
        "## Integration Notes",
        "## Evaluation Harness",
        "## Deployment Notes",
    ),
    "evaluation.md": (
        "## Decision Summary",
        "## Published Evidence",
        "## Assumptions And Scenario Model",
        "## Expected Economics",
        "## Quality, Risk, And Failure Modes",
        "## Rollout KPI Set",
        "## Open Questions",
    ),
    "references.md": (
        "## Source Quality Notes",
        "## Source Register",
        "## Claim Map",
    ),
}

EXPECTED_LAYOUTS = {
    "index.md": "use-case",
    "solution-design.md": "use-case-detail",
    "implementation-guide.md": "use-case-detail",
    "evaluation.md": "use-case-detail",
    "references.md": "use-case-detail",
}


def _extract_frontmatter(content: str) -> str | None:
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    return content[: end + 3]


def _extract_frontmatter_status(content: str) -> str | None:
    frontmatter = _extract_frontmatter(content)
    if frontmatter is None:
        return None
    match = FRONTMATTER_STATUS_RE.search(frontmatter)
    if not match:
        return None
    return match.group("status")


def _extract_frontmatter_layout(content: str) -> str | None:
    frontmatter = _extract_frontmatter(content)
    if frontmatter is None:
        return None
    match = FRONTMATTER_LAYOUT_RE.search(frontmatter)
    if not match:
        return None
    return match.group("layout")


def _extract_frontmatter_permalink(content: str) -> str | None:
    frontmatter = _extract_frontmatter(content)
    if frontmatter is None:
        return None
    match = FRONTMATTER_PERMALINK_RE.search(frontmatter)
    if not match:
        return None
    return match.group("permalink")


def _content_without_code(content: str) -> str:
    """Strip fenced code blocks and inline code spans.

    Inline code carries verbatim content (API path templates like
    ``/repos/{owner}/{repo}``, format strings, shell snippets, example URLs).
    These look identical to unfilled template placeholders and raw URLs to
    the prose-oriented heuristics below, so they must be excluded before the
    placeholder, raw-URL, and link checks run.
    """
    stripped = CODE_FENCE_RE.sub("", content)
    return INLINE_CODE_RE.sub("", stripped)


def _content_without_frontmatter(content: str) -> str:
    frontmatter = _extract_frontmatter(content)
    if frontmatter is None:
        return content
    return content[len(frontmatter) :]


def _clean_markdown_link_target(target: str) -> str:
    cleaned = target.strip()
    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned[1:-1]
    for separator in (' "', " '"):
        if separator in cleaned:
            cleaned = cleaned.split(separator, 1)[0]
            break
    return cleaned


def _slugify_heading(text: str) -> str:
    slug = text.strip().lower()
    slug = re.sub(r"<[^>]+>", "", slug)
    slug = re.sub(r"[`*_~\[\]()]", "", slug)
    slug = re.sub(r"[^a-z0-9 -]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-{2,}", "-", slug)
    return slug


def _heading_slugs(content: str) -> set[str]:
    body = _content_without_frontmatter(content)
    seen: Counter[str] = Counter()
    slugs: set[str] = set()
    for match in HEADING_RE.finditer(body):
        base = _slugify_heading(match.group("heading"))
        if not base:
            continue
        index = seen[base]
        seen[base] += 1
        slug = base if index == 0 else f"{base}-{index}"
        slugs.add(slug)
    return slugs


def _iter_repo_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        relative_parts = path.relative_to(root).parts
        if any(part in SKIP_DIR_NAMES or part.endswith(".egg-info") for part in relative_parts):
            continue
        files.append(path)
    return sorted(files)


def _normalize_permalink(permalink: str) -> str:
    cleaned = permalink.strip().strip('"').strip("'")
    if not cleaned.startswith("/"):
        cleaned = "/" + cleaned
    if cleaned != "/" and not cleaned.endswith("/"):
        cleaned += "/"
    return cleaned


def _build_permalink_map(root: Path) -> dict[str, Path]:
    permalink_map: dict[str, Path] = {}
    for path in _iter_repo_markdown_files(root):
        if "docs" not in path.relative_to(root).parts:
            continue
        content = path.read_text(encoding="utf-8")
        permalink = _extract_frontmatter_permalink(content)
        if permalink is None:
            continue
        permalink_map[_normalize_permalink(permalink)] = path
    permalink_map.setdefault("/", root / "docs" / "index.html")
    return permalink_map


def _resolve_site_root_target(root: Path, path_part: str, permalink_map: dict[str, Path]) -> Path | None:
    normalized = _normalize_permalink(path_part) if path_part.endswith("/") or path_part == "/" else path_part
    if normalized in permalink_map:
        return permalink_map[normalized]
    docs_candidate = root / "docs" / path_part.lstrip("/")
    if docs_candidate.exists():
        return docs_candidate
    root_candidate = root / path_part.lstrip("/")
    if root_candidate.exists():
        return root_candidate
    if path_part.endswith("/"):
        for suffix in ("index.md", "index.html", "README.md"):
            docs_index_candidate = docs_candidate / suffix
            if docs_index_candidate.exists():
                return docs_index_candidate
            root_index_candidate = root_candidate / suffix
            if root_index_candidate.exists():
                return root_index_candidate
    return None


def _resolve_local_target(
    root: Path,
    source_path: Path,
    target: str,
    permalink_map: dict[str, Path],
    source_permalink: str | None = None,
) -> tuple[Path | None, str | None]:
    parsed = urllib_parse.urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None, parsed.fragment or None

    path_part = urllib_parse.unquote(parsed.path)
    fragment = parsed.fragment or None
    if not path_part:
        return source_path, fragment

    if path_part.startswith("/"):
        return _resolve_site_root_target(root, path_part, permalink_map), fragment

    # Jekyll clean-URL resolution: when the source page has a permalink, a
    # relative link like "solution-design/" should resolve via the rendered
    # site URL (source_permalink + target) and look up the matching page in
    # the permalink map. This mirrors how Jekyll renders the link in prod.
    if source_permalink:
        joined = urllib_parse.urljoin(_normalize_permalink(source_permalink), path_part)
        if joined.startswith("/"):
            resolved = _resolve_site_root_target(root, joined, permalink_map)
            if resolved is not None and resolved.exists():
                return resolved, fragment

    candidate = (source_path.parent / path_part).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None, fragment
    if candidate.exists():
        return candidate, fragment

    # Fallback for clean-URL style relative links (e.g. "solution-design/"):
    # try a sibling Markdown file with the same basename. This handles the
    # common pattern where a sub-document lives next to index.md but is
    # linked via its trailing-slash URL form.
    if path_part.endswith("/"):
        base = path_part.rstrip("/")
        if base and not base.startswith("/"):
            sibling = (source_path.parent / f"{base}.md").resolve()
            try:
                sibling.relative_to(root.resolve())
            except ValueError:
                pass
            else:
                if sibling.exists():
                    return sibling, fragment

    return candidate, fragment


def _validate_markdown_anchor(target_path: Path, fragment: str) -> None:
    if target_path.suffix.lower() != ".md":
        return
    anchors = _heading_slugs(target_path.read_text(encoding="utf-8"))
    if fragment not in anchors:
        raise RuntimeError(f"{target_path} is missing anchor '#{fragment}'")


def _validate_remote_url(url: str) -> None:
    reachable_status_codes = {401, 403, 405, 429}

    def _status_is_acceptable(status_code: int) -> bool:
        return status_code < 400 or status_code in reachable_status_codes

    headers = {"User-Agent": "research-runner-link-check/1.0"}
    request = urllib_request.Request(url, method="HEAD", headers=headers)
    try:
        with urllib_request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            status_code = getattr(response, "status", 200)
            if not _status_is_acceptable(status_code):
                raise RuntimeError(f"URL returned HTTP {status_code}: {url}")
            return
    except urllib_error.HTTPError as exc:
        if not _status_is_acceptable(exc.code):
            raise RuntimeError(f"URL returned HTTP {exc.code}: {url}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"Could not reach URL {url}: {exc.reason}") from exc

    fallback = urllib_request.Request(url, method="GET", headers=headers)
    try:
        with urllib_request.urlopen(fallback, timeout=HTTP_TIMEOUT_SECONDS) as response:
            status_code = getattr(response, "status", 200)
            if not _status_is_acceptable(status_code):
                raise RuntimeError(f"URL returned HTTP {status_code}: {url}")
    except urllib_error.HTTPError as exc:
        if not _status_is_acceptable(exc.code):
            raise RuntimeError(f"URL returned HTTP {exc.code}: {url}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"Could not reach URL {url}: {exc.reason}") from exc


def _validate_markdown_links(
    path: Path,
    *,
    root: Path,
    permalink_map: dict[str, Path],
    check_remote: bool = False,
) -> None:
    content = path.read_text(encoding="utf-8")
    source_permalink = _extract_frontmatter_permalink(content)
    stripped = _content_without_code(content)

    placeholder_match = PLACEHOLDER_URL_RE.search(stripped)
    if placeholder_match:
        raise RuntimeError(f"{path} contains a placeholder URL: {placeholder_match.group(0)}")

    for match in MARKDOWN_LINK_RE.finditer(stripped):
        target = _clean_markdown_link_target(match.group("target"))
        if target.startswith(("mailto:", "tel:")):
            continue

        parsed = urllib_parse.urlsplit(target)
        if parsed.scheme in {"http", "https"}:
            if check_remote:
                _validate_remote_url(target)
            continue

        resolved, fragment = _resolve_local_target(
            root, path, target, permalink_map, source_permalink=source_permalink
        )
        if resolved is None or not resolved.exists():
            raise RuntimeError(f"{path} links to missing target: {target}")
        if fragment:
            _validate_markdown_anchor(resolved, fragment)

    masked = MARKDOWN_LINK_RE.sub("", stripped)
    raw_urls = RAW_URL_RE.findall(masked)
    if raw_urls:
        preview = ", ".join(sorted(set(raw_urls))[:3])
        raise RuntimeError(f"{path} contains raw URL text instead of clickable markdown links: {preview}")


def verify_document_links(
    root: Path,
    paths: list[Path],
    *,
    check_remote: bool = False,
) -> None:
    permalink_map = _build_permalink_map(root)
    for path in sorted(set(paths)):
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        _validate_markdown_links(path, root=root, permalink_map=permalink_map, check_remote=check_remote)


def verify_repository_documents(root: Path, *, check_remote: bool = False) -> int:
    paths = _iter_repo_markdown_files(root)
    verify_document_links(root, paths, check_remote=check_remote)
    return len(paths)


def _validate_markdown_file(
    path: Path,
    *,
    check_headings: bool = True,
    check_placeholders: bool = True,
) -> None:
    content = path.read_text(encoding="utf-8")
    layout = _extract_frontmatter_layout(content)
    expected_layout = EXPECTED_LAYOUTS.get(path.name)
    if expected_layout and layout != expected_layout:
        raise RuntimeError(f"{path} is missing expected layout '{expected_layout}'")

    if check_headings:
        for heading in REQUIRED_HEADINGS.get(path.name, ()):
            if heading not in content:
                raise RuntimeError(f"{path} is missing required heading: {heading}")

    if check_placeholders:
        stripped = _content_without_code(content)
        placeholder_match = PLACEHOLDER_RE.search(stripped)
        if placeholder_match:
            raise RuntimeError(f"{path} still contains template placeholder text: {placeholder_match.group(0)}")


def find_use_case_dirs(root: Path, topic_id: str) -> list[Path]:
    matches = sorted(path.parent for path in root.glob(f"docs/use-cases/*/{topic_id}-*/{USE_CASE_INDEX}"))
    return matches


def readme_row(root: Path, topic_id: str) -> str | None:
    for relative_path in INDEX_READMES:
        readme = root / relative_path
        if not readme.exists():
            continue
        for line in readme.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"| {topic_id} "):
                return line
    return None


def readme_row_has_status(row: str, status: str) -> bool:
    if f"`{status}`" in row:
        return True
    match = README_STATUS_RE.search(row)
    return bool(match and match.group(1).lower() == status.lower())


def use_case_status(index_md: Path) -> str | None:
    content = index_md.read_text(encoding="utf-8")
    return _extract_frontmatter_status(content)


def topic_id_from_use_case_dir(use_case_dir: Path) -> str | None:
    match = TOPIC_ID_RE.match(use_case_dir.name)
    if not match:
        return None
    return match.group("topic_id")


def find_next_topic_needing_detail(
    root: Path,
    *,
    excluded_ids: set[str] | None = None,
) -> VerificationResult | None:
    excluded = excluded_ids or set()
    candidates: list[tuple[int, str, str]] = []
    for index_md in root.glob(f"docs/use-cases/*/UC-*/{USE_CASE_INDEX}"):
        status = use_case_status(index_md)
        if status == "detailed":
            continue
        topic_id = topic_id_from_use_case_dir(index_md.parent)
        if topic_id is None or topic_id in excluded:
            continue
        candidates.append((int(topic_id.split("-", 1)[1]), topic_id, str(index_md.parent.relative_to(root))))

    if not candidates:
        return None

    _, topic_id, use_case_dir = min(candidates)
    return VerificationResult(topic_id=topic_id, use_case_dir=use_case_dir)


def verify_research_new(root: Path, topic_id: str) -> VerificationResult:
    row = readme_row(root, topic_id)
    if row is None:
        raise RuntimeError(f"{topic_id} is missing from the repository index files")
    if not readme_row_has_status(row, "research"):
        raise RuntimeError(f"{topic_id} row in the repository index files is not marked as research")

    matches = find_use_case_dirs(root, topic_id)
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one use case directory for {topic_id}, found {len(matches)}")

    index_md = matches[0] / USE_CASE_INDEX
    if not index_md.exists():
        raise RuntimeError(f"{index_md} does not exist")

    status = use_case_status(index_md)
    if status != "research":
        raise RuntimeError(f"{index_md} is not marked as research")

    _validate_markdown_file(index_md)
    verify_document_links(root, [root / "README.md", root / "docs/use-cases/README.md", index_md])

    return VerificationResult(topic_id=topic_id, use_case_dir=str(matches[0].relative_to(root)))


def verify_research_complete(root: Path, topic_id: str) -> VerificationResult:
    row = readme_row(root, topic_id)
    if row is None or not readme_row_has_status(row, "detailed"):
        raise RuntimeError(f"{topic_id} row in the repository index files is not marked as detailed")

    matches = find_use_case_dirs(root, topic_id)
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one use case directory for {topic_id}, found {len(matches)}")

    use_case_dir = matches[0]
    expected = [
        "solution-design.md",
        "implementation-guide.md",
        "evaluation.md",
        "references.md",
    ]
    missing = [name for name in expected if not (use_case_dir / name).exists()]
    if missing:
        raise RuntimeError(f"{topic_id} is missing expected files: {', '.join(missing)}")

    index_md = use_case_dir / USE_CASE_INDEX
    status = use_case_status(index_md)
    if status != "detailed":
        raise RuntimeError(f"{index_md} is not marked as detailed")

    _validate_markdown_file(index_md, check_headings=False)
    for name in expected:
        _validate_markdown_file(use_case_dir / name)
    verify_document_links(
        root,
        [root / "README.md", root / "docs/use-cases/README.md", index_md, *[use_case_dir / name for name in expected]],
    )

    return VerificationResult(topic_id=topic_id, use_case_dir=str(use_case_dir.relative_to(root)))
