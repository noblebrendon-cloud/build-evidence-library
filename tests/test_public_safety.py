from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".json", ".cff", ".txt"}
TEXT_NAMES = {".gitignore", "LICENSE"}
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
EXCLUDED_PATHS = {"tests/test_public_safety.py"}
PROHIBITED_VALUES = [
    "signal_agent",
    "Project Studio",
    "Governed Publishing",
    "Clarity Systems Group",
    "Laviathon",
    "Letters of Light",
    "E:",
    "C:\\Users",
    "mrcol",
]


def candidate_file_paths(root: Path = REPO_ROOT) -> list[Path]:
    git_result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={root.as_posix()}",
            "-C",
            str(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if git_result.returncode == 0:
        raw_paths = [root / line.strip() for line in git_result.stdout.splitlines() if line.strip()]
    else:
        raw_paths = [
            path
            for path in root.rglob("*")
            if path.is_file()
            and (path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES)
        ]
    return [path for path in raw_paths if _is_candidate(path, root)]


def _is_candidate(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    rel_text = rel.as_posix()
    if rel_text in EXCLUDED_PATHS:
        return False
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return False
    if not path.is_file():
        return False
    return path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES


def _read_text_or_none(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def test_public_files_do_not_contain_private_terms_or_paths() -> None:
    failures: list[str] = []
    for path in candidate_file_paths():
        text = _read_text_or_none(path)
        if text is None:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        for value in PROHIBITED_VALUES:
            if value in text:
                failures.append(f"{rel}: {value}")
    assert failures == []


def test_example_event_contains_no_private_references_or_sha1_values() -> None:
    example_root = REPO_ROOT / "examples" / "EVT-2026-01-15-api-rate-limit-hardening"
    combined = "\n".join(path.read_text(encoding="utf-8") for path in example_root.glob("*.md"))

    assert not re.search(r"\b[0-9a-fA-F]{40}\b", combined)
    assert not re.search(r"\b[A-Za-z]:[\\/]", combined)
    assert "/home/" not in combined
    assert "\\Users\\" not in combined
    for value in PROHIBITED_VALUES:
        assert value not in combined


def test_metadata_files_are_consistent_and_pre_repository_url() -> None:
    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    zenodo = json.loads((REPO_ROOT / ".zenodo.json").read_text(encoding="utf-8"))

    assert 'title: "Build Evidence Library"' in citation
    assert zenodo["title"] == "Build Evidence Library"
    assert 'version: "0.1.0"' in citation
    assert zenodo["version"] == "0.1.0"
    assert 'license: "MIT"' in citation
    assert zenodo["license"] == "mit"
    forbidden_metadata_terms = ("doi", "repository-code", "homepage", "url", "http://", "https://", "date-released")
    lowered_citation = citation.lower()
    lowered_zenodo = json.dumps(zenodo).lower()
    for term in forbidden_metadata_terms:
        assert term not in lowered_citation
        assert term not in lowered_zenodo


def test_git_candidate_list_includes_untracked_files_before_first_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    temp_file = repo / "untracked.md"
    temp_file.write_text("temporary public-safe text\n", encoding="utf-8")

    candidates = [path.relative_to(repo).as_posix() for path in candidate_file_paths(repo)]

    assert "untracked.md" in candidates
