# Stage 4 and complete-pipeline test design

## Automated evidence

The complete repository suite passed **796 tests** on 11 October 2026 with
Python 3.12, pyformlang 1.0.11, textX 4.4.0 and pytest 9.1.1.
This is a test-case count, not a code-coverage percentage or an accuracy measure.
The React production build also passed TypeScript checking and Vite compilation.

```powershell
python -m pytest tests -q
pnpm --dir frontend build
```

| Suite | Technique | Contract protected |
|---|---|---|
| `test_stage4_grammar.py` | Equivalence partitions; delimiter and order mutations | Whole-input recognition, required records, vocabulary and error locations |
| `test_stage4_generation.py` | Round trips; adversarial text; numeric boundaries | Model preservation, escaping, valid output, no file creation/overwrite on invalid input |
| `test_pipeline_stage4.py` | Four positive profile cases and negative controls | Real FST preparation, actual DFA acceptance copied to the DSL |
| `test_web_stage4.py` | HTTP integration, invalid request partitions | JSON contract, 400 errors with source locations, no HTML on failure |
| Existing Stages 1–3 suites | Formal-model and regression checks | Extraction boundaries, transductions, vocabulary, automaton transitions |

## Meaningful examples

1. `Git, SQL, Node.js, JavaScript` appears out of order in resume text. Stage 2
   orders the Full Stack sequence and Stage 3 accepts it. The same reverse order
   in direct-token mode is rejected.
2. `Python, Pandas, Matplotlib, Scikit-learn, SQL, Git` accepts both Machine
   Learning Engineer and Data Scientist. Both IDs survive DSL serialization.
3. A resume with `python@gmail.com` and no Python skill cannot acquire a Python
   qualification from the email address.
4. A complete profile with two jobs and two education records round-trips without
   losing optional attributes. The text extractor's partial records do not invent
   employers or dates.
5. Missing years produce no numeric claim. Explicit zero remains zero.
6. Quotes, backslashes, accented text, newlines and emoji remain data. HTML tags
   are escaped; unquoted identifier injection is rejected before serialization.
7. Invalid DSL leaves an existing output HTML file unchanged. Concurrent parsing
   keeps candidate models separate.

## Browser verification

The built React app was exercised against the local Python server. A fictional
candidate qualified for ML and Data Scientist; the generated preview contained
the same declarations and extracted contact/years. Editing the DSL to
`candidate {` immediately disabled HTML download and removed the preview.
Validation reported a syntax error at line 1, column 12. Restoring the generated
result and revalidating restored the preview. These observations complement the
automated tests; they do not constitute cross-browser certification.

Streamlit 1.65.0 was also checked with `streamlit.testing.v1.AppTest`: the normal
pipeline renders the structured profile, while strict-token and skipped-Stage-2
demonstrations do not expose a generated candidate document. All three runs
completed without application exceptions.

## Scope limits

There is no annotated real-world dataset, performance benchmark, fairness
evaluation or extraction precision/recall claim. The contact formats and fixed
vocabulary deliberately follow this project's implementation. Automated tests
do not prove student understanding or replace a live demonstration.
