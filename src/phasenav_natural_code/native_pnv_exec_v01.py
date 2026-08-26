from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import shlex
from typing import Any, Callable, Mapping


NATIVE_PNV_EXEC_SCHEMA = "PNCS_NATIVE_PNV_EXEC_V0_1"
RECEIPT_SCHEMA = "PNCS_NATIVE_PNV_EXEC_RECEIPT_V0_1"
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
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


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
    source_sha256: str

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
            continue
        if head == "MODE":
            if mode is not None or len(parts) != 2:
                raise NativePNVParseError(f"line {line_no}: expected exactly one MODE header")
            mode = parts[1]
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

    return PNVProgram(
        version=version,
        epistemic=epistemic,
        mode=mode,
        ops=tuple(ops),
        assertions=tuple(assertions),
        emits=tuple(emits),
        metadata=tuple(metadata),
        source_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


class NativePNVExecutor:
    """Fail-closed interpreter for native PNV1 relational programs.

    External semantics are injected explicitly through `sources`, `comparators`, and
    `transforms`. The executor performs no shell, subprocess, network, Git, device,
    or arbitrary filesystem operations.
    """

    def __init__(
        self,
        *,
        sources: Mapping[str, Any] | None = None,
        comparators: Mapping[str, Callable[[Any], bool]] | None = None,
        transforms: Mapping[str, Callable[[Any], Any]] | None = None,
    ) -> None:
        self.sources = dict(sources or {})
        self.comparators = dict(comparators or {})
        self.transforms = dict(transforms or {})

    def _resolve(self, token: str, values: Mapping[str, Any]) -> Any:
        if token in values:
            return values[token]
        if token in self.sources:
            return self.sources[token]
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
        except ValueError:
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
                return float(left) - float(right)
            return {"equal": left == right, "left_sha256": _sha256(left), "right_sha256": _sha256(right)}
        if code == "CONDITION":
            if len(op.args) != 2:
                raise NativePNVResolutionError(f"{op.name}: CONDITION requires value and comparator")
            value = self._resolve(op.args[0], values)
            comparator_name = op.args[1]
            comparator = self.comparators.get(comparator_name)
            if comparator is None:
                raise NativePNVResolutionError(f"{op.name}: comparator {comparator_name!r} is not admitted")
            result = comparator(value)
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
            return transform(value)
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

        values: dict[str, Any] = {}
        trace: list[dict[str, Any]] = []
        for op in program.ops:
            value = self._execute_op(op, values)
            values[op.name] = value
            trace.append({"op": op.name, "opcode": op.opcode, "result_sha256": _sha256(value)})

        assertion_results: list[dict[str, Any]] = []
        for name in program.assertions:
            value = values[name]
            passed = bool(value)
            assertion_results.append({"op": name, "passed": passed, "value_sha256": _sha256(value)})
            if not passed:
                raise NativePNVAssertionError(f"ASSERT failed for {name}")

        emitted = {name: values[name] for name in program.emits}
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
                "shell": False,
                "subprocess": False,
                "network": False,
                "git": False,
                "device": False,
                "arbitrary_filesystem": False,
                "external_effects": False,
            },
            "external_semantics_injected": True,
            "unknown_semantics_fail_closed": True,
            "deterministic_receipt": True,
        }
        receipt_sha256 = _sha256(payload)
        receipt = {**payload, "receipt_sha256": receipt_sha256}
        return NativePNVExecutionResult(program=program, values=values, emitted=emitted, receipt=receipt)


def execute_pnv(
    text: str,
    *,
    sources: Mapping[str, Any] | None = None,
    comparators: Mapping[str, Callable[[Any], bool]] | None = None,
    transforms: Mapping[str, Callable[[Any], Any]] | None = None,
) -> NativePNVExecutionResult:
    return NativePNVExecutor(sources=sources, comparators=comparators, transforms=transforms).execute(text)
