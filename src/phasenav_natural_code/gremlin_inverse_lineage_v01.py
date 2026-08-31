from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .gremlin_pnv_authoring_v02 import CANDIDATE_SCHEMA
from .gremlin_relational_compiler_v01 import RelationalCompilation
from .native_pnv_exec_v01 import (
    NativePNVExecutionResult,
    RECEIPT_SCHEMA as NATIVE_RECEIPT_SCHEMA,
)

LINEAGE_SCHEMA = "PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_V0_1"
LINEAGE_RECEIPT_SCHEMA = "PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_RECEIPT_V0_1"
_CONTENT_ID_RE = re.compile(
    r"pncs:(?:def|class|file|cluster|subsystem|daemon|low-orchestrator|high-orchestrator|system):sha256:[0-9a-f]{64}"
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class GremlinInverseLineageError(RuntimeError):
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


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise GremlinInverseLineageError(
            f"{field} must be lowercase 64-hex SHA-256"
        )
    return value


def _exact_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise GremlinInverseLineageError(f"{field} must be a non-empty string")
    return value


def _exact_text_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise GremlinInverseLineageError(f"{field} must be a list of strings")
    out: list[str] = []
    for index, item in enumerate(value):
        out.append(_exact_text(item, f"{field}[{index}]"))
    return out


def _validate_candidate(candidate: Mapping[str, Any], kind: str) -> str:
    if not isinstance(candidate, Mapping):
        raise GremlinInverseLineageError(f"{kind} candidate must be a mapping")
    if candidate.get("schema") != CANDIDATE_SCHEMA or candidate.get("kind") != kind:
        raise GremlinInverseLineageError(f"{kind} candidate schema/kind mismatch")
    if (
        candidate.get("epistemic") != "CHYBA"
        or candidate.get("promotion_state") != "CANDIDATE_ONLY"
    ):
        raise GremlinInverseLineageError(
            f"{kind} candidate epistemic/promotion boundary mismatch"
        )
    if (
        candidate.get("runtime_execution_authority") is not False
        or candidate.get("canon_write_authority") is not False
    ):
        raise GremlinInverseLineageError(
            f"{kind} candidate authority boundary mismatch"
        )
    candidate_id = candidate.get("candidate_id")
    prefix = f"pncs:gremlin-{kind.lower()}:sha256:"
    if not isinstance(candidate_id, str) or not candidate_id.startswith(prefix):
        raise GremlinInverseLineageError(f"{kind} candidate id prefix mismatch")
    expected = prefix + _sha256(
        {k: candidate[k] for k in candidate if k != "candidate_id"}
    )
    if candidate_id != expected:
        raise GremlinInverseLineageError(f"{kind} candidate content hash mismatch")
    _exact_text_list(candidate.get("evidence_refs"), f"{kind} evidence_refs")
    _exact_text_list(candidate.get("dependency_ids"), f"{kind} dependency_ids")
    return candidate_id


def _validate_compilation_receipt(compilation: RelationalCompilation) -> str:
    receipt = compilation.receipt
    if not isinstance(receipt, Mapping):
        raise GremlinInverseLineageError("relational compilation receipt required")
    receipt_sha = _digest(receipt.get("receipt_sha256"), "compilation receipt")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    if _sha256(body) != receipt_sha:
        raise GremlinInverseLineageError(
            "relational compilation receipt digest mismatch"
        )
    if (
        receipt.get("epistemic") != "CHYBA"
        or receipt.get("promotion_state") != "CANDIDATE_ONLY"
    ):
        raise GremlinInverseLineageError(
            "relational compilation epistemic boundary mismatch"
        )
    if (
        receipt.get("runtime_execution_authority") is not False
        or receipt.get("canon_write_authority") is not False
    ):
        raise GremlinInverseLineageError(
            "relational compilation authority boundary mismatch"
        )
    return receipt_sha


def _validate_execution(
    compilation: RelationalCompilation,
    result: NativePNVExecutionResult,
) -> tuple[str, dict[str, Any], bool]:
    if not isinstance(result, NativePNVExecutionResult):
        raise GremlinInverseLineageError("NativePNVExecutionResult required")
    receipt = result.receipt
    if not isinstance(receipt, Mapping) or receipt.get("schema") != NATIVE_RECEIPT_SCHEMA:
        raise GremlinInverseLineageError(
            "native PNV execution receipt schema mismatch"
        )
    receipt_sha = _digest(receipt.get("receipt_sha256"), "native execution receipt")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    if _sha256(body) != receipt_sha:
        raise GremlinInverseLineageError(
            "native PNV execution receipt digest mismatch"
        )
    if receipt.get("program_source_sha256") != compilation.receipt.get(
        "pnv_source_sha256"
    ):
        raise GremlinInverseLineageError(
            "execution/compilation PNV source hash mismatch"
        )
    if receipt.get("program_graph_sha256") != compilation.receipt.get(
        "pnv_graph_sha256"
    ):
        raise GremlinInverseLineageError(
            "execution/compilation PNV graph hash mismatch"
        )
    if (
        result.program.source_sha256 != receipt.get("program_source_sha256")
        or result.program.graph_sha256 != receipt.get("program_graph_sha256")
    ):
        raise GremlinInverseLineageError(
            "execution program object/receipt hash mismatch"
        )

    effect = receipt.get("effect_boundary")
    if not isinstance(effect, Mapping):
        raise GremlinInverseLineageError(
            "native PNV execution effect boundary required"
        )
    if effect.get("interpreter_external_effects") is not False:
        raise GremlinInverseLineageError(
            "candidate inverse lineage requires a pure native interpreter boundary"
        )

    external_effects = effect.get("external_effects")
    effect_status = effect.get("external_effects_status")
    callback_effects_verified = effect.get("callback_effects_verified")
    callbacks_invoked = effect.get("callbacks_invoked")
    if not isinstance(callbacks_invoked, list) or any(
        not isinstance(item, str) or not item for item in callbacks_invoked
    ):
        raise GremlinInverseLineageError(
            "native PNV callback effect-boundary provenance is malformed"
        )

    if external_effects is False:
        if effect_status != "VERIFIED_NONE_WITHIN_INTERPRETER_BOUNDARY":
            raise GremlinInverseLineageError(
                "pure native PNV effect-boundary status mismatch"
            )
        if callback_effects_verified is not True or callbacks_invoked:
            raise GremlinInverseLineageError(
                "pure native PNV callback boundary mismatch"
            )
    elif external_effects is None:
        if effect_status != "UNVERIFIED_CALLBACK_BOUNDARY":
            raise GremlinInverseLineageError(
                "unverified callback boundary status mismatch"
            )
        if callback_effects_verified is not False or not callbacks_invoked:
            raise GremlinInverseLineageError(
                "unverified callback boundary provenance mismatch"
            )
    else:
        raise GremlinInverseLineageError(
            "candidate inverse lineage rejects reported external effects"
        )

    callback_determinism_verified = receipt.get("callback_determinism_verified")
    if callback_determinism_verified is not (external_effects is False):
        raise GremlinInverseLineageError(
            "native PNV callback determinism status mismatch"
        )

    effect_summary = {
        "interpreter_external_effects": False,
        "external_effects": external_effects,
        "external_effects_status": effect_status,
        "callback_effects_verified": callback_effects_verified,
        "callbacks_invoked": list(callbacks_invoked),
    }
    return receipt_sha, effect_summary, bool(callback_determinism_verified)


def _operator_index(
    compilation: RelationalCompilation,
) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    radical_id = _validate_candidate(compilation.radical_candidate, "RADICAL")
    for candidate in compilation.operator_candidates:
        cid = _validate_candidate(candidate, "OPERATOR")
        content = candidate.get("content")
        if not isinstance(content, Mapping):
            raise GremlinInverseLineageError("OPERATOR candidate content required")
        name = content.get("name")
        if not isinstance(name, str) or not name:
            raise GremlinInverseLineageError("OPERATOR candidate name required")
        if name in index:
            raise GremlinInverseLineageError(
                f"duplicate candidate operator name: {name}"
            )
        if (
            content.get("radical_candidate_id") != radical_id
            or candidate.get("dependency_ids") != [radical_id]
        ):
            raise GremlinInverseLineageError(
                "OPERATOR candidate radical dependency mismatch"
            )
        index[name] = candidate
        if cid not in compilation.receipt.get("operator_candidate_ids", []):
            raise GremlinInverseLineageError(
                "OPERATOR candidate missing from compilation receipt"
            )
    if set(index) != {op.name for op in result_program_ops(compilation)}:
        raise GremlinInverseLineageError(
            "candidate operator schedule/program schedule mismatch"
        )
    return index


def result_program_ops(compilation: RelationalCompilation):
    from .native_pnv_exec_v01 import parse_pnv

    return parse_pnv(compilation.pnv_text).ops


def _validate_program_operator_bytes(
    compilation: RelationalCompilation,
    index: Mapping[str, Mapping[str, Any]],
) -> None:
    for op in result_program_ops(compilation):
        candidate = index[op.name]
        content = candidate["content"]
        if (
            content.get("opcode") != op.opcode
            or tuple(content.get("args", ())) != op.args
        ):
            raise GremlinInverseLineageError(
                f"candidate/program operator mismatch: {op.name}"
            )


def _reachable_operator_names(
    result: NativePNVExecutionResult,
    index: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    roots = tuple(result.program.emits)
    if not roots:
        raise GremlinInverseLineageError(
            "candidate inverse lineage requires at least one EMIT root"
        )
    missing = [name for name in roots if name not in index]
    if missing:
        raise GremlinInverseLineageError(
            f"EMIT root missing candidate operator: {missing}"
        )

    seen: set[str] = set()
    order: list[str] = []

    def visit(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        candidate = index[name]
        args = tuple(candidate["content"].get("args", ()))
        for token in args:
            if token in index:
                visit(token)
        order.append(name)

    for root in roots:
        visit(root)
    return tuple(order)


def _trace_index(
    result: NativePNVExecutionResult,
) -> dict[str, Mapping[str, Any]]:
    trace = result.receipt.get("trace")
    if not isinstance(trace, list):
        raise GremlinInverseLineageError("native PNV trace required")
    out: dict[str, Mapping[str, Any]] = {}
    for row in trace:
        if not isinstance(row, Mapping):
            raise GremlinInverseLineageError(
                "native PNV trace row must be mapping"
            )
        name = row.get("op")
        if not isinstance(name, str) or name in out:
            raise GremlinInverseLineageError(
                "native PNV trace operator identity invalid"
            )
        _digest(row.get("result_sha256"), "trace result digest")
        out[name] = row
    if set(out) != {op.name for op in result.program.ops}:
        raise GremlinInverseLineageError(
            "native PNV trace/program operator set mismatch"
        )
    return out


def _explicit_content_ids(
    candidate: Mapping[str, Any],
) -> tuple[str, ...]:
    values: list[str] = []
    content = candidate.get("content")
    if isinstance(content, Mapping):
        role = content.get("role")
        if isinstance(role, str):
            values.append(role)
    evidence = _exact_text_list(candidate.get("evidence_refs"), "candidate evidence_refs")
    values.extend(evidence)
    found: set[str] = set()
    for value in values:
        found.update(_CONTENT_ID_RE.findall(value))
    return tuple(sorted(found))


def _validate_radical_and_kaku(
    compilation: RelationalCompilation,
) -> tuple[str, dict[str, Mapping[str, Any]], dict[str, str]]:
    radical = compilation.radical_candidate
    radical_id = _validate_candidate(radical, "RADICAL")
    content = radical.get("content")
    if not isinstance(content, Mapping):
        raise GremlinInverseLineageError("RADICAL candidate content required")
    refs = content.get("kaku_candidate_ids")
    if not isinstance(refs, Mapping) or not refs:
        raise GremlinInverseLineageError(
            "RADICAL KAKU candidate refs required"
        )
    exact_refs: dict[str, str] = {}
    for node_id, candidate_id in refs.items():
        node_text = _exact_text(node_id, "RADICAL KAKU node id")
        candidate_text = _exact_text(candidate_id, f"RADICAL KAKU ref {node_text}")
        if node_text in exact_refs:
            raise GremlinInverseLineageError("duplicate RADICAL KAKU node id")
        exact_refs[node_text] = candidate_text

    kaku_index: dict[str, Mapping[str, Any]] = {}
    kaku_ids: dict[str, str] = {}
    for node_id, candidate in compilation.kaku_candidates.items():
        node_text = _exact_text(node_id, "compilation KAKU node id")
        candidate_id = _validate_candidate(candidate, "KAKU")
        candidate_content = candidate.get("content")
        if (
            not isinstance(candidate_content, Mapping)
            or candidate_content.get("kaku_id") != node_text
        ):
            raise GremlinInverseLineageError(
                "KAKU candidate node id mismatch"
            )
        if node_text in kaku_index:
            raise GremlinInverseLineageError("duplicate compilation KAKU node id")
        kaku_index[node_text] = candidate
        kaku_ids[node_text] = candidate_id
    if set(exact_refs) != set(kaku_index):
        raise GremlinInverseLineageError(
            "RADICAL node/KAKU candidate closure mismatch"
        )
    for node_id, cid in exact_refs.items():
        if kaku_ids[node_id] != cid:
            raise GremlinInverseLineageError(
                "RADICAL node points to wrong KAKU candidate"
            )
    expected_dependencies = sorted(kaku_ids.values())
    if radical.get("dependency_ids") != expected_dependencies:
        raise GremlinInverseLineageError(
            "RADICAL dependency closure mismatch"
        )
    if compilation.receipt.get("radical_candidate_id") != radical_id:
        raise GremlinInverseLineageError(
            "RADICAL candidate/compilation receipt mismatch"
        )
    receipt_nodes = compilation.receipt.get("node_candidate_ids")
    expected_nodes = {k: kaku_ids[k] for k in sorted(kaku_ids)}
    if not isinstance(receipt_nodes, Mapping) or dict(receipt_nodes) != expected_nodes:
        raise GremlinInverseLineageError(
            "KAKU candidate/compilation receipt mismatch"
        )
    return radical_id, kaku_index, dict(exact_refs)


@dataclass(frozen=True)
class GremlinCandidateInverseLineage:
    compilation_receipt_sha256: str
    execution_receipt_sha256: str
    emit_roots: tuple[str, ...]
    operator_rows: tuple[Mapping[str, Any], ...]
    radical_row: Mapping[str, Any]
    kaku_rows: tuple[Mapping[str, Any], ...]
    execution_effect_boundary: Mapping[str, Any]
    callback_determinism_verified: bool

    @property
    def inverse_chain(self) -> list[Mapping[str, Any]]:
        rows: list[Mapping[str, Any]] = [
            {
                "level": "RESULT",
                "execution_receipt_sha256": self.execution_receipt_sha256,
                "emit_roots": list(self.emit_roots),
            }
        ]
        rows.extend(self.operator_rows)
        rows.append(self.radical_row)
        rows.extend(self.kaku_rows)
        return rows

    @property
    def payload(self) -> dict[str, Any]:
        explicit_content_ids = sorted(
            {
                cid
                for row in self.kaku_rows
                for cid in row.get("explicit_content_ids", [])
            }
        )
        return {
            "schema": LINEAGE_SCHEMA,
            "compilation_receipt_sha256": self.compilation_receipt_sha256,
            "execution_receipt_sha256": self.execution_receipt_sha256,
            "emit_roots": list(self.emit_roots),
            "operator_rows": [dict(row) for row in self.operator_rows],
            "radical_row": dict(self.radical_row),
            "kaku_rows": [dict(row) for row in self.kaku_rows],
            "explicit_content_ids": explicit_content_ids,
            "v22_join_state": (
                "CONTENT_ID_AVAILABLE" if explicit_content_ids else "CONTENT_ID_OPEN"
            ),
            "execution_effect_boundary": dict(self.execution_effect_boundary),
            "epistemic": "CHYBA",
            "promotion_state": "CANDIDATE_ONLY",
            "runtime_execution_authority": False,
            "canon_write_authority": False,
            "numeric_realization_is_semantic_authority": False,
            "deterministic_fields_only": self.callback_determinism_verified,
            "deterministic_serialization": True,
            "callback_determinism_verified": self.callback_determinism_verified,
        }

    @property
    def lineage_id(self) -> str:
        return f"pncs:gremlin-candidate-lineage:sha256:{_sha256(self.payload)}"

    @property
    def receipt(self) -> dict[str, Any]:
        body = {**self.payload, "lineage_id": self.lineage_id}
        return {
            **body,
            "receipt_schema": LINEAGE_RECEIPT_SCHEMA,
            "receipt_sha256": _sha256(body),
        }


def resolve_gremlin_candidate_inverse_lineage(
    compilation: RelationalCompilation,
    result: NativePNVExecutionResult,
) -> GremlinCandidateInverseLineage:
    if not isinstance(compilation, RelationalCompilation):
        raise GremlinInverseLineageError("RelationalCompilation required")
    compilation_sha = _validate_compilation_receipt(compilation)
    execution_sha, effect_boundary, callback_determinism_verified = (
        _validate_execution(compilation, result)
    )
    operator_index = _operator_index(compilation)
    _validate_program_operator_bytes(compilation, operator_index)
    trace = _trace_index(result)
    reachable = _reachable_operator_names(result, operator_index)
    radical_id, kaku_index, radical_refs = _validate_radical_and_kaku(compilation)

    operator_rows: list[Mapping[str, Any]] = []
    for name in reversed(reachable):
        candidate = operator_index[name]
        content = candidate["content"]
        deps = [
            token
            for token in content.get("args", [])
            if token in operator_index
        ]
        operator_rows.append(
            {
                "level": "OPERATOR",
                "name": name,
                "candidate_id": candidate["candidate_id"],
                "opcode": content["opcode"],
                "depends_on_operator_names": deps,
                "result_sha256": trace[name]["result_sha256"],
                "radical_candidate_id": radical_id,
                "evidence_refs": list(candidate.get("evidence_refs", [])),
            }
        )

    radical_content = compilation.radical_candidate["content"]
    radical_row = {
        "level": "RADICAL",
        "candidate_id": radical_id,
        "radical_id": radical_content["radical_id"],
        "basis_id": radical_content["basis_id"],
        "kaku_candidate_ids": dict(radical_refs),
        "relations": list(radical_content.get("relations", [])),
        "evidence_refs": list(
            compilation.radical_candidate.get("evidence_refs", [])
        ),
    }

    kaku_rows: list[Mapping[str, Any]] = []
    for node_id in sorted(kaku_index):
        candidate = kaku_index[node_id]
        content = candidate["content"]
        kaku_rows.append(
            {
                "level": "KAKU",
                "node_id": node_id,
                "candidate_id": candidate["candidate_id"],
                "basis_id": content["basis_id"],
                "role": content["role"],
                "explicit_content_ids": list(
                    _explicit_content_ids(candidate)
                ),
                "evidence_refs": list(candidate.get("evidence_refs", [])),
            }
        )

    emitted_receipt = result.receipt.get("emitted")
    if not isinstance(emitted_receipt, list):
        raise GremlinInverseLineageError(
            "native PNV emitted receipt required"
        )
    expected_emitted = [
        [name, _sha256(result.emitted[name])]
        for name in result.program.emits
    ]
    if emitted_receipt != expected_emitted:
        raise GremlinInverseLineageError(
            "native PNV emitted value/receipt mismatch"
        )

    return GremlinCandidateInverseLineage(
        compilation_receipt_sha256=compilation_sha,
        execution_receipt_sha256=execution_sha,
        emit_roots=tuple(result.program.emits),
        operator_rows=tuple(operator_rows),
        radical_row=radical_row,
        kaku_rows=tuple(kaku_rows),
        execution_effect_boundary=effect_boundary,
        callback_determinism_verified=callback_determinism_verified,
    )


def persist_gremlin_candidate_inverse_lineage(
    lineage: GremlinCandidateInverseLineage,
    *,
    authoring_root: Path | str,
) -> str:
    if not isinstance(lineage, GremlinCandidateInverseLineage):
        raise GremlinInverseLineageError(
            "GremlinCandidateInverseLineage required"
        )
    root = Path(authoring_root) / "lineage"
    root.mkdir(parents=True, exist_ok=True)
    digest = lineage.lineage_id.rsplit(":", 1)[-1]
    target = root / f"{digest}.json"
    raw = _canonical_bytes(lineage.receipt) + b"\n"
    try:
        with target.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        if target.read_bytes() != raw:
            raise GremlinInverseLineageError(
                "content-addressed inverse-lineage collision"
            )
    return str(target)
