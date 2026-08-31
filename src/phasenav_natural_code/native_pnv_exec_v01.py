from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
import math
import shlex
from typing import Any, Callable, Mapping


NATIVE_PNV_EXEC_SCHEMA = "PNCS_NATIVE_PNV_EXEC_V0_1"
RECEIPT_SCHEMA = "PNCS_NATIVE_PNV_EXEC_RECEIPT_V0_1"
SUPPORTED_EPISTEMIC = frozenset({"CHYBA"})
SUPPORTED_MODES = frozenset({"READ_ONLY", "INTERNAL_EXECUTION"})
SUPPORTED_OPCODES = frozenset(
    {
        "SOURCE",
        "IDENTITY",
        "DIFFERENCE",
        "CONDITION",
        "ORDER",
        "TRANSFORM",
        "COMPOSITION",
        "RETURN",
    }
)


class NativePNVExecError(RuntimeError):
    pass


class NativePNVParseError(NativePNVExecError):
    pass


class NativePNVResolutionError(NativePNVExecError):
    pass


class NativePNVAssertionError(NativePNVExecError):
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
    try:
        raw = _canonical_bytes(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativePNVResolutionError("PNV value is not canonical finite JSON") from exc
    return hashlib.sha256(raw).hexdigest()


def _finite_number(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        converted = float(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return math.isfinite(converted)


def _finite_result(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativePNVResolutionError(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise NativePNVResolutionError(f"{field} must be finite")
    return out


def _snapshot_runtime_value(value: Any, field: str) -> Any:
    try:
        _canonical_bytes(value)
        return copy.deepcopy(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativePNVResolutionError(f"{field} is not canonical finite JSON") from exc


@dataclass(frozen=True)
class PNVOp:
    name: str
    opcode: str
    args: tuple[str, ...]
    line_no: int

    @property
    def payload(self) -> dict[str, Any]:
        return {"name": self.name, "opcode": self.opcode, "args": list(self.args), "line_no": self.line_no}


@dataclass(frozen=True)
class PNVProgram:
    version: int
    epistemic: str
    mode: str
    ops: tuple[PNVOp, ...]
    assertions: tuple[str, ...]
    emits: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...]
    source_text: str

    @property
    def source_sha256(self) -> str:
        return hashlib.sha256(self.source_text.encode("utf-8")).hexdigest()

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "schema": NATIVE_PNV_EXEC_SCHEMA,
            "version": self.version,
            "epistemic": self.epistemic,
            "mode": self.mode,
            "ops": [op.payload for op in self.ops],
            "assertions": list(self.assertions),
            "emits": list(self.emits),
            "metadata": [[k, v] for k, v in self.metadata],
            "source_sha256": self.source_sha256,
        }

    @property
    def graph_sha256(self) -> str:
        return _sha256(self.payload)


def _validate_program(program: PNVProgram) -> None:
    if not isinstance(program.version, int) or isinstance(program.version, bool) or program.version != 1:
        raise NativePNVParseError("PNVProgram carries an unsupported version")
    if program.epistemic not in SUPPORTED_EPISTEMIC:
        raise NativePNVParseError("PNVProgram carries an unsupported EPISTEMIC state")
    if program.mode not in SUPPORTED_MODES:
        raise NativePNVParseError("PNVProgram carries an unsupported MODE")
    if not isinstance(program.source_text, str) or not program.source_text.strip():
        raise NativePNVParseError("PNVProgram requires exact non-empty source_text")
    if not program.ops:
        raise NativePNVParseError("PNVProgram contains no operations")
    names: set[str] = set()
    for op in program.ops:
        if not isinstance(op, PNVOp):
            raise NativePNVParseError("PNVProgram ops must be PNVOp entries")
        if not isinstance(op.name, str) or not op.name or op.name in names:
            raise NativePNVParseError("PNVProgram operation names must be unique and non-empty")
        if op.opcode not in SUPPORTED_OPCODES:
            raise NativePNVParseError(f"unsupported opcode {op.opcode!r}")
        if not isinstance(op.args, tuple) or not op.args or any(not isinstance(x, str) or not x for x in op.args):
            raise NativePNVParseError("PNVProgram operation args must be non-empty string tuples")
        if not isinstance(op.line_no, int) or isinstance(op.line_no, bool) or op.line_no <= 0:
            raise NativePNVParseError("PNVProgram operation line_no must be a positive integer")
        names.add(op.name)
    for label, refs in (("ASSERT", program.assertions), ("EMIT", program.emits)):
        if any(not isinstance(name, str) or name not in names for name in refs):
            raise NativePNVParseError(f"{label} references unknown OP names")
    if any(
        not isinstance(row, tuple)
        or len(row) != 2
        or not all(isinstance(item, str) for item in row)
        for row in program.metadata
    ):
        raise NativePNVParseError("PNVProgram metadata must contain string pairs")


@dataclass(frozen=True)
class NativePNVExecutionResult:
    program: PNVProgram
    values: Mapping[str, Any]
    emitted: Mapping[str, Any]
    receipt: Mapping[str, Any]


def parse_pnv(text: str) -> PNVProgram:
    if not isinstance(text, str) or not text.strip():
        raise NativePNVParseError("non-empty PNV source text is required")

    version: int | None = None
    epistemic: str | None = None
    mode: str | None = None
    ops: list[PNVOp] = []
    assertions: list[str] = []
    emits: list[str] = []
    metadata: list[tuple[str, str]] = []
    seen_names: set[str] = set()

    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            body = line[1:].strip()
            if body and " " in body:
                key, value = body.split(None, 1)
                if key.replace("_", "").isalnum() and key.upper() == key:
                    metadata.append((key, value.strip()))
            continue
        try:
            parts = shlex.split(line, comments=False, posix=True)
        except ValueError as exc:
            raise NativePNVParseError(f"line {line_no}: invalid quoting: {exc}") from exc
        if not parts:
            continue
        head = parts[0]
        if head == "PNV":
            if version is not None or len(parts) != 2:
                raise NativePNVParseError(f"line {line_no}: expected exactly one 'PNV <version>' header")
            try:
                version = int(parts[1])
            except ValueError as exc:
                raise NativePNVParseError(f"line {line_no}: PNV version must be an integer") from exc
            if version != 1:
                raise NativePNVParseError(f"line {line_no}: unsupported PNV version {version}")
            continue
        if head == "EPISTEMIC":
            if epistemic is not None or len(parts) != 2:
                raise NativePNVParseError(f"line {line_no}: expected exactly one EPISTEMIC header")
            epistemic = parts[1]
            if epistemic not in SUPPORTED_EPISTEMIC:
                raise NativePNVParseError(f"line {line_no}: unsupported EPISTEMIC state {epistemic!r}")
            continue
        if head == "MODE":
            if mode is not None or len(parts) != 2:
                raise NativePNVParseError(f"line {line_no}: expected exactly one MODE header")
            mode = parts[1]
            if mode not in SUPPORTED_MODES:
                raise NativePNVParseError(f"line {line_no}: unsupported MODE {mode!r}")
            continue
        if head == "OP":
            if len(parts) < 4:
                raise NativePNVParseError(f"line {line_no}: OP requires name, opcode, and at least one argument")
            name, opcode = parts[1], parts[2]
            if name in seen_names:
                raise NativePNVParseError(f"line {line_no}: duplicate OP name {name!r}")
            if opcode not in SUPPORTED_OPCODES:
                raise NativePNVParseError(f"line {line_no}: unsupported opcode {opcode!r}")
            seen_names.add(name)
            ops.append(PNVOp(name=name, opcode=opcode, args=tuple(parts[3:]), line_no=line_no))
            continue
        if head == "ASSERT":
            if len(parts) != 2:
                raise NativePNVParseError(f"line {line_no}: ASSERT requires exactly one OP name")
            assertions.append(parts[1])
            continue
        if head == "EMIT":
            if len(parts) != 2:
                raise NativePNVParseError(f"line {line_no}: EMIT requires exactly one OP name")
            emits.append(parts[1])
            continue
        raise NativePNVParseError(f"line {line_no}: unknown statement {head!r}")

    if version is None:
        raise NativePNVParseError("missing PNV header")
    if epistemic is None:
        raise NativePNVParseError("missing EPISTEMIC header")
    if mode is None:
        raise NativePNVParseError("missing MODE header")
    if not ops:
        raise NativePNVParseError("PNV program contains no OP statements")
    missing_refs = [name for name in assertions + emits if name not in seen_names]
    if missing_refs:
        raise NativePNVParseError(f"ASSERT/EMIT references unknown OP names: {sorted(set(missing_refs))}")

    program = PNVProgram(
        version=version,
        epistemic=epistemic,
        mode=mode,
        ops=tuple(ops),
        assertions=tuple(assertions),
        emits=tuple(emits),
        metadata=tuple(metadata),
        source_text=text,
    )
    _validate_program(program)
    return program


class NativePNVExecutor:
    """Fail-closed interpreter for native PNV1 relational programs.

    External semantics are injected explicitly through `sources`, `comparators`, and
    `transforms`. The interpreter itself performs no shell, subprocess, network, Git,
    device, or arbitrary filesystem operations. Side effects of injected Python
    callbacks are outside the interpreter's observable boundary and are therefore
    reported as unverified whenever such callbacks are invoked.
    """

    def __init__(
        self,
        *,
        sources: Mapping[str, Any] | None = None,
        comparators: Mapping[str, Callable[[Any], bool]] | None = None,
        transforms: Mapping[str, Callable[[Any], Any]] | None = None,
    ) -> None:
        source_rows = dict(sources or {})
        self.comparators = dict(comparators or {})
        self.transforms = dict(transforms or {})
        for name, callback in (*self.comparators.items(), *self.transforms.items()):
            if not isinstance(name, str) or not name or not callable(callback):
                raise NativePNVResolutionError("callback registries require non-empty names and callables")
        self.sources: dict[str, Any] = {}
        for name, value in source_rows.items():
            if not isinstance(name, str) or not name:
                raise NativePNVResolutionError("source registry requires non-empty names")
            self.sources[name] = _snapshot_runtime_value(value, f"source {name!r}")

    def _resolve(self, token: str, values: Mapping[str, Any]) -> Any:
        if token in values:
            return _snapshot_runtime_value(values[token], f"resolved operation {token!r}")
        if token in self.sources:
            return _snapshot_runtime_value(self.sources[token], f"resolved source {token!r}")
        if token == "TRUE":
            return True
        if token == "FALSE":
            return False
        if token == "NONE":
            return None
        try:
            if token.startswith(("+", "-")):
                numeric = token[1:]
            else:
                numeric = token
            if numeric and all(ch.isdigit() or ch in ".eE+-" for ch in numeric):
                value = float(token) if any(ch in token for ch in ".eE") else int(token)
                if _finite_number(value):
                    return value
        except (ValueError, OverflowError):
            pass
        raise NativePNVResolutionError(f"unresolved PNV token {token!r}")

    def _execute_op(self, op: PNVOp, values: Mapping[str, Any]) -> Any:
        code = op.opcode
        if code == "SOURCE":
            if len(op.args) != 1:
                raise NativePNVResolutionError(f"{op.name}: SOURCE requires one argument")
            return self._resolve(op.args[0], values)
        if code == "IDENTITY":
            if len(op.args) == 1:
                return self._resolve(op.args[0], values)
            if len(op.args) == 2:
                return self._resolve(op.args[0], values) == self._resolve(op.args[1], values)
            raise NativePNVResolutionError(f"{op.name}: IDENTITY supports one or two arguments")
        if code == "DIFFERENCE":
            if len(op.args) != 2:
                raise NativePNVResolutionError(f"{op.name}: DIFFERENCE requires two arguments")
            left = self._resolve(op.args[0], values)
            right = self._resolve(op.args[1], values)
            if _finite_number(left) and _finite_number(right):
                return _finite_result(float(left) - float(right), f"{op.name} numeric difference")
            return {
                "equal": left == right,
                "left_sha256": _sha256(left),
                "right_sha256": _sha256(right),
            }
        if code == "CONDITION":
            if len(op.args) != 2:
                raise NativePNVResolutionError(f"{op.name}: CONDITION requires value and comparator")
            value = self._resolve(op.args[0], values)
            comparator_name = op.args[1]
            comparator = self.comparators.get(comparator_name)
            if comparator is None:
                raise NativePNVResolutionError(f"{op.name}: comparator {comparator_name!r} is not admitted")
            try:
                result = comparator(value)
            except Exception as exc:
                raise NativePNVResolutionError(f"{op.name}: comparator {comparator_name!r} failed") from exc
            if not isinstance(result, bool):
                raise NativePNVResolutionError(f"{op.name}: comparator must return bool")
            return result
        if code == "ORDER":
            if not op.args:
                raise NativePNVResolutionError(f"{op.name}: ORDER requires at least one argument")
            return [self._resolve(token, values) for token in op.args]
        if code == "TRANSFORM":
            if len(op.args) != 2:
                raise NativePNVResolutionError(f"{op.name}: TRANSFORM requires value and transform name")
            value = self._resolve(op.args[0], values)
            transform_name = op.args[1]
            transform = self.transforms.get(transform_name)
            if transform is None:
                raise NativePNVResolutionError(f"{op.name}: transform {transform_name!r} is not admitted")
            try:
                return transform(value)
            except Exception as exc:
                raise NativePNVResolutionError(f"{op.name}: transform {transform_name!r} failed") from exc
        if code == "COMPOSITION":
            if not op.args:
                raise NativePNVResolutionError(f"{op.name}: COMPOSITION requires at least one argument")
            return [self._resolve(token, values) for token in op.args]
        if code == "RETURN":
            if len(op.args) != 1:
                raise NativePNVResolutionError(f"{op.name}: RETURN requires one argument")
            return self._resolve(op.args[0], values)
        raise NativePNVResolutionError(f"{op.name}: unsupported opcode {code!r}")

    def execute(self, program: PNVProgram | str) -> NativePNVExecutionResult:
        if isinstance(program, str):
            program = parse_pnv(program)
        if not isinstance(program, PNVProgram):
            raise TypeError("PNVProgram or source string required")
        _validate_program(program)

        values: dict[str, Any] = {}
        trace: list[dict[str, Any]] = []
        invoked_callbacks: list[str] = []
        for op in program.ops:
            value = _snapshot_runtime_value(self._execute_op(op, values), f"{op.name} result")
            values[op.name] = value
            if op.opcode == "CONDITION":
                invoked_callbacks.append(f"comparator:{op.args[1]}")
            elif op.opcode == "TRANSFORM":
                invoked_callbacks.append(f"transform:{op.args[1]}")
            trace.append({"op": op.name, "opcode": op.opcode, "result_sha256": _sha256(value)})

        assertion_results: list[dict[str, Any]] = []
        for name in program.assertions:
            value = values[name]
            passed = bool(value)
            assertion_results.append({"op": name, "passed": passed, "value_sha256": _sha256(value)})
            if not passed:
                raise NativePNVAssertionError(f"ASSERT failed for {name}")

        emitted = {name: _snapshot_runtime_value(values[name], f"emitted {name!r}") for name in program.emits}
        callbacks_invoked = tuple(invoked_callbacks)
        callback_boundary_open = bool(callbacks_invoked)
        effect_value: bool | None = None if callback_boundary_open else False
        effect_status = (
            "UNVERIFIED_CALLBACK_BOUNDARY"
            if callback_boundary_open
            else "VERIFIED_NONE_WITHIN_INTERPRETER_BOUNDARY"
        )
        payload = {
            "schema": RECEIPT_SCHEMA,
            "program_source_sha256": program.source_sha256,
            "program_graph_sha256": program.graph_sha256,
            "pnv_version": program.version,
            "epistemic": program.epistemic,
            "mode": program.mode,
            "trace": trace,
            "assertions": assertion_results,
            "emitted": [[name, _sha256(value)] for name, value in emitted.items()],
            "effect_boundary": {
                "shell": effect_value,
                "subprocess": effect_value,
                "network": effect_value,
                "git": effect_value,
                "device": effect_value,
                "arbitrary_filesystem": effect_value,
                "external_effects": effect_value,
                "external_effects_status": effect_status,
                "interpreter_shell": False,
                "interpreter_subprocess": False,
                "interpreter_network": False,
                "interpreter_git": False,
                "interpreter_device": False,
                "interpreter_arbitrary_filesystem": False,
                "interpreter_external_effects": False,
                "callbacks_invoked": list(callbacks_invoked),
                "callback_effects_verified": not callback_boundary_open,
            },
            "external_semantics_injected": bool(self.sources or self.comparators or self.transforms),
            "unknown_semantics_fail_closed": True,
            "deterministic_receipt": True,
            "callback_determinism_verified": not callback_boundary_open,
        }
        receipt_sha256 = _sha256(payload)
        receipt = {**payload, "receipt_sha256": receipt_sha256}
        return NativePNVExecutionResult(
            program=program,
            values={name: _snapshot_runtime_value(value, f"final value {name!r}") for name, value in values.items()},
            emitted=emitted,
            receipt=receipt,
        )


def execute_pnv(
    text: str,
    *,
    sources: Mapping[str, Any] | None = None,
    comparators: Mapping[str, Callable[[Any], bool]] | None = None,
    transforms: Mapping[str, Callable[[Any], Any]] | None = None,
) -> NativePNVExecutionResult:
    return NativePNVExecutor(sources=sources, comparators=comparators, transforms=transforms).execute(text)
