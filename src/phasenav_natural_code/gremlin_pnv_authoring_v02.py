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
from .model import Kaku, RadicalGraph
from .native_pnv_exec_v01 import SUPPORTED_OPCODES, parse_pnv

AUTHORING_SCHEMA = "PNCS_GREMLIN_PNV_AUTHORING_V0_2"
CANDIDATE_SCHEMA = "PNCS_GREMLIN_PNV_CANDIDATE_V0_2"
RECEIPT_SCHEMA = "PNCS_GREMLIN_PNV_AUTHORING_RECEIPT_V0_2"
DEFAULT_AUTHORING_RELATIVE_ROOT = Path("gremlin/candidates/pncs")
_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class GremlinPNVAuthoringError(RuntimeError):
    pass


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GremlinPNVAuthoringError("non-finite float cannot enter a canonical GREMLIN candidate")
        return value
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, Mapping):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    raise GremlinPNVAuthoringError(f"unsupported canonical value: {type(value).__name__}")


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
    digest = candidate_id.rsplit(":", 1)[-1]
    if not _DIGEST_RE.fullmatch(digest):
        raise GremlinPNVAuthoringError("candidate_id does not terminate in canonical SHA-256")
    return digest


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
    kind = str(kind).upper()
    if kind not in {"KAKU", "RADICAL", "OPERATOR"}:
        raise GremlinPNVAuthoringError(f"unsupported GREMLIN authoring kind: {kind}")
    if not generation_binding or not identity or not authority:
        raise GremlinPNVAuthoringError("generation_binding, identity and authority are required")
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
        "evidence_refs": sorted(set(str(x) for x in evidence_refs if str(x))),
        "dependency_ids": sorted(set(str(x) for x in dependency_ids if str(x))),
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
    node_ids = sorted(radical.nodes)
    if set(node_ids) != set(kaku_candidate_ids):
        raise GremlinPNVAuthoringError("RADICAL must bind exactly one candidate KAKU for every graph node")
    refs = {node_id: str(kaku_candidate_ids[node_id]) for node_id in node_ids}
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
            for edge in sorted(radical.edges, key=lambda e: (e.relation_id, e.source_id, e.target_id, e.relation_type))
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
        raise GremlinPNVAuthoringError("operator name must be a non-empty PNV identifier")
    opcode = str(opcode).upper()
    if opcode not in SUPPORTED_OPCODES:
        raise GremlinPNVAuthoringError(f"unsupported native PNV opcode: {opcode}")
    canonical_args = tuple(str(x) for x in args)
    if not canonical_args or any(not x or "\n" in x or "\r" in x for x in canonical_args):
        raise GremlinPNVAuthoringError("operator requires at least one single-line argument")
    dependencies: list[str] = []
    if radical_candidate_id is not None:
        if not str(radical_candidate_id).startswith("pncs:gremlin-radical:sha256:"):
            raise GremlinPNVAuthoringError("radical_candidate_id must reference a GREMLIN RADICAL candidate")
        _digest_from_candidate_id(str(radical_candidate_id))
        dependencies.append(str(radical_candidate_id))
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
    lines = ["PNV 1", "EPISTEMIC CHYBA", f"MODE {mode}"]
    names: set[str] = set()
    for candidate in rows:
        if candidate.get("schema") != CANDIDATE_SCHEMA or candidate.get("kind") != "OPERATOR":
            raise GremlinPNVAuthoringError("render_operator_program accepts only GREMLIN OPERATOR candidates")
        if candidate.get("promotion_state") != "CANDIDATE_ONLY" or candidate.get("runtime_execution_authority") is not False:
            raise GremlinPNVAuthoringError("operator candidate authority boundary is invalid")
        content = candidate.get("content")
        if not isinstance(content, Mapping):
            raise GremlinPNVAuthoringError("operator candidate content is invalid")
        name = str(content.get("name", ""))
        opcode = str(content.get("opcode", ""))
        args = content.get("args")
        if name in names:
            raise GremlinPNVAuthoringError(f"duplicate operator name: {name}")
        if not isinstance(args, list):
            raise GremlinPNVAuthoringError("operator candidate args must be a list")
        names.add(name)
        lines.append("OP " + " ".join([shlex.quote(name), shlex.quote(opcode), *(shlex.quote(str(x)) for x in args)]))
    for name in assertions:
        if name not in names:
            raise GremlinPNVAuthoringError(f"ASSERT references unknown candidate operator: {name}")
        lines.append(f"ASSERT {shlex.quote(name)}")
    for name in emits:
        if name not in names:
            raise GremlinPNVAuthoringError(f"EMIT references unknown candidate operator: {name}")
        lines.append(f"EMIT {shlex.quote(name)}")
    text = "\n".join(lines) + "\n"
    parse_pnv(text)
    return text


def persist_candidate(
    candidate: Mapping[str, Any],
    *,
    authoring_root: Path | str,
) -> dict[str, Any]:
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        raise GremlinPNVAuthoringError("candidate schema mismatch")
    if candidate.get("promotion_state") != "CANDIDATE_ONLY":
        raise GremlinPNVAuthoringError("only CANDIDATE_ONLY objects may enter the GREMLIN authoring store")
    if candidate.get("runtime_execution_authority") is not False or candidate.get("canon_write_authority") is not False:
        raise GremlinPNVAuthoringError("candidate authority boundary is invalid")
    kind = str(candidate.get("kind", "")).upper()
    if kind not in {"KAKU", "RADICAL", "OPERATOR"}:
        raise GremlinPNVAuthoringError("candidate kind is invalid")
    candidate_id = str(candidate.get("candidate_id", ""))
    expected_id = _typed_candidate_id(kind, {k: candidate[k] for k in candidate if k != "candidate_id"})
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
            raise GremlinPNVAuthoringError(f"cannot verify existing candidate object: {target}") from exc
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

    def write_kaku(self, kaku: Kaku, *, evidence_refs: Sequence[str] = ()) -> tuple[dict[str, Any], dict[str, Any]]:
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
            candidate, _ = self.write_kaku(radical.nodes[node_id], evidence_refs=evidence_refs)
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
        raise GremlinPNVAuthoringError("live GREMLIN authoring must bind the canonical /dev/shm/ciel_noema surface")
    live = load_live_surface(root, socket_path=socket_path, require_socket=True, max_heartbeat_age_s=max_heartbeat_age_s)
    current_memory = _read_required_json(root / "current_memory.json")
    witness = _read_required_json(root / "gremlin/state/triple_pulse_conformance_witness.json")
    generation_binding = str(witness.get("generation_binding", ""))
    identity = str(current_memory.get("identity", ""))
    authority = str(current_memory.get("authority", ""))
    if not generation_binding or not identity or not authority:
        raise GremlinPNVAuthoringError("live GREMLIN authoring identity/domain/authority binding is incomplete")
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
