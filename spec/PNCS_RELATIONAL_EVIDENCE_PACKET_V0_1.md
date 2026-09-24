# PNCS Relational Evidence Packet v0.1

Status: `TYPED_DIAGNOSTIC_TRANSPORT / NON_PROMOTING / SOURCE_SELECTION_FORBIDDEN`

This contract carries a GREMLIN cross-modal evidence result through PNCS without conflating it with the separate observational tuple packet.

## 1. Upstream diagnostic object

Accepted upstream schema:

[
oxed{	exttt{GREMLIN_CROSS_MODAL_RELATIONAL_EVIDENCE_PACKET_V0_1}}
]

from:

https://github.com/AdrianLipa90/GREMLIN/pull/88

The object may contain:
- channel residuals and uncertainties;
- covariance-weighted consistency metadata;
- phase-identifiability state;
- known-sector independence/circular-fit flags;
- source-attribution admissibility as a routing gate.

It must not contain a selected physical source.

## 2. Separation from observation packet

PNCS now treats two distinct typed objects:

[
	exttt{PNCS_RELATIONAL_OBSERVATION_PACKET_V0_1}
]

for measured/derived observables, and

[
	exttt{PNCS_RELATIONAL_EVIDENCE_PACKET_V0_1}
]

for a cross-modal diagnostic result.

They are not interchangeable and neither is flattened into canonical T36.

## 3. Required invariants

The evidence packet requires:

- `physical_source_selected=false`;
- `flatten_into_t36=false`;
- `semantic_holonomy_equivalence=OPEN`;
- exact GREMLIN upstream commit and receipt;
- consistency state in
  [
  {	exttt{CONSISTENT},	exttt{INCONSISTENT},	exttt{UNDERDETERMINED}};
  ]
- `source_attribution_admissible` retained as a candidate routing permission only.

A value of `source_attribution_admissible=true` does not mean that PNCS may choose a source. It means only that the upstream GREMLIN diagnostic did not block downstream source-specific testing.

## 4. Execution behavior

PNCS may:
- validate and transport the diagnostic;
- persist its provenance;
- route it to a source-specific candidate test;
- stop a route when the state is `INCONSISTENT` or `UNDERDETERMINED`.

PNCS may not:
- select (U_I), holonomy, condensate, gravity, or any other physical origin;
- rewrite the evidence state;
- use successful software validation as scientific promotion;
- inject any diagnostic field into T36.

## 5. Routing semantics

A conservative routing rule is:

[
	exttt{INCONSISTENT}
Rightarrow
	exttt{STOP_DECLARED_MODEL},
]

[
	exttt{UNDERDETERMINED}
Rightarrow
	exttt{REQUEST_MORE_CONSTRAINTS},
]

[
	exttt{CONSISTENT}
land
	exttt{source_attribution_admissible=false}
Rightarrow
	exttt{NO_SOURCE_ROUTE},
]

[
	exttt{CONSISTENT}
land
	exttt{source_attribution_admissible=true}
Rightarrow
	exttt{ALLOW_CANDIDATE_SOURCE_TESTS}.
]

The final branch still remains candidate-only.

## 6. Cross-repository links

- FPDG: https://github.com/AdrianLipa90/Fundamental-Physics-Dependency-Graph/pull/22
- GREMLIN: https://github.com/AdrianLipa90/GREMLIN/pull/88
- PNCS observation packet: https://github.com/AdrianLipa90/PhaseNav-Natural-Coding-System/pull/70
- noema-phasenav-core: https://github.com/AdrianLipa90/noema-phasenav-core/pull/35
- PhaseNav Telescope: https://github.com/AdrianLipa90/PhaseNav-Telescope-Spectral-Modulation/pull/24

## 7. Epistemic firewall

The packet is an orchestration/evidence object only.

It does not establish:

[
W_{m chem}=W_{m sem},
qquad
U_I	ext{ physical},
qquad
Phi_{m phase}Rightarrow g_{mu
u},
qquad
	ext{BEC physical carrier}.
]
