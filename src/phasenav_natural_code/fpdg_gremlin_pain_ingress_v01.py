from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .gremlin_kaku_resolver_v01 import GremlinKakuResolver, compile_relation_mining_with_resolver
from .gremlin_relation_mining_adapter_v01 import (
    RelationMiningAlignment,
    RelationMiningFinding,
)

INGRESS_SCHEMA = "PNCS_FPDG_GREMLIN_PAIN_INGRESS_V0_1"
INGRESS_RECEIPT_SCHEMA = "PNCS_FPDG_GREMLIN_PAIN_INGRESS_RECEIPT_V0_1"
EXPECTED_PACKET_SCHEMA = "FPDG_GREMLIN_PAIN_PACKET_V0_1"
LEDGER_SCHEMA = "PNCS_RELATION_MINING_LEDGER_V0_3"


class FpdgGremlinPainIngressError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FpdgGremlinPainIngressError(f"{field} must be a non-empty string")
    return value.strip()


def _safe(value: str) -> str:
    token = "".join(ch if ch.isalnum() else "_" for ch in _nonempty(value, "token").upper()).strip("_")
    if not token:
        raise FpdgGremlinPainIngressError("empty safe token")
    return token


def _validate_packet(packet: Mapping[str, Any], packet_id: str) -> None:
    if packet.get("schema") != EXPECTED_PACKET_SCHEMA:
        raise FpdgGremlinPainIngressError(
            f"{packet_id}: expected {EXPECTED_PACKET_SCHEMA}, got {packet.get('schema')!r}"
        )
    required_safety = {
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "vector_guessing_allowed": False,
        "candidate_edges_enter_canon": False,
    }
    for key, expected in required_safety.items():
        if packet.get(key) != expected:
            raise FpdgGremlinPainIngressError(
                f"{packet_id}: unsafe or incompatible packet field {key}: "
                f"expected {expected!r}, got {packet.get(key)!r}"
            )
    zones = packet.get("zones")
    if zones is not None and not isinstance(zones, list):
        raise FpdgGremlinPainIngressError(f"{packet_id}: zones must be a list")


@dataclass(frozen=True)
class FpdgPainAlignment:
    left_chain_id: str
    left_claim_index: int
    right_chain_id: str
    right_claim_index: int
    relation_type: str = "ISOMORPHIC_TO"

    def __post_init__(self) -> None:
        object.__setattr__(self, "left_chain_id", _nonempty(self.left_chain_id, "left_chain_id"))
        object.__setattr__(self, "right_chain_id", _nonempty(self.right_chain_id, "right_chain_id"))
        object.__setattr__(self, "relation_type", _nonempty(self.relation_type, "relation_type").upper())
        if (
            not isinstance(self.left_claim_index, int)
            or isinstance(self.left_claim_index, bool)
            or self.left_claim_index < 0
        ):
            raise FpdgGremlinPainIngressError("left_claim_index must be a non-negative integer")
        if (
            not isinstance(self.right_claim_index, int)
            or isinstance(self.right_claim_index, bool)
            or self.right_claim_index < 0
        ):
            raise FpdgGremlinPainIngressError("right_claim_index must be a non-negative integer")
        if self.left_chain_id == self.right_chain_id:
            raise FpdgGremlinPainIngressError("FPDG pain alignment must bind two distinct chains")


@dataclass(frozen=True)
class FpdgPainIngressResult:
    ledger: Mapping[str, Any]
    finding: RelationMiningFinding
    receipt: Mapping[str, Any]


def _namespaced_chain_id(packet_id: str, chain_id: str) -> str:
    return f"FPDG.{_safe(packet_id)}.{_safe(chain_id)}"


