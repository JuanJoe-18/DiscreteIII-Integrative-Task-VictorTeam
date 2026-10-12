"""Generate the Stage 3 definition from the executable DFA models."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.stage3_classifier.automata_models import build_all_automata
from scripts.stage3_design_section import build_design_section
from scripts.stage3_theory_section import build_theory_section, models as theory_models, profile_properties


def export_formalization():
    lines = [
        '# Stage 3 — Qualification Pattern Recognition',
        '',
        'Generated with `python scripts/export_formalization.py` from the executable models.',
        '',
        '## Contract and design criteria',
        '',
        'The input is a list of canonical tokens produced by Stage 2, not résumé text. '
        'Four patterns are recognized by one common solution based on `pyformlang`. '
        'A candidate may satisfy zero, one or several profiles; no rankings or hiring decisions are produced.',
        '',
        '`classify(tokens)` prepares one sequence per profile: it keeps the symbols of the profile alphabet '
        'and sorts them by category. Unrelated skills are kept in `ignored_tokens` for auditing '
        'and never satisfy a requirement. `evaluated_tokens` holds the sequence that was actually recognized. '
        'This preparation is an integration step, not a DFA transition. '
        '`evaluate_profile(id, tokens)` and `classify(tokens, prepare_input=False)` recognize the word '
        'strictly, without filtering or sorting it. Direct mode and the demo without Stage 2 use this strict evaluation.',
        '',
        'Each symbol represents an explicitly identified competency; it does not certify proficiency. '
        '`EXPERIENCE_PRESENT` represents a reported number of years, zero included. Experience is optional '
        'and has no minimum threshold in this pattern. The exact years remain Stage 1 metadata. '
        'The literal symbol `\\d` and an infinite alphabet of numbers are not used.',
        '',
        '## Automaton type and formal semantics',
        '',
        'For each profile, M = (Q, Σ, δ, q0, F). The alphabet categories are pairwise disjoint within '
        'a profile. δ: Q × Σ → Q is total, with exactly one target per pair. There are no ε-transitions '
        'and no alternative choices for the same symbol, so the four models are DFAs. '
        '`q_trap` belongs to Q, does not belong to F and satisfies δ(q_trap, s) = q_trap for every s ∈ Σ. '
        'A token outside Σ is rejected before δ is applied; its move to the trap in the trace is a diagnostic '
        'convention, not an extension of the domain of δ.',
        '',
        'The states `q_<category>` record the last block consumed. In Full Stack they do not imply '
        'that all the previous categories were observed, because skips exist. '
        '`satisfied_categories` lists the categories observed in the input; `missing_categories` '
        'lists the absent mandatory requirements. A word that has every requirement can still be rejected '
        'for disorder in strict evaluation.',
        '',
        'Recognizing a word costs O(n) once the model is built. Preparing each profile by '
        'sorting costs O(n log n). In the expressions below, C+ means one or more '
        'skills of the category, C* allows zero or more, and | denotes alternatives.',
        '',
    ]
    THEORY = theory_models()
    lines += build_theory_section()
    for pid, auto in build_all_automata().items():
        formal = auto.get_formal_tuple()
        profile = auto.profile
        lines += [f'## {profile.title}', '', f'Domain: {profile.domain}.', '',
                  f'**Q** = {{{", ".join(sorted(formal.states))}}}', '',
                  '**q0** = `q0`.', '',
                  f'**F** = {{{", ".join(sorted(formal.final_states))}}}', '',
                  '**Σ** is the union of the following categories:', '',
                  '| Category | Symbols |', '|---|---|']
        for cat in profile.canonical_categories:
            lines.append(f'| {cat.name} | {", ".join(sorted(cat.skills))} |')
        if pid == 'full_stack':
            pattern = ('EXPERIENCE* FE_LANGUAGE+ FE_FRAMEWORK* '
                       '(BE_LANGUAGE+ BE_FRAMEWORK* | BE_FRAMEWORK+) API_COMMUNICATION* '
                       '(DATABASE_SQL+ DATABASE_NOSQL* | DATABASE_NOSQL+) DEVOPS_CLOUD* VERSION_CONTROL+')
        else:
            pattern = ' '.join(cat.name + '+' for cat in profile.canonical_categories)
        lines += ['', '**Recognized pattern:**', '', f'`{pattern}`', '',
                  '**Minimum requirements:** ' + '; '.join(
                      name + ' (' + ' or '.join(sorted(alts)) + ')'
                      for name, alts in profile.required_groups.items()) + '.', '',
                  '**Complete δ by category:** each cell applies to every symbol of its column.', '',
                  '| State | ' + ' | '.join(cat.name for cat in profile.canonical_categories) + ' |',
                  '|---|' + '---|' * len(profile.canonical_categories)]
        for state in sorted(formal.states):
            targets = []
            for cat in profile.canonical_categories:
                destinations = {formal.transitions[state, skill] for skill in cat.skills}
                assert len(destinations) == 1
                targets.append(destinations.pop())
            lines.append('| ' + state + ' | ' + ' | '.join(targets) + ' |')
        lines += [''] + profile_properties(THEORY[pid])
        lines += [f'![DFA {profile.title}](diagrams/{pid}.png)', '',
                  'In Graphviz, "other symbols of Σ" groups the exact complement of the solid edges '
                  'of the state. Mermaid contains one explicit transition for every pair of δ.', '']
    lines += [
        '## Verification against assignment item 3', '',
        '| Requirement | Evidence |', '|---|---|',
        '| Four profiles with one general solution | Common registry and shared construction/evaluation; Full Stack, ML, DevOps and Data Scientist |',
        '| Complete Q, Σ, δ, q0 and F per automaton | Sections above and `get_formal_tuple()`; total table generated from the DFA |',
        '| Explain and justify DFA/NFA/ε-NFA | Determinism, totality and absence of ε: Theorem 2; language of each automaton: Theorem 1; minimality: Theorem 4 |',
        '| Transition diagram | DOT/SVG/PNG and Mermaid derived from the model |',
        '| Correctness of the integration (filtering and sorting before the DFA) | Theorem 5 and the tests that verify it |',
        '| Explain the professional pattern | Regular expression and minimum requirements in each section; plain-language explanation in Part I (section 5) |',
        '| Implement with pyformlang | `ProfileAutomaton.dfa` is a `DeterministicFiniteAutomaton` |',
        '| Test cases and scenarios | `stage3_tests.md`; `tests/test_stage3.py` (section 8: scenarios), `test_stage3_regressions.py` and `test_pipeline_contract.py` |',
        '| Module design (functions, inputs and outputs) | Part I of this document (sections 2–4) |', '',
        'The assignment presents technologies as examples and asks the team to define the patterns. '
        'For that reason Full Stack accepts a backend by language/runtime or by framework, SQL or NoSQL, and makes '
        'the frontend framework, APIs and deployment optional. ML requires one skill from the ML_FRAMEWORKS group, '
        'without requiring Scikit-learn and a deep-learning framework at the same time. '
        'These are explicit team decisions, not additional textual requirements of the instructor.', '',
        'The assignment mentions detailed requirements that would be provided separately. '
        'This verification is based on `docs/Initial Doc.md`; it must also be checked against any '
        'instructor annex that is not in the repository.', '',
        'All four stages are integrated: extraction with re, normalization and ordering with '
        'pyformlang FSTs, DFA recognition, and a textX-validated DSL before HTML generation. '
        'The literature review is in `literature_review.md`. '
        'Stages 1 and 2 are documented in `stage1_regex.md` and `stage2_fst.md`.', '',
        'The test-case and scenario design of this stage is in [`stage3_tests.md`](stage3_tests.md).', '',
        'Run `python -m pytest -q` to verify the scenarios. The regressions cover '
        'simultaneous classification, strict evaluation, optional categories, years 0/3/10/25, '
        'totality of δ, diagrams, omission of each requirement and the 1024 presence combinations '
        'of the ten Full Stack categories.', '',
    ]
    def demote(block):
        out, fence = [], False
        for line in block:
            if line.startswith('```'):
                fence = not fence
            if not fence and line.startswith('#'):
                line = '#' + line
            out.append(line)
        return out

    first = lines.index('## Contract and design criteria')
    verification = lines.index('## Verification against assignment item 3')
    document = [
        '# Stage 3 — Qualification Pattern Recognition: Design and Formalization', '',
        'Generated with `python scripts/export_formalization.py` from the executable models: every table, count '
        'and example below was produced by running the real code, so the document cannot drift from the implementation.', '',
        '**Contents**', '',
        '- **Part I — Design:** purpose and scope, architecture, module reference (functions, inputs and outputs), '
        'how a candidate is classified, the four profiles in plain language, design notes on the automata, '
        'worked examples, integration with the other stages, design decisions, limitations, how to run, references.',
        '- **Part II — Formalization:** contract, automaton type and formal semantics; the formal framework '
        '(definitions, Lemmas 1–2 and Theorems 1–5 with proofs: language of each automaton, totality and determinism, '
        'no useless states, minimality, correctness of the preparation; complexity; correspondence between the mathematics '
        'and the code; worked examples of δ); and for each profile the tuple (Q, Σ, δ, q0, F), the recognized pattern, '
        'the complete δ table, structural properties (state languages, witnesses, minimality) and the diagram.',
        '- **Verification against assignment item 3.**',
        '- Test-case and scenario design: [`stage3_tests.md`](stage3_tests.md).', '',
        '---', '',
        '## Part I — Design', '',
    ] + demote(build_design_section()) + [
        '', '---', '', '## Part II — Formalization', '',
    ] + demote(lines[first:verification]) + ['---', ''] + lines[verification:]
    (ROOT / 'docs/stage3_formalization.md').write_text('\n'.join(document), encoding='utf-8')


if __name__ == '__main__':
    export_formalization()
