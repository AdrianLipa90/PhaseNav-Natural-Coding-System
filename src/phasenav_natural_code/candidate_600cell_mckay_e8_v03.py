from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping

SCHEMA = "PNCS_600CELL_MCKAY_E8_CANDIDATE_V0_3"
STATUS = "CANDIDATE"
PROMOTION_STATE = "CANDIDATE_ONLY"
PHYSICAL_BINDING = "OPEN"
CERTIFIED_ELL_MIN = 0
CERTIFIED_ELL_MAX = 7

IRREP_DIMS: dict[str, int] = {
    "rho1": 1,
    "rho2a": 2,
    "rho3a": 3,
    "rho4a": 4,
    "rho5": 5,
    "rho6": 6,
    "rho4b": 4,
    "rho3b": 3,
    "rho2b": 2,
}

# Stable local identifiers avoid treating author-dependent prime notation as a
# computational invariant. Edges encode tensoring by Q=rho2a.
MCKAY_ADJACENCY: dict[str, tuple[str, ...]] = {
    "rho1": ("rho2a",),
    "rho2a": ("rho1", "rho3a"),
    "rho3a": ("rho2a", "rho4a"),
    "rho4a": ("rho3a", "rho5"),
    "rho5": ("rho4a", "rho6"),
    "rho6": ("rho5", "rho4b", "rho3b"),
    "rho4b": ("rho6", "rho2b"),
    "rho3b": ("rho6",),
    "rho2b": ("rho4b",),
}

EXPECTED_RESTRICTIONS: dict[int, dict[str, int]] = {
    0: {"rho1": 1},
    1: {"rho2a": 1},
    2: {"rho3a": 1},
    3: {"rho4a": 1},
    4: {"rho5": 1},
    5: {"rho6": 1},
    6: {"rho4b": 1, "rho3b": 1},
    7: {"rho6": 1, "rho2b": 1},
}

EXPECTED_COEFFICIENT_RANKS = (1, 4, 9, 16, 25, 36, 25, 40)
EXPECTED_CUMULATIVE_RANKS = (1, 5, 14, 30, 55, 91, 116, 120)


class Candidate600CellMcKayError(ValueError):
    pass


@dataclass(frozen=True)
class McKayClosureReceipt:
    schema: str
    status: str
    promotion_state: str
    physical_binding: str
    certified_ell_min: int
    certified_ell_max: int
    ell6_coefficient_rank: int
    ell7_coefficient_rank: int
    ell7_cumulative_rank: int
    group_algebra_dimension: int
    runtime_default: bool
    canon_write_authority: bool


def _validate_ell(ell: int) -> int:
    if isinstance(ell, bool) or not isinstance(ell, int):
        raise Candidate600CellMcKayError("ell must be an integer")
    if not CERTIFIED_ELL_MIN <= ell <= CERTIFIED_ELL_MAX:
        raise Candidate600CellMcKayError(
            f"certified McKay range is ell={CERTIFIED_ELL_MIN}..{CERTIFIED_ELL_MAX}; got {ell}"
        )
    return ell


def _clean(decomposition: Mapping[str, int]) -> Counter[str]:
    out: Counter[str] = Counter()
    for irrep, multiplicity in decomposition.items():
        if irrep not in IRREP_DIMS:
            raise Candidate600CellMcKayError(f"unknown irrep: {irrep}")
        if isinstance(multiplicity, bool) or not isinstance(multiplicity, int) or multiplicity < 0:
            raise Candidate600CellMcKayError(
                f"multiplicity for {irrep} must be a non-negative integer"
            )
        if multiplicity:
            out[irrep] = multiplicity
    return out


def validate_mckay_graph() -> bool:
    if set(MCKAY_ADJACENCY) != set(IRREP_DIMS):
        raise Candidate600CellMcKayError("McKay graph and dimension table disagree")
    for irrep, neighbours in MCKAY_ADJACENCY.items():
        if len(neighbours) != len(set(neighbours)):
            raise Candidate600CellMcKayError(f"duplicate neighbour at {irrep}")
        for neighbour in neighbours:
            if neighbour not in IRREP_DIMS:
                raise Candidate600CellMcKayError(f"unknown McKay neighbour: {neighbour}")
            if irrep not in MCKAY_ADJACENCY[neighbour]:
                raise Candidate600CellMcKayError(f"asymmetric edge: {irrep} -- {neighbour}")
        if 2 * IRREP_DIMS[irrep] != sum(IRREP_DIMS[n] for n in neighbours):
            raise Candidate600CellMcKayError(f"dimension balance fails at {irrep}")
    return True


def tensor_by_fundamental(decomposition: Mapping[str, int]) -> Counter[str]:
    source = _clean(decomposition)
    out: Counter[str] = Counter()
    for irrep, multiplicity in source.items():
        for neighbour in MCKAY_ADJACENCY[irrep]:
            out[neighbour] += multiplicity
    return out


def subtract_representation_fail_closed(
    left: Mapping[str, int], right: Mapping[str, int]
) -> Counter[str]:
    a = _clean(left)
    b = _clean(right)
    keys = set(a) | set(b)
    raw = {key: a.get(key, 0) - b.get(key, 0) for key in keys}
    negatives = {key: value for key, value in raw.items() if value < 0}
    if negatives:
        raise Candidate600CellMcKayError(
            f"negative representation multiplicity is forbidden: {negatives}"
        )
    return Counter({key: value for key, value in raw.items() if value > 0})


