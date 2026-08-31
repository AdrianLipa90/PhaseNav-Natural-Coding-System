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


def test_post_consolidation_feature_workflows_target_main_not_deleted_branches():
    cases = {
        "pncs-full-program-executor-integration.yml": (
            "feat/pncs-full-program-executor-v01",
            "feat/pncs-v029-orchorbital-harvest-hardening",
        ),
        "pncs-native-pnv-exec.yml": ("feat/native-pnv-exec-tool",),
        "pncs-v030-resident-hotpath.yml": ("feat/pncs-v0.30-resident-hotpath",),
        "pncs-semantic-orbital-carrier-v01.yml": (
            "feat/pncs-semantic-orbital-carrier-v0.1",
        ),
        "pncs-semantic-phase-inverse-v02.yml": (
            "feat/pncs-semantic-phase-inverse-v0.2",
        ),
        "pncs-semantic-orbital-trajectory-v03.yml": (
            "feat/pncs-semantic-orbital-trajectory-v0.3",
        ),
        "pncs-tau-liminal-file-v01.yml": (
            "feat/pncs-tau-liminal-file-v0.1",
        ),
    }
    for workflow_name, deleted_branches in cases.items():
        text = _workflow(workflow_name)
        assert "pull_request:" in text
        assert "      - main" in text
        assert "workflow_dispatch:" in text
        for deleted_branch in deleted_branches:
            assert deleted_branch not in text


def test_newly_consolidated_layers_remain_in_ci_coverage():
    native = _workflow("pncs-native-pnv-exec.yml")
    assert "tests/test_native_pnv_exec_v01.py" in native
    assert "tests/test_dncrypt_native_pncs_v04_causality.py" in native
    assert "native/programs/DNCRYPT_NATIVE_PNCS_V0_4.pnv" in native

    full_executor = _workflow("pncs-full-program-executor-integration.yml")
    assert "tests/test_full_program_executor_receipt_integrity_v01.py" in full_executor

    gremlin = _workflow("pncs-gremlin-pnv-authoring.yml")
    for path in (
        "src/phasenav_natural_code/model.py",
        "src/phasenav_natural_code/pnv_holonomy_numeric_v01.py",
        "tests/test_model_integrity_v01.py",
        "tests/test_gremlin_pnv_authoring_canonical_boundary_v01.py",
        "tests/test_gremlin_radical_candidate_integrity_v01.py",
        "tests/test_gremlin_relational_compiler_integrity_v01.py",
        "tests/test_gremlin_relational_admission_v01.py",
        "tests/test_gremlin_relation_mining_admission_v01.py",
        "tests/test_gremlin_kaku_resolver_admission_v01.py",
        "tests/test_pnv_holonomy_numeric_hardening_v01.py",
        "tests/test_gremlin_cross_formalism_bank_v02.py",
        "tests/test_gremlin_cross_formalism_sealed_bundle_v01.py",
        "tests/test_gremlin_cross_formalism_round28_v01.py",
        "tests/test_gremlin_round28_sealed_bundle_v01.py",
        "tests/test_fpdg_gremlin_pain_ingress_v01.py",
    ):
        assert path in gremlin

    tau = _workflow("pncs-tau-liminal-file-v01.yml")
    for path in (
        "src/phasenav_natural_code/gremlin_tau_codec_v01.py",
        "src/phasenav_natural_code/gremlin_isomorphic_codec_merge_v01.py",
        "tests/test_gremlin_tau_codec_v01.py",
        "tests/test_gremlin_isomorphic_codec_merge_v01.py",
    ):
        assert path in tau


def test_v1_release_closure_runs_full_post_merge_regression_surface():
    text = _workflow("pncs-v1-release-closure.yml")
    assert "python -m pip install pytest numpy" in text
    for test_path in (
        "tests/test_post_consolidation_workflow_integrity_v01.py",
        "tests/test_manifest_tool_v28.py",
        "tests/test_model_integrity_v01.py",
        "tests/test_full_program_executor_v01.py",
        "tests/test_full_program_executor_receipt_integrity_v01.py",
        "tests/test_runtime_v30_hot.py",
        "tests/test_native_pnv_exec_v01.py",
        "tests/test_gremlin_pnv_authoring_v02.py",
        "tests/test_gremlin_pnv_authoring_canonical_boundary_v01.py",
        "tests/test_gremlin_radical_candidate_integrity_v01.py",
        "tests/test_gremlin_relational_compiler_v01.py",
        "tests/test_gremlin_relational_compiler_integrity_v01.py",
        "tests/test_gremlin_relational_admission_v01.py",
        "tests/test_gremlin_relation_mining_adapter_v01.py",
        "tests/test_gremlin_relation_mining_admission_v01.py",
        "tests/test_gremlin_kaku_resolver_v01.py",
        "tests/test_gremlin_kaku_resolver_admission_v01.py",
        "tests/test_gremlin_kaku_resolver_pipeline_v01.py",
        "tests/test_tau_frame_codec_v01.py",
        "tests/test_pnh5_tau_realization_v01.py",
        "tests/test_gremlin_tau_codec_v01.py",
        "tests/test_gremlin_isomorphic_codec_merge_v01.py",
        "tests/test_gremlin_inverse_lineage_v01.py",
        "tests/test_gremlin_pnv_holonomy_v01.py",
        "tests/test_gremlin_pnv_holonomy_effect_boundary_v01.py",
        "tests/test_pnv_holonomy_numeric_hardening_v01.py",
        "tests/test_pnv_source_holonomy_v01.py",
        "tests/test_pnv_noether_collective_holonomy_v01.py",
        "tests/test_pnv_noether_rfc_current_holonomy_v01.py",
        "tests/test_pnv_scalar_field_rotor_reduction_v01.py",
        "tests/test_pnv_gauge_covariant_phase_pullback_v01.py",
        "tests/test_gremlin_pnv_bridge_source_holonomy_v02.py",
        "tests/test_gremlin_pnv_bridge_noether_collective_v02.py",
        "tests/test_gremlin_pnv_bridge_noether_rfc_current_v02.py",
        "tests/test_gremlin_pnv_bridge_scalar_field_rotor_v02.py",
        "tests/test_gremlin_pnv_bridge_gauge_covariant_pullback_v02.py",
        "tests/test_dncrypt_native_pncs_v04_causality.py",
        "tests/test_fpdg_gremlin_pain_ingress_v01.py",
        "tests/test_gremlin_cross_formalism_bank_v02.py",
        "tests/test_gremlin_cross_formalism_sealed_bundle_v01.py",
        "tests/test_gremlin_cross_formalism_round28_v01.py",
        "tests/test_gremlin_round28_sealed_bundle_v01.py",
        "tests/test_semantic_orbital_carrier_v01.py",
        "tests/test_semantic_phase_inverse_v02.py",
        "tests/test_semantic_orbital_trajectory_v03.py",
    ):
        assert test_path in text
