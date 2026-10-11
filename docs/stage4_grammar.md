# Stage 4 - Candidate Profile Language

## 1. Purpose and current scope

Stage 4 represents candidate information in a domain-specific language (DSL).
The grammar describes the structure of the information; Stage 3 remains responsible
for deciding which qualification patterns the candidate satisfies.

This increment implements the grammar, textX parser, domain checks, immutable
output records, a validation command, and valid/invalid examples. Automatic DSL
generation from Stages 1-3 and HTML/Markdown rendering are subsequent increments.
The validation command's JSON is an inspection aid, not the final visualization.

## 2. Module design and contracts

| Module | Responsibility | Input | Output |
|---|---|---|---|
| `src/stage4_grammar/candidate.tx` | Executable syntax | DSL source | textX object graph |
| `src/stage4_grammar/parser.py` | Parsing, domain checks, conversion | Complete source string or UTF-8 file | `CandidateProfile` or `ProfileValidationError` |
| `src/stage4_grammar/models.py` | Structured candidate records | Parsed values | Frozen Python dataclasses |
| `src/stage4_grammar/__main__.py` | Command-line validation | `.resume` path | JSON and exit 0, or error and exit 1 |

Public Python API:

```python
from src.stage4_grammar import parse_profile, parse_profile_file, ProfileValidationError

profile = parse_profile_file("docs/examples/wednesday.resume")
print(profile.name, profile.skills, profile.accepted_profiles)

try:
    parse_profile("candidate {}")
except ProfileValidationError as error:
    print(error.kind, error.line, error.column, error.message)
```

The returned model contains `name`, `summary`, `location`, `contacts`,
`years_of_experience`, `experiences`, `education`, `skills`,
`unrecognized_skills`, and `accepted_profiles`. Repeated values are tuples;
missing optional scalars are `None`. The model can be converted to a dictionary
with `dataclasses.asdict`. Its constructor alone does not validate values:
`parse_profile` and `parse_profile_file` are the validation boundary.

## 3. Formal grammar

We define a token-level context-free grammar **G = (N, T, P, S)**:

- **S** = `Candidate`.
- **N** = {`Candidate`, `Personal`, `ContactSection`, `Contact`, `ContactKind`,
  `ExperienceSection`, `Experience`, `EducationSection`, `Education`,
  `SkillSection`, `Skill`, `KnownSkill`, `UnrecognizedSkill`, `Classification`,
  `AcceptedProfile`, `ProfileId`}.
- **T** consists of the keyword and punctuation terminals written between quotes
  in the productions below, plus the token kinds `TEXT`, `CANONICAL_TOKEN`, and
  `UINT`. A token carries its lexeme as an attribute; those lexical classes are
  defined in section 4.
- **P** is the following EBNF. Commas denote concatenation, `|` alternatives,
  square brackets an optional sequence, and unquoted braces repetition.

```ebnf
Candidate = "candidate", "{", Personal, ContactSection, ExperienceSection,
            EducationSection, SkillSection, Classification, "}" ;

Personal = "personal", "{",
           ["name", TEXT, ";"],
           ["summary", TEXT, ";"],
           ["location", TEXT, ";"], "}" ;

ContactSection = "contact", "{", {Contact}, "}" ;
Contact = ContactKind, TEXT, ";" ;
ContactKind = "email" | "phone" | "linkedin" | "github" ;

ExperienceSection = "experience", "{", ["total_years", UINT, ";"],
                    {Experience}, "}" ;
Experience = "entry", "{", "title", TEXT, ";",
             ["organization", TEXT, ";"],
             ["period", TEXT, ";"],
             ["description", TEXT, ";"], "}" ;

EducationSection = "education", "{", {Education}, "}" ;
Education = "entry", "{", "qualification", TEXT, ";",
            ["institution", TEXT, ";"],
            ["period", TEXT, ";"], "}" ;

SkillSection = "skills", "{", {Skill}, "}" ;
Skill = KnownSkill | UnrecognizedSkill ;
KnownSkill = "skill", CANONICAL_TOKEN, ";" ;
UnrecognizedSkill = "unrecognized", TEXT, ";" ;

Classification = "classification", "{", {AcceptedProfile}, "}" ;
AcceptedProfile = "accepted", ProfileId, ";" ;
ProfileId = "full_stack" | "machine_learning" | "cloud_devops" | "data_scientist" ;
```

An optional sequence `A = [B]` can be expanded into `A -> B | epsilon`.
A repetition `A = {B}` can be expanded into `A -> B A | epsilon`.
Every production has one nonterminal on its left-hand side, so these expansions
give CFG productions. Every nonterminal is reachable from `Candidate` and
productive; optional/repeated components have finite base cases.

The grammar models a fixed section structure with repeated records. It does not
claim that this language is nonregular, nor require arbitrary recursive nesting.
textX executes its grammar through a PEG parser with ordered choices. Here the
alternatives have distinct leading keywords, avoiding dependence on ambiguous
alternatives. This is an implementation of the documented syntax, not a claim
that textX is a general-purpose CFG parser.

## 4. Lexical specification

| EBNF token | textX match rule | Language |
|---|---|---|
| `TEXT` | `Text` | Double-quoted JSON-style string |
| `CANONICAL_TOKEN` | `CanonicalToken` | `[A-Z][A-Z0-9_]*` |
| `UINT` | `NonNegativeInt` | `0` or `[1-9][0-9]*` |

