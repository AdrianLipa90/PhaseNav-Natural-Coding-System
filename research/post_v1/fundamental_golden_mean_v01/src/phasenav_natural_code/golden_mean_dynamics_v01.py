"""PNCS candidate kernel for the exact TIR golden-mean dynamics stack.

This module is additive and non-actuating.  It implements only mathematical
objects whose upstream claim class is exact (or a standard theorem applied
exactly).  Physical time, thermodynamic pressure, arithmetic-prime/Riemann-zeta
identifications, and E7/E8 operator identifications are intentionally absent.
"""
from __future__ import annotations

from fractions import Fraction
from math import comb, isfinite, isqrt, log, pi, sqrt
from types import MappingProxyType
from typing import Iterator


class GoldenMeanKernelError(ValueError):
    pass


PHI = (1.0 + sqrt(5.0)) / 2.0
KAPPA = log(2.0) / (24.0 * pi)

SOURCE_COMMITS = MappingProxyType(
    {
        "idt_collatz_fs_phase": "afed815f190ee5b162d1406878305a4259536af0",
        "tir_cp1_dyadic_fractal": "2c23cc50357c136cf21e14a8f9552a30e8496489",
        "tir_homogeneous_fibration_5_1_2": "0772bca5852194a0bf0edbe2cdd49993bb7ed5ba",
        "tir_golden_mean_transfer_kappa": "0593bfc5af98224b8f788ee958e7e011c785bf9e",
        "tir_golden_mean_pressure_kappa": "c6e282980377b43c1209ad4842b3b71e4fc394f3",
        "tir_golden_mean_coding_zeta": "2097ddc26f97dfca2141e52bf53fed7d9fee2994",
        "tir_primitive_orbit_euler_product": "18947402100145b5e8b88865ea90e4aab146a8dc",
        "sohalf_repository_holonomy": "23eae95d8cbc33782c4a819ae40b2b166b566235",
        "rfc_collatz_fs_phase_fibre": "dbbfcc83de96246aa96217a9c40def64661474d7",
    }
)

FIREWALLS = (
    "RUNTIME_DEFAULT_OFF",
    "PHYSICAL_BINDING_OPEN",
    "THERMODYNAMIC_PRESSURE_NOT_CLAIMED",
    "RIEMANN_ZETA_FIREWALL",
    "ARITHMETIC_PRIME_FIREWALL",
    "E7_E8_LINEAR_INTERTWINER_NOGO",
    "METRIC_COUPLING_NOT_ACTIVATED",
)


def _require_nonnegative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GoldenMeanKernelError(f"{name} must be a non-negative integer")
    return value


def _require_positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GoldenMeanKernelError(f"{name} must be a positive integer")
    return value


def _require_binary_word(word: str, *, admissible: bool = False) -> str:
    if not isinstance(word, str) or any(ch not in "01" for ch in word):
        raise GoldenMeanKernelError("binary word must contain only '0' and '1'")
    if admissible and "11" in word:
        raise GoldenMeanKernelError("unreduced Collatz language forbids the block '11'")
    return word


def fibonacci(n: int) -> int:
    n = _require_nonnegative_int(n, "n")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def lucas(n: int) -> int:
    n = _require_nonnegative_int(n, "n")
    if n == 0:
        return 2
    if n == 1:
        return 1
    a, b = 2, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def is_admissible_word(word: str) -> bool:
    try:
        _require_binary_word(word)
    except GoldenMeanKernelError:
        return False
    return "11" not in word


def iter_admissible_words(length: int) -> Iterator[str]:
    length = _require_nonnegative_int(length, "length")

    def visit(prefix: str) -> Iterator[str]:
        if len(prefix) == length:
            yield prefix
            return
        yield from visit(prefix + "0")
        if not prefix or prefix[-1] != "1":
            yield from visit(prefix + "1")

    yield from visit("")


def admissible_word_count(length: int) -> int:
    length = _require_nonnegative_int(length, "length")
    return fibonacci(length + 2)


def unreduced_collatz_step(n: int) -> int:
    n = _require_positive_int(n, "n")
    return n // 2 if n % 2 == 0 else 3 * n + 1


def collatz_parity_prefix(n: int, length: int) -> str:
    n = _require_positive_int(n, "n")
    length = _require_nonnegative_int(length, "length")
    bits: list[str] = []
    x = n
    for _ in range(length):
        bits.append(str(x & 1))
        x = unreduced_collatz_step(x)
    word = "".join(bits)
    if "11" in word:
        raise AssertionError("unreduced Collatz parity invariant violated")
    return word


