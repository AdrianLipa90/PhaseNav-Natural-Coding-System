from __future__ import annotations

from dataclasses import dataclass
import cmath
import hashlib
import json
import math
from typing import Iterable, Mapping, Sequence


class PrimeTemporalV01Error(ValueError):
    pass


REGISTRY_SCHEMA = "PNCS_PRIME_TEMPORAL_SPECTRAL_REGISTRY_V0_1"
OBSERVABLE_SCHEMA = "PNCS_TEMPORAL_HYDRO_OBSERVABLE_V0_1"
CONTRACT_ID = "PHASENAV_PRIME_TEMPORAL_HYDRO_V0_1"


def _require_int(n: object, field: str = "n") -> int:
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise PrimeTemporalV01Error(f"{field} must be a positive integer")
    return n


def _require_finite(x: object, field: str) -> float:
    try:
        value = float(x)
    except (TypeError, ValueError) as exc:
        raise PrimeTemporalV01Error(f"{field} must be finite") from exc
    if not math.isfinite(value):
        raise PrimeTemporalV01Error(f"{field} must be finite")
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _typed_id(prefix: str, payload: object) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def shortcut_collatz(n: int) -> int:
    n = _require_int(n)
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def prime_valuation(n: int, *, max_integer_bits: int = 4096) -> tuple[tuple[int, int], ...]:
    n = _require_int(n)
    if isinstance(max_integer_bits, bool) or not isinstance(max_integer_bits, int) or max_integer_bits < 1:
        raise PrimeTemporalV01Error("max_integer_bits must be a positive integer")
    if n.bit_length() > max_integer_bits:
        raise PrimeTemporalV01Error("integer exceeds declared factorization bound")

    value = n
    factors: list[tuple[int, int]] = []
    exponent = 0
    while value % 2 == 0:
        value //= 2
        exponent += 1
    if exponent:
        factors.append((2, exponent))

    p = 3
    while p * p <= value:
        exponent = 0
        while value % p == 0:
            value //= p
            exponent += 1
        if exponent:
            factors.append((p, exponent))
        p += 2
    if value > 1:
        factors.append((value, 1))
    return tuple(factors)


def valuation_mapping(n: int, *, max_integer_bits: int = 4096) -> dict[int, int]:
    return dict(prime_valuation(n, max_integer_bits=max_integer_bits))


def prime_flux(n: int, next_n: int | None = None, *, max_integer_bits: int = 4096) -> tuple[tuple[int, int], ...]:
    n = _require_int(n)
    target = shortcut_collatz(n) if next_n is None else _require_int(next_n, "next_n")
    if target != shortcut_collatz(n):
        raise PrimeTemporalV01Error("next_n is not the exact shortcut-Collatz successor")

    before = valuation_mapping(n, max_integer_bits=max_integer_bits)
    after = valuation_mapping(target, max_integer_bits=max_integer_bits)
    primes = sorted(set(before) | set(after))
    return tuple((p, after.get(p, 0) - before.get(p, 0)) for p in primes if after.get(p, 0) != before.get(p, 0))


def flux_log_scale(flux: Sequence[tuple[int, int]]) -> float:
    total = 0.0
    seen: set[int] = set()
    for prime, delta in flux:
        prime = _require_int(prime, "prime")
        if prime in seen:
            raise PrimeTemporalV01Error("duplicate prime channel")
        seen.add(prime)
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise PrimeTemporalV01Error("valuation delta must be an integer")
        total += delta * math.log(prime)
    return total


def orbit_prime_flux(start_n: int, steps: int, *, max_integer_bits: int = 4096) -> tuple[tuple[int, int], ...]:
    n = _require_int(start_n, "start_n")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise PrimeTemporalV01Error("steps must be a non-negative integer")
    start = valuation_mapping(n, max_integer_bits=max_integer_bits)
    current = n
    for _ in range(steps):
        current = shortcut_collatz(current)
        if current.bit_length() > max_integer_bits:
            raise PrimeTemporalV01Error("orbit integer exceeds declared bound")
    end = valuation_mapping(current, max_integer_bits=max_integer_bits)
    primes = sorted(set(start) | set(end))
    return tuple((p, end.get(p, 0) - start.get(p, 0)) for p in primes if end.get(p, 0) != start.get(p, 0))


def odd_branch_support_disjoint(n: int, *, max_integer_bits: int = 4096) -> bool:
    n = _require_int(n)
    if n % 2 == 0:
        raise PrimeTemporalV01Error("odd branch requires an odd source integer")
    nxt = shortcut_collatz(n)
    a = {p for p, _ in prime_valuation(n, max_integer_bits=max_integer_bits)}
    b = {p for p, _ in prime_valuation(nxt, max_integer_bits=max_integer_bits)}
    return a.isdisjoint(b) and math.gcd(n, nxt) == 1


