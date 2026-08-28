# PNLF Orbital Memory Contract v0.1

Status: CANDIDATE
Schema family: `PNLF_ORBITAL_MEMORY_V0_1`
Format name: **PhaseNav Liminal File (PNLF)**

## 1. Purpose

PNLF represents persistent memory as immutable admitted state checkpoints connected by liminal trajectories in proper time.

Canonical form:

```text
S_i -- Lambda_i(tau) --> S_{i+1}
```

`S_i` is State Memory. `Lambda_i(tau)` is Liminal Memory. Stable memory is produced by an admitted reduction/consolidation event; a raw input event does not become a State Memory checkpoint by storage alone.

PNLF is a logical memory contract. Physical placement is delegated to the storage profile. `.pnh5` is the HDF5 compatibility/storage profile for PNLF. `.paux` remains the persistent AUX carrier for relational PNV state. PNStore remains the generation/commit/recovery layer.

## 2. Identity invariants

These identifiers are distinct and MUST NOT be collapsed:

```text
FILE_ID != CONTENT_COMMITMENT != CHECKPOINT_OBJECT_ID
SEGMENT_ID != SEGMENT_COMMITMENT
```

- `FILE_ID` identifies a PNLF lineage/container.
- `OBJECT_ID` identifies the persistent semantic/state object represented by the lineage.
- `CONTENT_COMMITMENT` commits exact payload bytes or canonical content.
- `CHECKPOINT_OBJECT_ID` identifies one immutable State Memory checkpoint.
- `SEGMENT_ID` identifies one logical liminal trajectory across its append-only revisions.
- `SEGMENT_COMMITMENT` identifies one immutable revision of that liminal trajectory.

Canonical logical address:

```text
(OBJECT_ID, tau, relation)
```

## 3. Two orthogonal memory axes

PNLF MUST separate functional memory channel from orbital binding.

### 3.1 Functional M-layer

`active_m_layers` describes which memory channels participate in the state/trajectory.

CIEL compatibility channel names:

| Layer | Channel |
|---|---|
| `M0` | PerceptualMemory |
| `M1` | WorkingMemory |
| `M2` | EpisodicMemory |
| `M3` | SemanticMemory |
| `M4` | ProceduralMemory |
| `M5` | AffectiveEthicalMemory |
| `M6.1a` | IdentityMemory |
| `M7` | BraidInvariantMemory |
| `M8` | AuditJournalMemory |

M-layer is functional classification. It is not orbital radius, persistence temperature, or promotion rank.

### 3.2 Orbital band

`orbital_band` describes current binding to the selected attractor.

Canonical v0.1 band labels:

```text
O0 O1 O2 O3 O4 O5 O6 O7 O8
```

Lower band index means stronger binding under the declared `orbit_quantizer_id`. The exact mapping from geometry to band belongs to the quantizer profile and is not hard-coded by the PNLF container contract.

A semantic memory (`M3`) can occupy any admitted orbital band. An audit record (`M8`) can also occupy any admitted orbital band. Therefore:

```text
M_LAYER != ORBITAL_BAND
```

## 4. PNLF header

Required logical header fields:

```text
schema                   = PNLF_ORBITAL_MEMORY_V0_1
file_id                  = stable lineage/container ID
object_id                = persistent represented object ID
genesis_anchor           = immutable genesis commitment
basis_id                 = PhaseNav basis binding
schema_binding           = exact schema/profile identifier
storage_profile          = e.g. PNLF_NATIVE / PNH5_V0_1
mass_model_id            = semantic/orbital mass model identifier
orbit_quantizer_id       = geometry -> O0..O8 profile identifier
proper_time_model_id     = model/kernel provenance for tau
t36_basis_id             = T36 witness basis
lineage_head             = current admitted checkpoint ID or null
```

The header does not grant runtime execution authority or canon-write authority.

## 5. Orbital state

Each admitted checkpoint carries an `orbital_state`:

