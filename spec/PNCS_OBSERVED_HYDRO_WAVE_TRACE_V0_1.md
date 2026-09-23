# PNCS Observed-Hydro Wave Trace Binding v0.1

Status: `CANDIDATE / READ_ONLY / EXACT_SOURCE_COMPONENT_BINDING / FROZEN_POST_OBSERVATION_AMPLITUDE_POLICY / NO_QHTRI_GRAPH_COEFFICIENT_DEPENDENCY`

## 1. Purpose

This gate binds one existing temporal-observation post-state to one existing
hydrodynamic (T^{36}) phase trace without introducing a QHTRI graph
Hamiltonian.

The composition is:

[
	ext{TemporalObservationReceipt}
	o
	ext{fixed post-observation amplitudes}
]

plus

[
	ext{PhaseFlowState36}
	o
	ext{HydrodynamicTrace}
	o
	heta(	au).
]

The output is a content-addressed candidate receipt proving that the two source
components share one exact initial (T^{36}) phase section and that the
hydrodynamic trajectory replays exactly.

## 2. Source contracts

Parent source commit:

`8855abed440e9949f576ffbe2153325f69e78963`

Reused contracts:

- `PNCS_TEMPORAL_GEOMETRY_V0_2`;
- `PNCS_HYDRODYNAMIC_PROPER_TIME_V0_27`.

No new phase equation, amplitude evolution equation, QHTRI coefficient or PNV
opcode is introduced.

## 3. Exact initial-section gate

The observation post-state carries the temporal conformal phase projection

[
	heta^{m obs}in T^{36}.
]

The hydrodynamic trace begins from

[
	heta^{m hydro}_0in T^{36}.
]

Admission requires exact component equality

[
oxed{
	heta^{m obs}
=
	heta^{m hydro}_0.
}
]

This is the current basis-binding mechanism.  The parent contracts do not
provide a separate shared `t36_basis_id`, so v0.1 does not invent one.

## 4. Hydrodynamic replay gate

The caller supplies the drive vector used to produce the source
`HydrodynamicTrace`.

v0.1 normalizes it by the parent rule and replays every hydrodynamic step from
the supplied initial state with the source gate carried by the trace.

Admission requires exact equality of:

- ordered step IDs;
- final phase-state ID;
- trace initial-state ID.

Thus a valid trace object paired with the wrong drive fails closed.

## 5. Amplitude policy

v0.1 admits exactly one amplitude policy:

[
oxed{
	exttt{FROZEN_POST_OBSERVATION}.
}
]

The normalized probability vector from
`TemporalObservationReceipt.after_state` remains fixed while the hydrodynamic
source evolves the phase coordinates.

This is a typed composition policy, not a claim that the current PNCS runtime
physically advects observation amplitudes in this way.

A future dynamic-amplitude policy requires its own source law and receipt.

## 6. Pair profile

For pair (j), with indices (L=2j), (R=2j+1), v0.1 exposes

[
q_j=p_L+p_R
]

and, for (q_j>0),

[
oxed{
u_j
=
rac{p_L-p_R}{p_L+p_R}.
}
]

Zero-support pairs fail closed.

No phase or Hamiltonian coefficient enters this profile.

## 7. Receipt identity

The candidate receipt commits:

- observation receipt ID;
- post-observation state ID;
- temporal projection ID;
- exact hydrodynamic initial-state ID;
- hydro trace ID;
- gate ID;
- drive digest;
- ordered hydro step IDs;
- start/end phase proper time;
- amplitude policy;
- post-observation probability digest;
- exact-initial-theta binding mode.

Authority remains:

`CHYBA / CANDIDATE_ONLY / runtime_execution_authority=false / canon_write_authority=false / state_memory_write_authority=false`.

## 8. Explicit firewall

This gate does not use or derive:

[
0.25,qquad0.7
]

from `qhtri_graph_hamiltonian()`.

It does not claim a predictive quantum Hamiltonian.

It only binds already-existing source observation data to an already-existing
source hydrodynamic phase trajectory.

## 9. Validation

Reference implementation:

`src/phasenav_natural_code/observed_hydro_wave_trace_v01.py`

Reference tests:

`tests/test_observed_hydro_wave_trace_v01.py`


## 10. Native pair transport witness

For a successfully replayed binding, v0.1 can evaluate a declared pair on two
ordered replay sections without introducing a graph Hamiltonian.

Let

[
u_j=rac{p_L-p_R}{p_L+p_R},
qquad
r_j=sqrt{1-u_j^2},
]

with probabilities fixed by the bound post-observation state.

For one replay state,

[
delta_j
=
operatorname{wrap}(	heta_R-	heta_L),
qquad
dotdelta_j
=
v_R-v_L.
]

The coefficient-free local connection vector is

[
oxed{
Omega_j
=
dotdelta_j
(-u_jr_jcosdelta_j,,-u_jr_jsindelta_j,,r_j^2).
}
]

For two ordered replay sections (a<b), the native witness reports

[
oxed{
W_{ab,j}
=
|Omega_{a,j}	imesOmega_{b,j}|.
}
]

The witness is typed as non-Abelian when (W_{ab,j}>0).

The deterministic reference fixture uses pair 9 and replay sections 50 and 100.
It gives

[
oxed{
W_{50,100,9}
approx
5.440204449331002	imes10^{-6}>0.
}
]

The payload explicitly records

`qhtri_graph_hamiltonian_used=false`.

This is an operator/trajectory statement inside the composed PNCS model.  It
does not identify a physical neutrino or gravitational carrier.

## 11. Falsification gates

The native tests additionally require:

- observation identity supplied to the witness equals the replay binding;
- replay sections are in range and strictly ordered;
- changing observation resolution changes binding identity even when the phase
  trace is unchanged;
- zero-support observed pairs fail closed;
- wrong drive fails exact hydrodynamic replay.
