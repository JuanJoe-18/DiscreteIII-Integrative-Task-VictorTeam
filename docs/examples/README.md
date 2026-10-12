# `docs/examples/` — Stage 4 examples

| File | What it is |
|---|---|
| `wednesday.resume` | A complete, valid DSL document (fictional): two jobs, two studies, contacts, canonical and unrecognized skills, one accepted profile |
| `wednesday.html` | The HTML generated from `wednesday.resume` with `python -m src.stage4_grammar docs/examples/wednesday.resume --html docs/examples/wednesday.html` |
| `invalid_candidate.resume` | An invalid document (lower-case skill symbol `javascript`) used to demonstrate a located syntax error and exit code 1 |

The grammar of these files is explained in [`../stage4_grammar.md`](../stage4_grammar.md).