`TEXT` allows Unicode characters except raw control characters, quotes, and
backslashes. Quotes and backslashes must be escaped. Supported escape forms are
`\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\u` followed by four hexadecimal
digits. The matched literal is decoded with `json.loads`. Single-quoted strings,
unknown escapes, and raw newlines inside strings are rejected.

Whitespace between tokens is ignored. `//` starts a line comment outside a text
literal. Keywords are case sensitive and matched on word boundaries. Semicolons
terminate scalar fields and list entries; braces delimit sections and records.
The entire input must be consumed, including the rejection of trailing text.

## 5. Structural and domain decisions

1. **Six sections in a fixed order.** Every document has personal, contact,
   experience, education, skills and classification sections, even when empty.
   Fixed field order and explicit delimiters simplify generation and explanation.
2. **Partial candidate information is valid.** Missing name, contact, years or
   education is represented by omission or empty lists. No placeholder identity
   is invented. Missing years and `total_years 0` remain distinct by disabling
   textX's automatic scalar defaults.
3. **Repeated information is preserved.** Multiple contacts, work experiences,
   qualifications, skills and accepted profiles can be represented. Each work
   record requires a title; each education record requires a qualification.
   Organizations, institutions, periods and descriptions are optional.
4. **Experience is independent of qualification symbols.** `EXPERIENCE_PRESENT`
   is not a technical skill. The exact amount is represented by `total_years`.
   The DSL imposes no hiring threshold and does not sum potentially overlapping jobs.
5. **Unknown skills remain evidence.** `skill` accepts the canonical vocabulary
   from Stage 2. Other text can be preserved using `unrecognized "Figma";`.
   These entries do not satisfy an automaton requirement. The parser does not
   normalize them or silently convert them into known skills.
6. **No new qualification decisions.** `accepted full_stack;` records a Stage 3
   result. An empty classification section represents no accepted profiles.
   Successful DSL validation proves neither that a declaration is true nor that
   the candidate meets the pattern. The future pipeline adapter must copy actual
   Stage 3 results; it must not invent accepted profiles from the DSL.

After syntax recognition, textX model processors enforce these domain checks:

- Present text fields must contain non-whitespace content.
- Contact values must fully match the corresponding Stage 1 contact expression.
  This reuses the project's supported formats, not a universal email/phone standard.
- Known skill tokens must belong to `all_canonical_tokens()` from Stage 2.
- Exact duplicate contacts, known skills, unrecognized skills, or accepted
  profiles are rejected. Different contacts of the same kind are allowed.

These checks are semantic constraints and are **not** part of the CFG's syntax.
Periods remain descriptive text; no date arithmetic is attempted. Text fields
may contain HTML characters; the later renderer must escape them before display.

## 6. Validation and examples

```bash
python -m pip install -r requirements.txt
python -m src.stage4_grammar docs/examples/wednesday.resume
python -m src.stage4_grammar docs/examples/invalid_candidate.resume
python -m pytest tests/test_stage4_grammar.py -q
```

The first example is fictional and demonstrates two work records, two education
records, contact data, canonical and unrecognized skills, and an accepted profile.
The second intentionally uses lowercase `javascript`, which is not a canonical
token. A validation failure writes an error to stderr, emits no successful model,
and exits with code 1. Syntax and semantic errors include line and column; a file
input also retains its filename. Semantic locations point to the offending record.

## 7. Test-case design

Tests are in `tests/test_stage4_grammar.py`.

| Scenario / technique | Expected behavior |
|---|---|
| Valid complete example; repeated records | Preserve values, order and optional omissions |
| Minimal document; missing vs zero years | Empty sections accepted; `None` differs from `0` |
| Vocabulary contract with Stages 2/3 | Every canonical skill and the four profile IDs are representable |
| Lexical partitions | Reject lowercase tokens, dotted tokens, invalid escapes and unquoted text |
| Numeric boundaries | Accept zero; reject negatives, decimals, quoted numbers and leading zeros |
| Syntactic mutations | Reject missing/duplicated/reordered sections, missing delimiters and trailing text |
| Record requirements | Reject a work entry without title or an education entry without qualification |
| Domain constraints | Reject unsupported contact formats, unknown canonical skills and duplicate set entries |
| Data preservation | Keep Unicode, quotes, backslashes, escaped newlines and punctuation within text |
| Isolation | Parsing a second document cannot change the first immutable result |
| Error diagnostics / CLI | Preserve location and nonzero failure status; no traceback for missing files |
| Separation from Stage 3 | Parsing a declaration never recomputes or certifies qualification acceptance |

## 8. References

- Course assignment, *Integrative Task 1 (2026-2)*, Stage 4: EBNF, textX,
  validation and visualization; reproduced in `docs/Initial Doc.md`.
- Course material: *BNF* and *Context-Free Grammars*, supplied with the assignment.
- [textX grammar](https://textx.github.io/textX/grammar.html): assignments,
  repetitions, match rules and PEG choices.
- [textX metamodel](https://textx.github.io/textX/metamodel.html): model processors,
  match-rule conversions and optional attribute initialization.
- [textX error handling](https://textx.github.io/textX/error_handling.html):
  syntax/semantic errors and source locations.