def critical_line_prime_factor(prime: int, delta_v: int, tau: float) -> complex:
    prime = _require_int(prime, "prime")
    if isinstance(delta_v, bool) or not isinstance(delta_v, int):
        raise PrimeTemporalV01Error("delta_v must be an integer")
    tau = _require_finite(tau, "tau")
    return (prime ** (-0.5 * delta_v)) * cmath.exp(-1j * tau * delta_v * math.log(prime))


@dataclass(frozen=True)
class SpectralRegistry:
    registry_kind: str
    frequencies: tuple[float, ...]
    labels: tuple[str, ...]
    source_id: str
    omega_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.registry_kind not in {"PRIME_LOG", "ZETA_ZERO", "EXPLICIT"}:
            raise PrimeTemporalV01Error("unsupported spectral registry kind")
        if not self.source_id:
            raise PrimeTemporalV01Error("source_id is required")
        scale = _require_finite(self.omega_scale, "omega_scale")
        if scale <= 0.0:
            raise PrimeTemporalV01Error("omega_scale must be positive")
        object.__setattr__(self, "omega_scale", scale)
        if not self.frequencies or len(self.frequencies) != len(self.labels):
            raise PrimeTemporalV01Error("frequency and label registries must be non-empty and aligned")
        freqs = tuple(_require_finite(x, "frequency") for x in self.frequencies)
        if any(x < 0.0 for x in freqs):
            raise PrimeTemporalV01Error("frequencies must be non-negative")
        if len(set(self.labels)) != len(self.labels) or any(not x for x in self.labels):
            raise PrimeTemporalV01Error("labels must be unique non-empty strings")
        object.__setattr__(self, "frequencies", freqs)

    @classmethod
    def from_primes(cls, primes: Iterable[int], *, omega_scale: float, source_id: str) -> "SpectralRegistry":
        ordered = tuple(_require_int(p, "prime") for p in primes)
        if len(set(ordered)) != len(ordered):
            raise PrimeTemporalV01Error("prime registry contains duplicates")
        return cls(
            registry_kind="PRIME_LOG",
            frequencies=tuple(math.log(p) for p in ordered),
            labels=tuple(f"p:{p}" for p in ordered),
            source_id=source_id,
            omega_scale=omega_scale,
        )

    @property
    def angular_frequencies(self) -> tuple[float, ...]:
        return tuple(self.omega_scale * x for x in self.frequencies)

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": REGISTRY_SCHEMA,
            "contract_id": CONTRACT_ID,
            "registry_kind": self.registry_kind,
            "frequencies": list(self.frequencies),
            "labels": list(self.labels),
            "source_id": self.source_id,
            "omega_scale": self.omega_scale,
        }

    @property
    def registry_id(self) -> str:
        return _typed_id("pncs:prime-temporal-registry", self.payload)


@dataclass(frozen=True)
class TemporalSpectrum:
    registry: SpectralRegistry
    probabilities: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.registry, SpectralRegistry):
            raise PrimeTemporalV01Error("SpectralRegistry required")
        if len(self.probabilities) != len(self.registry.frequencies):
            raise PrimeTemporalV01Error("probability count must equal registry dimension")
        probs = tuple(_require_finite(x, "probability") for x in self.probabilities)
        if any(x < 0.0 for x in probs):
            raise PrimeTemporalV01Error("probabilities must be non-negative")
        total = sum(probs)
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise PrimeTemporalV01Error("probabilities must sum to one")
        object.__setattr__(self, "probabilities", probs)

    def coherence(self, t: float) -> float:
        t = _require_finite(t, "t")
        phases = (
            p * cmath.exp(-1j * omega * t)
            for p, omega in zip(self.probabilities, self.registry.angular_frequencies)
        )
        value = abs(sum(phases, 0j))
        return min(1.0, max(0.0, float(value)))

    def fuzziness(self, t: float) -> float:
        c = self.coherence(t)
        return min(1.0, max(0.0, 1.0 - c * c))

    def phase_speed(self) -> float:
        omegas = self.registry.angular_frequencies
        mean = sum(p * w for p, w in zip(self.probabilities, omegas))
        var = sum(p * (w - mean) ** 2 for p, w in zip(self.probabilities, omegas))
        return math.sqrt(max(0.0, var))

    def energy_spread(self, *, hbar: float = 1.0) -> float:
        hbar = _require_finite(hbar, "hbar")
        if hbar <= 0.0:
            raise PrimeTemporalV01Error("hbar must be positive")
        return hbar * self.phase_speed()


