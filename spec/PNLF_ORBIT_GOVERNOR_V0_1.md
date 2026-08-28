# PNLF Orbital Memory Governor v0.1

Status: CANDIDATE
Contract: `PNLF_ORBIT_GOVERNOR_V0_1`
Depends on: `PNLF_ORBITAL_MEMORY_V0_1`

## 1. Governing principle

PNLF does not assign memory orbit by a free weighted priority score.

The runtime dynamics produces a memory phase and attractor phase. Their circular phase distance is the orbital coordinate:

```text
r_phase = d_S1(phi_memory, phi_attractor) in [0, pi]
```

A declared quantizer maps that coordinate into one of nine discrete orbital bands:

```text
orbital_band = Q(r_phase) in {O0,...,O8}
```

The quantizer classifies geometry. It does not itself admit a stable memory update.

## 2. Proper-time provenance

The current PNCS OrchOrbital contract already defines subjective/proper time through an explicit kernel:

```text
Delta_tau_i = Delta_t * g(r_i, C_i, Delta_i, m_i, A_i)
```

PNLF stores the resulting `proper_time` and binds it to `proper_time_model_id`. PNLF does not infer or recalibrate the time kernel from persisted memory data.

Winding is accumulated from the admitted phase trajectory and proper-time binding. Wall-clock time is provenance only; it is not the primary orbital ageing coordinate.

## 3. Neutral phase quantizer profile

Candidate profile:

```text
orbit_quantizer_id = PNLF_PHASE9_UNIFORM_V0_1
```

Define:

```text
u = clamp(r_phase / pi, 0, 1)
q = min(8, floor(9*u))
orbital_band = Oq
```

Therefore:

- `O0` is nearest the attractor;
- `O8` is farthest from the attractor;
- the mapping contains no semantic-score coefficients;
- the same `r_phase` always maps to the same band.

The exact endpoint `r_phase = pi` maps to `O8`.

## 4. CIEL compatibility quantizer

Existing CIEL orbital-shell data MAY use an explicit compatibility profile, for example:

```text
CIEL_ORBITAL_SHELL_COMPAT_V1
```

That profile may reproduce the historical shell mapping and its historical parameters. Those parameters remain properties of the compatibility profile and are not PNLF container invariants.

## 5. Transition candidate

For an admitted checkpoint `S_i` on `O_i`, runtime evolution creates a liminal trajectory:

```text
S_i -> Lambda(tau)
```

At each liminal revision the runtime may compute a candidate orbital state:

```text
phi(tau)
r_phase(tau)
O_candidate(tau) = Q(r_phase(tau))
winding(tau)
proper_time(tau)
```

This candidate orbital state is Liminal Memory. It does not mutate `S_i`.

## 6. Admission rule

The existing PNCS reduction boundary remains the stable-memory gate:

```text
Omega = lambda1*C + lambda2*R(S,I) - lambda3*Delta - lambda4*Xi
reduce_ready = Omega >= Omega_crit
```

A new PNLF State Memory checkpoint requires:

1. an OPEN liminal segment;
2. continuous proper-time lineage to its `tau_cursor`;
3. an explicit reduction witness;
4. an explicit consolidation/holonomy witness required by policy;
5. a selected/candidate orbital state produced by the declared quantizer;
6. an admitted right checkpoint at exactly the current `tau_cursor`.

Without admission, the orbital candidate remains liminal.

## 7. Promotion and demotion

Let the source band index be `i` and the admitted target band index be `j`.

```text
j < i  -> PNLF.ORBIT_PROMOTE
j = i  -> PNLF.ORBIT_BIND / same-band update
j > i  -> PNLF.ORBIT_DEMOTE
```

Promotion and demotion are descriptions of the admitted geometric transition. They do not independently authorize the transition.

A change in orbital band always produces a new checkpoint through Liminal Memory. Prior checkpoint content remains immutable.

## 8. Recall

Recall is a new trajectory, not an in-place cache promotion.

```text
S_old -- Lambda_recall(tau) --> S_new
```

Procedure:

1. locate an admitted checkpoint using `(OBJECT_ID, tau, relation)` plus relational indexes;
2. materialize the required payload/relations into the live runtime surface;
3. open `PNLF.ORBIT_RECALL` Liminal Memory from `S_old`;
4. evolve under the current attractor and current proper-time binding;
5. quantize the current `r_phase` into `O_candidate`;
6. create `S_new` only after the reduction/consolidation boundary admits the trajectory.

The recalled checkpoint `S_old` is not mutated.

## 9. Functional M-layer participation

Orbital motion and M-layer participation are independent.

Examples:

```text
(M3, O7) -> (M3, O2)       semantic memory recalled toward active attractor
(M2,M3,O3) -> (M3,O1)      episodic+semantic liminal trajectory consolidates semantically
(M8,O1) -> (M8,O6)         audit record becomes less tightly bound without changing channel
```

An M-layer transition MAY occur during Liminal Memory, but it requires its own lineage evidence and is not implied by orbital motion.

## 10. Runtime residency is a projection

PNLF orbital bands are logical memory geometry. Runtime materialization is a separate policy projection.

Recommended projection vocabulary:

```text
LIVE      materialized on current live NOEMA/PhaseNav surface
HOT       immediately materializable from PNStore
WARM      indexed durable material
COLD      durable archived material
```

No fixed `O_i -> residency` mapping is part of the PNLF core. A deployment profile may define one.

This preserves:

```text
logical orbital binding != physical extent location
```

and allows PNStore to migrate extents without changing memory semantics.

## 11. Hysteresis / orbit flapping

The quantizer MAY classify every liminal revision, but State Memory changes only at admitted reduction points. Therefore band-boundary jitter cannot by itself create persistent O_i <-> O_{i+1} flapping.

A deployment MAY add a geometric hysteresis margin around quantizer boundaries. Any such margin belongs to `orbit_quantizer_id` and must be explicit and deterministic.

## 12. PNV realization

The v0.1 PNLF transition verbs are RADICAL contracts composed from existing admitted PNV operators:

```text
PNLF.ORBIT_BIND
PNLF.LIMINAL_ENTER
PNLF.LIMINAL_ADVANCE
PNLF.STATE_COMMIT
PNLF.STATE_SUPERSEDE
PNLF.ORBIT_PROMOTE
PNLF.ORBIT_DEMOTE
PNLF.ORBIT_RECALL
```

No new native PNV opcode is required for the v0.1 governor.

## 13. GREMLIN boundary

GREMLIN may propose:

- a relation that changes the current attractor coupling;
- a candidate recall path;
- a candidate M-layer participation change;
- KAKU/RADICAL/OPERATOR representations of the transition.

GREMLIN output enters Liminal Memory as a candidate. It carries no independent runtime execution authority and no canon-write authority. Promotion into State Memory remains controlled by the admitted reduction/consolidation boundary.
