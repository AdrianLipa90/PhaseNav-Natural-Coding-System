from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
from typing import Any, Iterable, Mapping, Sequence

from .execution_v20_live import load_live_surface
from .execution_v20_model import DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT
from .model import Kaku, RadicalGraph, Relation
from .native_pnv_exec_v01 import SUPPORTED_OPCODES, parse_pnv

AUTHORING_SCHEMA = "PNCS_GREMLIN_PNV_AUTHORING_V0_2"
CANDIDATE_SCHEMA = "PNCS_GREMLIN_PNV_CANDIDATE_V0_2"
RECEIPT_SCHEMA = "PNCS_GREMLIN_PNV_AUTHORING_RECEIPT_V0_2"
DEFAULT_AUTHORING_RELATIVE_ROOT = Path("gremlin/candidates/pncs")
_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class GremlinPNVAuthoringError(RuntimeError):
    pass


def _nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GremlinPNVAuthoringError(f"{field} must be a non-empty string")
    return value.strip()


def _canonical_refs(values: Sequence[str], field: str) -> list[str]:
    if isinstance(values, (str, bytes, bytearray)):
        raise GremlinPNVAuthoringError(f"{field} must be a sequence of strings")
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise GremlinPNVAuthoringError(f"{field} must be a sequence of strings") from exc
    return sorted({_nonempty_text(value, field) for value in raw})


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GremlinPNVAuthoringError(
                "non-finite float cannot enter a canonical GREMLIN candidate"
            )
        return value
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, Mapping):
        for key in value:
            if not isinstance(key, str):
                raise GremlinPNVAuthoringError(
                    "canonical GREMLIN mapping keys must be strings"
                )
        return {key: _jsonable(value[key]) for key in sorted(value)}
    raise GremlinPNVAuthoringError(
        f"unsupported canonical value: {type(value).__name__}"
    )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _typed_candidate_id(kind: str, payload: Mapping[str, Any]) -> str:
    return f"pncs:gremlin-{kind.lower()}:sha256:{_sha256(payload)}"


def _digest_from_candidate_id(candidate_id: str) -> str:
    if not isinstance(candidate_id, str):
        raise GremlinPNVAuthoringError("candidate_id must be a string")
    digest = candidate_id.rsplit(":", 1)[-1]
    if not _DIGEST_RE.fullmatch(digest):
        raise GremlinPNVAuthoringError(
            "candidate_id does not terminate in canonical SHA-256"
        )
    return digest


def _typed_dependency_ref(candidate_id: Any, kind: str, field: str) -> str:
    value = _nonempty_text(candidate_id, field)
    prefix = f"pncs:gremlin-{kind.lower()}:sha256:"
    if not value.startswith(prefix):
        raise GremlinPNVAuthoringError(
            f"{field} must reference a GREMLIN {kind} candidate"
        )
    _digest_from_candidate_id(value)
    if len(value) != len(prefix) + 64:
        raise GremlinPNVAuthoringError(
            f"{field} must terminate in exactly one SHA-256 digest"
        )
    return value


def _candidate_envelope(
    kind: str,
    content: Mapping[str, Any],
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    evidence_refs: Sequence[str] = (),
    dependency_ids: Sequence[str] = (),
) -> dict[str, Any]:
    kind = _nonempty_text(kind, "kind").upper()
    if kind not in {"KAKU", "RADICAL", "OPERATOR"}:
        raise GremlinPNVAuthoringError(f"unsupported GREMLIN authoring kind: {kind}")
    generation_binding = _nonempty_text(generation_binding, "generation_binding")
    identity = _nonempty_text(identity, "identity")
    authority = _nonempty_text(authority, "authority")
    body = {
        "schema": CANDIDATE_SCHEMA,
        "authoring_contract": AUTHORING_SCHEMA,
        "kind": kind,
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "generation_binding": generation_binding,
        "identity": identity,
        "authority": authority,
        "evidence_refs": _canonical_refs(evidence_refs, "evidence_ref"),
        "dependency_ids": _canonical_refs(dependency_ids, "dependency_id"),
        "content": _jsonable(content),
    }
    candidate_id = _typed_candidate_id(kind, body)
    return {**body, "candidate_id": candidate_id}


def _kaku_content(kaku: Kaku) -> dict[str, Any]:
    if not isinstance(kaku, Kaku):
        raise GremlinPNVAuthoringError("Kaku instance required")
    return {
        "kaku_id": kaku.kaku_id,
        "basis_id": kaku.vector.basis_id,
        "v36": list(kaku.vector.values),
        "phase": None if kaku.phase is None else list(kaku.phase),
        "semantic_mass": float(kaku.semantic_mass),
        "direction": kaku.direction,
        "polarity": float(kaku.polarity),
        "role": kaku.role,
    }


