# `tests/` — automated tests

Run everything from the repository root with `python -m pytest -q` (**883** test cases). A single file: `python -m pytest -q tests/test_stage4_grammar.py`. The design of the tests of each stage (techniques, scenarios, coverage, mutation analysis) is explained in `docs/stage<N>_tests.md`.

| File | Cases | What it tests | Design document |
|---|---|---|---|
| `test_stage1_patterns.py` | 66 | each regular expression against its accepted/rejected examples | [`stage1_tests.md`](../docs/stage1_tests.md) |
| `test_stage1_sections.py` | 10 | section detection and skill-list splitting | ″ |
| `test_stage1_extractor.py` | 32 | extraction on whole résumés | ″ |
| `test_stage1_boundaries.py` | 31 | boundary and negative cases found by mutation analysis | ″ |
| `test_stage1_storage.py` | 2 | JSON persistence | ″ |
| `test_stage1_contract.py` | 68 | contract Stage 1 → Stages 2/3 | ″ |
| `test_stage2_transducers.py` | 66 | transducers as formal 7-tuples and their pyformlang versions | [`stage2_tests.md`](../docs/stage2_tests.md) |
| `test_stage2_vocabulary.py` | 290 | specification table of every alias → canonical token | ″ |
| `test_stage2_normalizer.py` | 70 | normalization, canonical sort and pipeline contracts | ″ |
| `test_stage3.py` | 106 | DFAs: equivalence classes, boundaries, exhaustive and differential tests, scenarios | [`stage3_tests.md`](../docs/stage3_tests.md) |
| `test_stage3_regressions.py` | 12 | regressions and exhaustive Full Stack combinations | ″ |
| `test_pipeline_contract.py` | 3 | contracts between Stages 1, 2 and 3 | ″ |
| `test_stage4_grammar.py` | 58 | DSL syntax partitions, domain checks, CLI | [`stage4_tests.md`](../docs/stage4_tests.md) |
| `test_stage4_generation.py` | 29 | round trip, injection, validation before HTML | ″ |
| `test_pipeline_stage4.py` | 11 | Stages 1 → 4 end to end | ″ |
| `test_web_api.py` | 19 | HTTP API: evaluation, validation of requests | [`architecture.md`](../docs/architecture.md) |
| `test_web_stage4.py` | 10 | HTTP API: generated documents and DSL validation endpoint | [`stage4_tests.md`](../docs/stage4_tests.md) |

## Helpers and data

| Path | Purpose |
|---|---|
| `data/resumes/wednesday_addams.txt` | the Full Stack example of the assignment |
| `data/resumes/mary_jane_watson.txt` | the Machine Learning example of the assignment |
| `data/resumes/rich_resume.txt` | a résumé with contact data, several sections, titles and degrees |
| `data/resumes/spanish_resume.txt` | a résumé written in Spanish (section names and "años de experiencia") |