def _packet_chains(packet_id: str, packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for zone_index, zone in enumerate(packet.get("zones", [])):
        if not isinstance(zone, Mapping):
            raise FpdgGremlinPainIngressError(f"{packet_id}: zone {zone_index} must be an object")
        domains_raw = zone.get("domains", [])
        if not isinstance(domains_raw, list) or any(not isinstance(item, str) for item in domains_raw):
            raise FpdgGremlinPainIngressError(f"{packet_id}: zone {zone_index} domains must be strings")
        domains = tuple(
            sorted(
                set(
                    _nonempty(item, f"{packet_id}: zone {zone_index} domain")
                    for item in domains_raw
                )
            )
        )
        raw_chains = zone.get("raw_chains", [])
        if not isinstance(raw_chains, list):
            raise FpdgGremlinPainIngressError(f"{packet_id}: zone {zone_index} raw_chains must be a list")
        for chain_index, chain in enumerate(raw_chains):
            if not isinstance(chain, Mapping):
                raise FpdgGremlinPainIngressError(
                    f"{packet_id}: zone {zone_index} chain {chain_index} must be an object"
                )
            raw_id = _nonempty(str(chain.get("chain_id", "")), "chain_id")
            claims = chain.get("claims")
            if not isinstance(claims, list) or not claims:
                raise FpdgGremlinPainIngressError(f"{packet_id}:{raw_id}: claims must be non-empty list")
            if any(not isinstance(claim, str) for claim in claims):
                raise FpdgGremlinPainIngressError(f"{packet_id}:{raw_id}: invalid claim id")
            normalized_claims = tuple(
                _nonempty(claim, f"{packet_id}:{raw_id}: claim_id") for claim in claims
            )
            evidence_refs_raw = zone.get("evidence_refs", [])
            if not isinstance(evidence_refs_raw, list):
                raise FpdgGremlinPainIngressError(
                    f"{packet_id}: zone {zone_index} evidence_refs must be a list"
                )
            normalized_evidence_refs = tuple(
                _nonempty(ref, f"{packet_id}: zone {zone_index} evidence_ref")
                for ref in evidence_refs_raw
                if isinstance(ref, str) and ref.strip()
            )
            out.append(
                {
                    "id": _namespaced_chain_id(packet_id, raw_id),
                    "packet_id": packet_id,
                    "raw_chain_id": raw_id,
                    "zone_index": zone_index,
                    "zone_domains": domains,
                    "status": str(chain.get("status", "OBSERVED_DIAGNOSTIC_WITNESS")),
                    "claims": normalized_claims,
                    "evidence_refs": normalized_evidence_refs,
                }
            )
    return out


def collect_packet_chains(packets: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    if not isinstance(packets, Mapping) or not packets:
        raise FpdgGremlinPainIngressError("at least one FPDG pain packet is required")
    out: dict[str, dict[str, Any]] = {}
    for packet_id, packet in packets.items():
        packet_id = _nonempty(str(packet_id), "packet_id")
        if not isinstance(packet, Mapping):
            raise FpdgGremlinPainIngressError(f"{packet_id}: packet must be a mapping")
        _validate_packet(packet, packet_id)
        for chain in _packet_chains(packet_id, packet):
            if chain["id"] in out:
                raise FpdgGremlinPainIngressError(f"duplicate namespaced FPDG chain id: {chain['id']}")
            out[chain["id"]] = chain
    if not out:
        raise FpdgGremlinPainIngressError(
            "FPDG packet set contains no claim witness chains; integration-only pain cannot be lowered to relation mining"
        )
    return out


def _resolve_domain(chain: Mapping[str, Any], chain_domains: Mapping[str, str]) -> str:
    chain_id = str(chain["id"])
    explicit = chain_domains.get(chain_id)
    if explicit is not None:
        return _nonempty(str(explicit), f"chain domain {chain_id}")
    hints = tuple(chain.get("zone_domains", ()))
    if len(hints) == 1:
        return _nonempty(str(hints[0]), f"chain domain {chain_id}")
    if not hints:
        raise FpdgGremlinPainIngressError(
            f"{chain_id}: no source domain in packet; explicit chain_domains binding required"
        )
    raise FpdgGremlinPainIngressError(
        f"{chain_id}: packet exposes multiple possible domains {list(hints)!r}; explicit chain_domains binding required"
    )


def build_relation_mining_inputs(
    packets: Mapping[str, Mapping[str, Any]],
    *,
    claim_to_atom: Mapping[str, str],
    alignments: Sequence[FpdgPainAlignment],
    finding_id: str,
    invariant_id: str,
    invariant_description: str,
    chain_domains: Mapping[str, str] | None = None,
    selected_chain_ids: Sequence[str] | None = None,
    evidence_refs: Sequence[str] = (),
) -> FpdgPainIngressResult:
    """Lower reviewed FPDG witness chains to the existing PNCS relation-mining format.

    Claim IDs are never treated as atoms. Every selected claim requires an explicit
    claim_to_atom binding. The resulting atoms must still pass the canonical KAKU
    resolver before the existing GREMLIN relational compiler may run.
    """

    chains = collect_packet_chains(packets)
    chain_domains = {} if chain_domains is None else chain_domains
    if not isinstance(claim_to_atom, Mapping) or not claim_to_atom:
        raise FpdgGremlinPainIngressError("explicit claim_to_atom bindings are required")
    if not alignments:
        raise FpdgGremlinPainIngressError("at least one explicit FPDG cross-chain alignment is required")

    if selected_chain_ids is None:
        selected = tuple(sorted(chains))
    else:
        selected = tuple(_nonempty(str(value), "selected_chain_id") for value in selected_chain_ids)
        if len(selected) != len(set(selected)):
            raise FpdgGremlinPainIngressError("selected_chain_ids must be unique")
    if len(selected) < 2:
        raise FpdgGremlinPainIngressError("relation mining requires at least two selected FPDG chains")
    unknown = sorted(set(selected) - set(chains))
    if unknown:
        raise FpdgGremlinPainIngressError(f"selected unknown FPDG chains: {unknown}")

    ledger_chains: list[dict[str, Any]] = []
    domain_by_chain: dict[str, str] = {}
    required_claims: set[str] = set()
    normalized_claim_to_atom: dict[str, str] = {}
    for chain_id in selected:
        chain = chains[chain_id]
        domain = _resolve_domain(chain, chain_domains)
        domain_by_chain[chain_id] = domain
        atoms = []
        for claim in chain["claims"]:
            required_claims.add(claim)
            atom = claim_to_atom.get(claim)
            if atom is None:
                raise FpdgGremlinPainIngressError(
                    f"explicit claim_to_atom binding required before GREMLIN lowering: {claim}"
                )
            normalized_atom = _nonempty(str(atom), f"claim_to_atom[{claim}]").upper()
            normalized_claim_to_atom[claim] = normalized_atom
            atoms.append(normalized_atom)
        ledger_chains.append(
            {
                "id": chain_id,
                "source": domain,
                "status": chain["status"],
                "atoms": atoms,
                "statement": "FPDG localized pain witness chain",
                "fpdg_claims": list(chain["claims"]),
                "fpdg_packet_id": chain["packet_id"],
                "fpdg_raw_chain_id": chain["raw_chain_id"],
            }
        )

    if len(set(domain_by_chain.values())) < 2:
        raise FpdgGremlinPainIngressError("selected FPDG chains must span at least two explicit source domains")

    relation_alignments: list[RelationMiningAlignment] = []
    for row in alignments:
        if not isinstance(row, FpdgPainAlignment):
            raise FpdgGremlinPainIngressError("FpdgPainAlignment required")
        if row.left_chain_id not in selected or row.right_chain_id not in selected:
            raise FpdgGremlinPainIngressError("alignment references a chain outside selected_chain_ids")
        left = chains[row.left_chain_id]
        right = chains[row.right_chain_id]
        if row.left_claim_index >= len(left["claims"]) or row.right_claim_index >= len(right["claims"]):
            raise FpdgGremlinPainIngressError("alignment claim index is out of range")
        if domain_by_chain[row.left_chain_id] == domain_by_chain[row.right_chain_id]:
            raise FpdgGremlinPainIngressError("alignment must bind distinct source domains")
        relation_alignments.append(
            RelationMiningAlignment(
                row.left_chain_id,
                row.left_claim_index,
                row.right_chain_id,
                row.right_claim_index,
                row.relation_type,
            )
        )

    packet_hashes = {packet_id: _sha256(dict(packet)) for packet_id, packet in sorted(packets.items())}
    signature_refs = []
    for packet_id, packet in sorted(packets.items()):
        signature = packet.get("incident_signature")
        if isinstance(signature, Mapping) and isinstance(signature.get("signature_hash"), str):
            signature_refs.append(f"fpdg_pain_signature:{packet_id}:{signature['signature_hash']}")

    all_evidence = set(_nonempty(str(ref), "evidence_ref") for ref in evidence_refs)
    all_evidence.update(signature_refs)
    all_evidence.update(f"fpdg_packet:{packet_id}:{digest}" for packet_id, digest in packet_hashes.items())
    for chain_id in selected:
        all_evidence.update(chains[chain_id]["evidence_refs"])

    ledger = {
        "schema": LEDGER_SCHEMA,
        "status": "FPDG_PAIN_INGRESS_CANDIDATE_ONLY",
        "chains": ledger_chains,
        "source_adapter": INGRESS_SCHEMA,
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
    }
    finding = RelationMiningFinding(
        finding_id=_nonempty(finding_id, "finding_id"),
        invariant_id=_nonempty(invariant_id, "invariant_id"),
        invariant_description=_nonempty(invariant_description, "invariant_description"),
        chain_ids=selected,
        alignments=tuple(relation_alignments),
        evidence_refs=tuple(sorted(all_evidence)),
    )

    receipt_body = {
        "schema": INGRESS_RECEIPT_SCHEMA,
        "adapter_contract": INGRESS_SCHEMA,
        "source_packet_schema": EXPECTED_PACKET_SCHEMA,
        "relation_mining_ledger_schema": LEDGER_SCHEMA,
        "packet_sha256": packet_hashes,
        "selected_chain_ids": list(selected),
        "chain_domains": {key: domain_by_chain[key] for key in sorted(domain_by_chain)},
        "claim_to_atom": {claim: normalized_claim_to_atom[claim] for claim in sorted(required_claims)},
        "alignments": [
            {
                "left_chain_id": row.left_chain_id,
                "left_claim_index": row.left_claim_index,
                "right_chain_id": row.right_chain_id,
                "right_claim_index": row.right_claim_index,
                "relation_type": row.relation_type,
            }
            for row in alignments
        ],
        "finding_id": finding.finding_id,
        "invariant_id": finding.invariant_id,
        "claim_ids_are_kaku_atoms": False,
        "vector_guessing_allowed": False,
        "canonical_kaku_resolution_required": True,
        "single_exact_36d_basis_required": True,
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }
    receipt = {**receipt_body, "receipt_sha256": _sha256(receipt_body)}
    return FpdgPainIngressResult(ledger=ledger, finding=finding, receipt=receipt)


def compile_fpdg_pain_with_resolver(
    packets: Mapping[str, Mapping[str, Any]],
    *,
    claim_to_atom: Mapping[str, str],
    alignments: Sequence[FpdgPainAlignment],
    finding_id: str,
    invariant_id: str,
    invariant_description: str,
    resolver: GremlinKakuResolver,
    generation_binding: str,
    identity: str,
    authority: str,
    chain_domains: Mapping[str, str] | None = None,
    selected_chain_ids: Sequence[str] | None = None,
    evidence_refs: Sequence[str] = (),
    authoring_root: Path | str | None = None,
):
    """Run FPDG pain evidence through the existing GREMLIN KAKU + compiler pipeline."""

    if not isinstance(resolver, GremlinKakuResolver):
        raise FpdgGremlinPainIngressError("canonical GremlinKakuResolver required")
    ingress = build_relation_mining_inputs(
        packets,
        claim_to_atom=claim_to_atom,
        alignments=alignments,
        finding_id=finding_id,
        invariant_id=invariant_id,
        invariant_description=invariant_description,
        chain_domains=chain_domains,
        selected_chain_ids=selected_chain_ids,
        evidence_refs=evidence_refs,
    )
    compilation = compile_relation_mining_with_resolver(
        ingress.ledger,
        ingress.finding,
        resolver=resolver,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        authoring_root=str(authoring_root) if authoring_root is not None else None,
    )
    return ingress, compilation
