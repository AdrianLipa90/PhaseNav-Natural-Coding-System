#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable

SCHEMA = "PNCS_TRACKED_TREE_SHA256_MANIFEST_V2"
DEFAULT_OUTPUT = "MANIFEST.sha256.json"
DEFAULT_EXCLUSIONS = (
    DEFAULT_OUTPUT,
    "provenance/receipts/FOUNDATION_STATUS_V0_28.json",
)
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


class ManifestError(RuntimeError):
    pass


def _run_git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace")
        raise ManifestError(f"git command failed: {' '.join(args)}: {detail}") from exc
    return proc.stdout.decode("utf-8", "strict").strip()


def _decode_nul_paths(raw: bytes, label: str) -> tuple[str, ...]:
    try:
        paths = tuple(item.decode("utf-8", "strict") for item in raw.split(b"\0") if item)
    except UnicodeDecodeError as exc:
        raise ManifestError(f"{label} path is not valid UTF-8") from exc
    return tuple(sorted(set(paths)))


def _changed_paths(root: Path, source_commit: str) -> tuple[str, ...]:
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "diff",
                "--name-only",
                "-z",
                source_commit,
                "HEAD",
                "--",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace")
        raise ManifestError(f"cannot compare manifest source commit to HEAD: {detail}") from exc
    return _decode_nul_paths(proc.stdout, "changed tracked")


def _working_tree_changed_paths(root: Path) -> tuple[str, ...]:
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "diff",
                "--name-only",
                "-z",
                "HEAD",
                "--",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace")
        raise ManifestError(f"cannot inspect tracked working tree: {detail}") from exc
    return _decode_nul_paths(proc.stdout, "working-tree tracked")


def _require_clean_declared_scope(root: Path, exclusions: Iterable[str]) -> None:
    allowed = set(str(item) for item in exclusions)
    dirty = tuple(path for path in _working_tree_changed_paths(root) if path not in allowed)
    if dirty:
        raise ManifestError(
            "tracked working tree differs from HEAD outside declared exclusions: "
            + ", ".join(dirty)
        )


def tracked_paths(root: Path) -> tuple[str, ...]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace")
        raise ManifestError(f"git ls-files failed: {detail}") from exc
    raw = proc.stdout
    if not raw:
        raise ManifestError("tracked file set is empty")
    paths = _decode_nul_paths(raw, "tracked")
    if len(paths) != len(tuple(item for item in raw.split(b"\0") if item)):
        raise ManifestError("duplicate tracked path")
    return paths


def _entry(root: Path, rel: str) -> dict[str, object]:
    path = root / rel
    if path.is_symlink():
        # Git stores a symlink as mode 120000 whose blob is exactly the link
        # target bytes. Hash that object identity without dereferencing it, so
        # directory and dangling symlinks remain inside the authoritative tree.
        try:
            raw = os.fsencode(os.readlink(path))
        except OSError as exc:
            raise ManifestError(f"cannot read tracked symlink target: {rel}") from exc
    elif path.is_file():
        raw = path.read_bytes()
    else:
        # Submodules, devices, FIFOs or any other non-file tracked objects are
        # not silently admitted by this schema.
        raise ManifestError(f"tracked path has unsupported filesystem type: {rel}")
    return {
        "path": rel,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
    }


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def build_manifest(root: Path, *, exclusions: Iterable[str] = DEFAULT_EXCLUSIONS) -> dict[str, object]:
    root = root.resolve()
    excluded = tuple(sorted(set(str(item) for item in exclusions)))
    _require_clean_declared_scope(root, excluded)
    tracked = tracked_paths(root)
    entries = [_entry(root, rel) for rel in tracked if rel not in excluded]
    if not entries:
        raise ManifestError("manifest file set is empty")
    entry_root = hashlib.sha256(_canonical_json(entries)).hexdigest()
    source_commit = _run_git(root, "rev-parse", "HEAD")
    source_tree = _run_git(root, "rev-parse", "HEAD^{tree}")
    return {
        "schema": SCHEMA,
        "status": "AUTHORITATIVE_FOR_DECLARED_SCOPE",
        "hash_algorithm": "SHA-256",
        "path_order": "UTF8_LEXICOGRAPHIC_ASCENDING",
        "scope": "ALL_GIT_TRACKED_REGULAR_FILES_AND_SYMLINK_BLOBS_EXCEPT_DECLARED_EXCLUSIONS",
        "source_commit": source_commit,
        "source_tree": source_tree,
        "exclusions": list(excluded),
        "file_count": len(entries),
        "entries_sha256": entry_root,
        "files": entries,
        "fail_closed": True,
    }


