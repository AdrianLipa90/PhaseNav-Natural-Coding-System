# PNCS GREMLIN NOEMA↔QHTRI Isomorphism Bank v0.1

Status: `ARCHITECTURE_CANDIDATE / RELATIONAL_ISOMORPHISM_BANK_DERIVED`

GREMLIN role: `CANDIDATE_ONLY / CHYBA`.

## 1. Purpose

This bank is a source-pinned set of structural isomorphism candidates used to write and audit the NOEMA↔QHTRI hardware-semantic architecture.

Each bank entry is independent. Each preserves one declared invariant and compiles through the existing GREMLIN path

```text
RELATIONAL_ISOMORPHISM
 -> KAKU candidates
 -> RADICAL candidate
 -> OPERATORS candidates
 -> READ_ONLY PNV conformance graph
```

Runtime authority and canon-write authority remain outside GREMLIN candidate generation.

## 2. Fundamental source pins

| Bank | Repository | Commit |
|---|---|---|
| TIR | `AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations` | `26bd867c10b6f6e21b54f2a4dc7b2f49df62907a` |
| IDT | `AdrianLipa90/Informational-Dynamics-of-Time` | `3ac1f53af5223d16f8818dba99a63a6af2ba9498` |
| RFC | `AdrianLipa90/Relational-Field-Closure` | `3ebd7761ccfa70858ab8af1933c2208a82260f9d` |
| SOH | `AdrianLipa90/secret-of-a-half` | `4cf36453ee2b6d33a1f9177ca324b9ef491270be` |

A source-pin change creates a new bank generation and requires fresh compilation receipts.

## 3. Target loop

The bank supports the architecture candidate

\[
\boxed{
QHTRI_{GPU}
\rightarrow BIFURCATION
\rightarrow NOEMA_{CPU}
\rightarrow SEMANTIC\ PATH
\rightarrow STATE\ MEMORY/PNFS
\rightarrow ADMITTED\ OPERATOR
\rightarrow QHTRI_{GPU}.
}
\]

The GPU side carries resident endogenous phase dynamics. The CPU/NOEMA side carries relational interpretation, provenance, admission and memory crystallization.

## 4. Bank entries

### ISO.NQ.01 — CP1/Berry source geometry → QHTRI resident phase potential

Sources:
- TIR `TIR/integration/TIR_IDT_INFORMATION_AREA_CURVATURE_V0_1.md`
- SOH `monograph/chapters/06_bloch_and_spinorial_phase.tex`

Preserved structure:
- CP1 state typing;
- Fubini–Study orientation;
- Berry orientation/holonomy witness.

Hardware realization receives an independent implementation receipt.

### ISO.NQ.02 — IDT NOW/bifurcation → NOEMA↔QHTRI branch receipt

Sources:
- IDT `formalism/04A_now_bifurcation_hyperbolic_coordinates.md`
- IDT `formalism/04_causal_bifurcation.md`

The typed source decomposition is

\[
(\mathfrak a,\mathfrak j)\longleftrightarrow(M,\beta),
\]

with current reversal

\[
M\mapsto M,
\qquad
\beta\mapsto-\beta,
\qquad
B_\phi(-\beta)=B_\phi(\beta)^\dagger.
\]

The branch receipt therefore carries magnitude/admission and signed orientation as separate fields.

### ISO.NQ.03 — CP1 branch → Poincaré semantic anchor

Sources:
- RFC `formalism/RF03_EULER_BERRY_REALITY_AND_POINCARE_GATE.md`
- TIR Stage-5 Poincaré/Z2 validation
- TIR Poincaré appendix

The edge is typed `MAPS_TO`.

The adapter preserves separate contracts for:
- source CP1/Fubini–Study geometry;
- target Poincaré geometry;
- dimension;
- curvature sign;
- holonomy;
- declared projective invariants.

This gives an auditable continuation/bifurcation map rather than collapsing the two metric structures into one field.

### ISO.NQ.04 — SU(2) double cover → Z2 sheet witness

Sources:
- SOH `research/SOH_G013_PAULI_SPINOR_LIFT_V0_1.md`
- TIR Stage-5 Poincaré/Z2 validation

A spinorial handoff is represented by

\[
\boxed{(z,\zeta),\qquad z\in\mathbb D,\;\zeta\in Z_2.}
\]

The projective coordinate and the sheet/parity witness are jointly carried in provenance. Spinorial lineage admission requires the declared sheet witness.

### ISO.NQ.05 — directed affinity → semantic traversal orientation