def accelerated_collatz_step(n: int) -> int:
    n = _require_positive_int(n, "n")
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def _accelerated_step_nonnegative(n: int) -> int:
    if n < 0:
        raise GoldenMeanKernelError("internal residue representative must be non-negative")
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def accelerated_parity_residue(bits: str) -> tuple[int, int]:
    """Return the unique residue modulo 2**len(bits) with this T-parity vector."""
    bits = _require_binary_word(bits)
    residue = 0
    modulus = 1
    for index, symbol in enumerate(bits):
        wanted = int(symbol)
        good: list[int] = []
        for candidate in (residue, residue + modulus):
            x = candidate
            for _ in range(index):
                x = _accelerated_step_nonnegative(x)
            if (x & 1) == wanted:
                good.append(candidate)
        if len(good) != 1:
            raise AssertionError("accelerated parity-vector bijection failed")
        residue = good[0]
        modulus *= 2
    return residue, modulus


def positive_integer_witness_for_admissible_word(word: str) -> int:
    """Construct a positive integer whose unreduced Collatz prefix is ``word``.

    The exact no-11 C-language is parsed into accelerated-map blocks 0 and 10.
    A terminal 1 is completed by an auxiliary 0 only for witness construction.
    """
    word = _require_binary_word(word, admissible=True)
    extended = word + "0" if word.endswith("1") else word
    accelerated_bits: list[str] = []
    i = 0
    while i < len(extended):
        if extended[i] == "0":
            accelerated_bits.append("0")
            i += 1
        else:
            if i + 1 >= len(extended) or extended[i + 1] != "0":
                raise AssertionError("admissible C word failed 0/10 parsing")
            accelerated_bits.append("1")
            i += 2
    residue, modulus = accelerated_parity_residue("".join(accelerated_bits))
    witness = residue if residue > 0 else modulus
    if collatz_parity_prefix(witness, len(word)) != word:
        raise AssertionError("constructed witness does not realize requested C prefix")
    return witness


def coding_fraction(word: str) -> Fraction:
    """Finite golden-mean coding with an implicit all-zero tail."""
    word = _require_binary_word(word, admissible=True)
    value = Fraction(0, 1)
    for k, bit in enumerate(word):
        if bit == "1":
            value += Fraction(1, 2 ** (k + 1))
    return value


