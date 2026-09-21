from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping

from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    RelationalCompilation,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
    validate_compiled_relational_candidate,
)
from phasenav_natural_code.model import Kaku, Vector36

BANK_SCHEMA = "PNCS_GREMLIN_FUNDAMENTAL_SEAM_BANK_V0_1"
BASIS = "pncs:t36:fundamental-seam-bank:v1"

SOURCE_PINS: Mapping[str, Mapping[str, str]] = {
    "TIR": {
        "repository": "AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations",
        "commit": "f7b754347502f5051d423867f8a8d60627b1f8d7",
    },
    "IDT": {
        "repository": "AdrianLipa90/Informational-Dynamics-of-Time",
        "commit": "2960a936e3f74b07a4bf30ebc5cb78b6c1811b4c",
    },
    "RFC": {
        "repository": "AdrianLipa90/Relational-Field-Closure",
        "commit": "786d1e1a9f9c91a4c3174719ed76966aa73edcef",
    },
    "SOH": {
        "repository": "AdrianLipa90/secret-of-a-half",
        "commit": "41772776dadf837c7a2f8b095b752e586d85c5dc",
    },
    "INFINITIES": {
        "repository": "AdrianLipa90/Infinities",
        "commit": "c1ad8376f9dd4c2daf2c4ea0bf61568d718fd794",
    },
}

ALLOWED_CLASSES = {"EXACT_CONDITIONAL", "STRONG_STRUCTURAL"}


class FundamentalSeamBankError(RuntimeError):
    pass


@dataclass(frozen=True)
class FundamentalSeamEntry:
    spec: RelationalIsomorphism
    classification: str
    preserved_structure: tuple[str, ...]
    falsification_gate: str
    guardrails: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.classification not in ALLOWED_CLASSES:
            raise FundamentalSeamBankError(
                f"unsupported seam classification: {self.classification}"
            )
        if not self.preserved_structure or not self.falsification_gate:
            raise FundamentalSeamBankError(
                "seam requires preserved structure and falsification gate"
            )


def _source(bank: str, path: str) -> str:
    pin = SOURCE_PINS[bank]
    return f"github:{pin['repository']}@{pin['commit']}:{path}"


def _vector(seed: int) -> Vector36:
    values = tuple(((seed * 71 + i * 29) % 307) / 307.0 for i in range(36))
    return Vector36(values, BASIS)


def _node(kaku_id: str, seed: int, role: str, domain: str, observation_ref: str) -> RelationalNode:
    return RelationalNode(
        Kaku(
            kaku_id,
            _vector(seed),
            1.0 + seed / 19.0,
            "FORWARD",
            1.0,
            role,
            tuple(((seed * 11 + i) % 36) / 36.0 for i in range(36)),
        ),
        domain,
        observation_ref,
    )


