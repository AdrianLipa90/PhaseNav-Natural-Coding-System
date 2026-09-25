# PNCS Hybrid Grammar v0.2

Status: \`CANDIDATE_ONLY / CIELINGO_INSPIRED / FAIL_CLOSED / NO_IMPLICIT_EFFECTS\`

## 1. Purpose

PNCS Hybrid Grammar v0.2 is the semantic program layer above the low-level
Quantum Gate Language.

The architectural split is:

\`\`\`text
CIELingo-inspired meaning/roles
        |
        v
PNCS Hybrid Grammar v0.2
        |
        +--> typed semantic DAG / constraints / effects
        |
        +--> PNCS Quantum Gate Language v0.1
                  |
                  v
         PHASENAV_QUANTUM_GATE_IR_V1
                  |
                  v
       causal cone before hydration
                  |
                  v
       Q28 / future QHTRI / external QPU
\`\`\`

The program states **what relation or computation is requested**. Backend
selection is not the semantics of the program.

## 2. CIELingo-inspired grammatical roles

The mapping is intentionally structural:

- subject / noun phrase -> typed symbol or state;
- verb -> operator node;
- object -> operator target/input;
- modifier -> operator parameter or constraint;
- condition -> guard;
- evidential requirement -> \`REQUIRE\`;
- persistence/effect verb -> explicit authorization boundary;
- requested observation -> \`OBSERVE\`.

This is inspiration, not a claim that free-form natural language is executable.
v0.2 rejects unregistered syntax rather than guessing.

## 3. Types

Atomic types:

\`QUERY TEXT PAGE DOCUMENT GRAPH STATE QUANTUM_STATE OBSERVABLE REAL INTEGER BOOLEAN JSON BYTES URL ANY\`

Container types:

\`SET<T> LIST<T> STREAM<T>\`

where \`T\` is an admitted atomic type.

## 4. Statements

### Program and task scopes

\`\`\`text
PROGRAM <id>
TASK <id>
\`\`\`

\`TASK\` changes the semantic task label for subsequent nodes. \`root\` exists
implicitly.

### Inputs

\`\`\`text
INPUT query : QUERY
INPUT page : PAGE FROM browser.current_page
\`\`\`

### Search and filtering

\`\`\`text
FIND pages : SET<PAGE> FROM web.index RELATED_TO query
FILTER verified : SET<PAGE> FROM pages BY verified_source
\`\`\`

\`FIND\` is represented as a read-only source query. It does not itself grant
network or connector authority.

### Compute

\`\`\`text
COMPUTE ranked : LIST<PAGE> USING semantic_rank INPUT verified query MODE AUTO
\`\`\`

Modes:

- \`AUTO\`
- \`CLASSICAL_PREFERRED\`
- \`QUANTUM_PREFERRED\`
- \`QUANTUM_REQUIRED\`

\`QUANTUM_REQUIRED\` must name a declared quantum kernel.

### Quantum kernel

\`\`\`text
QUANTUM BEGIN local_z QUBITS 1000000 MODE RESULT_DIRECTED
GATE H q0
GATE CZ q0 q1
GATE CZ q1 q2
OBSERVE Z q2
QUANTUM END

OBSERVE score : REAL FROM local_z
\`\`\`

The block is delegated byte-for-byte at semantic level to PNCS Quantum Gate
Language v0.1 and therefore produces the same
\`PHASENAV_QUANTUM_GATE_IR_V1\` digest as a directly compiled gate program.

v0.2 does not yet bind symbolic hybrid inputs into a quantum kernel. Attempting
to do so fails closed.

### Control and scheduling

\`\`\`text
WHEN ready ENABLE compute.rank
PARALLEL fetchers : compute.left compute.right
\`\`\`

\`WHEN\` requires a \`BOOLEAN\` symbol.

\`PARALLEL\` is a scheduler hint only. It cannot alter semantic equivalence.

### Constraints

\`\`\`text
REQUIRE verified_source ON compute.ranked
\`\`\`

A requirement becomes a first-class constraint node.

### Persistence and external effects

\`\`\`text
PERSIST ranked AS library/search/latest REQUIRE storage_write
EFFECT show USING browser.render INPUT ranked REQUIRE user_authorization
\`\`\`

Both compile to:

\`\`\`text
external_effect = true
execution_authorized = false
actuation_performed = false
\`\`\`

The grammar cannot self-authorize a mutation or external action.

### Return

\`\`\`text
RETURN ranked
RETURN result provenance
\`\`\`

\`RETURN\` is mandatory and terminal.

## 5. Example: browser-like search task

\`\`\`text
PROGRAM browser_demo
TASK search

INPUT query : QUERY

FIND pages : SET<PAGE> FROM web.index RELATED_TO query
FILTER verified : SET<PAGE> FROM pages BY verified_source
COMPUTE ranked : LIST<PAGE> USING semantic_rank INPUT verified query MODE AUTO

REQUIRE verified_source ON compute.ranked

RETURN ranked
\`\`\`

Nothing in the semantic source says CPU, GPU, Q28, QHTRI, IBM, CUDA, or memory
size. Those belong to planning/execution.

## 6. Fail-closed rules

v0.2 rejects:

- unknown statements;
- undeclared input symbols;
- duplicate outputs;
- malformed types;
- quantum-required operators without a declared quantum kernel;
- symbolic runtime inputs into v0.2 quantum kernels;
- non-Boolean \`WHEN\` conditions;
- unknown node references in \`WHEN\`, \`PARALLEL\`, or \`REQUIRE\`;
- non-terminal or missing \`RETURN\`;
- implicit authorization of \`PERSIST\` or \`EFFECT\`.

## 7. Non-claims

v0.2 does not claim:

- unrestricted general-purpose language completeness;
- free-form natural-language compilation;
- automatic proof of semantic equivalence for arbitrary rewrites;
- physical QPU execution;
- quantum advantage;
- external actuation authority.

It is a typed deterministic bridge from semantic program structure to the
existing PNCS/PhaseNav execution stack.
