from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]


def _text_files(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".py", ".yml", ".yaml"}:
            yield path


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
    forbidden = "/dev" + "/shm/ciel_noema"
    offenders = []
    for path in _text_files(REPO_ROOT / "tests"):
        if "tests/live/" in path.relative_to(REPO_ROOT).as_posix():
            continue
        if forbidden in path.read_text("utf-8"):
            offenders.append(path.relative_to(REPO_ROOT).as_posix())
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
