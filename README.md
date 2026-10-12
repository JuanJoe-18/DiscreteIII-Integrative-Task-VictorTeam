# ResumeLens — Formal Language-Based Résumé Screening

> **Computación y Estructuras Discretas III (2026-2) — Integrative Task 1** · Universidad Icesi
> **Team:** Víctor Team

ResumeLens processes plain-text résumés and decides, for four professional profiles, whether the qualifications **explicitly written** in the résumé satisfy a formally defined qualification pattern. Every stage of the pipeline is a formal model: regular expressions, finite-state transducers, deterministic finite automata and a context-free grammar. ResumeLens does **not** score, rank or recommend candidates and does not make hiring decisions; a candidate may satisfy zero, one or several profiles.

## Team

| Member | GitHub | Main responsibility |
|---|---|---|
| Víctor Cardona | [@victor-xnieb](https://github.com/victor-xnieb) | Stage 1 (regular expressions) and Stage 2 (finite-state transducers); Stage 3 documentation and tests review; poster |
| Juan José Aponza Valencia | [@JuanJoe-18](https://github.com/JuanJoe-18) | Stage 3 (DFA classifier), Streamlit interface, repository |
| Juan David Gomez | [@Juancho31g](https://github.com/Juancho31g) | Stage 4 (textX DSL and HTML), React interface and web API, literature review |

**IDE:** Visual Studio Code (Python and Pylance extensions) · **Language:** Python 3.12 · **Formal-language libraries:** `re`, `pyformlang` 1.0.11, `textX` 4.4 · **Tests:** `pytest` · **Interfaces:** Streamlit and React (Vite + TypeScript) over a local JSON API.

## The pipeline

| Stage | Formal model | Input → output | Package | Design / formalization | Test design |
|---|---|---|---|---|---|
| 1. Information extraction | Regular expressions (`re`) | résumé text → mentions of skills, contact data, years, titles, education | [`src/stage1_regex`](src/stage1_regex) | [`docs/stage1_regex.md`](docs/stage1_regex.md) | [`docs/stage1_tests.md`](docs/stage1_tests.md) |
| 2. Normalization and canonical order | Finite-state transducers (`pyformlang`) | raw mentions → canonical tokens (`JS` → `JAVASCRIPT`) sorted per profile | [`src/stage2_fst`](src/stage2_fst) | [`docs/stage2_fst.md`](docs/stage2_fst.md) | [`docs/stage2_tests.md`](docs/stage2_tests.md) |
| 3. Qualification-pattern recognition | Deterministic finite automata (`pyformlang`) | canonical tokens → ACCEPTED / REJECTED per profile, with trace | [`src/stage3_classifier`](src/stage3_classifier) | [`docs/stage3_formalization.md`](docs/stage3_formalization.md) | [`docs/stage3_tests.md`](docs/stage3_tests.md) |
| 4. Candidate profile language | Context-free grammar in EBNF (`textX`) | stage results → validated DSL document → HTML | [`src/stage4_grammar`](src/stage4_grammar) | [`docs/stage4_grammar.md`](docs/stage4_grammar.md) | [`docs/stage4_tests.md`](docs/stage4_tests.md) |

`src/pipeline.py` (`process_resume`) runs the four stages and is shared by both interfaces. The architecture and the contracts between stages are in [`docs/architecture.md`](docs/architecture.md); the literature review is in [`docs/literature_review.md`](docs/literature_review.md).

## Supported profiles

| # | Profile | Domain | Canonical order of categories |
|---|---|---|---|
| 1 | Full Stack Developer *(given)* | Software engineering | Experience? → Frontend language → Frontend framework? → Backend (language or framework) → API? → Database (SQL or NoSQL) → DevOps/cloud? → Version control |
| 2 | Machine Learning Engineer *(given)* | AI / data | Language → Data processing → ML framework → Database → Version control |
| 3 | Cloud & DevOps Engineer *(proposed)* | Software engineering | Scripting/OS → CI/CD → Containers → Cloud/IaC → Version control |
| 4 | Data Scientist *(proposed)* | AI / data | Language → Data analysis/statistics → Visualization → Machine learning → Version control |

`?` marks optional categories. Each DFA is total, has an explicit trap state `q_trap` and is documented with its 5-tuple, transition table and diagram.

## Repository structure

```text
DiscreteIII-Integrative-Task-VictorTeam/
├── README.md                     ← this file
├── requirements.txt              ← Python dependencies
├── src/                          ← implementation (see src/README.md)
│   ├── stage1_regex/             ← Stage 1: regular expressions, sections, extractor, JSON storage
│   ├── stage2_fst/               ← Stage 2: aliases, FST cascade, normalizer and canonical sort
│   ├── stage3_classifier/        ← Stage 3: profiles, DFAs, classifier, diagram generator
│   ├── stage4_grammar/           ← Stage 4: candidate.tx grammar, parser, generator, HTML renderer, CLI
│   ├── pipeline.py               ← process_resume: Stages 1 → 4
│   ├── web_api/server.py         ← local JSON API + static server for the React app
│   └── ui/app.py                 ← Streamlit interface
├── frontend/                     ← React + TypeScript interface (see frontend/README.md)
├── tests/                        ← pytest suites and résumé fixtures (see tests/README.md)
├── docs/                         ← design, formalization, tests, literature review (see docs/README.md)
│   ├── diagrams/                 ← PNG diagrams of every stage and their sources
│   └── examples/                 ← example DSL documents and generated HTML
├── scripts/                      ← generators of diagrams and formal documents (see scripts/README.md)
└── output/pdf/                   ← poster PDF
```

Each folder has its own README with the location and purpose of every file: [`src/`](src/README.md), [`tests/`](tests/README.md), [`docs/`](docs/README.md), [`scripts/`](scripts/README.md), [`frontend/`](frontend/README.md), [`docs/diagrams/`](docs/diagrams/README.md), [`docs/examples/`](docs/examples/README.md).

## Installation

```bash
git clone https://github.com/JuanJoe-18/DiscreteIII-Integrative-Task-VictorTeam.git
cd DiscreteIII-Integrative-Task-VictorTeam
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\python -m pip install -r requirements.txt
# Linux / macOS:       .venv/bin/python -m pip install -r requirements.txt
```

Use `.venv\Scripts\python` (Windows) or `.venv/bin/python` (Linux/macOS), or activate the environment, in the commands below. The checks for the delivery used Python 3.12. Graphviz (`dot`) is needed only to regenerate diagrams.

## Running

```bash
# All tests (883 test cases)
python -m pytest -q

# Streamlit interface → http://localhost:8501
python -m streamlit run src/ui/app.py

# React interface + JSON API → http://127.0.0.1:8000
# A prebuilt copy of the interface is committed in frontend/dist, so Python is enough:
python -m src.web_api.server

# Only if you change the React code (needs Node.js 22+ and pnpm), rebuild first:
# pnpm --dir frontend install --frozen-lockfile
# pnpm --dir frontend build

# Stage 4 on its own: validate a DSL document and write its HTML
python -m src.stage4_grammar docs/examples/wednesday.resume --html candidate.html
python -m src.stage4_grammar docs/examples/invalid_candidate.resume      # located syntax error, exit code 1
```

Both interfaces call the same Python pipeline; the browser never simulates the automata. The Streamlit app shows the extraction, normalization, per-profile verdicts, the state trace on each DFA, the formal 5-tuples and the validated profile; the React app adds a DSL editor with validation and downloads of the `.resume` and `.html` files.

## Quick example

Résumé fragment: *"Wednesday Addams — 3 years of experience developing web applications. Technical Skills: JS, React.js, NodeJS, Postgres, Git."*

1. **Stage 1** finds `JS`, `React.js`, `NodeJS`, `Postgres`, `Git` and 3 years of experience.
2. **Stage 2** produces `EXPERIENCE_PRESENT JAVASCRIPT REACT NODE_JS POSTGRESQL GIT`.
3. **Stage 3**: the Full Stack DFA ends in its accepting state → **ACCEPTED**; the other three profiles are rejected with the missing categories.
4. **Stage 4** writes and validates `candidate { personal { name "Wednesday Addams"; } … classification { accepted full_stack; } }` and renders it as a self-contained HTML page (a richer example: [`docs/examples/wednesday.html`](docs/examples/wednesday.html)).

## Regenerating the documentation

```bash
python scripts/export_formalization.py      # docs/stage3_formalization.md from the real DFAs
python scripts/export_diagrams.py           # DFA diagrams in docs/diagrams/
python scripts/export_stage4_artifacts.py   # Stage 4 diagrams; --tables prints FIRST/FOLLOW/PREDICT
```

## Scope and limits

The examples are fictional. The system checks patterns over **reported** skills: it does not measure real competence, interpret negation ("no experience with Java") or estimate hiring accuracy, and there is no annotated dataset for precision/recall. Résumés are processed in memory by a local server bound to `127.0.0.1`.