def _verify_source_identity(root: Path, manifest: dict[str, object], exclusions: list[str]) -> None:
    source_commit = manifest.get("source_commit")
    source_tree = manifest.get("source_tree")
    if not isinstance(source_commit, str) or not _HEX40_RE.fullmatch(source_commit):
        raise ManifestError("invalid source_commit")
    if not isinstance(source_tree, str) or not _HEX40_RE.fullmatch(source_tree):
        raise ManifestError("invalid source_tree")

    resolved_commit = _run_git(root, "rev-parse", f"{source_commit}^{{commit}}")
    if resolved_commit != source_commit:
        raise ManifestError("source_commit does not resolve exactly")
    actual_tree = _run_git(root, "rev-parse", f"{source_commit}^{{tree}}")
    if actual_tree != source_tree:
        raise ManifestError("source_commit/source_tree mismatch")

    changed = _changed_paths(root, source_commit)
    allowed = set(exclusions)
    out_of_scope = tuple(path for path in changed if path not in allowed)
    if out_of_scope:
        raise ManifestError(
            "manifest source commit differs from HEAD outside declared exclusions: "
            + ", ".join(out_of_scope)
        )


def verify_manifest(root: Path, manifest: dict[str, object]) -> None:
    root = root.resolve()
    if manifest.get("schema") != SCHEMA:
        raise ManifestError("unexpected manifest schema")
    exclusions = manifest.get("exclusions")
    if (
        not isinstance(exclusions, list)
        or not exclusions
        or not all(isinstance(x, str) and x for x in exclusions)
    ):
        raise ManifestError("manifest exclusions must be a non-empty string list")
    canonical_exclusions = list(sorted(DEFAULT_EXCLUSIONS))
    if exclusions != canonical_exclusions:
        raise ManifestError("manifest exclusions differ from canonical exclusions")

    expected = build_manifest(root, exclusions=DEFAULT_EXCLUSIONS)
    for field in (
        "status",
        "hash_algorithm",
        "path_order",
        "scope",
        "exclusions",
        "file_count",
        "entries_sha256",
        "files",
        "fail_closed",
    ):
        if manifest.get(field) != expected.get(field):
            raise ManifestError(f"manifest mismatch: {field}")
    # The manifest may survive a later metadata-only commit, but its declared
    # source identity must be a real commit/tree pair whose differences from
    # current HEAD are confined to the canonical exclusions.
    _verify_source_identity(root, manifest, canonical_exclusions)


def _load_manifest(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError("manifest root must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate or verify the PNCS tracked-tree SHA-256 manifest.")
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--output", default=DEFAULT_OUTPUT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    output = root / args.output
    try:
        if args.check:
            verify_manifest(root, _load_manifest(output))
            print(json.dumps({"schema": SCHEMA, "status": "PASS", "manifest": args.output}, sort_keys=True))
            return 0
        manifest = build_manifest(root)
        raw = _canonical_json(manifest) + b"\n"
        output.write_bytes(raw)
        print(json.dumps({
            "schema": SCHEMA,
            "status": "WRITTEN",
            "manifest": args.output,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "file_count": manifest["file_count"],
            "entries_sha256": manifest["entries_sha256"],
        }, sort_keys=True))
        return 0
    except ManifestError as exc:
        print(json.dumps({"schema": SCHEMA, "status": "FAIL", "error": str(exc), "fail_closed": True}, sort_keys=True), file=sys.stderr)
        return 23


if __name__ == "__main__":
    raise SystemExit(main())
