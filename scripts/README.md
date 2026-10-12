# `scripts/` — generators of documentation

Run from the repository root. They read the real models, so the documents and diagrams cannot drift from the code.

| Script | Produces | Needs |
|---|---|---|
| `export_formalization.py` | `docs/stage3_formalization.md` (5-tuples, δ tables, theorems; stops if the code contradicts the text) | Python only |
| `stage3_design_section.py`, `stage3_theory_section.py` | Part I (design) and the formal framework of the Stage 3 document; imported by `export_formalization.py` | — |
| `export_diagrams.py` | `docs/diagrams/<profile>.{dot,svg,png}` and `docs/diagrams/ver_diagramas.html` (offline DFA viewer) | Graphviz `dot` (falls back to an online renderer) |
| `stage4_bnf.py` | Helper module (not run directly): the Stage 4 grammar as pure BNF, with FIRST/FOLLOW sets, the LL(1) table and derivations; imported by `export_stage4_artifacts.py` | — |
| `export_stage4_artifacts.py` | `docs/diagrams/stage4/*` and `docs/diagrams/stage4_tests/*` (parse tree, lexical automata, textX metamodel, architecture and flow diagrams); `--tables` prints the FIRST/FOLLOW/PREDICT tables, `--bnf` the BNF grouped by left-hand side and `--proof` the tabular proof of `docs/stage4_grammar.md` | Graphviz `dot`; `mmdc` (mermaid-cli) for the Mermaid diagrams |