```text
attractor_id
orbital_band             O0..O8
r_phase                  finite phase distance in [0,pi]
phase                    finite wrapped phase
E_bind                   finite binding-energy coordinate
L_phase                  finite phase angular-momentum coordinate
semantic_mass            finite non-negative value
orbit_period             finite positive value
winding                  finite winding coordinate
proper_time              finite non-negative tau
memory_affinity          finite value in [0,1]
mass_model_id
orbit_quantizer_id
proper_time_model_id
```

PNLF records the coordinates and the model/profile identifiers that produced them. It does not require one universal semantic-gravity constant or one universal shell-capacity rule.

Compatibility implementations MAY project the existing CIEL orbital-shell coordinates (`r_phase`, `E_bind`, `L_phase`, shell) into this record through an explicit compatibility `orbit_quantizer_id`.

## 6. State Memory checkpoint

A State Memory checkpoint is immutable and content-addressed.

Required fields:

```text
checkpoint_object_id
object_id
tau
content_commitment
predecessor_checkpoint_id | null
active_m_layers[]
orbital_state
state_commitment
t36_witness_sha256
reduction_witness_sha256
consolidation_witness_sha256
relation_braid_commitment
admission_state = ADMITTED
```

`reduction_witness_sha256` is mandatory for a stable checkpoint. This enforces the memory-update rule:

```text
no admitted reduction -> no new State Memory checkpoint
```

A new admitted checkpoint supersedes the lineage head but does not mutate previous checkpoints.

## 7. Liminal Memory segment

Liminal Memory is the transition space between admitted states. It is not another M-layer and not another orbital band.

A segment revision has:

```text
segment_id
segment_commitment
previous_segment_commitment | null
object_id
pilot_l_checkpoint_id
pilot_r_checkpoint_id | null
tau_start
tau_cursor
tau_end | null
active_m_layers[]
relation_braid_commitment
trajectory_commitment
modulation_commitment
t36_trajectory_commitment
event_commitments[]
source_orbital_state
target_orbital_state | null
epistemic_state
resolution_state = OPEN | ADMITTED | REJECTED
resolution_witness_sha256 | null
```

`segment_id` is stable for the logical trajectory. `segment_commitment` changes for every immutable append-only revision. `previous_segment_commitment` links the revision chain.

`tau_cursor` is the proper-time coordinate represented by that revision. For an OPEN segment, `tau_start <= tau_cursor` and `tau_end` is null. For a closed segment, `tau_end == tau_cursor`.

`LIMINAL_ADVANCE` MUST create a new revision commitment; it MUST NOT overwrite a prior revision.

An OPEN segment may exist without a right admitted checkpoint. Admission closes the segment and binds it to the newly created checkpoint. Rejection closes it without creating a new State Memory checkpoint.

## 8. TAU FRAME

Canonical local traversal unit:

```text
TAU_FRAME = (PILOT_L, Lambda(tau), PILOT_R, T36)
```

- `PILOT_L` is the admitted left-state anchor.
- `Lambda(tau)` carries the liminal trajectory content.
- `PILOT_R` is the target/right anchor; it may be unresolved while the segment is OPEN.
- `T36` is the relational/integrity witness for the traversal.

`tau` is the primary trajectory coordinate. Wall-clock timestamps MAY be included as provenance but do not replace proper time.

## 9. Orbital transitions

Orbital motion is represented as a state transition receipt; it does not rewrite prior checkpoint content.

Canonical transition verbs for v0.1:

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

These names are **RADICAL contracts composed from admitted native PNV operators** in v0.1. They are not new native PNV opcodes.

### `ORBIT_BIND`
Bind a checkpoint/segment to an attractor and quantizer profile.

### `LIMINAL_ENTER`
Open a new segment from an admitted checkpoint.

### `LIMINAL_ADVANCE`
Append a proper-time trajectory residue/event by creating a new immutable revision of an OPEN segment.

