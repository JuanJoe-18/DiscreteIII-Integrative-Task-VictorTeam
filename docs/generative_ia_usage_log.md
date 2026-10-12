# Generative AI Usage Log (Level 3: own input and prompts)

**Tool:** Claude (Anthropic), used through Claude Code
**Scope:** Stages 1–4 documentation, test design, English translation of the interfaces, repository review and delivery. The program logic of each stage was designed and written by the team; the AI was used as an assistant for review, documentation and translation.

## How the AI was used

| Area | Own input given to the AI | What the AI produced | What I did with it |
|---|---|---|---|
| Stage 1–3 documents and tests | My code, my design notes and the assignment text | Drafts of formal specifications, test-design documents and scenario tests | Read them, ran the tests, corrected wrong statements (for example the minimality of the Full Stack DFA) and kept only what I could explain |
| Stage 4 grammar document | The repository code (`candidate.tx`, parser, generator, renderer) and the assignment text | Formal definition of the grammar, FIRST/FOLLOW tables, derivations, theorems, diagrams | Compared it against the code, regenerated the tables with `scripts/export_stage4_artifacts.py`, and asked for changes to match the course notation |
| Stage 4 test design | The existing Stage 4 tests of the repository | Design document: techniques, decision tables, catalog of the 108 tests, coverage and mutation analysis | Asked the AI to remove the extra tests it had added and to document only the existing ones |
| Literature review | The topics and sources already in the repository | Expansion of the review (50 references) | Checked that the cited works are the ones described |
| Interfaces in English | The Streamlit and React interfaces | Translation of labels and messages; compiled `frontend/dist` from the repository source | Ran both interfaces and the tests |
| Repository review | The GitHub repository and the assignment | Review of requirements, consistency checks, broken links | Applied the fixes and committed them with my own identity |

## Interaction log

### 1. Stage 3 review and scenario tests (11 Oct 2026)
- **Own input:** the Stage 3 code and formal document of the repository. [add the exact prompt]
- **AI output:** review of the formalization, scenario tests and test-design document for Stage 3.
- **My validation:** ran `python -m pytest -q`; corrected the statement about the Full Stack automaton not being minimal.

### 2. Stage 4 documentation, tests document, literature and READMEs (11 Oct 2026, 18:45)
- **Prompt (as written):** "Hay muchas cosas que cambiar en la parte de documentación y todo lo que dijiste. Necesito que mejoremos la documentación de la etapa 4 como lo hicimos con las otras etapas. Con diagramas si corresponde y con la formalidad matematica o explicaciones en lenguaje natural. Lo mismo con los test de esta etapa. Además me gustaría agregar más cosas en la parte de la literatura. También podemos aprovechar para arreglar el readme de cada una de las seciones del proyecto indicando la ubicación de cada archivo y todo eso. Dame todo esto listo en un zip como has estado haciendo. Trata de no momver nada del código a menos que sea necesario como lo de cambiar el idioma de las interfaces."
- **AI output:** rewritten `docs/stage4_grammar.md` with diagrams, expanded `docs/literature_review.md`, a README for each folder, and the English interfaces.
- **My validation:** ran the full test suite and the build; read the documents.

### 3. Correction: no new tests (11 Oct 2026, 19:23)
- **Prompt (as written):** "Me equivoqué al darte una indicación. No quería que agregaras más test para la etapa 4. Queria que mejoraras el documento del diseño de test de esta etapa con los que ya habia. Vuelve a dejar esta parte como estaba y dame el md del diseño de pruebas de esta etapa teniendo en cuenta los que habia hecho mi compañero. Si hay algun archivo que nombre a estos test que hiciste también modificalo. Vuelve a darme el zip teniendo en cuenta esto."
- **AI output:** removed the extra tests and rewrote `docs/stage4_tests.md` around the 108 existing tests, with the original coverage (97 %) and mutation results (29 of 37 mutants killed), listing the survivors as known gaps.
- **My validation:** confirmed that the repository still has 883 passing tests.

### 4. Course notation for the grammar (11 Oct 2026, ~20:00)
- **Own input:** the course slides *BNF and EBNF – Backus Naur Form* (PDF) and my question about whether the course notation (`S -> aS | a | BA`) was in the document.
- **AI output:** the grammar in the class notation (⟨ ⟩ and `::=`), productions grouped as `A → α | β`, and a tabular proof like the one in the slides; options `--bnf` and `--proof` in `scripts/export_stage4_artifacts.py`.
- **My validation:** checked that the notation matches the slides and committed the result.

### 5. Final repository review and how to run it (11 Oct 2026, ~20:25)
- **Prompt (as written):** "Por favor revisa si todo está bien y cumplimos con lo que pide la consigna y luego dime cómo prubo el programa"
- **AI output:** checked the tests, the build, the commit history and the poster against the assignment; found links to the deleted `docs/delivery_checklist.md`; gave the commands to run the program.
- **My validation:** ran the program on my computer after installing Python 3.12.

### 6. Prebuilt React interface (11 Oct 2026, ~21:00)
- **Own input:** my question about leaving the compiled folder in the repository.
- **AI output:** the compiled `frontend/dist`, built from the source of `frontend/src`, and README and `.gitignore` changes explaining that Python alone is enough to run it.
- **My validation:** opened the interface at `http://127.0.0.1:8000` and evaluated the example résumés.

## Declaration

I used the AI for documentation, review, translation and compilation. The decisions about each stage are explained in the design documents in `docs/`, and I can explain the formal model of each stage, how the stages are connected in `src/pipeline.py`, and the tests, as required for the presentation. The AI did not make commits: I made them with my own identity.