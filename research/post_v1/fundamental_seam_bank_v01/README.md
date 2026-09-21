# PNCS GREMLIN Fundamental Seam Bank v0.1

Status: `POST_V1_EXPERIMENTAL / CANDIDATE_ONLY / CHYBA / READ_ONLY`

Date: 2026-09-21

## Purpose

Reuse the existing PNCS canonical 36D relational graph and relational-isomorphism
compiler as the machine-readable carrier for the highest-leverage seams found by
the GREMLIN fundamental repository overlay.

This bank does **not** create a second dependency graph and does not promote any
source claim. FPDG remains the dependency/status authority; source repositories
remain theorem/physics authorities; GREMLIN remains the candidate-discovery and
audit layer.

The compilation path is the existing PNCS path:

```text
source claims
 -> reviewed relational seam
 -> KAKU nodes
 -> RADICAL
 -> relation OPERATORS
 -> native PNV READ_ONLY candidate
 -> conformance receipt
```

## Frozen source heads

| Bank | Repository | Commit |
|---|---|---|
| TIR | `AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations` | `f7b754347502f5051d423867f8a8d60627b1f8d7` |
| IDT | `AdrianLipa90/Informational-Dynamics-of-Time` | `2960a936e3f74b07a4bf30ebc5cb78b6c1811b4c` |
| RFC | `AdrianLipa90/Relational-Field-Closure` | `786d1e1a9f9c91a4c3174719ed76966aa73edcef` |
| SOH | `AdrianLipa90/secret-of-a-half` | `41772776dadf837c7a2f8b095b752e586d85c5dc` |
| Infinities | `AdrianLipa90/Infinities` | `c1ad8376f9dd4c2daf2c4ea0bf61568d718fd794` |

## FSI.01 — TIR SE(3) affine glue ↔ RFC rigid overlap cocycle

Class: `EXACT_CONDITIONAL`

TIR uses

[
G_{ba}=(R_{ba},t_{ba})in SE(3)
]

with composition

[
(R_2,t_2)(R_1,t_1)
=
(R_2R_1,R_2t_1+t_2).
]

RFC GSC4G uses

[
x_q=A_{qp}x_p+t_{qp}
]

with

[
A_{rp}=A_{rq}A_{qp},
qquad
t_{rp}=A_{rq}t_{qp}+t_{rq}.
]

Under the explicit convention map

[
R_{ba}leftrightarrow A_{qp},
qquad
t_{ba}leftrightarrow t_{qp},
]

the group law, inverse law, path composition and identity-loop closure are the
same (SE(3)) semidirect-product algebra.

Preserved invariant:

[
oxed{	ext{affine transport composition and loop identity closure}.}
]

Firewall: this crosswalk does not supply the production numeric overlap cocycle,
the production coframe, or a continuum curvature/torsion identification.

## FSI.02 — global cocycle / path-independence spine

Class: `STRONG_STRUCTURAL`

Three separately typed exact structures share one local-to-global pattern:

- IDT 05E: positive multiplicative clock cocycle, cycle product (=1), global
  positive potential;
- TIR: (SE(3))-valued transition composition and loop closure;
- RFC E25: coordinate and Lorentz-frame triple-overlap cocycles.

Common relational spine:

```text
local transition
 -> ordered composition
 -> closed-cycle / triple-overlap consistency
 -> path-independent global object
```

The groups and target objects are not identified. This entry preserves only the
typed cocycle/gluing grammar.

Firewall: clock ratios, affine (SE(3)) transport and Lorentz atlas transitions
remain distinct source-domain objects.

## FSI.03 — representation quotient / relational observable spine

Class: `STRONG_STRUCTURAL`

The existing PNCS XFI.05 already records the positive-ray / projective-(U(1))
quotient analogy. The present seam extends the family with current TIR/RFC
source objects:

- IDT: (Qsimlambda Q), (lambda>0), with normalized simplex shape retained;
- TIR: local-frame rephasing/gauge changes cancel in closed holonomy invariants;
- RFC GSC4F: one common global (SE(3)) action is quotiented while relative
  overlap geometry is retained.

Common spine:

[
oxed{
	ext{raw representation}
	o
	ext{declared group orbit}
	o
	ext{quotient/invariant relational data}.
}
]

Firewall: the quotient groups, metrics and physical interpretations remain
source-typed. No universal quotient theorem is claimed beyond the declared
instances.

## FSI.04 — accelerated Collatz block ↔ unreduced parity/phase shift

Class: `EXACT_CONDITIONAL`

For odd (n), Infinities defines

[
a(n)=v_2(3n+1),
qquad
U(n)=rac{3n+1}{2^{a(n)}}.
]

For the unreduced Collatz map

[
C(n)=
egin{cases}
n/2,&n	ext{ even},\
3n+1,&n	ext{ odd},
end{cases}
]

one accelerated odd step is exactly the unreduced block

[
oxed{U(n)=C^{a(n)+1}(n)}
]

and its parity word is

[
oxed{1,0^{a(n)}}.
]

IDT/TIR supply the parity phase relation

[
q_C(Cx)=2q_C(x)pmod1.
]

Therefore wherever (q_C) is defined,

[
oxed{
q_C(U(n))
=
2^{a(n)+1}q_C(n)
pmod1.
}
]

This is a local operator crosswalk. It does not imply global Collatz
convergence and does not identify Collatz iteration count with physical time.

## Machine contract

Every FSI entry is compiled through
`PNCS_GREMLIN_RELATIONAL_ISOMORPHISM_COMPILER_V0_1` with:

```text
EPISTEMIC CHYBA
MODE READ_ONLY
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
```

Unknown relation lowering, mixed 36D bases, malformed source bindings or
candidate-envelope mismatch fail closed.

## GREMLIN / Lean handoff

The intended later comparison is:

```text
PNCS/GREMLIN seam compiles
   + source claims retain exact typed premises
   -> submit exact mathematical core to Lean

Lean accepts without hidden axiom
   -> mathematical seam can be promoted independently

Lean requires an extra premise
   -> return that premise to GREMLIN/FPDG as an explicit gap

physical/source input
   -> remains a premise; Lean must not fabricate it
```

No RH, Collatz-conjecture, physical-(G), flavour, clock or QHTRI physical
binding is promoted by this bank.
