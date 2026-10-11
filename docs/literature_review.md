# Literature review and design rationale

## Scope

This focused review supports an educational, deterministic resume-processing
pipeline. It covers explicit extraction, formal transduction and recognition,
and structured profile languages. It is not a systematic review of recruitment
systems and does not evaluate candidate ranking. Sources were consulted on
11 October 2026; the implemented behavior is documented separately in the stage
formalizations and tests.

## Regular expressions for explicit evidence

Python's `re` documentation distinguishes searching from matching an entire
string and provides grouping, alternation and repetition constructs. Those
operations support the project's extraction patterns and full contact checks.
The project additionally tracks sections and overlap so that text inside contact
addresses does not supply skills. These contextual decisions are application
logic, rather than properties guaranteed by a regex engine. [Python `re`](https://docs.python.org/3/library/re.html)

The course notes on regular languages supply the connection between expressions
and finite automata. Python patterns can include implementation features beyond
basic regular-language notation; therefore the formal explanations identify
the supported pattern language and boundaries explicitly. The files
`docs/stage1_regex.md` and `docs/stage1_tests.md` explain each extractor and its
negative examples. A phrase mentioning a technology still does not establish
proficiency, recency or actual experience.

## Executable formal models with pyformlang

Romero presents pyformlang as an educational Python library for manipulating
formal languages and experimenting with their algorithms. Its executable models
make it suitable for comparing formal definitions with program behavior. The
paper supports the educational choice; it is not evidence that ResumeLens has
high hiring accuracy. [Romero, 2021](https://doi.org/10.1145/3408877.3432464)

In ResumeLens, Stage 2 uses transducers to map variants such as `Node.js` into
`NODE_JS`, while Stage 3 executes four DFAs on canonical symbols. We chose a
deterministic model because each state/input pair has one next state and a trace
can explain every decision. A lookup table alone could normalize aliases, but
would not demonstrate the required transduction model. The formal 7-tuples and
5-tuples are in the Stage 2 and Stage 3 documentation. These are project design
decisions grounded in the assignment, not comparative benchmark findings.

## A candidate DSL with textX

Dejanović and colleagues describe textX as a Python tool that builds a parser
and metamodel from a language description and constructs an object model from
the input. This supports a concise grammar for repeated work, education, contact
and profile records. [Dejanović et al., 2017](https://doi.org/10.1016/j.knosys.2016.10.023)

The official grammar documentation describes textX's PEG-based choices and
assignments. We document an EBNF structure, while acknowledging that textX uses
an Arpeggio PEG parser: ordered choice is not arbitrary CFG nondeterminism. Our
alternatives begin with distinct keywords, limiting that operational difference
for this DSL. [textX grammar documentation](https://textx.github.io/textX/grammar.html)

The model processor checks facts that are not purely grammatical, such as
membership in the skill vocabulary and duplicate entries. Optional values must
preserve absence: unknown experience differs from zero years. textX exposes
model processors and configurable attribute initialization for these tasks.
[textX metamodel documentation](https://textx.github.io/textX/metamodel.html)

## Alternatives and synthesis

| Approach | Possible role | Reason for this project's choice |
|---|---|---|
| Regex-only document processing | Extract individual fragments | Explicit grammar better documents the six output sections and repeated records |
| Direct JSON output | General interchange representation | JSON remains the API format; the task specifically requires an EBNF/textX DSL |
| Direct template rendering | Turn extracted values into HTML | An intermediate validated language exposes structural errors before rendering |
| Probabilistic semantic extraction | Broader contextual interpretation | Outside this implementation; no dataset or comparative evaluation was supplied |

The resulting separation makes the artifact explainable: regex finds reported
evidence, FSTs normalize it, DFAs decide pattern membership, and textX checks the
output document. Grammar validity, rule-based acceptance and factual correctness
remain separate claims. Further research should use an annotated resume corpus
to measure extraction precision/recall and examine context such as negation.
The current tests do not substitute for that study.

## Bibliography

1. Romero, J. (2021). *Pyformlang: An Educational Library for Formal Language
   Manipulation*. SIGCSE '21. DOI: 10.1145/3408877.3432464.
2. Dejanović, I., Vaderna, R., Milosavljević, G., & Vuković, Ž. (2017).
   *TextX: A Python tool for Domain-Specific Languages implementation*.
   Knowledge-Based Systems, 115, 1–4. DOI: 10.1016/j.knosys.2016.10.023.
3. Python Software Foundation. *re — Regular expression operations*. Online documentation.
4. textX contributors. *Grammar*, *Meta-model*, and *Error handling*. Online documentation.
5. Course material supplied with the task: *BNF*, *CFG*, *CyEDIIITransducers*,
   *mainRegexReviewRepaso*, *RG*, and *Integrative Task 1 (2026-2)*.