def fundamental_seam_bank() -> tuple[FundamentalSeamEntry, ...]:
    tir_se3 = _node(
        "K.FSI.TIR.SE3.GLUE", 1, "se3_affine_transport", "TIR_SE3", "TIR:SE3-GLOBAL-GLUE"
    )
    rfc_se3 = _node(
        "K.FSI.RFC.SE3.COCYCLE", 2, "rigid_overlap_cocycle", "RFC_SE3", "RFC:GSC4G"
    )

    idt_clock = _node(
        "K.FSI.IDT.CLOCK.COCYCLE", 3, "positive_clock_cocycle", "IDT_CLOCK", "IDT:05E"
    )
    rfc_atlas = _node(
        "K.FSI.RFC.ATLAS.COCYCLE", 4, "lorentz_atlas_cocycle", "RFC_ATLAS", "RFC:E25"
    )

    idt_quotient = _node(
        "K.FSI.IDT.POSITIVE.RAY", 5, "positive_ray_quotient", "IDT_QUOTIENT", "IDT:01X"
    )
    tir_gauge = _node(
        "K.FSI.TIR.LOOP.GAUGE", 6, "loop_conjugacy_invariant", "TIR_GAUGE", "TIR:WIJ"
    )
    rfc_quotient = _node(
        "K.FSI.RFC.SE3.QUOTIENT", 7, "global_se3_gauge_quotient", "RFC_QUOTIENT", "RFC:GSC4F"
    )

    inf_collatz = _node(
        "K.FSI.INF.COLLATZ.ACCEL", 8, "accelerated_odd_collatz_branch", "INFINITIES_COLLATZ", "INF:FOUNDATIONS-6"
    )
    tir_collatz = _node(
        "K.FSI.TIR.COLLATZ.LANGUAGE", 9, "unreduced_collatz_parity_language", "TIR_COLLATZ", "TIR:CP1-DYADIC"
    )
    idt_collatz = _node(
        "K.FSI.IDT.COLLATZ.PHASE", 10, "collatz_parity_phase_shift", "IDT_COLLATZ", "IDT:CFS"
    )

    return (
        FundamentalSeamEntry(
            spec=RelationalIsomorphism(
                isomorphism_id="FSI.01.SE3.AFFINE.GLUE.TIR.RFC",
                invariant_id="INV.FSI.SE3.SEMIDIRECT.PRODUCT.GLUE",
                invariant_description=(
                    "under explicit convention matching, TIR affine glue and RFC rigid overlap "
                    "cocycles share the same SE3 semidirect-product composition, inverse and loop-identity closure"
                ),
                nodes=(tir_se3, rfc_se3),
                edges=(
                    RelationalEdge(
                        "REL.FSI.01",
                        tir_se3.kaku.kaku_id,
                        rfc_se3.kaku.kaku_id,
                        "ISOMORPHIC_TO",
                    ),
                ),
                evidence_refs=(
                    _source("TIR", "TIR/foundations/TIR_SE3_GLOBAL_GLUE_HOLONOMY_V0_1.md"),
                    _source("RFC", "closure/einstein/RF_GSC4G_RIGID_OVERLAP_COCYCLE_RECONSTRUCTION.md"),
                ),
            ),
            classification="EXACT_CONDITIONAL",
            preserved_structure=(
                "SE3 semidirect-product composition",
                "inverse law",
                "ordered path composition",
                "identity loop closure",
            ),
            falsification_gate=(
                "the explicit convention map fails to preserve composition, inverse or identity-loop closure"
            ),
            guardrails=(
                "production numeric overlap cocycle remains an RFC source input",
                "curvature/torsion physical interpretation remains separately gated",
            ),
        ),
        FundamentalSeamEntry(
            spec=RelationalIsomorphism(
                isomorphism_id="FSI.02.GLOBAL.COCYCLE.GLUE.SPINE",
                invariant_id="INV.FSI.LOCAL.TRANSITION.CYCLE.CLOSURE.GLOBAL.OBJECT",
                invariant_description=(
                    "IDT clock synchronization, TIR affine transport and RFC atlas gluing share "
                    "a typed local-transition -> ordered-composition -> cycle/cocycle consistency -> global-object spine"
                ),
                nodes=(idt_clock, tir_se3, rfc_atlas),
                edges=(
                    RelationalEdge("REL.FSI.02.A", idt_clock.kaku.kaku_id, tir_se3.kaku.kaku_id, "ISOMORPHIC_TO"),
                    RelationalEdge("REL.FSI.02.B", tir_se3.kaku.kaku_id, rfc_atlas.kaku.kaku_id, "ISOMORPHIC_TO"),
                ),
                evidence_refs=(
                    _source("IDT", "formalism/05E_global_relational_clock_cocycle.md"),
                    _source("TIR", "TIR/foundations/TIR_SE3_GLOBAL_GLUE_HOLONOMY_V0_1.md"),
                    _source("RFC", "closure/einstein/RF_E25_SHARED_SPACETIME_ATLAS_COCYCLE.md"),
                ),
            ),
            classification="STRONG_STRUCTURAL",
            preserved_structure=(
                "typed local transitions",
                "ordered composition",
                "closed-cycle or triple-overlap consistency",
                "path-independent global reconstruction",
            ),
            falsification_gate=(
                "a claimed source instance lacks its own composition/cycle closure law or global reconstruction consequence"
            ),
            guardrails=(
                "clock ratios, SE3 affine maps and Lorentz atlas transitions remain distinct groups/types",
                "structural isomorphism is not physical identity",
            ),
        ),
        FundamentalSeamEntry(
            spec=RelationalIsomorphism(
                isomorphism_id="FSI.03.REPRESENTATION.QUOTIENT.RELATIONAL.INVARIANT",
                invariant_id="INV.FSI.REPRESENTATION.ORBIT.QUOTIENT.RELATIONAL.DATA",
                invariant_description=(
                    "IDT positive-ray normalization, TIR local-frame/rephasing loop invariants and RFC global SE3 quotient "
                    "share the representation-orbit -> retained relational invariant pattern"
                ),
                nodes=(idt_quotient, tir_gauge, rfc_quotient),
                edges=(
                    RelationalEdge("REL.FSI.03.A", idt_quotient.kaku.kaku_id, tir_gauge.kaku.kaku_id, "ISOMORPHIC_TO"),
                    RelationalEdge("REL.FSI.03.B", tir_gauge.kaku.kaku_id, rfc_quotient.kaku.kaku_id, "ISOMORPHIC_TO"),
                ),
                evidence_refs=(
                    _source("IDT", "formalism/01X_RFC_normalized_shape_extensive_scale_interface.md"),
                    _source("TIR", "TIR/foundations/TIR_WIJ_HOLONOMY_CROSSWALK_V0_1.md"),
                    _source("RFC", "closure/einstein/RF_GSC4F_GLOBAL_SE3_GAUGE_QUOTIENT.md"),
                ),
            ),
            classification="STRONG_STRUCTURAL",
            preserved_structure=(
                "declared representation-group orbit is non-observable",
                "relative/relational data survive",
                "invariant closure data do not depend on arbitrary common representation",
            ),
            falsification_gate=(
                "a declared gauge transformation changes the source-defined invariant relational observable"
            ),
            guardrails=(
                "the quotient groups and metrics remain source-domain specific",
                "no universal physical quotient is inferred from the structural pattern",
            ),
        ),
        FundamentalSeamEntry(
            spec=RelationalIsomorphism(
                isomorphism_id="FSI.04.COLLATZ.ACCELERATED.BLOCK.PHASE",
                invariant_id="INV.FSI.COLLATZ.ACCELERATED.STEP.UNREDUCED.BLOCK",
                invariant_description=(
                    "for odd n, the accelerated Collatz step U(n) equals a+1 unreduced Collatz steps, "
                    "with parity block 1 followed by a zeros; the IDT parity phase therefore shifts by 2^(a+1)"
                ),
                nodes=(inf_collatz, tir_collatz, idt_collatz),
                edges=(
                    RelationalEdge("REL.FSI.04.A", inf_collatz.kaku.kaku_id, tir_collatz.kaku.kaku_id, "MAPS_TO"),
                    RelationalEdge("REL.FSI.04.B", tir_collatz.kaku.kaku_id, idt_collatz.kaku.kaku_id, "MAPS_TO"),
                ),
                evidence_refs=(
                    _source("INFINITIES", "FOUNDATIONS.md"),
                    _source("TIR", "TIR/foundations/TIR_CP1_DYADIC_FRACTAL_GATE_V0_1.md"),
                    _source("IDT", "docs/IDT_COLLATZ_FS_PHASE_REGISTRY_SUPPLEMENT_V0_1.md"),
                ),
            ),
            classification="EXACT_CONDITIONAL",
            preserved_structure=(
                "accelerated odd branch equals an unreduced 1-0^a block",
                "parity shift length a+1",
                "phase-doubling exponent 2^(a+1) where q_C is defined",
            ),
            falsification_gate=(
                "for an odd integer n, repeated unreduced Collatz application a(n)+1 times differs from U(n) "
                "or the initial parity block differs from 1 followed by a(n) zeros"
            ),
            guardrails=(
                "no global Collatz convergence claim",
                "no identification of iteration count or phase with physical elapsed time",
            ),
        ),
    )


