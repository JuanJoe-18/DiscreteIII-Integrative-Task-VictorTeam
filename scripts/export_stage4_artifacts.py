"""Regenerate the Stage 4 diagrams and formal tables used by docs/stage4_grammar.md.

    python scripts/export_stage4_artifacts.py            # diagrams + tables
    python scripts/export_stage4_artifacts.py --tables   # only print the tables
    python scripts/export_stage4_artifacts.py --bnf      # BNF grouped by left-hand side
    python scripts/export_stage4_artifacts.py --proof    # tabular proof of an example

Outputs (docs/diagrams/stage4 and docs/diagrams/stage4_tests):
* DOT diagrams computed from the code: the parse tree of an example built by
  the pure-BNF model of scripts/stage4_bnf.py, the lexical automata and
  the textX metamodel exported from candidate.tx;
* Mermaid diagrams kept as .mmd sources next to their PNG.
PNG files need Graphviz ``dot`` and, for Mermaid, ``mmdc`` (mermaid-cli). If a
tool is missing the sources are still written and the step is reported.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import stage4_bnf as G  # noqa: E402

OUT = ROOT / 'docs' / 'diagrams' / 'stage4'
OUT_TESTS = ROOT / 'docs' / 'diagrams' / 'stage4_tests'

EXAMPLE = ('candidate { personal { name "Ana"; } contact { email "ana@example.com"; } '
           'experience { total_years 2; } education { } '
           'skills { skill PYTHON; unrecognized "Figma"; } '
           'classification { accepted data_scientist; } }')

MERMAID = {
    OUT / 's4_00_architecture': '''flowchart LR
  subgraph S4["src/stage4_grammar"]
    TX["candidate.tx<br/>EBNF grammar (textX)"]
    PA["parser.py<br/>parse_profile · domain checks"]
    MO["models.py<br/>CandidateProfile (frozen)"]
    GE["generator.py<br/>candidate_from_results · serialize_profile"]
    RE["renderer.py<br/>validate_document · HTML"]
    CLI["__main__.py<br/>command line"]
  end
  S1["Stage 1<br/>contact regexes"] -.reused by.-> PA
  S2["Stage 2<br/>canonical vocabulary"] -.reused by.-> PA
  S2 -.-> GE
  S3["Stage 3<br/>profile titles · DFA results"] -.-> RE
  TX --> PA --> MO
  PA --> GE --> RE
  RE --> CLI
  RE --> PIPE["src/pipeline.py"]
  PIPE --> API["src/web_api/server.py"] --> WEB["frontend (React)"]
  PIPE --> UI["src/ui/app.py (Streamlit)"]
''',
    OUT / 's4_01_processing_flow': '''flowchart TD
  A(["DSL text"]) --> B{"Lexical + syntactic<br/>recognition (textX PEG)<br/>w ∈ L(G)?"}
  B -- no --> E1["ProfileValidationError<br/>kind = syntax, line:column"]
  B -- yes --> C["Object graph<br/>(parse tree with attributes)"]
  C --> D{"Model processor<br/>domain predicate D(m)?<br/>C1 … C5"}
  D -- no --> E2["ProfileValidationError<br/>kind = semantic, line:column"]
  D -- yes --> F["CandidateProfile<br/>(immutable)"]
  F --> G["_render: escape every value"]
  G --> H(["ProfileDocument<br/>profile · dsl · html"])
  style E1 fill:#fde2e2,stroke:#b42318
  style E2 fill:#fde2e2,stroke:#b42318
  style H fill:#dcfce7,stroke:#15803d
''',
    OUT / 's4_02_generation_sequence': '''sequenceDiagram
  autonumber
  participant P as pipeline.process_resume
  participant S1 as Stage 1 (re)
  participant S2 as Stage 2 (FST)
  participant S3 as Stage 3 (DFA)
  participant A as candidate_from_results
  participant Z as serialize_profile
  participant V as validate_document
  P->>S1: résumé text
  S1-->>P: ExtractionResult (name, contact, years, titles, education)
  P->>S2: raw skill mentions
  S2-->>P: canonical tokens + traces
  P->>S3: canonical tokens
  S3-->>P: verdict per profile
  P->>A: extraction, normalization, classification
  A-->>P: CandidateProfile (no invented data)
  P->>Z: CandidateProfile
  Z->>Z: emit DSL, then parse it again (round trip)
  Z-->>P: DSL text
  P->>V: DSL text
  V-->>P: ProfileDocument (profile, dsl, html)
''',
    OUT / 's4_03_document_structure': '''flowchart LR
  C["candidate { … }"] --> P["personal<br/>name? · summary? · location?"]
  C --> K["contact<br/>(email | phone | linkedin | github TEXT ;)*"]
  C --> X["experience<br/>total_years? · entry*"]
  X --> XE["entry<br/>title · organization? · period? · description?"]
  C --> E["education<br/>entry*"]
  E --> EE["entry<br/>qualification · institution? · period?"]
  C --> S["skills<br/>(skill TOKEN ; | unrecognized TEXT ;)*"]
  C --> L["classification<br/>(accepted profile_id ;)*"]
''',
    OUT / 's4_04_class_diagram': '''classDiagram
  class CandidateProfile {
    +str|None name
    +str|None summary
    +str|None location
    +tuple~Contact~ contacts
    +int|None years_of_experience
    +tuple~Experience~ experiences
    +tuple~Education~ education
    +tuple~str~ skills
    +tuple~str~ unrecognized_skills
    +tuple~str~ accepted_profiles
  }
  class Contact { +str kind  +str value }
  class Experience { +str title  +str|None organization  +str|None period  +str|None description }
  class Education { +str qualification  +str|None institution  +str|None period }
  class ProfileDocument { +CandidateProfile profile  +str dsl  +str html  +to_dict() }
  class ProfileValidationError { +str kind  +int|None line  +int|None column  +str|None filename }
  CandidateProfile "1" *-- "0..*" Contact
  CandidateProfile "1" *-- "0..*" Experience
  CandidateProfile "1" *-- "0..*" Education
  ProfileDocument "1" o-- "1" CandidateProfile
  ValueError <|-- ProfileValidationError
''',
    OUT / 's4_08_adapter_mapping': '''flowchart LR
  subgraph In["Results of Stages 1–3"]
    N["candidate_name"]
    CT["contact{kind: [values]}"]
    Y["years_of_experience"]
    J["job_titles"]
    ED["education"]
    T["normalized_tokens"]
    TR["traces (recognized = false)"]
    R["results_by_profile (is_accepted)"]
  end
  subgraph Out["DSL sections"]
    PN["personal.name"]
    CO["contact entries"]
    TY["experience.total_years"]
    XE["experience.entry.title"]
    EQ["education.entry.qualification"]
    SK["skills: skill TOKEN"]
    UN["skills: unrecognized TEXT"]
    AC["classification: accepted id"]
  end
  N --> PN
  CT -->|dedupe, keep order| CO
  Y -->|None stays absent; 0 stays 0| TY
  J -->|one partial record each| XE
  ED -->|one partial record each| EQ
  T -->|∩ vocabulary, without EXPERIENCE_PRESENT| SK
  TR -->|original spelling| UN
  R -->|copy, never recompute| AC
''',
    OUT / 's4_09_language_layers': '''flowchart TB
  subgraph U["T* — every token sequence"]
    subgraph LG["L(G) — syntactically valid documents (LL(1), regular)"]
      subgraph LV["L_valid = { w ∈ L(G) : D(model(w)) } — accepted by parse_profile"]
        GEN["image of serialize_profile<br/>(canonical forms)"]
      end
    end
  end
  style U fill:#f8fafc,stroke:#64748b
  style LG fill:#e0f2fe,stroke:#0369a1
  style LV fill:#dcfce7,stroke:#15803d
  style GEN fill:#fef9c3,stroke:#a16207
''',
    OUT_TESTS / 's4t_00_layers': '''flowchart TB
  A["test_stage4_grammar.py · 58<br/>language: partitions, violations, unicode, CLI"]
  B["test_stage4_generation.py · 29<br/>serialization, round trips, HTML, concurrency"]
  C["test_pipeline_stage4.py · 11<br/>Stages 1 → 4 with résumé fixtures"]
  D["test_web_stage4.py · 10<br/>HTTP: /api/evaluate and /api/validate-profile"]
  U["Unit level: parser, generator, renderer"]
  I["Integration level: pipeline and web API"]
  A --> U
  B --> U
  C --> I
  D --> I
  U --> I
''',
    OUT_TESTS / 's4t_01_validation': '''flowchart LR
  S["DSL text"] --> L{"textX: lexical and<br/>syntactic rules"}
  L -- no --> E1["syntax error<br/>line and column"]
  L -- yes --> M["model processors<br/>C1 to C5"]
  M --> C{"domain predicate"}
  C -- no --> E2["semantic error"]
  C -- yes --> V["validated model"]
  V --> R["serialize + re-parse<br/>(round-trip check)"]
  R --> H["escaped HTML"]
  E1 --> N["no HTML written"]
  E2 --> N
''',
    OUT_TESTS / 's4t_02_mutation': '''flowchart LR
  F["fresh copy of src/stage4_grammar"] --> X["apply one mutant<br/>(literal text replacement)"]
  X --> T["run the 108 Stage 4 tests"]
  T --> Q{"any failure?"}
  Q -- yes --> K["mutant killed"]
  Q -- no --> S["mutant survived<br/>(gap or equivalent)"]
''',
}


EXAMPLE_PROOF = ('candidate { personal { name "Ana" ; } contact { } experience { } education { } '
                 'skills { skill PYTHON ; } classification { } }')


def class_notation() -> str:
    """The pure BNF grouped by left-hand side, written as in class: A -> alpha | beta."""
    lines = []
    for lhs, rhss in G.BNF.items():
        alts = ' | '.join(' '.join(r) if r else 'ε' for r in rhss)
        lines.append(f'{lhs} → {alts}')
    return '\n'.join(lines)


def tabular_proof(source: str = EXAMPLE_PROOF) -> str:
    """Tabular proof (step, rule, sentential form) that `source` is generated by G."""
    prods = G.productions()
    index = {pr: n for n, pr in enumerate(prods, 1)}
    tree = G.parse_tokens(G.tokenize(source))
    frontier = [tree]
    rows = []

    def show(nodes):
        out = []
        for n in nodes:
            if n.symbol in G.BNF:
                out.append(f'⟨{n.symbol}⟩')
            elif n.symbol in G.TOKEN_CLASSES:
                out.append(n.token.lexeme)
            else:
                out.append(n.symbol)
        return ' '.join(out) if out else 'ε'

    rows.append((1, 'Start', show(frontier)))
    step = 1
    while True:
        for i, n in enumerate(frontier):
            if n.symbol in G.BNF:
                rhs = tuple(c.symbol for c in n.children if c.symbol != G.EPS)
                step += 1
                label = f'Expand ⟨{n.symbol}⟩ with p{index[(n.symbol, rhs)]}' + (' (ε)' if not rhs else '')
                frontier = frontier[:i] + [c for c in n.children if c.symbol != G.EPS] + frontier[i + 1:]
                rows.append((step, label, show(frontier)))
                break
        else:
            break
    out = ['| Step | Rule / action | Sentential form |', '|---|---|---|']
    out += [f'| {a} | {b} | {c} |' for a, b, c in rows]
    return '\n'.join(out)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def render_dot(dot_source: str, target: Path, dpi=120):
    target.with_suffix('.dot').write_text(dot_source, encoding='utf-8')
    if not shutil.which('dot'):
        print(f'skip {target.name}.png (Graphviz dot not installed)')
        return
    r = run(['dot', '-Tpng', f'-Gdpi={dpi}', str(target.with_suffix('.dot')), '-o', str(target.with_suffix('.png'))])
    if r.returncode:
        raise RuntimeError(r.stderr)


def render_mermaid(source: str, target: Path):
    target.with_suffix('.mmd').write_text(source, encoding='utf-8')
    mmdc = shutil.which('mmdc')
    if not mmdc:
        print(f'skip {target.name}.png (mermaid-cli mmdc not installed)')
        return
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / 'puppeteer.json'
        chromium = shutil.which('chromium') or '/opt/pw-browsers/chromium'
        cfg.write_text(json.dumps({'executablePath': chromium, 'args': ['--no-sandbox']}))
        r = run([mmdc, '-p', str(cfg), '-i', str(target.with_suffix('.mmd')),
                 '-o', str(target.with_suffix('.png')), '-s', '2', '-b', 'white'])
    if r.returncode:
        raise RuntimeError(r.stderr or r.stdout)


def parse_tree_dot(source: str) -> str:
    tree = G.parse_tokens(G.tokenize(source))
    lines = ['digraph parse_tree {', '  graph [rankdir=TB, nodesep=0.12, ranksep=0.35, fontname="Helvetica"];',
             '  node [fontname="Helvetica", fontsize=11, shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0369a1"];',
             '  edge [color="#64748b", arrowsize=0.5];']
    counter = [0]

    def visit(node):
        counter[0] += 1
        nid = f'n{counter[0]}'
        if node.symbol in G.BNF:
            lines.append(f'  {nid} [label="{node.symbol}"];')
        elif node.symbol == G.EPS:
            lines.append(f'  {nid} [label="ε", shape=plaintext, style="", fontcolor="#94a3b8"];')
        else:
            label = node.token.lexeme if node.symbol in G.TOKEN_CLASSES else node.symbol
            label = label.replace('\\', '\\\\').replace('"', '\\"')
            if node.symbol in G.TOKEN_CLASSES:
                label = f'{node.symbol}\\n{label}'
            lines.append(f'  {nid} [label="{label}", shape=box, style="filled", fillcolor="#fef9c3", color="#a16207"];')
        for child in node.children:
            cid = visit(child)
            lines.append(f'  {nid} -> {cid};')
        return nid

    visit(tree)
    lines.append('}')
    return '\n'.join(lines)


LEXICAL_DOT = r'''digraph lexical {
  graph [rankdir=LR, fontname="Helvetica", nodesep=0.3];
  node [fontname="Helvetica", fontsize=11, shape=circle, style=filled, fillcolor="#e0f2fe", color="#0369a1"];
  edge [fontname="Helvetica", fontsize=10, color="#334155"];
  subgraph cluster_uint { label="UINT  =  0 | [1-9][0-9]*"; color="#94a3b8"; fontname="Helvetica";
    u0 [label="u0"]; u1 [label="u1", shape=doublecircle]; u2 [label="u2", shape=doublecircle];
    su [shape=point, width=0.05]; su -> u0;
    u0 -> u1 [label="0"]; u0 -> u2 [label="1-9"]; u2 -> u2 [label="0-9"]; }
  subgraph cluster_canon { label="CANONICAL_TOKEN  =  [A-Z][A-Z0-9_]*"; color="#94a3b8"; fontname="Helvetica";
    c0 [label="c0"]; c1 [label="c1", shape=doublecircle];
    sc [shape=point, width=0.05]; sc -> c0;
    c0 -> c1 [label="A-Z"]; c1 -> c1 [label="A-Z 0-9 _"]; }
  subgraph cluster_text { label="TEXT  =  \" ( [^\"\\ control] | \\ ( [\"\\/bfnrt] | u hex{4} ) )* \""; color="#94a3b8"; fontname="Helvetica";
    t0 [label="t0"]; t1 [label="t1"]; t2 [label="t2", shape=doublecircle]; te [label="esc"];
    h1 [label="h1"]; h2 [label="h2"]; h3 [label="h3"]; h4 [label="h4"];
    st [shape=point, width=0.05]; st -> t0;
    t0 -> t1 [label="\""]; t1 -> t1 [label="any char except \" \\ U+0000–U+001F"];
    t1 -> te [label="\\"]; te -> t1 [label="\" \\ / b f n r t"];
    te -> h1 [label="u"]; h1 -> h2 [label="hex"]; h2 -> h3 [label="hex"]; h3 -> h4 [label="hex"]; h4 -> t1 [label="hex"];
    t1 -> t2 [label="\""]; }
}
'''


def metamodel_dot() -> str | None:
    try:
        from textx import metamodel_from_file
        from textx.export import metamodel_export
    except ImportError:
        return None
    mm = metamodel_from_file(str(ROOT / 'src' / 'stage4_grammar' / 'candidate.tx'), autokwd=True)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'mm.dot'
        metamodel_export(mm, str(path))
        return path.read_text(encoding='utf-8')


# ----------------------------------------------------------------------- tables

def fmt_set(values):
    order = lambda v: (v == G.END, v)
    return ', '.join(f'`{v}`' for v in sorted(values, key=order))


def tables() -> str:
    nullable, first, follow = G.nullable_set(), G.first_sets(), G.follow_sets()
    out = ['| Nonterminal | Nullable | FIRST | FOLLOW |', '|---|---|---|---|']
    for a in G.NONTERMINALS:
        out.append(f'| `{a}` | {"yes" if a in nullable else "no"} | {fmt_set(first[a])} | {fmt_set(follow[a])} |')
    out += ['', '| # | Production | PREDICT |', '|---|---|---|']
    for i, (lhs, rhs, predict) in enumerate(G.predict_sets(), 1):
        body = ' '.join(rhs) if rhs else 'ε'
        out.append(f'| p{i} | `{lhs} → {body}` | {fmt_set(predict)} |')
    table, conflicts = G.ll1_table()
    out += ['', f'LL(1) table entries: {len(table)}; conflicts: {len(conflicts)}.']
    return '\n'.join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--tables', action='store_true', help='only print the FIRST/FOLLOW/PREDICT tables')
    parser.add_argument('--bnf', action='store_true', help='only print the BNF grouped by left-hand side')
    parser.add_argument('--proof', action='store_true', help='only print the tabular proof of the example')
    args = parser.parse_args(argv)
    if args.bnf:
        print(class_notation())
        return 0
    if args.proof:
        print(tabular_proof())
        return 0
    if args.tables:
        print(tables())
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_TESTS.mkdir(parents=True, exist_ok=True)
    for target, source in MERMAID.items():
        render_mermaid(source, target)
    render_dot(parse_tree_dot(EXAMPLE), OUT / 's4_05_parse_tree', dpi=90)
    render_dot(LEXICAL_DOT, OUT / 's4_06_lexical_automata')
    mm = metamodel_dot()
    if mm:
        render_dot(mm, OUT / 's4_07_textx_metamodel', dpi=110)
    print(f'diagrams written to {OUT.relative_to(ROOT)} and {OUT_TESTS.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