Source: IDT `formalism/00B_transition_affinity.md`.

Preserved structure:
- antisymmetry under edge reversal;
- ordered-cycle direction;
- separate state-content and transition-orientation types.

### ISO.NQ.06 — memory orbit → ordered meaning path

Sources:
- IDT `formalism/00D_memory_orbit_drive.md`
- IDT `formalism/06C_kahler_memory_frame_cp1.md`

Candidate semantic path:

\[
\Gamma=(z_0,\zeta_0,R_1,K_1,z_1,\ldots),
\qquad
M=\mathfrak M(\Gamma).
\]

The invariant is ordered relational content: path order, orientation and local Kähler-frame displacement remain attached to the meaning receipt.

### ISO.NQ.07 — oriented RFC holonomy → branch-channel witness

Source: RFC `formalism/RFL1_RELATIONAL_LAMBDA_ORIENTED_HOLONOMY.md`.

The source carrier

\[
h_R=e^{i\tau_R}
\]

and complementary channels

\[
C_h=\cos^2(\tau_R/2),
\qquad
D_h=\sin^2(\tau_R/2)
\]

provide a branch-channel grammar. Orientation reversal preserves the magnitude channel and reverses the signed quadrature. Probability semantics require a separately declared normalized admission contract.

### ISO.NQ.08 — coframe gluing/holonomy → QHTRI cell relation transport

Source: RFC `formalism/RF02I_HEXAHEDRAL_COFRAME_CONNECTION.md`.

Preserved structure:
- local frame relation;
- ordered loop holonomy;
- conjugacy-level loop witness.

The current bank entry is a discrete transport candidate; continuum convergence is a separate validation gate.

### ISO.NQ.09 — memory persistence → State Memory / PNFS crystallization

Source: IDT `formalism/06D_memory_persistence_recall.md`.

Preserved structure:
- append-only event order;
- receipt lineage;
- model/version interpretation identity;
- declared-class replay and recall data.

This entry joins the semantic loop to State Memory and PNFS checkpoint contracts.

### ISO.NQ.10 — oriented Hermitian exchange → NOEMA-authorized QHTRI feedback

Source: RFC `formalism/RFL1A_HERMITIAN_ORIENTED_EXCHANGE_GATE.md`.

The source pattern is

\[
\Lambda_R
\rightarrow E_R
\rightarrow\tau_R
\rightarrow\mathcal J_R
\rightarrow H=H^\dagger
\rightarrow U(t).
\]

The architecture reuses the structural interface as

\[
M_t
\xrightarrow{NOEMA\ admission}
O_t
\xrightarrow{QHTRI\ boundary\ binding}
QHTRI_{t+1}.
\]

The operator receipt carries source commitments, the semantic-path commitment and the NOEMA/PNCAP admission token. Canon-write authority remains on the NOEMA/authority side of the boundary.

## 5. Hardware split inferred by the bank

The bank suggests a compact two-plane implementation contract.

### GPU / QHTRI resident plane

Responsible for:
- endogenous oscillator evolution;
- phase relations and native phase logic;
- local CP1/Bloch state;
- local bifurcation quantities;
- T36 whole-lane witness generation;
- compact event/branch receipt emission.

### CPU / NOEMA relational plane

Responsible for:
- branch receipt admission;
- CP1→Poincaré continuation receipt;
- Z2 sheet lineage;
- KAKU/RADICAL/OPERATORS semantic traversal;
- State Memory / PNFS crystallization;
- capability and effect admission;
- construction of the next QHTRI boundary/operator envelope.

The interface transfers commitments and typed invariants rather than copying the entire GPU resident state.

## 6. Cross-repository composition rule

A BioOS architecture receipt may reference a GREMLIN bank candidate only when it carries:

```text
bank_schema
bank_manifest_sha256
isomorphism_id
invariant_id
source repository pins
candidate compilation receipt sha256
```

A semantic-loop receipt additionally carries the exact ordered subset of bank entries used for that transition.

## 7. Promotion gates

A bank entry advances only through independent receipts appropriate to its layer:

1. source-pin integrity;
2. deterministic KAKU/RADICAL/OPERATORS compilation;
3. READ_ONLY conformance execution;
4. adapter-level invariant tests;
5. adversarial/tamper tests;
6. hardware binding tests where hardware is involved;
7. NOEMA/PNCAP authority check for any feedback path.

Until those receipts are attached, the bank remains `CANDIDATE_ONLY / CHYBA`.
