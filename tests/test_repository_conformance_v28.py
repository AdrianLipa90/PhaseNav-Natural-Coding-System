from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
LIVE_ROOT = "/dev" + "/shm/ciel_noema"


def _text_files(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".py", ".yml", ".yaml"}:
            yield path


def _constant_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _constant_text(node.left)
        right = _constant_text(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _call_name(node: ast.Call) -> str:
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return fn.attr
    return ""


def _live_io_reasons(path: Path) -> list[str]:
    tree = ast.parse(path.read_text("utf-8"), filename=str(path))
    reasons: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        values = [_constant_text(arg) for arg in node.args]
        values.extend(_constant_text(kw.value) for kw in node.keywords)
        if name in {"Path", "open"} and any(value and LIVE_ROOT in value for value in values):
            reasons.append(f"line {node.lineno}: direct {name} binding to canonical live root")
        for kw in node.keywords:
            value = _constant_text(kw.value)
            if kw.arg == "surface_root" and value and LIVE_ROOT in value:
                reasons.append(f"line {node.lineno}: canonical live surface_root passed explicitly")
        if (name.startswith("load_live_") or name.startswith("read_live_")) and not node.args and not node.keywords:
            reasons.append(f"line {node.lineno}: {name} uses its canonical live-root default")
    return reasons


def test_hosted_pure_tests_have_no_historical_mnt_data_dependency():
    forbidden = "/mnt" + "/data/"
    offenders = []
    for path in _text_files(REPO_ROOT / "tests"):
        if "tests/live/" in path.relative_to(REPO_ROOT).as_posix():
            continue
        if forbidden in path.read_text("utf-8"):
            offenders.append(path.relative_to(REPO_ROOT).as_posix())
    assert offenders == []


def test_hosted_pure_tests_do_not_require_live_dev_shm_surface():
    offenders = []
    for path in _text_files(REPO_ROOT / "tests"):
        if "tests/live/" in path.relative_to(REPO_ROOT).as_posix():
            continue
        reasons = _live_io_reasons(path)
        if reasons:
            offenders.append({"path": path.relative_to(REPO_ROOT).as_posix(), "reasons": reasons})
    assert offenders == []


def test_workflows_have_no_historical_mnt_data_dependency():
    forbidden = "/mnt" + "/data/"
    offenders = []
    for path in _text_files(REPO_ROOT / ".github/workflows"):
        if forbidden in path.read_text("utf-8"):
            offenders.append(path.relative_to(REPO_ROOT).as_posix())
    assert offenders == []


def test_live_tests_are_physically_separated():
    live = REPO_ROOT / "tests/live"
    assert live.is_dir()
    assert any(path.name.startswith("test_") and path.suffix == ".py" for path in live.iterdir())
