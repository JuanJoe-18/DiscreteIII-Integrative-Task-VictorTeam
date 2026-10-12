# `docs/` — design documents

All the design documents required by the assignment (design of modules, formalization, design of test cases including scenarios) are here, in English and in Markdown. Diagrams are PNG images, so they render on GitHub and in any Markdown viewer.

## Reading order

| # | Document | Contents |
|---|---|---|
| 0 | [`Initial Doc.md`](Initial%20Doc.md) | The assignment statement (transcription) |
| 1 | [`architecture.md`](architecture.md) | Data flow of the four stages, module responsibilities, integration decisions, limits |
| 2 | [`literature_review.md`](literature_review.md) | Literature review: related work on résumé processing, the four formal models, DSLs/textX, fairness and testing; synthesis of design decisions |
| 3 | [`stage1_regex.md`](stage1_regex.md) | Stage 1 — module design; formalization of the 19 regular expressions (equivalent automata and grammars); section handling |
| 4 | [`stage1_tests.md`](stage1_tests.md) | Stage 1 — test techniques, scenarios, mutation analysis |
| 5 | [`stage2_fst.md`](stage2_fst.md) | Stage 2 — the transducers as 7-tuples, their composition, aliases, canonical sorting |
| 6 | [`stage2_tests.md`](stage2_tests.md) | Stage 2 — test design, differential tests, mutation analysis |
| 7 | [`stage3_formalization.md`](stage3_formalization.md) | Stage 3 — design (Part I) and formalization (Part II): 5-tuples, δ tables, Theorems 1–5, diagrams |
| 8 | [`stage3_tests.md`](stage3_tests.md) | Stage 3 — decision table, catalog of tests, coverage, mutation analysis |
| 9 | [`stage4_grammar.md`](stage4_grammar.md) | Stage 4 — design (Part I) and formalization (Part II): EBNF/BNF, terminals and nonterminals, lexical automata, derivations, parse tree, LL(1) and regularity theorems, static semantics, round trip, HTML safety |
| 10 | [`stage4_tests.md`](stage4_tests.md) | Stage 4 — test techniques, decision tables, catalog of the 108 tests, coverage, mutation analysis |


---
## Folders

| Folder | Contents |
|---|---|
| [`diagrams/`](diagrams/README.md) | All diagrams (PNG) and their sources (`.dot`, `.mmd`) |
| [`examples/`](examples/README.md) | Stage 4 example documents (`.resume`) and the generated HTML |