def _all_restrictions() -> dict[int, Counter[str]]:
    validate_mckay_graph()
    out: dict[int, Counter[str]] = {
        0: Counter({"rho1": 1}),
        1: Counter({"rho2a": 1}),
    }
    for ell in range(1, CERTIFIED_ELL_MAX):
        out[ell + 1] = subtract_representation_fail_closed(
            tensor_by_fundamental(out[ell]), out[ell - 1]
        )
    return out


def sym_power_restriction(ell: int, *, candidate_enabled: bool) -> dict[str, int]:
    """Return V_ell|_2I in the certified ell=0..7 candidate range.

    This is a representation contract only. It does not activate the S^3
    Laplacian outside the independently validated ell<=5 runtime sector.
    """
    if candidate_enabled is not True:
        raise Candidate600CellMcKayError(
            "McKay closure is CANDIDATE; pass candidate_enabled=True explicitly"
        )
    ell = _validate_ell(ell)
    return dict(sorted(_all_restrictions()[ell].items()))


def representation_dimension(ell: int, *, candidate_enabled: bool) -> int:
    restriction = sym_power_restriction(ell, candidate_enabled=candidate_enabled)
    return sum(IRREP_DIMS[irrep] * mult for irrep, mult in restriction.items())


def coefficient_rank(ell: int, *, candidate_enabled: bool) -> int:
    restriction = sym_power_restriction(ell, candidate_enabled=candidate_enabled)
    # The finite-group coefficient space contains End(V_rho) once for every
    # irrep type that occurs; multiplicity does not duplicate that function
    # space on the finite group.
    return sum(IRREP_DIMS[irrep] ** 2 for irrep in restriction)


def cumulative_carrier_rank(ell: int, *, candidate_enabled: bool) -> int:
    ell = _validate_ell(ell)
    if candidate_enabled is not True:
        raise Candidate600CellMcKayError(
            "McKay closure is CANDIDATE; pass candidate_enabled=True explicitly"
        )
    restrictions = _all_restrictions()
    seen: set[str] = set()
    for level in range(ell + 1):
        seen.update(restrictions[level])
    return sum(IRREP_DIMS[irrep] ** 2 for irrep in seen)


def validate_exact_closure(*, candidate_enabled: bool) -> McKayClosureReceipt:
    if candidate_enabled is not True:
        raise Candidate600CellMcKayError(
            "McKay closure is CANDIDATE; pass candidate_enabled=True explicitly"
        )
    restrictions = _all_restrictions()
    for ell in range(8):
        actual = dict(sorted(restrictions[ell].items()))
        expected = dict(sorted(EXPECTED_RESTRICTIONS[ell].items()))
        if actual != expected:
            raise Candidate600CellMcKayError(
                f"ell={ell} restriction mismatch: {actual} != {expected}"
            )
        dim = sum(IRREP_DIMS[irrep] * mult for irrep, mult in actual.items())
        if dim != ell + 1:
            raise Candidate600CellMcKayError(f"ell={ell} dimension mismatch: {dim}")

    ranks = tuple(
        sum(IRREP_DIMS[irrep] ** 2 for irrep in restrictions[ell]) for ell in range(8)
    )
    cumulative = tuple(
        cumulative_carrier_rank(ell, candidate_enabled=True) for ell in range(8)
    )
    if ranks != EXPECTED_COEFFICIENT_RANKS:
        raise Candidate600CellMcKayError(f"coefficient-rank mismatch: {ranks}")
    if cumulative != EXPECTED_CUMULATIVE_RANKS:
        raise Candidate600CellMcKayError(f"cumulative-rank mismatch: {cumulative}")

    first_reducible = next(
        ell for ell in range(8) if sum(restrictions[ell].values()) > 1
    )
    if first_reducible != 6:
        raise Candidate600CellMcKayError(
            f"first irreducibility break must be ell=6, got ell={first_reducible}"
        )

    all_irreps = set().union(*(set(restrictions[ell]) for ell in range(8)))
    if all_irreps != set(IRREP_DIMS):
        raise Candidate600CellMcKayError("ell=0..7 does not encounter all 2I irreps")

    group_algebra_dimension = sum(dim * dim for dim in IRREP_DIMS.values())
    if group_algebra_dimension != 120:
        raise Candidate600CellMcKayError("2I group-algebra dimension must be 120")

    return McKayClosureReceipt(
        schema=SCHEMA,
        status=STATUS,
        promotion_state=PROMOTION_STATE,
        physical_binding=PHYSICAL_BINDING,
        certified_ell_min=CERTIFIED_ELL_MIN,
        certified_ell_max=CERTIFIED_ELL_MAX,
        ell6_coefficient_rank=ranks[6],
        ell7_coefficient_rank=ranks[7],
        ell7_cumulative_rank=cumulative[7],
        group_algebra_dimension=group_algebra_dimension,
        runtime_default=False,
        canon_write_authority=False,
    )


def candidate_metadata() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "promotion_state": PROMOTION_STATE,
        "physical_binding": PHYSICAL_BINDING,
        "runtime_default": False,
        "canon_write_authority": False,
        "stable_irrep_labels": True,
        "prime_aliases_canonical": False,
        "mckay_graph": "AFFINE_E8",
        "fundamental_irrep": "rho2a",
        "certified_ell": list(range(8)),
        "coefficient_ranks": list(EXPECTED_COEFFICIENT_RANKS),
        "cumulative_carrier_ranks": list(EXPECTED_CUMULATIVE_RANKS),
        "runtime_laplacian_extension_authorized": False,
        "interpretation": {
            "ell6": "FIRST_IRREDUCIBILITY_BREAKING_FINITE_RESOLUTION_THRESHOLD",
            "ell7": "FINITE_REPRESENTATION_CLOSURE",
        },
    }