### `STATE_COMMIT`
Close an OPEN liminal segment as ADMITTED and create a new immutable State Memory checkpoint. Requires reduction and consolidation witnesses.

### `STATE_SUPERSEDE`
Advance lineage head from the previous admitted checkpoint to the new admitted checkpoint. Does not delete or overwrite the predecessor.

### `ORBIT_PROMOTE` / `ORBIT_DEMOTE`
Produce a new orbital binding through a liminal transition. The content commitment MAY remain unchanged while the orbital-state commitment changes.

### `ORBIT_RECALL`
Recall MUST NOT mutate an archived checkpoint in place. It opens a new liminal segment whose source is the remembered checkpoint and whose target is an active orbital state.

Canonical recall form:

```text
S_old -- Lambda_recall(tau) --> S_active_new
```

## 10. Promotion/admission boundary

GREMLIN and other candidate generators MAY create KAKU/RADICAL/OPERATOR candidates and liminal proposals, but a candidate does not become State Memory by generation alone.

Admission requires the configured reduction/consolidation/holonomy policy and writes an explicit receipt. Candidate generation carries no independent runtime execution authority and no canon-write authority.

## 11. Physical storage boundary

Logical memory geometry and physical storage topology are independent:

```text
logical orbital binding != physical extent location
```

PNStore MAY migrate extents according to a storage policy after an orbital transition, but an `O_i -> O_j` transition does not require physical relocation.

Profiles:

- `PNLF_NATIVE` — logical/native PNLF representation.
- `PNH5_V0_1` — HDF5-compatible persistent profile carrying the same logical objects/commitments.
- `PAUX` — relational PNV/AUX state carrier; may reference PNLF object/checkpoint IDs.

## 12. Append-only lineage

State checkpoints, liminal segment revisions, transition receipts, and admission receipts are append-only/content-addressed objects. Mutable convenience indexes (for example `lineage_head`) are projections over immutable lineage and MUST be reconstructible from receipts.

## 13. v0.1 validation gates

A conforming implementation MUST reject:

1. a checkpoint with missing reduction witness;
2. a checkpoint whose `checkpoint_object_id` does not match canonical content;
3. a segment whose left pilot is not an admitted checkpoint;
4. a closed ADMITTED segment without a right checkpoint;
5. an orbital band outside `O0..O8`;
6. non-finite orbital coordinates or `r_phase` outside `[0,pi]`;
7. an orbital transition that overwrites the predecessor checkpoint;
8. a recall operation that mutates the recalled checkpoint;
9. conflation of `FILE_ID`, `CONTENT_COMMITMENT`, and `CHECKPOINT_OBJECT_ID`;
10. a candidate object claiming independent runtime execution or canon-write authority;
11. a liminal advance that overwrites a previous segment revision instead of linking a new `segment_commitment`;
12. an OPEN segment whose `tau_cursor < tau_start`, or a closed segment whose `tau_end != tau_cursor`;
13. a checkpoint/segment whose mass, orbit-quantizer, or proper-time model differs from its PNLF header without an explicit lineage/profile transition;
14. `STATE_COMMIT` when the right checkpoint tau differs from the current liminal `tau_cursor`.

## 14. Initial compatibility mapping

Existing CIEL orbital memory can be imported without redefining its functional channels:

```text
CIEL M0..M8 channel -> PNLF active_m_layers
CIEL r_phase        -> PNLF orbital_state.r_phase
CIEL E_bind         -> PNLF orbital_state.E_bind
CIEL L_phase        -> PNLF orbital_state.L_phase
CIEL shell 0..8     -> PNLF O0..O8 through explicit compatibility quantizer
CIEL phase trace    -> PNLF Lambda(tau) / T36 trajectory witness
CIEL consolidation -> PNLF consolidation witness
CIEL retrieval      -> PNLF ORBIT_RECALL transition
PNCS time binding   -> PNLF proper_time + proper_time_model_id
```

This mapping preserves the existing orbital-memory mechanism while moving persistence, lineage and transition semantics into PNLF.
