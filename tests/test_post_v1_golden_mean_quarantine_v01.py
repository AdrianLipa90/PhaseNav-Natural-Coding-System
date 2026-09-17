from __future__ import annotations

import hashlib
from pathlib import Path

from phasenav_natural_code.release_train_v1 import (
    ChangeClass,
    Decision,
    ReleaseStage,
    classify_change,
    post_v1_idea_registry,
)

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_MODULE = ROOT / "src/phasenav_natural_code/golden_mean_dynamics_v01.py"
ACTIVE_TEST = ROOT / "tests/test_golden_mean_dynamics_v01.py"
RESEARCH_ROOT = ROOT / "research/post_v1/fundamental_golden_mean_v01"
RESEARCH_MODULE = RESEARCH_ROOT / "src/phasenav_natural_code/golden_mean_dynamics_v01.py"
RESEARCH_TEST = RESEARCH_ROOT / "tests/test_golden_mean_dynamics_v01.py"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def test_golden_mean_is_not_in_active_v1_package_or_test_graph() -> None:
    assert not ACTIVE_MODULE.exists()
    assert not ACTIVE_TEST.exists()
    for path in (ROOT / "src/phasenav_natural_code").rglob("*.py"):
        assert "golden_mean_dynamics_v01" not in path.read_text(encoding="utf-8")


def test_exact_research_payload_is_preserved() -> None:
    assert RESEARCH_MODULE.is_file()
    assert RESEARCH_TEST.is_file()
    assert git_blob_sha(RESEARCH_MODULE) == "766d6ea951c820f5be0513eef2849cbca4d15b26"
    assert git_blob_sha(RESEARCH_TEST) == "0939ef460906fffeddc8081bb3ff9227de03ddf5"


def test_release_controller_routes_golden_mean_to_post_v1_quarantine() -> None:
    assert "fundamental_golden_mean_v01" in post_v1_idea_registry()
    receipt = classify_change(
        change_id="fundamental_golden_mean_v01",
        change_class=ChangeClass.EXPERIMENTAL_IDEA,
        stage=ReleaseStage.V028_CLOSURE,
        evidence=("historical_main_commit:85f0b3bebb67248f449fa13721481f44ce6840cf",),
    )
    assert receipt.decision is Decision.QUARANTINE
    assert receipt.reason
    assert receipt.receipt_sha256
