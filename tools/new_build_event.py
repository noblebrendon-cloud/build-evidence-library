from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


STANDARD_EVENT_FILES = (
    "00_EVENT.md",
    "01_EVIDENCE.md",
    "02_TEACHING_ATOMS.md",
    "03_DERIVATIVE_BACKLOG.md",
    "04_PUBLICATION_LEDGER.md",
)

INDEX_HEADER = """# Build Event Index

Purpose: track captured build events, their status, and their event records.

| Event ID | Captured | Title | Status | Event Record |
| --- | --- | --- | --- | --- |
"""


class BuildEventError(RuntimeError):
    pass


class IntegrityConflict(BuildEventError):
    pass


def canonical_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def create_or_reopen_event(
    event_id: str,
    year: str,
    title: str,
    *,
    output_root: str | Path | None = None,
) -> str:
    normalized_event_id = _validate_event_id(event_id)
    normalized_year = _validate_year(year)
    normalized_title = _required(title, "title")

    template_root = canonical_repo_root()
    root = _resolve_output_root(output_root or template_root)
    events_root = _contained_path(root, root / "events")
    index_path = _contained_path(root, root / "BUILD_EVENT_INDEX.md")
    event_dir = _contained_path(events_root, events_root / normalized_year / normalized_event_id)

    if event_dir.exists():
        return f"Reopened existing event {normalized_event_id}; no changes made."

    index_text = _read_or_initialize_index(index_path, root)
    indexed = _index_contains_event(index_text, normalized_event_id)

    if indexed:
        raise IntegrityConflict(
            f"Integrity conflict: event ID {normalized_event_id} is already indexed but its event "
            "directory is unavailable. Restore the event directory, intentionally remove the stale "
            "index record, or reconcile the stale index record before creating a new event."
        )

    events_root.mkdir(parents=True, exist_ok=True)
    event_dir.mkdir(parents=True, exist_ok=False)

    context = {
        "EVENT_ID": normalized_event_id,
        "YEAR": normalized_year,
        "TITLE": normalized_title,
        "CAPTURED_DATE": date.today().isoformat(),
    }
    for filename in STANDARD_EVENT_FILES:
        target = _contained_path(root, event_dir / filename)
        template = _template_text(template_root, filename)
        target.write_text(_render(template, context), encoding="utf-8")

    row = (
        f"| `{normalized_event_id}` | {context['CAPTURED_DATE']} | {normalized_title} | draft | "
        f"[00_EVENT.md](events/{normalized_year}/{normalized_event_id}/00_EVENT.md) |\n"
    )
    current_index = index_path.read_text(encoding="utf-8")
    if not _index_contains_event(current_index, normalized_event_id):
        if not current_index.endswith("\n"):
            current_index += "\n"
        index_path.write_text(current_index + row, encoding="utf-8")

    return f"Created new event {normalized_event_id} under {event_dir}."


def _resolve_output_root(value: str | Path) -> Path:
    root = Path(value).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _contained_path(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    if candidate.exists():
        resolved_candidate = candidate.resolve()
    else:
        resolved_candidate = candidate.parent.resolve() / candidate.name
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise BuildEventError(f"output_path_escapes_root:{resolved_candidate}") from exc
    return resolved_candidate


def _read_or_initialize_index(index_path: Path, root: Path) -> str:
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    parent = _contained_path(root, index_path.parent)
    parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(INDEX_HEADER, encoding="utf-8")
    return INDEX_HEADER


def _index_contains_event(index_text: str, event_id: str) -> bool:
    return f"`{event_id}`" in index_text


def _template_text(template_root: Path, filename: str) -> str:
    if filename == "00_EVENT.md":
        template_name = "BUILD_EVENT_TEMPLATE.md"
    elif filename == "01_EVIDENCE.md":
        return "# Evidence\n\nEvent ID: `{{EVENT_ID}}`\n\n## Verified Facts\n\n| Fact | Evidence |\n| --- | --- |\n\n## Test Evidence\n\n| Command | Result |\n| --- | --- |\n"
    elif filename == "02_TEACHING_ATOMS.md":
        return "# Teaching Atoms\n\nEvent ID: `{{EVENT_ID}}`\n\n| Atom | Concept | Origin |\n| --- | --- | --- |\n"
    elif filename == "03_DERIVATIVE_BACKLOG.md":
        template_name = "DERIVATIVE_TEMPLATE.md"
    elif filename == "04_PUBLICATION_LEDGER.md":
        template_name = "PUBLICATION_RECORD_TEMPLATE.md"
    else:
        raise BuildEventError(f"unknown_event_file:{filename}")

    path = template_root / "templates" / template_name
    return path.read_text(encoding="utf-8")


def _render(template: str, context: dict[str, str]) -> str:
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def _validate_event_id(value: str) -> str:
    event_id = _required(value, "event_id")
    if "/" in event_id or "\\" in event_id or ".." in event_id:
        raise ValueError("event_id_must_be_path_safe")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", event_id):
        raise ValueError("event_id_must_use_safe_characters")
    return event_id


def _validate_year(value: str) -> str:
    year = _required(value, "year")
    if not re.fullmatch(r"\d{4}", year):
        raise ValueError("year_must_be_four_digits")
    return year


def _required(value: str, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name}_required")
    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or reopen a build evidence event.")
    parser.add_argument("event_id")
    parser.add_argument("year")
    parser.add_argument("title", nargs="+")
    parser.add_argument("--root", help="Output root for events and BUILD_EVENT_INDEX.md")
    args = parser.parse_args(argv)

    try:
        message = create_or_reopen_event(
            args.event_id,
            args.year,
            " ".join(args.title),
            output_root=args.root,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
