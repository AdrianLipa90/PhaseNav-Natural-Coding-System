# PNCS Higher Hierarchy Paths v0.14

Status: `CONTENT_ADDRESSED / READ_ONLY / CHYBA / NO_NEW_OPCODE`

## Levels

```text
CLUSTER
  -> SUBSYSTEM / DAEMON
  -> LOW_ORCHESTRATOR
  -> HIGH_ORCHESTRATOR
  -> SYSTEM
```

SUBSYSTEM and DAEMON are sibling semantic levels over ordered CLUSTER content IDs. Their level tag is part of semantic identity; identical child IDs therefore do not make a SUBSYSTEM and DAEMON identical. LOW_ORCHESTRATOR may compose content IDs from both sibling levels. HIGH_ORCHESTRATOR composes LOW_ORCHESTRATOR IDs, and SYSTEM composes HIGH_ORCHESTRATOR IDs.

Aliases, service names, deployment paths, process labels and repository locations remain record metadata only. Ordering is semantic at every higher level.

Native PNV roots reference only content-derived child roots and use recovered `IDENTITY`, `ORDER`, and `COMPOSITION` operators. No new machine opcode is introduced.

Full inverse expansion is deterministic:

```text
SYSTEM -> HIGH_ORCHESTRATOR -> LOW_ORCHESTRATOR -> SUBSYSTEM/DAEMON -> CLUSTER -> FILE -> CLASS -> DEFINITION -> KAKU
```

Missing or wrongly typed dependencies fail closed. Historical native-runtime replay and external canon promotion are not claimed.