def fs_population_speed(probabilities: Sequence[float], probability_rates: Sequence[float]) -> float:
    if len(probabilities) != len(probability_rates) or not probabilities:
        raise PrimeTemporalV01Error("population vectors must be non-empty and aligned")
    total = 0.0
    rate_sum = 0.0
    for p_raw, dp_raw in zip(probabilities, probability_rates):
        p = _require_finite(p_raw, "probability")
        dp = _require_finite(dp_raw, "probability_rate")
        if p < 0.0:
            raise PrimeTemporalV01Error("probability must be non-negative")
        if p == 0.0:
            if dp != 0.0:
                raise PrimeTemporalV01Error("nonzero probability flow through a zero-probability channel is singular")
            continue
        total += 0.25 * dp * dp / p
        rate_sum += dp
    if not math.isclose(rate_sum, 0.0, rel_tol=0.0, abs_tol=1e-12):
        raise PrimeTemporalV01Error("probability rates must conserve normalization")
    return math.sqrt(max(0.0, total))


def fs_temporal_speed(
    spectrum: TemporalSpectrum,
    *,
    probability_rates: Sequence[float] | None = None,
) -> float:
    phase_sq = spectrum.phase_speed() ** 2
    population_sq = 0.0
    if probability_rates is not None:
        population_sq = fs_population_speed(spectrum.probabilities, probability_rates) ** 2
    return math.sqrt(phase_sq + population_sq)


def advance_continuity(previous: float, temporal_speed: float, delta_t: float) -> float:
    previous = _require_finite(previous, "previous")
    temporal_speed = _require_finite(temporal_speed, "temporal_speed")
    delta_t = _require_finite(delta_t, "delta_t")
    if previous < 0.0 or temporal_speed < 0.0 or delta_t < 0.0:
        raise PrimeTemporalV01Error("continuity arguments must be non-negative")
    return previous + temporal_speed * delta_t


def t36_temporal_pairs(
    frequencies: Sequence[float],
    *,
    t: float,
    center_phase: float,
) -> tuple[float, ...]:
    if len(frequencies) != 18:
        raise PrimeTemporalV01Error("T36 projection requires exactly 18 frequencies")
    t = _require_finite(t, "t")
    center = _require_finite(center_phase, "center_phase")
    tau = math.tau
    out: list[float] = []
    for raw in frequencies:
        omega = _require_finite(raw, "frequency")
        if omega < 0.0:
            raise PrimeTemporalV01Error("frequency must be non-negative")
        out.append((center - omega * t) % tau)
        out.append((center + omega * t) % tau)
    return tuple(out)


@dataclass(frozen=True)
class TemporalHydroObservable:
    registry_id: str
    coherence: float
    fuzziness: float
    temporal_speed: float
    continuity_length: float
    t36_realization_id: str | None = None
    routing_feedback_opened: bool = False
    external_effects: bool = False
    semantic_identity_modified: bool = False
    laboratory_time_modified: bool = False

    def __post_init__(self) -> None:
        if not self.registry_id.startswith("pncs:prime-temporal-registry:sha256:"):
            raise PrimeTemporalV01Error("invalid registry_id")
        for field in ("coherence", "fuzziness", "temporal_speed", "continuity_length"):
            value = _require_finite(getattr(self, field), field)
            object.__setattr__(self, field, value)
        if not (0.0 <= self.coherence <= 1.0 and 0.0 <= self.fuzziness <= 1.0):
            raise PrimeTemporalV01Error("coherence/fuzziness must be in [0,1]")
        if self.temporal_speed < 0.0 or self.continuity_length < 0.0:
            raise PrimeTemporalV01Error("temporal speed and continuity length must be non-negative")
        if any((
            self.routing_feedback_opened,
            self.external_effects,
            self.semantic_identity_modified,
            self.laboratory_time_modified,
        )):
            raise PrimeTemporalV01Error("experimental temporal observable cannot open authority or physical-time claims")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": OBSERVABLE_SCHEMA,
            "contract_id": CONTRACT_ID,
            "registry_id": self.registry_id,
            "coherence": self.coherence,
            "fuzziness": self.fuzziness,
            "temporal_speed": self.temporal_speed,
            "continuity_length": self.continuity_length,
            "t36_realization_id": self.t36_realization_id,
            "routing_feedback_opened": False,
            "external_effects": False,
            "semantic_identity_modified": False,
            "laboratory_time_modified": False,
            "static_runtime_fallback": False,
            "scientific_promotion": False,
        }

    @property
    def observable_id(self) -> str:
        return _typed_id("pncs:temporal-hydro-observable", self.payload)


def make_temporal_hydro_observable(
    spectrum: TemporalSpectrum,
    *,
    t: float,
    previous_continuity: float,
    delta_t: float,
    probability_rates: Sequence[float] | None = None,
    t36_realization_id: str | None = None,
) -> TemporalHydroObservable:
    speed = fs_temporal_speed(spectrum, probability_rates=probability_rates)
    continuity = advance_continuity(previous_continuity, speed, delta_t)
    return TemporalHydroObservable(
        registry_id=spectrum.registry.registry_id,
        coherence=spectrum.coherence(t),
        fuzziness=spectrum.fuzziness(t),
        temporal_speed=speed,
        continuity_length=continuity,
        t36_realization_id=t36_realization_id,
    )
