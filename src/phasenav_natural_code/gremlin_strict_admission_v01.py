from __future__ import annotations

"""Shared fail-closed admission primitives for GREMLIN candidate mathematics.

The kernel performs type and numeric-domain admission only. It does not assign
semantic identity, candidate authority, runtime authority, or canon status.
Callers may provide their own exception type so domain-specific APIs retain
their established error contracts.
"""

import math
from numbers import Complex, Real
from typing import Iterable

STRICT_ADMISSION_SCHEMA = "PNCS_GREMLIN_STRICT_ADMISSION_V0_1"


class GremlinStrictAdmissionError(ValueError):
    pass


def _fail(error_type: type[Exception], message: str):
    raise error_type(message)


def exact_sequence(
    values: Iterable[object],
    field: str,
    *,
    exact_length: int | None = None,
    min_length: int | None = None,
    error_type: type[Exception] = GremlinStrictAdmissionError,
) -> tuple[object, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        _fail(error_type, f"{field} must be an explicit iterable container")
    try:
        result = tuple(values)
    except TypeError as exc:
        raise error_type(f"{field} must be an explicit iterable container") from exc
    if exact_length is not None and len(result) != exact_length:
        _fail(error_type, f"{field} must contain exactly {exact_length} values")
    if min_length is not None and len(result) < min_length:
        _fail(error_type, f"{field} must contain at least {min_length} values")
    return result


def finite_real(
    value: object,
    field: str,
    *,
    error_type: type[Exception] = GremlinStrictAdmissionError,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        _fail(error_type, f"{field} must be a finite real number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise error_type(f"{field} must be a finite real number") from exc
    if not math.isfinite(result):
        _fail(error_type, f"{field} must be a finite real number")
    return result


def positive_real(
    value: object,
    field: str,
    *,
    error_type: type[Exception] = GremlinStrictAdmissionError,
) -> float:
    result = finite_real(value, field, error_type=error_type)
    if result <= 0.0:
        _fail(error_type, f"{field} must be strictly positive")
    return result


def nonnegative_real(
    value: object,
    field: str,
    *,
    error_type: type[Exception] = GremlinStrictAdmissionError,
) -> float:
    result = finite_real(value, field, error_type=error_type)
    if result < 0.0:
        _fail(error_type, f"{field} must be non-negative")
    return result


def closed_unit_interval(
    value: object,
    field: str,
    *,
    error_type: type[Exception] = GremlinStrictAdmissionError,
) -> float:
    result = finite_real(value, field, error_type=error_type)
    if not 0.0 <= result <= 1.0:
        _fail(error_type, f"{field} must be in [0,1]")
    return result


def finite_real_sequence(
    values: Iterable[object],
    field: str,
    *,
    exact_length: int | None = None,
    min_length: int | None = None,
    error_type: type[Exception] = GremlinStrictAdmissionError,
) -> tuple[float, ...]:
    raw = exact_sequence(
        values,
        field,
        exact_length=exact_length,
        min_length=min_length,
        error_type=error_type,
    )
    return tuple(
        finite_real(value, f"{field}[{index}]", error_type=error_type)
        for index, value in enumerate(raw)
    )


def finite_complex(
    value: object,
    field: str,
    *,
    error_type: type[Exception] = GremlinStrictAdmissionError,
) -> complex:
    if isinstance(value, bool) or not isinstance(value, Complex):
        _fail(error_type, f"{field} must be a finite complex number")
    try:
        result = complex(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise error_type(f"{field} must be a finite complex number") from exc
    if not math.isfinite(result.real) or not math.isfinite(result.imag):
        _fail(error_type, f"{field} must be a finite complex number")
    return result


def finite_complex_sequence(
    values: Iterable[object],
    field: str,
    *,
    exact_length: int | None = None,
    min_length: int | None = None,
    error_type: type[Exception] = GremlinStrictAdmissionError,
) -> tuple[complex, ...]:
    raw = exact_sequence(
        values,
        field,
        exact_length=exact_length,
        min_length=min_length,
        error_type=error_type,
    )
    return tuple(
        finite_complex(value, f"{field}[{index}]", error_type=error_type)
        for index, value in enumerate(raw)
    )
