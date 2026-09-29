"""PNCS quantum gate language v0.1.

A small fail-closed textual language that compiles to the PhaseNav QIR v1
payload. It is backend-neutral: the language describes logical gates and the
requested observable, not IBM/Q28/QHTRI hardware details.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import shlex

PROGRAM_SCHEMA = "PNCS_QUANTUM_GATE_PROGRAM_V0_1"
QIR_SCHEMA = "PHASENAV_QUANTUM_GATE_IR_V1"
ALLOWED_GATES = {
    "H": (1, False),
    "X": (1, False),
    "RZ": (1, True),
    "PHASE": (1, True),
    "CNOT": (2, False),
    "CZ": (2, False),
}


class QuantumGateLanguageError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _qubit(token: str) -> int:
    token = str(token)
    if len(token) < 2 or token[0].lower() != "q" or not token[1:].isdigit():
        raise QuantumGateLanguageError(f"invalid qubit token: {token}")
    return int(token[1:])


@dataclass(frozen=True)
class CompiledQuantumGateProgram:
    program_id: str
    logical_qubits: int
    mode: str
    qir_payload: dict
    source_sha256: str
    qir_sha256: str

    def to_dict(self) -> dict:
        return {
            "schema": PROGRAM_SCHEMA,
            "program_id": self.program_id,
            "logical_qubits": self.logical_qubits,
            "mode": self.mode,
            "source_sha256": self.source_sha256,
            "qir_sha256": self.qir_sha256,
            "qir": self.qir_payload,
        }


def compile_quantum_gate_program(source: str) -> CompiledQuantumGateProgram:
    if not isinstance(source, str) or not source.strip():
        raise QuantumGateLanguageError("program source must be non-empty text")

    program_id = None
    logical_qubits = None
    mode = None
    gates: list[dict] = []
    observable = None

    for line_no, raw in enumerate(source.splitlines(), start=1):
        stripped = raw.split("#", 1)[0].strip()
        if not stripped:
            continue
        try:
            parts = shlex.split(stripped)
        except ValueError as exc:
            raise QuantumGateLanguageError(f"line {line_no}: {exc}") from exc
        head = parts[0].upper()

        if head == "PROGRAM":
            if len(parts) != 2 or program_id is not None:
                raise QuantumGateLanguageError(f"line {line_no}: invalid PROGRAM")
            program_id = parts[1]
            continue

        if head == "QUBITS":
            if len(parts) != 2 or logical_qubits is not None:
                raise QuantumGateLanguageError(f"line {line_no}: invalid QUBITS")
            try:
                logical_qubits = int(parts[1])
            except ValueError as exc:
                raise QuantumGateLanguageError(f"line {line_no}: QUBITS must be integer") from exc
            if logical_qubits < 1:
                raise QuantumGateLanguageError(f"line {line_no}: QUBITS must be positive")
            continue

        if head == "MODE":
            if len(parts) != 2 or mode is not None:
                raise QuantumGateLanguageError(f"line {line_no}: invalid MODE")
            mode = parts[1].upper()
            if mode not in {"RESULT_DIRECTED", "FULL_STATE"}:
                raise QuantumGateLanguageError(f"line {line_no}: unsupported MODE")
            continue

        if head == "GATE":
            if len(parts) < 3:
                raise QuantumGateLanguageError(f"line {line_no}: incomplete GATE")
            op = parts[1].upper()
            if op not in ALLOWED_GATES:
                raise QuantumGateLanguageError(f"line {line_no}: unsupported gate {op}")
            arity, has_angle = ALLOWED_GATES[op]
            expected = 2 + arity + (1 if has_angle else 0)
            if len(parts) != expected:
                raise QuantumGateLanguageError(f"line {line_no}: wrong arity for {op}")
            qs = [_qubit(tok) for tok in parts[2:2 + arity]]
            if len(set(qs)) != len(qs):
                raise QuantumGateLanguageError(f"line {line_no}: repeated gate qubit")
            item = {"op": op, "qubits": qs}
            if has_angle:
                try:
                    angle = float(parts[-1])
                except ValueError as exc:
                    raise QuantumGateLanguageError(f"line {line_no}: invalid angle") from exc
                if not math.isfinite(angle):
                    raise QuantumGateLanguageError(f"line {line_no}: angle must be finite")
                item["angle"] = angle
            gates.append(item)
            continue

        if head == "OBSERVE":
            if observable is not None or len(parts) < 3:
                raise QuantumGateLanguageError(f"line {line_no}: invalid OBSERVE")
            pauli = parts[1].upper()
            if not pauli or any(ch not in "IXYZ" for ch in pauli):
                raise QuantumGateLanguageError(f"line {line_no}: invalid Pauli word")
            qs = [_qubit(tok) for tok in parts[2:]]
            if len(qs) != len(pauli):
                raise QuantumGateLanguageError(
                    f"line {line_no}: Pauli word length must match qubit count"
                )
            if len(set(qs)) != len(qs):
                raise QuantumGateLanguageError(f"line {line_no}: repeated observable qubit")
            if all(ch == "I" for ch in pauli):
                raise QuantumGateLanguageError(f"line {line_no}: empty observable support")
            observable = {"pauli": pauli, "qubits": qs}
            continue

        raise QuantumGateLanguageError(f"line {line_no}: unknown statement {head}")

    if program_id is None:
        raise QuantumGateLanguageError("missing PROGRAM")
    if logical_qubits is None:
        raise QuantumGateLanguageError("missing QUBITS")
    if mode is None:
        raise QuantumGateLanguageError("missing MODE")
    if observable is None:
        raise QuantumGateLanguageError("missing OBSERVE")

    for item in gates:
        if any(q >= logical_qubits for q in item["qubits"]):
            raise QuantumGateLanguageError("gate qubit exceeds logical extent")
    if any(q >= logical_qubits for q in observable["qubits"]):
        raise QuantumGateLanguageError("observable qubit exceeds logical extent")

    qir = {
        "schema": QIR_SCHEMA,
        "logical_qubits": logical_qubits,
        "mode": mode,
        "gates": gates,
        "observable": observable,
    }
    source_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return CompiledQuantumGateProgram(
        program_id=program_id,
        logical_qubits=logical_qubits,
        mode=mode,
        qir_payload=qir,
        source_sha256=source_sha,
        qir_sha256=_digest(qir),
    )


__all__ = [
    "PROGRAM_SCHEMA",
    "QIR_SCHEMA",
    "ALLOWED_GATES",
    "QuantumGateLanguageError",
    "CompiledQuantumGateProgram",
    "compile_quantum_gate_program",
]
