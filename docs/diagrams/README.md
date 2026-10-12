# `docs/diagrams/` — diagrams

Every diagram used by the documents is a PNG image; when it is generated from code, its source (`.dot` for Graphviz, `.mmd` for Mermaid) is kept next to it.

| Location | Used by | How it is produced |
|---|---|---|
| `full_stack.*`, `machine_learning.*`, `cloud_devops.*`, `data_scientist.*` (`.dot`, `.svg`, `.png`) | `stage3_formalization.md` | `python scripts/export_diagrams.py` from the real `pyformlang` transitions |
| `ver_diagramas.html` | — | offline viewer of the four DFAs, written by `export_diagrams.py` |
| `stage1/` (39) | `stage1_regex.md` | Mermaid diagrams of the Stage 1 design and one automaton per regular expression |
| `stage1_tests/` (6) | `stage1_tests.md` | test levels, techniques, mutation analysis |
| `stage2/` (118) | `stage2_fst.md` | pipeline, CLEAN and EXPERIENCE transducers, one ALIAS transducer per canonical token, families, FILTER transducers and passes per profile |
| `stage2_tests/` (5) | `stage2_tests.md` | test levels, techniques, differential and mutation flows |
| `stage3/` (4) | `stage3_formalization.md` | architecture, classification flow, accepted and rejected traces |
| `stage3_tests/` (1) | `stage3_tests.md` | layers of verification |
| `stage4/` | `stage4_grammar.md` | `python scripts/export_stage4_artifacts.py`: architecture, processing flow, generation sequence, document structure, class diagram, **parse tree** (built by an LL(1) table parser over the BNF), **lexical automata**, **textX metamodel** (exported from `candidate.tx`), adapter mapping, language layers; `s4_10_html_preview.png` is a screenshot of `docs/examples/wednesday.html` |
| `stage4_tests/` | `stage4_tests.md` | test suites by level, validation flow, mutation procedure |

## Conventions of the DFA diagrams

Solid edges show individual symbols. A dashed edge labelled "other symbols of Σ" groups exactly the alphabet symbols that do not appear on the solid edges of the source state; all of them lead to `q_trap`. On `q_trap` the loop Σ includes the whole alphabet. The accepting state is drawn with a double circle. The exporter renders SVG/PNG with the local Graphviz `dot` binary and falls back to the QuickChart web service when `dot` is not installed (which then requires a connection).
