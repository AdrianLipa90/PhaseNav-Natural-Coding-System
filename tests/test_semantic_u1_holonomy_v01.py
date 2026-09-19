from __future__ import annotations

import cmath
from pathlib import Path

import pytest

from phasenav_natural_code.native_pnv_exec_v01 import parse_pnv
from phasenav_natural_code.semantic_u1_holonomy_v01 import (
    closed_gauge_shift,
    open_gauge_shift,
    semantic_u1_coupling,
    semantic_u1_phase,
    semantic_u1_transport,
)

ROOT=Path(__file__).resolve().parents[1]


def test_native_contract_parses_without_new_opcodes():
    text=(ROOT/"native"/"PNCS_NONLOCAL_SEMANTIC_U1_HOLONOMY_V0_1.pnv").read_text(encoding="utf-8")
    program=parse_pnv(text)
    assert [op.opcode for op in program.ops] == ["SOURCE","TRANSFORM","SOURCE","COMPOSITION","RETURN"]
    assert program.mode == "READ_ONLY"


def test_transport_composition_and_reversal():
    a=(0.2,-0.35)
    b=(0.8,0.1)
    wa=semantic_u1_transport(a)
    assert abs(wa) == pytest.approx(1.0)
    assert semantic_u1_transport(a+b) == pytest.approx(wa*semantic_u1_transport(b))
    assert semantic_u1_transport(tuple(-x for x in reversed(a))) == pytest.approx(wa.conjugate())


def test_open_gauge_covariance():
    edges=(0.25,-0.40,0.75)
    chi=(0.10,0.55,-0.20,0.35)
    shifted=open_gauge_shift(edges,chi)
    expected=cmath.exp(1j*(chi[-1]-chi[0]))*semantic_u1_transport(edges)
    assert semantic_u1_transport(shifted) == pytest.approx(expected)


def test_closed_gauge_invariance():
    edges=(0.25,-0.40,0.75)
    chi=(0.10,0.55,-0.20)
    shifted=closed_gauge_shift(edges,chi)
    assert semantic_u1_transport(shifted) == pytest.approx(semantic_u1_transport(edges))


def test_nonlocal_semantic_coupling_preserves_overlap_strength():
    z=complex(0.31,-0.47)
    edges=(0.17,0.29,-0.08)
    c=semantic_u1_coupling(z,edges)
    assert abs(c) == pytest.approx(abs(z))
    assert c/z == pytest.approx(semantic_u1_transport(edges))
    assert semantic_u1_phase(edges) == pytest.approx(cmath.phase(semantic_u1_transport(edges)))
