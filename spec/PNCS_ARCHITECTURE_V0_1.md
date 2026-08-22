# PNCS Architecture v0.1

## Canonical hierarchy

L0 KAKU
- atomic semantic stroke
- carries a finite 36D vector and explicit relational metadata

L1 RADICAL
- graph composed from KAKU atoms
- first reusable semantic component

L2 DEFINITION_PATH
- ordered relational path through radicals
- canonical definition of a concept/operator

L3 CLASS_PATH
- graph of definitions and admissible transitions

L4 FILE_PATH
- namespace/path graph containing classes, functions, definitions

L5 CLUSTER_PATH
- graph of files sharing a semantic/execution domain

L6 SUBSYSTEM_PATH / DAEMON_PATH
- persistent executable path set

L7 LOW_LEVEL_ORCHESTRATOR_PATH
- routing graph among subsystems/daemons

L8 HIGH_LEVEL_ORCHESTRATOR_PATH
- routing graph among lower orchestrators and system policies

L9 SYSTEM_PATH
- complete executable semantic-phase graph

## Text is not authority

Written code is a projection:

canonical 36D relational graph -> textual surface

Natural-language input is resolved in the reverse direction:

utterance -> concepts -> relations -> canonical definition paths -> 36D graph -> executable path

## Required lineage

Every executable high-level path MUST be auditable downward to KAKU atoms.

instruction -> path -> class -> definition -> radical -> KAKU -> 36D vector

## Fail-closed rule

Unknown dimensions, malformed vectors, unresolved relations, ambiguous path targets, or missing lineage MUST NOT be silently replaced with zero vectors, empty graphs, guessed meanings, or static fallbacks.
