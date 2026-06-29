from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_tool():
    tool_path = Path(__file__).resolve().parents[1] / "tools" / "new_build_event.py"
    spec = importlib.util.spec_from_file_location("new_build_event", tool_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_create_event_writes_standard_files_and_index(tmp_path: Path) -> None:
    tool = _load_tool()
    root = tmp_path / "blank-root"

    message = tool.create_or_reopen_event(
        "EVT-2026-01-20-cache-timeout-fix",
        "2026",
        "Cache timeout fix",
        output_root=root,
    )

    event_dir = root / "events" / "2026" / "EVT-2026-01-20-cache-timeout-fix"
    assert "Created new event EVT-2026-01-20-cache-timeout-fix" in message
    assert (event_dir / "00_EVENT.md").exists()
    assert (event_dir / "01_EVIDENCE.md").exists()
    assert (event_dir / "02_TEACHING_ATOMS.md").exists()
    assert (event_dir / "03_DERIVATIVE_BACKLOG.md").exists()
    assert (event_dir / "04_PUBLICATION_LEDGER.md").exists()
    index = (root / "BUILD_EVENT_INDEX.md").read_text(encoding="utf-8")
    assert "# Build Event Index" in index
    assert index.count("`EVT-2026-01-20-cache-timeout-fix`") == 1


def test_duplicate_reopens_without_writing_or_duplicating_index(tmp_path: Path) -> None:
    tool = _load_tool()
    root = tmp_path / "blank-root"
    event_id = "EVT-2026-01-20-cache-timeout-fix"

    tool.create_or_reopen_event(event_id, "2026", "Cache timeout fix", output_root=root)
    event_file = root / "events" / "2026" / event_id / "00_EVENT.md"
    event_file.write_text("operator edits stay intact\n", encoding="utf-8")
    index_before = (root / "BUILD_EVENT_INDEX.md").read_text(encoding="utf-8")

    message = tool.create_or_reopen_event(event_id, "2026", "Changed title", output_root=root)

    assert "Reopened existing event EVT-2026-01-20-cache-timeout-fix" in message
    assert event_file.read_text(encoding="utf-8") == "operator edits stay intact\n"
    assert (root / "BUILD_EVENT_INDEX.md").read_text(encoding="utf-8") == index_before
    assert index_before.count(f"`{event_id}`") == 1


def test_existing_event_directory_reopens_without_creating_missing_index(tmp_path: Path) -> None:
    tool = _load_tool()
    root = tmp_path / "blank-root"
    event_id = "EVT-2026-01-20-existing-event"
    event_dir = root / "events" / "2026" / event_id
    event_dir.mkdir(parents=True)

    message = tool.create_or_reopen_event(event_id, "2026", "Existing event", output_root=root)

    assert "Reopened existing event EVT-2026-01-20-existing-event" in message
    assert not (root / "BUILD_EVENT_INDEX.md").exists()


@pytest.mark.parametrize(
    "event_id",
    [
        "../EVT-2026-01-20-bad",
        "EVT-2026-01-20/bad",
        "EVT-2026-01-20\\bad",
        "",
        "EVT-2026-01-20 bad",
    ],
)
def test_unsafe_event_ids_are_rejected(tmp_path: Path, event_id: str) -> None:
    tool = _load_tool()

    with pytest.raises(ValueError):
        tool.create_or_reopen_event(event_id, "2026", "Bad", output_root=tmp_path)


def test_blank_root_initializes_only_output_files(tmp_path: Path) -> None:
    tool = _load_tool()
    root = tmp_path / "blank-output"

    tool.create_or_reopen_event("EVT-2026-01-21-new-event", "2026", "New event", output_root=root)

    assert sorted(item.name for item in root.iterdir()) == ["BUILD_EVENT_INDEX.md", "events"]
    assert not (root / "templates").exists()


def test_indexed_but_missing_event_directory_is_integrity_conflict(tmp_path: Path) -> None:
    tool = _load_tool()
    root = tmp_path / "blank-output"
    event_id = "EVT-2026-01-21-missing-event"

    tool.create_or_reopen_event(event_id, "2026", "Missing event", output_root=root)
    event_dir = root / "events" / "2026" / event_id
    for path in event_dir.iterdir():
        path.unlink()
    event_dir.rmdir()
    index_path = root / "BUILD_EVENT_INDEX.md"
    index_before = index_path.read_text(encoding="utf-8")

    with pytest.raises(tool.IntegrityConflict, match="already indexed but its event directory is unavailable"):
        tool.create_or_reopen_event(event_id, "2026", "Missing event", output_root=root)

    assert not event_dir.exists()
    assert index_path.read_text(encoding="utf-8") == index_before
