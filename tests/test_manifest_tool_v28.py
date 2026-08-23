from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


def _load_tool():
    path = Path(__file__).parents[1] / "scripts" / "regenerate_manifest.py"
    spec = importlib.util.spec_from_file_location("pncs_regenerate_manifest", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


m = _load_tool()


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "pncs@example.invalid")
    _git(root, "config", "user.name", "PNCS Test")
    (root / "src").mkdir()
    (root / "src" / "a.txt").write_text("alpha\n", "utf-8")
    (root / "z.txt").write_text("omega\n", "utf-8")
    (root / "MANIFEST.sha256.json").write_text("legacy\n", "utf-8")
    (root / "provenance" / "receipts").mkdir(parents=True)
    (root / "provenance" / "receipts" / "FOUNDATION_STATUS_V0_28.json").write_text("pending\n", "utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture")
    return root


def test_manifest_hashes_all_tracked_files_except_declared_release_metadata(tmp_path):
    root = _repo(tmp_path)
    manifest = m.build_manifest(root)
    paths = [entry["path"] for entry in manifest["files"]]
    assert paths == ["src/a.txt", "z.txt"]
    assert manifest["file_count"] == 2
    assert manifest["exclusions"] == sorted(m.DEFAULT_EXCLUSIONS)
    assert manifest["status"] == "AUTHORITATIVE_FOR_DECLARED_SCOPE"
    assert manifest["fail_closed"] is True


def test_manifest_path_order_and_identity_are_deterministic(tmp_path):
    root = _repo(tmp_path)
    a = m.build_manifest(root)
    b = m.build_manifest(root)
    assert a == b
    assert a["entries_sha256"] == b["entries_sha256"]
    assert [entry["path"] for entry in a["files"]] == sorted(entry["path"] for entry in a["files"])


def test_verify_detects_tracked_file_tamper(tmp_path):
    root = _repo(tmp_path)
    manifest = m.build_manifest(root)
    m.verify_manifest(root, manifest)
    (root / "src" / "a.txt").write_text("tampered\n", "utf-8")
    with pytest.raises(m.ManifestError, match="manifest mismatch"):
        m.verify_manifest(root, manifest)


def test_verify_allows_excluded_foundation_receipt_to_change(tmp_path):
    root = _repo(tmp_path)
    manifest = m.build_manifest(root)
    receipt = root / "provenance" / "receipts" / "FOUNDATION_STATUS_V0_28.json"
    receipt.write_text(json.dumps({"status": "PASS_RELEASE_CLOSED"}) + "\n", "utf-8")
    m.verify_manifest(root, manifest)


def test_untracked_file_does_not_silently_enter_manifest_scope(tmp_path):
    root = _repo(tmp_path)
    (root / "untracked.txt").write_text("not tracked\n", "utf-8")
    manifest = m.build_manifest(root)
    assert "untracked.txt" not in [entry["path"] for entry in manifest["files"]]


def test_empty_non_git_directory_fails_closed(tmp_path):
    with pytest.raises(m.ManifestError):
        m.build_manifest(tmp_path)
