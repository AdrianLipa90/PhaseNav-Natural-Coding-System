from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, TypeVar


ErrorT = TypeVar("ErrorT", bound=Exception)


def finite_float(value: Any, field: str, error_type: type[ErrorT]) -> float:
    if isinstance(value, bool):
        raise error_type(f"{field} must be finite numeric")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise error_type(f"{field} must be finite numeric") from exc
    if not math.isfinite(out):
        raise error_type(f"{field} must be finite numeric")
    return out


def checked_sum(values: Iterable[float], field: str, error_type: type[ErrorT]) -> float:
    total = 0.0
    for index, raw in enumerate(values):
        value = finite_float(raw, f"{field}[{index}]", error_type)
        total = finite_float(total + value, field, error_type)
    return total


def checked_product(
    *values: float,
    field: str,
    error_type: type[ErrorT],
) -> float:
    out = 1.0
    for index, raw in enumerate(values):
        value = finite_float(raw, f"{field}[{index}]", error_type)
        out = finite_float(out * value, field, error_type)
    return out


def checked_difference(
    left: float,
    right: float,
    field: str,
    error_type: type[ErrorT],
) -> float:
    a = finite_float(left, f"{field}.left", error_type)
    b = finite_float(right, f"{field}.right", error_type)
    return finite_float(a - b, field, error_type)


def checked_ratio(
    numerator: float,
    denominator: float,
    field: str,
    error_type: type[ErrorT],
) -> float:
    num = finite_float(numerator, f"{field}.numerator", error_type)
    den = finite_float(denominator, f"{field}.denominator", error_type)
    if den == 0.0:
        raise error_type(f"{field} denominator must be nonzero")
    return finite_float(num / den, field, error_type)


def checked_abs_difference_ratio(
    left: float,
    right: float,
    scale: float,
    field: str,
    error_type: type[ErrorT],
) -> float:
    delta = abs(checked_difference(left, right, f"{field}.difference", error_type))
    denominator = abs(finite_float(scale, f"{field}.scale", error_type))
    return checked_ratio(delta, denominator, field, error_type)


def finite_tree(value: Any, field: str, error_type: type[ErrorT]) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return finite_float(value, field, error_type)
    if isinstance(value, tuple):
        return tuple(
            finite_tree(item, f"{field}[{index}]", error_type)
            for index, item in enumerate(value)
        )
    if isinstance(value, list):
        return [
            finite_tree(item, f"{field}[{index}]", error_type)
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        return {
            key: finite_tree(item, f"{field}.{key}", error_type)
            for key, item in value.items()
        }
    return value
