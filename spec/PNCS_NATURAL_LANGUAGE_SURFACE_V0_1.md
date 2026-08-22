# PNCS Natural Language Surface v0.1

Natural language is an input surface, not the canonical semantic representation.

Pipeline:

    utterance
      -> lexical/concept candidates
      -> relation candidates
      -> canonical definition-path resolution
      -> ambiguity gate
      -> 36D relational graph
      -> executable path

The system MUST fail closed when multiple incompatible canonical paths remain unresolved.

The compiler interface exists in v0.1, but semantic compilation is intentionally not implemented until the 36D basis and first radical/definition canon are fixed.
