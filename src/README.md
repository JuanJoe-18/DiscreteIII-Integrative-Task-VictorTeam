# `src/` — implementation

All the Python code of ResumeLens. Each stage is an independent package; `pipeline.py` connects them, and the two user interfaces only call `pipeline.py` (they never re-implement a stage).

```text
src/
├── pipeline.py              process_resume(text) → PipelineResult (Stages 1 → 4)
├── stage1_regex/            Stage 1 — regular expressions
├── stage2_fst/              Stage 2 — finite-state transducers
├── stage3_classifier/       Stage 3 — deterministic finite automata
├── stage4_grammar/          Stage 4 — context-free grammar with textX
├── web_api/                 local JSON API used by the React app
└── ui/                      Streamlit app
```

## `pipeline.py`

| Name | Input | Output |
|---|---|---|
| `extract_and_normalize(text)` | résumé text | `(ExtractionResult, NormalizationResult, candidate dict)` |
| `process_resume(text, *, classifier=None)` | résumé text | `PipelineResult(extraction, normalization, classification, document, candidate)`; `ValueError` if the text is empty or has no catalog skills |

## `stage1_regex/` — information extraction · docs: [`stage1_regex.md`](../docs/stage1_regex.md), [`stage1_tests.md`](../docs/stage1_tests.md)

| File | Contents |
|---|---|
| `expressions.py` | The 19 regular expressions written as raw strings, with their boundary helpers (`_LB`, `_RB`) |
| `patterns.py` | Catalog of `RegexSpec` objects (name, category, scope, pattern, accepted/rejected examples); `SPECS_BY_NAME` (reused by Stage 4 to validate contacts) |
| `sections.py` | `split_sections`, `find_section`, `split_skill_items`: résumé sections (Skills, Experience, Education…) and skill lists |
| `extractor.py` | `ResumeExtractor` / `extract_qualifications(text)`: runs the catalog, resolves overlaps, ignores technologies inside contact data |
| `models.py` | `Category`, `Scope`, `RegexSpec`, `ExtractedItem`, `ExtractionResult` (raw tokens, contact, years, job titles, education, name) |
| `storage.py` | `save_result` / `load_result`: an `ExtractionResult` as JSON |

## `stage2_fst/` — normalization · docs: [`stage2_fst.md`](../docs/stage2_fst.md), [`stage2_tests.md`](../docs/stage2_tests.md)

| File | Contents |
|---|---|
| `aliases.py` | Vocabulary: every accepted spelling of each of the 79 canonical tokens, grouped by family; `all_canonical_tokens()` (reused by Stage 4) |
| `transducers.py` | `Transducer` (7-tuple) and the builders of CLEAN, ALIAS (per family and full), EXPERIENCE and FILTER, run with `pyformlang` |
| `normalizer.py` | `normalize_token`, `normalize_qualifications`, `sort_to_canonical_order`, `normalize_and_sort` → `NormalizationResult` with one `TokenTrace` per input |

## `stage3_classifier/` — pattern recognition · docs: [`stage3_formalization.md`](../docs/stage3_formalization.md), [`stage3_tests.md`](../docs/stage3_tests.md)

| File | Contents |
|---|---|
| `profiles.py` | The four profiles: categories, canonical order, alphabet Σ, required groups; `PROFILES_REGISTRY` |
| `automata_models.py` | One total DFA per profile built with `pyformlang`, with trap state; `get_formal_tuple()` returns (Q, Σ, δ, q0, F) |
| `classifier.py` | `ResumeClassifier.classify(tokens)` and `evaluate_profile(id, tokens)` → verdict, step trace, missing categories, ignored tokens |
| `visualizer.py` | Graphviz / Mermaid diagrams generated from the real transition table, optionally highlighting a trace |

## `stage4_grammar/` — candidate profile language · docs: [`stage4_grammar.md`](../docs/stage4_grammar.md), [`stage4_tests.md`](../docs/stage4_tests.md)

| File | Contents |
|---|---|
| `candidate.tx` | The grammar (textX EBNF): 16 syntactic rules + 4 lexical rules |
| `parser.py` | `parse_profile(source)`, `parse_profile_file(path)`, `ProfileValidationError` (kind `syntax`/`semantic`, line, column); domain checks |
| `models.py` | Frozen dataclasses `CandidateProfile`, `Contact`, `Experience`, `Education` |
| `generator.py` | `candidate_from_results(...)` (Stages 1–3 → model) and `serialize_profile(profile)` (model → canonical DSL, re-parsed) |
| `renderer.py` | `validate_document`, `generate_document`, `render_profile_html` → `ProfileDocument(profile, dsl, html)` |
| `__main__.py` | `python -m src.stage4_grammar FILE [--html OUT]` |

## `web_api/` and `ui/`

| File | Contents |
|---|---|
| `web_api/server.py` | `python -m src.web_api.server [--port 8000]`: serves `frontend/dist` and `GET /api/profiles`, `POST /api/evaluate`, `POST /api/validate-profile` on `127.0.0.1` (max. 100,000 characters per text) |
| `ui/app.py` | `python -m streamlit run src/ui/app.py`: evaluation tab (full pipeline or direct tokens, trace, DSL/HTML), formalization tab (5-tuples, δ table), test runner, about |