def doubling_map(q: Fraction) -> Fraction:
    if not isinstance(q, Fraction):
        raise GoldenMeanKernelError("q must be fractions.Fraction")
    if q < 0 or q >= 1:
        raise GoldenMeanKernelError("q must lie in [0,1)")
    doubled = 2 * q
    return doubled - (doubled.numerator // doubled.denominator)


def finite_shift_conjugacy_holds(word: str) -> bool:
    word = _require_binary_word(word, admissible=True)
    if not word:
        return True
    return doubling_map(coding_fraction(word)) == coding_fraction(word[1:])


def golden_mean_branch_0(x: Fraction) -> Fraction:
    if not isinstance(x, Fraction):
        raise GoldenMeanKernelError("x must be fractions.Fraction")
    return x / 2


def golden_mean_branch_10(x: Fraction) -> Fraction:
    if not isinstance(x, Fraction):
        raise GoldenMeanKernelError("x must be fractions.Fraction")
    return Fraction(1, 2) + x / 4


def transfer_matrix() -> tuple[tuple[int, int], tuple[int, int]]:
    return ((1, 1), (1, 0))


def transfer_power(n: int) -> tuple[tuple[int, int], tuple[int, int]]:
    n = _require_nonnegative_int(n, "n")
    if n == 0:
        return ((1, 0), (0, 1))
    return ((fibonacci(n + 1), fibonacci(n)), (fibonacci(n), fibonacci(n - 1)))


def topological_entropy() -> float:
    return log(PHI)


def hausdorff_dimension() -> float:
    return log(PHI) / log(2.0)


def parry_transition_matrix() -> tuple[tuple[float, float], tuple[float, float]]:
    return ((PHI ** -1, PHI ** -2), (1.0, 0.0))


def parry_stationary_distribution() -> tuple[float, float]:
    denominator = PHI * PHI + 1.0
    return (PHI * PHI / denominator, 1.0 / denominator)


def pressure(s: float) -> float:
    if not isinstance(s, (int, float)) or not isfinite(float(s)):
        raise GoldenMeanKernelError("s must be finite")
    return log(PHI) - float(s) * log(2.0)


def pressure_slope() -> float:
    return -log(2.0)


def weighted_transfer_matrix(s: float) -> tuple[tuple[float, float], tuple[float, float]]:
    if not isinstance(s, (int, float)) or not isfinite(float(s)):
        raise GoldenMeanKernelError("s must be finite")
    q = 2.0 ** (-float(s))
    return ((q, q), (q, 0.0))


def critical_dimension() -> float:
    return hausdorff_dimension()


def weighted_positive_pole(s: float) -> float:
    if not isinstance(s, (int, float)) or not isfinite(float(s)):
        raise GoldenMeanKernelError("s must be finite")
    return (2.0 ** float(s)) / PHI


def mobius(n: int) -> int:
    n = _require_positive_int(n, "n")
    m = n
    prime_count = 0
    p = 2
    while p * p <= m:
        if m % p == 0:
            m //= p
            prime_count += 1
            if m % p == 0:
                return 0
        p = 3 if p == 2 else p + 2
    if m > 1:
        prime_count += 1
    return -1 if prime_count % 2 else 1


def divisors(n: int) -> tuple[int, ...]:
    n = _require_positive_int(n, "n")
    low: list[int] = []
    high: list[int] = []
    for d in range(1, isqrt(n) + 1):
        if n % d == 0:
            low.append(d)
            if d * d != n:
                high.append(n // d)
    return tuple(low + list(reversed(high)))


def fixed_point_count(period: int) -> int:
    period = _require_positive_int(period, "period")
    return lucas(period)


def exact_period_point_count(period: int) -> int:
    period = _require_positive_int(period, "period")
    return sum(mobius(period // d) * fixed_point_count(d) for d in divisors(period))


def primitive_orbit_count(period: int) -> int:
    period = _require_positive_int(period, "period")
    points = exact_period_point_count(period)
    quotient, remainder = divmod(points, period)
    if remainder != 0 or quotient < 0:
        raise AssertionError("primitive-orbit multiplicity is not a non-negative integer")
    return quotient


def artin_mazur_series_coefficients(max_degree: int) -> tuple[int, ...]:
    """Coefficients of 1/(1-z-z^2) through z**max_degree."""
    max_degree = _require_nonnegative_int(max_degree, "max_degree")
    return tuple(fibonacci(n + 1) for n in range(max_degree + 1))


def orbit_euler_product_coefficients(max_degree: int) -> tuple[int, ...]:
    """Expand prod_{m<=N}(1-z^m)^(-O_m) exactly through degree N."""
    max_degree = _require_nonnegative_int(max_degree, "max_degree")
    coeff = [1] + [0] * max_degree
    for m in range(1, max_degree + 1):
        multiplicity = primitive_orbit_count(m)
        if multiplicity == 0:
            continue
        factor = [0] * (max_degree + 1)
        for j in range(0, max_degree // m + 1):
            factor[j * m] = comb(multiplicity + j - 1, j)
        updated = [0] * (max_degree + 1)
        for i, left in enumerate(coeff):
            if left == 0:
                continue
            for j, right in enumerate(factor):
                if right == 0 or i + j > max_degree:
                    continue
                updated[i + j] += left * right
        coeff = updated
    return tuple(coeff)


def finite_euler_product_matches_zeta(max_degree: int) -> bool:
    max_degree = _require_nonnegative_int(max_degree, "max_degree")
    return orbit_euler_product_coefficients(max_degree) == artin_mazur_series_coefficients(max_degree)


def artin_mazur_zeta(z: float) -> float:
    if not isinstance(z, (int, float)) or not isfinite(float(z)):
        raise GoldenMeanKernelError("z must be finite")
    z = float(z)
    denominator = 1.0 - z - z * z
    if denominator == 0.0:
        raise GoldenMeanKernelError("z is a pole of the Artin-Mazur zeta function")
    return 1.0 / denominator


def weighted_artin_mazur_zeta(z: float, s: float) -> float:
    if not isinstance(z, (int, float)) or not isfinite(float(z)):
        raise GoldenMeanKernelError("z must be finite")
    if not isinstance(s, (int, float)) or not isfinite(float(s)):
        raise GoldenMeanKernelError("s must be finite")
    z = float(z)
    q = 2.0 ** (-float(s))
    denominator = 1.0 - q * z - q * q * z * z
    if denominator == 0.0:
        raise GoldenMeanKernelError("z is a pole of the weighted dynamical zeta function")
    return 1.0 / denominator