def build_kaku_candidate(
    kaku: Kaku,
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    return _candidate_envelope(
        "KAKU",
        _kaku_content(kaku),
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        evidence_refs=evidence_refs,
    )


def _validated_radical_snapshot(radical: RadicalGraph) -> tuple[list[str], list[Relation]]:
    radical_id = _nonempty_text(radical.radical_id, "RADICAL graph id")
    basis_id = _nonempty_text(radical.basis_id, "RADICAL graph basis_id")
    if radical_id != radical.radical_id or basis_id != radical.basis_id:
        raise GremlinPNVAuthoringError(
            "RADICAL graph identity must already be canonical"
        )
    if not isinstance(radical.nodes, dict):
        raise GremlinPNVAuthoringError("RADICAL graph node integrity requires a dict")
    node_ids: list[str] = []
    for node_id, node in radical.nodes.items():
        if (
            not isinstance(node_id, str)
            or not isinstance(node, Kaku)
            or node_id != node.kaku_id
            or node.vector.basis_id != basis_id
        ):
            raise GremlinPNVAuthoringError(
                "RADICAL graph node integrity mismatch"
            )
        node_ids.append(node_id)
    if len(node_ids) != len(set(node_ids)):
        raise GremlinPNVAuthoringError("RADICAL graph duplicate node id")

    if not isinstance(radical.edges, list):
        raise GremlinPNVAuthoringError("RADICAL graph relation integrity requires a list")
    relations: list[Relation] = []
    relation_ids: set[str] = set()
    allowed = set(node_ids)
    for edge in radical.edges:
        if not isinstance(edge, Relation):
            raise GremlinPNVAuthoringError(
                "RADICAL graph relation integrity mismatch"
            )
        if edge.source_id not in allowed or edge.target_id not in allowed:
            raise GremlinPNVAuthoringError(
                "RADICAL graph relation integrity endpoint mismatch"
            )
        if edge.relation_id in relation_ids:
            raise GremlinPNVAuthoringError(
                f"RADICAL graph duplicate relation id: {edge.relation_id}"
            )
        relation_ids.add(edge.relation_id)
        relations.append(edge)
    return sorted(node_ids), sorted(
        relations,
        key=lambda edge: (
            edge.relation_id,
            edge.source_id,
            edge.target_id,
            edge.relation_type,
        ),
    )


def build_radical_candidate(
    radical: RadicalGraph,
    *,
    kaku_candidate_ids: Mapping[str, str],
    generation_binding: str,
    identity: str,
    authority: str,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    if not isinstance(radical, RadicalGraph):
        raise GremlinPNVAuthoringError("RadicalGraph instance required")
    if not isinstance(kaku_candidate_ids, Mapping):
        raise GremlinPNVAuthoringError("kaku_candidate_ids must be a mapping")
    if any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in kaku_candidate_ids.items()
    ):
        raise GremlinPNVAuthoringError(
            "kaku_candidate_ids must map string node ids to string candidate ids"
        )

    node_ids, relations = _validated_radical_snapshot(radical)
    if set(node_ids) != set(kaku_candidate_ids):
        raise GremlinPNVAuthoringError(
            "RADICAL must bind exactly one candidate KAKU for every graph node"
        )
    refs = {
        node_id: _typed_dependency_ref(
            kaku_candidate_ids[node_id],
            "KAKU",
            "KAKU candidate id",
        )
        for node_id in node_ids
    }
    content = {
        "radical_id": radical.radical_id,
        "basis_id": radical.basis_id,
        "kaku_candidate_ids": refs,
        "relations": [
            {
                "relation_id": edge.relation_id,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "relation_type": edge.relation_type,
            }
            for edge in relations
        ],
    }
    return _candidate_envelope(
        "RADICAL",
        content,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        evidence_refs=evidence_refs,
        dependency_ids=[refs[node_id] for node_id in node_ids],
    )


def build_operator_candidate(
    name: str,
    opcode: str,
    args: Sequence[str],
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    radical_candidate_id: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    if not isinstance(name, str) or not _ID_RE.fullmatch(name):
        raise GremlinPNVAuthoringError(
            "operator name must be a non-empty PNV identifier"
        )
    if not isinstance(opcode, str):
        raise GremlinPNVAuthoringError("operator opcode must be a string")
    opcode = opcode.upper()
    if opcode not in SUPPORTED_OPCODES:
        raise GremlinPNVAuthoringError(f"unsupported native PNV opcode: {opcode}")
    if isinstance(args, (str, bytes, bytearray)):
        raise GremlinPNVAuthoringError("operator args must be a sequence of strings")
    try:
        canonical_args = tuple(args)
    except TypeError as exc:
        raise GremlinPNVAuthoringError("operator args must be a sequence of strings") from exc
    if (
        not canonical_args
        or any(
            not isinstance(x, str)
            or not x
            or "\n" in x
            or "\r" in x
            for x in canonical_args
        )
    ):
        raise GremlinPNVAuthoringError(
            "operator requires at least one single-line string argument"
        )
    dependencies: list[str] = []
    if radical_candidate_id is not None:
        radical_candidate_id = _typed_dependency_ref(
            radical_candidate_id,
            "RADICAL",
            "radical_candidate_id",
        )
        dependencies.append(radical_candidate_id)
    content = {
        "name": name,
        "opcode": opcode,
        "args": list(canonical_args),
        "radical_candidate_id": radical_candidate_id,
    }
    return _candidate_envelope(
        "OPERATOR",
        content,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        evidence_refs=evidence_refs,
        dependency_ids=dependencies,
    )


def render_operator_program(
    operator_candidates: Iterable[Mapping[str, Any]],
    *,
    assertions: Sequence[str] = (),
    emits: Sequence[str] = (),
    mode: str = "READ_ONLY",
) -> str:
    rows = list(operator_candidates)
    if not rows:
        raise GremlinPNVAuthoringError("at least one OPERATOR candidate is required")
    if not isinstance(mode, str):
        raise GremlinPNVAuthoringError("mode must be a string")
    lines = ["PNV 1", "EPISTEMIC CHYBA", f"MODE {mode}"]
    names: set[str] = set()
    for candidate in rows:
        if (
            candidate.get("schema") != CANDIDATE_SCHEMA
            or candidate.get("kind") != "OPERATOR"
        ):
            raise GremlinPNVAuthoringError(
                "render_operator_program accepts only GREMLIN OPERATOR candidates"
            )
        if (
            candidate.get("promotion_state") != "CANDIDATE_ONLY"
            or candidate.get("runtime_execution_authority") is not False
        ):
            raise GremlinPNVAuthoringError(
                "operator candidate authority boundary is invalid"
            )
        content = candidate.get("content")
        if not isinstance(content, Mapping):
            raise GremlinPNVAuthoringError("operator candidate content is invalid")
        name = content.get("name")
        opcode = content.get("opcode")
        args = content.get("args")
        if not isinstance(name, str) or not isinstance(opcode, str):
            raise GremlinPNVAuthoringError(
                "operator candidate name/opcode must be strings"
            )
        if name in names:
            raise GremlinPNVAuthoringError(f"duplicate operator name: {name}")
        if not isinstance(args, list) or any(not isinstance(x, str) for x in args):
            raise GremlinPNVAuthoringError(
                "operator candidate args must be a list of strings"
            )
        names.add(name)
        lines.append(
            "OP "
            + " ".join(
                [shlex.quote(name), shlex.quote(opcode), *(shlex.quote(x) for x in args)]
            )
        )
    for name in assertions:
        if not isinstance(name, str):
            raise GremlinPNVAuthoringError("ASSERT names must be strings")
        if name not in names:
            raise GremlinPNVAuthoringError(
                f"ASSERT references unknown candidate operator: {name}"
            )
        lines.append(f"ASSERT {shlex.quote(name)}")
    for name in emits:
        if not isinstance(name, str):
            raise GremlinPNVAuthoringError("EMIT names must be strings")
        if name not in names:
            raise GremlinPNVAuthoringError(
                f"EMIT references unknown candidate operator: {name}"
            )
        lines.append(f"EMIT {shlex.quote(name)}")
    text = "\n".join(lines) + "\n"
    parse_pnv(text)
    return text


def persist_candidate(
    candidate: Mapping[str, Any],
    *,
    authoring_root: Path | str,
) -> dict[str, Any]:
    if not isinstance(candidate, Mapping):
        raise GremlinPNVAuthoringError("candidate mapping required")
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        raise GremlinPNVAuthoringError("candidate schema mismatch")
    if candidate.get("promotion_state") != "CANDIDATE_ONLY":
        raise GremlinPNVAuthoringError(
            "only CANDIDATE_ONLY objects may enter the GREMLIN authoring store"
        )
    if (
        candidate.get("runtime_execution_authority") is not False
        or candidate.get("canon_write_authority") is not False
    ):
        raise GremlinPNVAuthoringError("candidate authority boundary is invalid")
    kind_raw = candidate.get("kind")
    if not isinstance(kind_raw, str):
        raise GremlinPNVAuthoringError("candidate kind is invalid")
    kind = kind_raw.upper()
    if kind not in {"KAKU", "RADICAL", "OPERATOR"}:
        raise GremlinPNVAuthoringError("candidate kind is invalid")
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str):
        raise GremlinPNVAuthoringError("candidate_id must be a string")
    expected_id = _typed_candidate_id(
        kind,
        {key: candidate[key] for key in candidate if key != "candidate_id"},
    )
    if candidate_id != expected_id:
        raise GremlinPNVAuthoringError("candidate content hash mismatch")
    digest = _digest_from_candidate_id(candidate_id)
    root = Path(authoring_root)
    target_dir = root / kind.lower()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{digest}.json"
    raw = _canonical_bytes(candidate) + b"\n"
    created = False
    try:
        with target.open("xb") as handle:
            handle.write(raw)
        created = True
    except FileExistsError:
        try:
            existing = target.read_bytes()
        except OSError as exc:
            raise GremlinPNVAuthoringError(
                f"cannot verify existing candidate object: {target}"
            ) from exc
        if existing != raw:
            raise GremlinPNVAuthoringError("content-addressed candidate path collision")
    receipt_body = {
        "schema": RECEIPT_SCHEMA,
        "authoring_contract": AUTHORING_SCHEMA,
        "candidate_id": candidate_id,
        "kind": kind,
        "path": str(target),
        "created": created,
        "idempotent": not created,
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }
    return {**receipt_body, "receipt_sha256": _sha256(receipt_body)}


def _read_required_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GremlinPNVAuthoringError(f"invalid required live JSON: {path}") from exc
    if not isinstance(value, dict):
        raise GremlinPNVAuthoringError(f"required live JSON is not an object: {path}")
    return value


@dataclass(frozen=True)
class GremlinPNVAuthoringSession:
    surface_root: Path
    authoring_root: Path
    generation_binding: str
    identity: str
    authority: str
    tether_receipt_sha256: str

    def write_kaku(
        self,
        kaku: Kaku,
        *,
        evidence_refs: Sequence[str] = (),
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        candidate = build_kaku_candidate(
            kaku,
            generation_binding=self.generation_binding,
            identity=self.identity,
            authority=self.authority,
            evidence_refs=evidence_refs,
        )
        return candidate, persist_candidate(candidate, authoring_root=self.authoring_root)

    def write_radical(
        self,
        radical: RadicalGraph,
        *,
        evidence_refs: Sequence[str] = (),
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        refs: dict[str, str] = {}
        for node_id in sorted(radical.nodes):
            candidate, _ = self.write_kaku(
                radical.nodes[node_id],
                evidence_refs=evidence_refs,
            )
            refs[node_id] = str(candidate["candidate_id"])
        candidate = build_radical_candidate(
            radical,
            kaku_candidate_ids=refs,
            generation_binding=self.generation_binding,
            identity=self.identity,
            authority=self.authority,
            evidence_refs=evidence_refs,
        )
        return candidate, persist_candidate(candidate, authoring_root=self.authoring_root)

    def write_operator(
        self,
        name: str,
        opcode: str,
        args: Sequence[str],
        *,
        radical_candidate_id: str | None = None,
        evidence_refs: Sequence[str] = (),
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        candidate = build_operator_candidate(
            name,
            opcode,
            args,
            generation_binding=self.generation_binding,
            identity=self.identity,
            authority=self.authority,
            radical_candidate_id=radical_candidate_id,
            evidence_refs=evidence_refs,
        )
        return candidate, persist_candidate(candidate, authoring_root=self.authoring_root)


def open_gremlin_pnv_authoring_live(
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
) -> GremlinPNVAuthoringSession:
    root = Path(surface_root)
    if root != DEFAULT_SURFACE_ROOT:
        raise GremlinPNVAuthoringError(
            "live GREMLIN authoring must bind the canonical /dev/shm/ciel_noema surface"
        )
    live = load_live_surface(
        root,
        socket_path=socket_path,
        require_socket=True,
        max_heartbeat_age_s=max_heartbeat_age_s,
    )
    current_memory = _read_required_json(root / "current_memory.json")
    witness = _read_required_json(
        root / "gremlin/state/triple_pulse_conformance_witness.json"
    )
    generation_binding = _nonempty_text(
        witness.get("generation_binding"),
        "generation_binding",
    )
    identity = _nonempty_text(current_memory.get("identity"), "identity")
    authority = _nonempty_text(current_memory.get("authority"), "authority")
    authoring_root = root / DEFAULT_AUTHORING_RELATIVE_ROOT
    authoring_root.mkdir(parents=True, exist_ok=True)
    return GremlinPNVAuthoringSession(
        surface_root=root,
        authoring_root=authoring_root,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        tether_receipt_sha256=live.tether_receipt_sha256,
    )