def bank_manifest() -> Mapping[str, object]:
    entries = fundamental_seam_bank()
    body = {
        "schema": BANK_SCHEMA,
        "status": "POST_V1_EXPERIMENTAL_CANDIDATE_ONLY",
        "source_pins": {name: dict(pin) for name, pin in sorted(SOURCE_PINS.items())},
        "entry_count": len(entries),
        "entries": [
            {
                "isomorphism_id": entry.spec.isomorphism_id,
                "invariant_id": entry.spec.invariant_id,
                "classification": entry.classification,
                "preserved_structure": list(entry.preserved_structure),
                "falsification_gate": entry.falsification_gate,
                "guardrails": list(entry.guardrails),
                "evidence_refs": list(entry.spec.evidence_refs),
            }
            for entry in entries
        ],
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return {**body, "manifest_sha256": digest}


def accelerated_collatz_block(n: int) -> tuple[int, int, tuple[int, ...]]:
    if not isinstance(n, int) or n <= 0 or n % 2 == 0:
        raise FundamentalSeamBankError("n must be a positive odd integer")
    value = 3 * n + 1
    a = 0
    while value % 2 == 0:
        value //= 2
        a += 1
    if a <= 0:
        raise FundamentalSeamBankError("odd Collatz branch must have positive 2-adic valuation")
    return value, a, (1,) + (0,) * a


def unreduced_collatz_step(n: int) -> int:
    if not isinstance(n, int) or n <= 0:
        raise FundamentalSeamBankError("n must be a positive integer")
    return n // 2 if n % 2 == 0 else 3 * n + 1


def validate_accelerated_block(n: int) -> bool:
    accelerated, a, parity = accelerated_collatz_block(n)
    x = n
    observed = []
    for _ in range(a + 1):
        observed.append(x % 2)
        x = unreduced_collatz_step(x)
    return x == accelerated and tuple(observed) == parity


def compile_fundamental_seam_candidates(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    authoring_root=None,
) -> Mapping[str, RelationalCompilation]:
    out = {}
    for entry in fundamental_seam_bank():
        out[entry.spec.isomorphism_id] = compile_relational_isomorphism(
            entry.spec,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            authoring_root=authoring_root,
        )
    return out


def validate_fundamental_seam_candidates(
    compilations: Mapping[str, RelationalCompilation],
):
    expected = {entry.spec.isomorphism_id for entry in fundamental_seam_bank()}
    if set(compilations) != expected:
        raise FundamentalSeamBankError("fundamental seam compilation keyset mismatch")
    results = {}
    for seam_id, compilation in sorted(compilations.items()):
        result = validate_compiled_relational_candidate(compilation)
        if result.receipt["effect_boundary"]["external_effects"] is not False:
            raise FundamentalSeamBankError(
                f"candidate crossed external effect boundary: {seam_id}"
            )
        results[seam_id] = result
    return results
