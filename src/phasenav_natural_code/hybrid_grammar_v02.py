"""PNCS Hybrid Grammar v0.2.

CIELingo-inspired semantic grammar for hybrid programs.

The grammar is deliberately bounded and fail-closed. It compiles explicit
semantic statements into a deterministic PNCS hybrid IR. Quantum blocks are
delegated to PNCS Quantum Gate Language v0.1 so there is one quantum IR path,
not a competing second gate representation.

External effects and persistence are represented as authorization boundaries;
this module never actuates them.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import shlex
from typing import Mapping

from .quantum_gate_language_v01 import (
    CompiledQuantumGateProgram,
    QuantumGateLanguageError,
    compile_quantum_gate_program,
)

GRAMMAR_SCHEMA = "PNCS_HYBRID_GRAMMAR_V0_2"
IR_SCHEMA = "PNCS_HYBRID_IR_V0_2"
NODE_SCHEMA = "PNCS_HYBRID_NODE_V0_2"
SYMBOL_SCHEMA = "PNCS_HYBRID_SYMBOL_V0_2"
QUANTUM_BINDING_SCHEMA = "PNCS_HYBRID_QUANTUM_BINDING_V0_2"

_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
_SLOT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/-]*$")

_ATOMIC_TYPES = frozenset(
    {
        "QUERY",
        "TEXT",
        "PAGE",
        "DOCUMENT",
        "GRAPH",
        "STATE",
        "QUANTUM_STATE",
        "OBSERVABLE",
        "REAL",
        "INTEGER",
        "BOOLEAN",
        "JSON",
        "BYTES",
        "URL",
        "ANY",
    }
)
_GENERIC_TYPES = frozenset({"SET", "LIST", "STREAM"})
_COMPUTE_MODES = frozenset(
    {"AUTO", "CLASSICAL_PREFERRED", "QUANTUM_PREFERRED", "QUANTUM_REQUIRED"}
)
_QUANTUM_MODES = frozenset({"RESULT_DIRECTED", "FULL_STATE"})


class HybridGrammarError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise HybridGrammarError(f"{field} must be a PNCS identifier")
    return value


def _slot(value: str) -> str:
    if not isinstance(value, str) or not _SLOT_RE.fullmatch(value):
        raise HybridGrammarError("persistence slot must be a bounded identifier/path")
    return value


def parse_type(token: str) -> str:
    raw = str(token).upper()
    if raw in _ATOMIC_TYPES:
        return raw
    if "<" in raw or ">" in raw:
        match = re.fullmatch(r"([A-Z][A-Z0-9_]*)<([A-Z][A-Z0-9_]*)>", raw)
        if match is None:
            raise HybridGrammarError(f"invalid type expression: {token}")
        container, inner = match.groups()
        if container not in _GENERIC_TYPES or inner not in _ATOMIC_TYPES:
            raise HybridGrammarError(f"unsupported type expression: {token}")
        return f"{container}<{inner}>"
    raise HybridGrammarError(f"unsupported PNCS hybrid type: {token}")


@dataclass(frozen=True)
class HybridSymbol:
    name: str
    type_name: str
    producer_node_id: str
    task_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _identifier(self.name, "symbol"))
        object.__setattr__(self, "type_name", parse_type(self.type_name))
        object.__setattr__(
            self, "producer_node_id", _identifier(self.producer_node_id, "producer node")
        )
        object.__setattr__(self, "task_id", _identifier(self.task_id, "task"))

    def to_dict(self) -> dict:
        return {
            "schema": SYMBOL_SCHEMA,
            "name": self.name,
            "type": self.type_name,
            "producer_node_id": self.producer_node_id,
            "task_id": self.task_id,
        }


@dataclass(frozen=True)
class HybridNode:
    node_id: str
    kind: str
    task_id: str
    inputs: tuple[str, ...] = ()
    output: str | None = None
    output_type: str | None = None
    execution_class: str = "INTERNAL"
    attributes: Mapping[str, object] | None = None
    external_effect: bool = False
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", _identifier(self.node_id, "node_id"))
        object.__setattr__(self, "kind", _identifier(self.kind, "node kind").upper())
        object.__setattr__(self, "task_id", _identifier(self.task_id, "task"))
        for item in self.inputs:
            _identifier(item, "input symbol")
        if self.output is not None:
            _identifier(self.output, "output symbol")
        if self.output_type is not None:
            object.__setattr__(self, "output_type", parse_type(self.output_type))
        if self.external_effect and self.execution_authorized:
            raise HybridGrammarError(
                "v0.2 cannot self-authorize external effects or persistence"
            )

    def to_dict(self) -> dict:
        return {
            "schema": NODE_SCHEMA,
            "node_id": self.node_id,
            "kind": self.kind,
            "task_id": self.task_id,
            "inputs": list(self.inputs),
            "output": self.output,
            "output_type": self.output_type,
            "execution_class": self.execution_class,
            "attributes": dict(self.attributes or {}),
            "external_effect": self.external_effect,
            "execution_authorized": self.execution_authorized,
        }


@dataclass(frozen=True)
class QuantumBinding:
    kernel_id: str
    task_id: str
    compiled: CompiledQuantumGateProgram

    def __post_init__(self) -> None:
        object.__setattr__(self, "kernel_id", _identifier(self.kernel_id, "quantum kernel"))
        object.__setattr__(self, "task_id", _identifier(self.task_id, "task"))

    def to_dict(self) -> dict:
        return {
            "schema": QUANTUM_BINDING_SCHEMA,
            "kernel_id": self.kernel_id,
            "task_id": self.task_id,
            "logical_qubits": self.compiled.logical_qubits,
            "mode": self.compiled.mode,
            "source_sha256": self.compiled.source_sha256,
            "qir_sha256": self.compiled.qir_sha256,
            "qir": self.compiled.qir_payload,
        }


@dataclass(frozen=True)
class CompiledHybridProgram:
    program_id: str
    tasks: tuple[str, ...]
    symbols: tuple[HybridSymbol, ...]
    nodes: tuple[HybridNode, ...]
    quantum_bindings: tuple[QuantumBinding, ...]
    return_symbols: tuple[str, ...]
    source_sha256: str
    ir_sha256: str

    @property
    def has_external_effects(self) -> bool:
        return any(node.external_effect for node in self.nodes)

    @property
    def all_external_effects_authorized(self) -> bool:
        return all(
            node.execution_authorized for node in self.nodes if node.external_effect
        )

    def to_ir(self) -> dict:
        return {
            "schema": IR_SCHEMA,
            "grammar_schema": GRAMMAR_SCHEMA,
            "program_id": self.program_id,
            "tasks": list(self.tasks),
            "symbols": [item.to_dict() for item in self.symbols],
            "nodes": [item.to_dict() for item in self.nodes],
            "quantum_bindings": [item.to_dict() for item in self.quantum_bindings],
            "return_symbols": list(self.return_symbols),
            "effect_policy": {
                "external_effects_present": self.has_external_effects,
                "external_effects_authorized": self.all_external_effects_authorized,
                "implicit_authorization": False,
                "actuation_performed": False,
            },
            "compiler_policy": {
                "free_form_natural_language": False,
                "backend_names_in_semantics": False,
                "quantum_gate_language": "PNCS_QUANTUM_GATE_PROGRAM_V0_1",
                "quantum_ir": "PHASENAV_QUANTUM_GATE_IR_V1",
                "unsupported_constructs": "FAIL_CLOSED",
            },
        }

    def to_dict(self) -> dict:
        return {
            "schema": GRAMMAR_SCHEMA,
            "program_id": self.program_id,
            "source_sha256": self.source_sha256,
            "ir_sha256": self.ir_sha256,
            "ir": self.to_ir(),
        }


class _Builder:
    def __init__(self, program_id: str) -> None:
        self.program_id = _identifier(program_id, "program")
        self.current_task = "root"
        self.tasks: list[str] = ["root"]
        self.symbols: dict[str, HybridSymbol] = {}
        self.nodes: list[HybridNode] = []
        self.node_ids: set[str] = set()
        self.quantum: dict[str, QuantumBinding] = {}
        self.pending_node_refs: list[tuple[int, str, str]] = []
        self.return_symbols: tuple[str, ...] | None = None

    def set_task(self, task_id: str) -> None:
        task_id = _identifier(task_id, "task")
        if task_id not in self.tasks:
            self.tasks.append(task_id)
        self.current_task = task_id

    def require_symbol(self, name: str) -> HybridSymbol:
        try:
            return self.symbols[name]
        except KeyError as exc:
            raise HybridGrammarError(f"unknown symbol: {name}") from exc

    def add_node(self, node: HybridNode) -> None:
        if node.node_id in self.node_ids:
            raise HybridGrammarError(f"duplicate node id: {node.node_id}")
        self.node_ids.add(node.node_id)
        self.nodes.append(node)
        if node.output is not None:
            if node.output in self.symbols:
                raise HybridGrammarError(f"duplicate symbol: {node.output}")
            self.symbols[node.output] = HybridSymbol(
                node.output,
                node.output_type or "ANY",
                node.node_id,
                node.task_id,
            )

    def add_quantum(self, binding: QuantumBinding) -> None:
        if binding.kernel_id in self.quantum:
            raise HybridGrammarError(f"duplicate quantum kernel: {binding.kernel_id}")
        self.quantum[binding.kernel_id] = binding

    def validate_refs(self) -> None:
        for line_no, field, target in self.pending_node_refs:
            if target not in self.node_ids:
                raise HybridGrammarError(
                    f"line {line_no}: {field} references unknown node {target}"
                )


def _tokenize(line: str, line_no: int) -> list[str]:
    try:
        return shlex.split(line)
    except ValueError as exc:
        raise HybridGrammarError(f"line {line_no}: {exc}") from exc


def _expect_colon(parts: list[str], index: int, line_no: int) -> None:
    if len(parts) <= index or parts[index] != ":":
        raise HybridGrammarError(f"line {line_no}: expected ':'")


def _parse_input(parts: list[str], b: _Builder, line_no: int) -> None:
    if len(parts) not in {4, 6}:
        raise HybridGrammarError(
            f"line {line_no}: INPUT syntax is INPUT name : TYPE [FROM source]"
        )
    _expect_colon(parts, 2, line_no)
    name = _identifier(parts[1], "input")
    typ = parse_type(parts[3])
    attrs: dict[str, object] = {}
    if len(parts) == 6:
        if parts[4].upper() != "FROM":
            raise HybridGrammarError(f"line {line_no}: expected FROM")
        attrs["source_ref"] = _identifier(parts[5], "source")
    b.add_node(
        HybridNode(
            node_id=f"input.{name}",
            kind="INPUT",
            task_id=b.current_task,
            output=name,
            output_type=typ,
            execution_class="INPUT_BOUNDARY",
            attributes=attrs,
        )
    )


def _parse_find(parts: list[str], b: _Builder, line_no: int) -> None:
    # FIND out : TYPE FROM source RELATED_TO query
    if len(parts) != 8:
        raise HybridGrammarError(
            f"line {line_no}: FIND syntax is FIND out : TYPE FROM source RELATED_TO symbol"
        )
    _expect_colon(parts, 2, line_no)
    if parts[4].upper() != "FROM" or parts[6].upper() != "RELATED_TO":
        raise HybridGrammarError(f"line {line_no}: malformed FIND")
    out = _identifier(parts[1], "FIND output")
    typ = parse_type(parts[3])
    source_ref = _identifier(parts[5], "FIND source")
    relation_symbol = _identifier(parts[7], "RELATED_TO symbol")
    b.require_symbol(relation_symbol)
    b.add_node(
        HybridNode(
            node_id=f"find.{out}",
            kind="FIND",
            task_id=b.current_task,
            inputs=(relation_symbol,),
            output=out,
            output_type=typ,
            execution_class="READ_ONLY_SOURCE_QUERY",
            attributes={
                "source_ref": source_ref,
                "relation": "RELATED_TO",
                "read_only": True,
            },
        )
    )


def _parse_filter(parts: list[str], b: _Builder, line_no: int) -> None:
    # FILTER out : TYPE FROM source BY predicate
    if len(parts) != 8:
        raise HybridGrammarError(
            f"line {line_no}: FILTER syntax is FILTER out : TYPE FROM symbol BY predicate"
        )
    _expect_colon(parts, 2, line_no)
    if parts[4].upper() != "FROM" or parts[6].upper() != "BY":
        raise HybridGrammarError(f"line {line_no}: malformed FILTER")
    out = _identifier(parts[1], "FILTER output")
    typ = parse_type(parts[3])
    source = _identifier(parts[5], "FILTER source")
    predicate = _identifier(parts[7], "FILTER predicate")
    b.require_symbol(source)
    b.add_node(
        HybridNode(
            node_id=f"filter.{out}",
            kind="FILTER",
            task_id=b.current_task,
            inputs=(source,),
            output=out,
            output_type=typ,
            execution_class="CLASSICAL_OR_VECTOR",
            attributes={"predicate": predicate},
        )
    )


def _parse_compute(parts: list[str], b: _Builder, line_no: int) -> None:
    # COMPUTE out : TYPE USING operator [INPUT a b ...] [MODE X]
    if len(parts) < 6:
        raise HybridGrammarError(f"line {line_no}: incomplete COMPUTE")
    _expect_colon(parts, 2, line_no)
    if parts[4].upper() != "USING":
        raise HybridGrammarError(f"line {line_no}: COMPUTE requires USING")
    out = _identifier(parts[1], "COMPUTE output")
    typ = parse_type(parts[3])
    operator = _identifier(parts[5], "COMPUTE operator")
    inputs: list[str] = []
    mode = "AUTO"
    i = 6
    if i < len(parts) and parts[i].upper() == "INPUT":
        i += 1
        start = i
        while i < len(parts) and parts[i].upper() != "MODE":
            name = _identifier(parts[i], "COMPUTE input")
            b.require_symbol(name)
            inputs.append(name)
            i += 1
        if i == start:
            raise HybridGrammarError(f"line {line_no}: INPUT requires symbol(s)")
    if i < len(parts):
        if parts[i].upper() != "MODE" or i + 2 != len(parts):
            raise HybridGrammarError(f"line {line_no}: malformed COMPUTE MODE")
        mode = parts[i + 1].upper()
        if mode not in _COMPUTE_MODES:
            raise HybridGrammarError(f"line {line_no}: unsupported compute mode {mode}")
        i += 2
    if i != len(parts):
        raise HybridGrammarError(f"line {line_no}: trailing COMPUTE tokens")
    quantum_kernel = operator if operator in b.quantum else None
    if mode == "QUANTUM_REQUIRED" and quantum_kernel is None:
        raise HybridGrammarError(
            f"line {line_no}: QUANTUM_REQUIRED operator must be a declared QUANTUM kernel"
        )
    if quantum_kernel is not None and inputs:
        raise HybridGrammarError(
            f"line {line_no}: v0.2 quantum kernels do not yet accept symbolic runtime inputs"
        )
    if quantum_kernel is not None and typ != "REAL":
        raise HybridGrammarError(
            f"line {line_no}: v0.2 quantum kernel result type must be REAL"
        )
    execution_class = {
        "AUTO": "PLANNER_SELECTED",
        "CLASSICAL_PREFERRED": "CLASSICAL_PREFERRED",
        "QUANTUM_PREFERRED": "QUANTUM_PREFERRED",
        "QUANTUM_REQUIRED": "QUANTUM_REQUIRED",
    }[mode]
    b.add_node(
        HybridNode(
            node_id=f"compute.{out}",
            kind="COMPUTE",
            task_id=b.current_task,
            inputs=tuple(inputs),
            output=out,
            output_type=typ,
            execution_class=execution_class,
            attributes={
                "operator": operator,
                "mode": mode,
                "quantum_kernel_id": quantum_kernel,
            },
        )
    )


def _parse_observe(parts: list[str], b: _Builder, line_no: int) -> None:
    # OBSERVE out : REAL FROM kernel
    if len(parts) != 6:
        raise HybridGrammarError(
            f"line {line_no}: OBSERVE syntax is OBSERVE out : REAL FROM quantum_kernel"
        )
    _expect_colon(parts, 2, line_no)
    if parts[4].upper() != "FROM":
        raise HybridGrammarError(f"line {line_no}: OBSERVE requires FROM")
    out = _identifier(parts[1], "OBSERVE output")
    typ = parse_type(parts[3])
    if typ != "REAL":
        raise HybridGrammarError(f"line {line_no}: v0.2 OBSERVE output must be REAL")
    kernel = _identifier(parts[5], "quantum kernel")
    if kernel not in b.quantum:
        raise HybridGrammarError(f"line {line_no}: unknown quantum kernel {kernel}")
    binding = b.quantum[kernel]
    b.add_node(
        HybridNode(
            node_id=f"observe.{out}",
            kind="OBSERVE",
            task_id=b.current_task,
            output=out,
            output_type="REAL",
            execution_class="QUANTUM_RESULT",
            attributes={
                "quantum_kernel_id": kernel,
                "qir_sha256": binding.compiled.qir_sha256,
                "requested_observable": binding.compiled.qir_payload["observable"],
            },
        )
    )


def _parse_when(parts: list[str], b: _Builder, line_no: int) -> None:
    # WHEN bool_symbol ENABLE node_id
    if len(parts) != 4 or parts[2].upper() != "ENABLE":
        raise HybridGrammarError(
            f"line {line_no}: WHEN syntax is WHEN boolean_symbol ENABLE node_id"
        )
    cond = _identifier(parts[1], "WHEN condition")
    symbol = b.require_symbol(cond)
    if symbol.type_name != "BOOLEAN":
        raise HybridGrammarError(f"line {line_no}: WHEN condition must be BOOLEAN")
    target = _identifier(parts[3], "WHEN target")
    node_id = f"when.{cond}.{target}"
    b.add_node(
        HybridNode(
            node_id=node_id,
            kind="WHEN",
            task_id=b.current_task,
            inputs=(cond,),
            execution_class="CONTROL",
            attributes={"target_node_id": target},
        )
    )
    b.pending_node_refs.append((line_no, "WHEN", target))


def _parse_parallel(parts: list[str], b: _Builder, line_no: int) -> None:
    # PARALLEL group : node1 node2 ...
    if len(parts) < 5:
        raise HybridGrammarError(
            f"line {line_no}: PARALLEL syntax is PARALLEL group : node1 node2 ..."
        )
    _expect_colon(parts, 2, line_no)
    group = _identifier(parts[1], "parallel group")
    members = tuple(_identifier(x, "parallel member") for x in parts[3:])
    if len(set(members)) != len(members):
        raise HybridGrammarError(f"line {line_no}: duplicate PARALLEL member")
    b.add_node(
        HybridNode(
            node_id=f"parallel.{group}",
            kind="PARALLEL",
            task_id=b.current_task,
            execution_class="SCHEDULER_HINT",
            attributes={"members": list(members), "semantic_equivalence_change": False},
        )
    )
    for target in members:
        b.pending_node_refs.append((line_no, "PARALLEL", target))


def _parse_require(parts: list[str], b: _Builder, line_no: int) -> None:
    # REQUIRE capability ON node_id
    if len(parts) != 4 or parts[2].upper() != "ON":
        raise HybridGrammarError(
            f"line {line_no}: REQUIRE syntax is REQUIRE capability ON node_id"
        )
    capability = _identifier(parts[1], "capability")
    target = _identifier(parts[3], "REQUIRE target")
    b.add_node(
        HybridNode(
            node_id=f"require.{capability}.{target}",
            kind="REQUIRE",
            task_id=b.current_task,
            execution_class="CONSTRAINT",
            attributes={"capability": capability, "target_node_id": target},
        )
    )
    b.pending_node_refs.append((line_no, "REQUIRE", target))


def _parse_persist(parts: list[str], b: _Builder, line_no: int) -> None:
    # PERSIST symbol AS slot REQUIRE capability
    if len(parts) != 6 or parts[2].upper() != "AS" or parts[4].upper() != "REQUIRE":
        raise HybridGrammarError(
            f"line {line_no}: PERSIST syntax is PERSIST symbol AS slot REQUIRE capability"
        )
    symbol = _identifier(parts[1], "PERSIST symbol")
    b.require_symbol(symbol)
    slot = _slot(parts[3])
    capability = _identifier(parts[5], "PERSIST capability")
    b.add_node(
        HybridNode(
            node_id=f"persist.{symbol}",
            kind="PERSIST",
            task_id=b.current_task,
            inputs=(symbol,),
            execution_class="EXTERNAL_EFFECT_BOUNDARY",
            attributes={
                "slot": slot,
                "required_capability": capability,
                "mutation": True,
            },
            external_effect=True,
            execution_authorized=False,
        )
    )


def _parse_effect(parts: list[str], b: _Builder, line_no: int) -> None:
    # EFFECT id USING adapter INPUT a b REQUIRE capability
    if len(parts) < 8:
        raise HybridGrammarError(f"line {line_no}: incomplete EFFECT")
    effect_id = _identifier(parts[1], "effect")
    if parts[2].upper() != "USING":
        raise HybridGrammarError(f"line {line_no}: EFFECT requires USING")
    adapter = _identifier(parts[3], "effect adapter")
    if parts[4].upper() != "INPUT":
        raise HybridGrammarError(f"line {line_no}: EFFECT requires INPUT")
    try:
        req_index = next(
            i for i in range(5, len(parts)) if parts[i].upper() == "REQUIRE"
        )
    except StopIteration as exc:
        raise HybridGrammarError(f"line {line_no}: EFFECT requires REQUIRE capability") from exc
    if req_index == 5 or req_index + 2 != len(parts):
        raise HybridGrammarError(f"line {line_no}: malformed EFFECT")
    inputs = tuple(_identifier(x, "EFFECT input") for x in parts[5:req_index])
    for name in inputs:
        b.require_symbol(name)
    capability = _identifier(parts[req_index + 1], "effect capability")
    b.add_node(
        HybridNode(
            node_id=f"effect.{effect_id}",
            kind="EFFECT",
            task_id=b.current_task,
            inputs=inputs,
            execution_class="EXTERNAL_EFFECT_BOUNDARY",
            attributes={
                "adapter": adapter,
                "required_capability": capability,
                "mutation_or_external_action": True,
            },
            external_effect=True,
            execution_authorized=False,
        )
    )


def _compile_quantum_block(
    kernel_id: str,
    task_id: str,
    logical_qubits: int,
    mode: str,
    body_lines: list[str],
) -> QuantumBinding:
    source = "\n".join(
        [
            f"PROGRAM {kernel_id}",
            f"QUBITS {logical_qubits}",
            f"MODE {mode}",
            *body_lines,
            "",
        ]
    )
    try:
        compiled = compile_quantum_gate_program(source)
    except QuantumGateLanguageError as exc:
        raise HybridGrammarError(f"quantum kernel {kernel_id}: {exc}") from exc
    return QuantumBinding(kernel_id, task_id, compiled)


def compile_hybrid_program(source: str) -> CompiledHybridProgram:
    if not isinstance(source, str) or not source.strip():
        raise HybridGrammarError("hybrid source must be non-empty text")

    cleaned: list[tuple[int, str, list[str]]] = []
    for line_no, raw in enumerate(source.splitlines(), start=1):
        stripped = raw.split("#", 1)[0].strip()
        if stripped:
            cleaned.append((line_no, stripped, _tokenize(stripped, line_no)))
    if not cleaned:
        raise HybridGrammarError("hybrid source contains no statements")

    first_line, _, first = cleaned[0]
    if len(first) != 2 or first[0].upper() != "PROGRAM":
        raise HybridGrammarError(
            f"line {first_line}: first statement must be PROGRAM <id>"
        )
    builder = _Builder(first[1])

    in_quantum = False
    q_kernel = ""
    q_task = ""
    q_logical = 0
    q_mode = ""
    q_body: list[str] = []
    returned = False

    for line_no, stripped, parts in cleaned[1:]:
        head = parts[0].upper()

        if in_quantum:
            if head == "QUANTUM":
                if len(parts) != 2 or parts[1].upper() != "END":
                    raise HybridGrammarError(
                        f"line {line_no}: expected QUANTUM END"
                    )
                binding = _compile_quantum_block(
                    q_kernel, q_task, q_logical, q_mode, q_body
                )
                builder.add_quantum(binding)
                in_quantum = False
                q_kernel, q_task, q_mode, q_body = "", "", "", []
                q_logical = 0
                continue
            if head not in {"GATE", "OBSERVE"}:
                raise HybridGrammarError(
                    f"line {line_no}: quantum block accepts only GATE/OBSERVE/QUANTUM END"
                )
            q_body.append(" ".join(parts))
            continue

        if returned:
            raise HybridGrammarError(
                f"line {line_no}: RETURN must be the final top-level statement"
            )

        if head == "PROGRAM":
            raise HybridGrammarError(f"line {line_no}: duplicate PROGRAM")

        if head == "TASK":
            if len(parts) != 2:
                raise HybridGrammarError(f"line {line_no}: TASK requires one id")
            builder.set_task(parts[1])
            continue

        if head == "QUANTUM":
            # QUANTUM BEGIN id QUBITS N MODE RESULT_DIRECTED
            if (
                len(parts) != 7
                or parts[1].upper() != "BEGIN"
                or parts[3].upper() != "QUBITS"
                or parts[5].upper() != "MODE"
            ):
                raise HybridGrammarError(
                    f"line {line_no}: QUANTUM syntax is "
                    "QUANTUM BEGIN id QUBITS N MODE RESULT_DIRECTED|FULL_STATE"
                )
            q_kernel = _identifier(parts[2], "quantum kernel")
            if q_kernel in builder.quantum:
                raise HybridGrammarError(
                    f"line {line_no}: duplicate quantum kernel {q_kernel}"
                )
            try:
                q_logical = int(parts[4])
            except ValueError as exc:
                raise HybridGrammarError(
                    f"line {line_no}: QUBITS must be a positive integer"
                ) from exc
            if q_logical < 1:
                raise HybridGrammarError(
                    f"line {line_no}: QUBITS must be a positive integer"
                )
            q_mode = parts[6].upper()
            if q_mode not in _QUANTUM_MODES:
                raise HybridGrammarError(
                    f"line {line_no}: unsupported quantum mode {q_mode}"
                )
            q_task = builder.current_task
            q_body = []
            in_quantum = True
            continue

        if head == "INPUT":
            _parse_input(parts, builder, line_no)
        elif head == "FIND":
            _parse_find(parts, builder, line_no)
        elif head == "FILTER":
            _parse_filter(parts, builder, line_no)
        elif head == "COMPUTE":
            _parse_compute(parts, builder, line_no)
        elif head == "OBSERVE":
            _parse_observe(parts, builder, line_no)
        elif head == "WHEN":
            _parse_when(parts, builder, line_no)
        elif head == "PARALLEL":
            _parse_parallel(parts, builder, line_no)
        elif head == "REQUIRE":
            _parse_require(parts, builder, line_no)
        elif head == "PERSIST":
            _parse_persist(parts, builder, line_no)
        elif head == "EFFECT":
            _parse_effect(parts, builder, line_no)
        elif head == "RETURN":
            if len(parts) < 2:
                raise HybridGrammarError(f"line {line_no}: RETURN requires symbol(s)")
            names = tuple(_identifier(x, "return symbol") for x in parts[1:])
            if len(set(names)) != len(names):
                raise HybridGrammarError(f"line {line_no}: duplicate RETURN symbol")
            for name in names:
                builder.require_symbol(name)
            builder.return_symbols = names
            returned = True
        else:
            raise HybridGrammarError(
                f"line {line_no}: unsupported v0.2 statement {head}"
            )

    if in_quantum:
        raise HybridGrammarError("unterminated QUANTUM block")
    if builder.return_symbols is None:
        raise HybridGrammarError("hybrid program requires terminal RETURN")

    builder.validate_refs()

    source_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
    symbols = tuple(builder.symbols[name] for name in sorted(builder.symbols))
    nodes = tuple(builder.nodes)
    quantum = tuple(builder.quantum[name] for name in sorted(builder.quantum))

    provisional = {
        "schema": IR_SCHEMA,
        "grammar_schema": GRAMMAR_SCHEMA,
        "program_id": builder.program_id,
        "tasks": builder.tasks,
        "symbols": [item.to_dict() for item in symbols],
        "nodes": [item.to_dict() for item in nodes],
        "quantum_bindings": [item.to_dict() for item in quantum],
        "return_symbols": list(builder.return_symbols),
        "effect_policy": {
            "external_effects_present": any(x.external_effect for x in nodes),
            "external_effects_authorized": all(
                x.execution_authorized for x in nodes if x.external_effect
            ),
            "implicit_authorization": False,
            "actuation_performed": False,
        },
        "compiler_policy": {
            "free_form_natural_language": False,
            "backend_names_in_semantics": False,
            "quantum_gate_language": "PNCS_QUANTUM_GATE_PROGRAM_V0_1",
            "quantum_ir": "PHASENAV_QUANTUM_GATE_IR_V1",
            "unsupported_constructs": "FAIL_CLOSED",
        },
    }
    ir_sha = _sha256(provisional)
    return CompiledHybridProgram(
        program_id=builder.program_id,
        tasks=tuple(builder.tasks),
        symbols=symbols,
        nodes=nodes,
        quantum_bindings=quantum,
        return_symbols=builder.return_symbols,
        source_sha256=source_sha,
        ir_sha256=ir_sha,
    )


__all__ = [
    "GRAMMAR_SCHEMA",
    "IR_SCHEMA",
    "NODE_SCHEMA",
    "SYMBOL_SCHEMA",
    "QUANTUM_BINDING_SCHEMA",
    "HybridGrammarError",
    "HybridSymbol",
    "HybridNode",
    "QuantumBinding",
    "CompiledHybridProgram",
    "parse_type",
    "compile_hybrid_program",
]
