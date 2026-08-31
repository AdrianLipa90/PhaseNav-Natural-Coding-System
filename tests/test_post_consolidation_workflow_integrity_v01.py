from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_v028_workflow_has_no_deleted_branch_routing_or_storage_regression():
    text = _workflow("pncs-v028-adversarial-conformance.yml")
    for deleted_branch in (
        "feat/pncs-v0.28-release-closure",
        "fix/pncs-v028-postmerge-conformance",
        "feat/libpnv36-rust-v0.1",
    ):
        assert deleted_branch not in text

    assert "pure-conformance:" in text
    assert "structural-authority:" not in text
    assert "semantic-equivalence:" not in text
    assert "dynamics-pure:" not in text
    assert "concurrency-pure:" not in text
    assert "repository-integrity:" not in text
    assert "retention-days: 7" not in text
    assert "retention-days: 1" in text


def test_v1_release_closure_is_compact_and_does_not_archive_full_source():
    text = _workflow("pncs-v1-release-closure.yml")
    assert "release-closure:" in text
    assert "macos-latest" not in text
    assert "PNCS_closure_source.zip" not in text
    assert "retention-days: 7" not in text
    assert "retention-days: 1" in text
    assert text.count("actions/checkout@v4") == 1
    assert text.count("actions/setup-python@v5") == 1


def test_v1_release_closure_runs_this_regression_guard():
    text = _workflow("pncs-v1-release-closure.yml")
    assert "tests/test_post_consolidation_workflow_integrity_v01.py" in text
