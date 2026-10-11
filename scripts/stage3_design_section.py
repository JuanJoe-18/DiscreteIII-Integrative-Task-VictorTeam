"""Design section of docs/stage3_formalization.md.

Builds, by running the real Stage 3 objects (and Stages 1-2 for the worked examples), the Markdown lines
of Part I (design: modules, inputs/outputs, flow, profiles in plain language, worked examples).
Used by scripts/export_formalization.py.
"""
import dataclasses
import inspect
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_design_section():
    """Return the Markdown lines of the design part (headings start at level 2)."""
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        return _build()
    finally:
        os.chdir(cwd)


def _build():
    from src.stage1_regex import extract_qualifications
    from src.stage2_fst import normalize_and_sort
    from src.stage3_classifier import ResumeClassifier
    from src.stage3_classifier import classifier as C, automata_models as A, profiles as P, visualizer as V
    from src.stage3_classifier import PROFILES_REGISTRY
    clf = ResumeClassifier()
    autos = clf.automata
    out = []
    w = out.append


    def sig(fn):
        return str(inspect.signature(fn)).replace("src.stage3_classifier.", "").replace("|", "\\|")


    def render_trace(auto, result, name):
        dot = V.build_graphviz_diagram(auto, result)
        dot.format = "png"
        dot.attr(dpi="110")
        p = f"docs/diagrams/stage3/{name}"
        open(p + ".dot", "w", encoding="utf-8").write(dot.source)
        try:
            subprocess.run(["dot", "-Tpng", "-Gdpi=110", p + ".dot", "-o", p + ".png"], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("Warning: Graphviz `dot` not available; keeping the existing diagram", p)
        finally:
            os.remove(p + ".dot")


    def fields_table(cls):
        rows = ["| Field | Type | Meaning |", "|---|---|---|"]
        doc = {
            "step_number": "1-based position of the token in the evaluated word",
            "source_state": "state before reading the token (`q_trap` once trapped)",
            "symbol": "the token read",
            "target_state": "state after reading it",
            "category": "category of the token in the profile, `None` if the token is outside Σ",
            "is_valid_transition": "`False` when the move goes to (or stays in) `q_trap`",
            "profile_id": "registry key (`full_stack`, `machine_learning`, `cloud_devops`, `data_scientist`)",
            "profile_title": "human-readable profile name",
            "status": "`ACCEPTED` or `REJECTED`",
            "is_accepted": "boolean shortcut for `status == ACCEPTED`",
            "final_state": "state where the run ended (`q_trap` if rejected by a violation)",
            "expected_final_state": "the single accepting state F of the profile",
            "trace": "one `StepTransition` per input token",
            "evaluated_tokens": "the word the DFA actually read",
            "ignored_tokens": "tokens outside Σ of the profile (only filled when `prepare_input=True`)",
            "rejection_reason": "diagnostic text; `None` when accepted",
            "missing_categories": "mandatory requirement groups with no token in the input",
            "satisfied_categories": "categories of the profile observed in the input, in canonical order",
            "input_tokens": "the list given to `classify`",
            "accepted_profiles": "titles of the accepted profiles",
            "rejected_profiles": "titles of the rejected profiles",
            "results_by_profile": "`profile_id` → `ProfileEvaluationResult`",
            "name": "category name", "description": "category description", "skills": "set of canonical tokens",
            "canonical_categories": "ordered list of categories (the canonical order)",
            "domain": "domain of the profile",
            "states": "Q", "alphabet": "Σ", "transitions": "δ as a dict `(state, symbol) → state`",
            "initial_state": "q0", "final_states": "F",
        }
        for f in dataclasses.fields(cls):
            t = str(f.type).replace("typing.", "").replace("src.stage3_classifier.classifier.", "")
            rows.append(f"| `{f.name}` | `{t}` | {doc.get(f.name, '')} |")
        return "\n".join(rows)


    def run(pid, word):
        r = clf.evaluate_profile(pid, word)
        return r


    def row(case, pid, word):
        r = run(pid, word)
        w_ = ", ".join(word) if word else "*(empty)*"
        res = "ACCEPTED" if r.is_accepted else "REJECTED"
        why = f"ends in `{r.final_state}`" if r.is_accepted else (r.rejection_reason or "").replace("|", "/")
        return f"| {case} | {w_} | **{res}** | {why} |"


    w("## 1. Purpose and scope")
    w("")
    w("Stage 3 decides, for each of four professional profiles, whether a candidate's qualifications form a **word of the language** that the profile describes. The input is the list of *canonical tokens* produced by Stage 2 (for instance `PYTHON`, `PANDAS`, `GIT`); the output is, per profile, an **ACCEPTED/REJECTED verdict with a step-by-step trace** and a diagnosis (missing requirements, offending token, foreign tokens).")
    w("")
    w("| | |")
    w("|---|---|")
    w("| Input | `List[str]` of canonical tokens (Stage 2 output, sorted or not) |")
    w("| Output | `ResumeClassificationReport` (verdict + trace per profile) |")
    w("| Formal model | one **DFA** per profile, built with `pyformlang` (`DeterministicFiniteAutomaton`) |")
    w("| Profiles | Full Stack Developer, Machine Learning Engineer, Cloud & DevOps Engineer, Data Scientist |")
    w("| Not in scope | scoring, ranking, proficiency levels, hiring decisions (a candidate may match 0–4 profiles) |")
    w("")
    w("## 2. Architecture")
    w("")
    w("![Modules of Stage 3](diagrams/stage3/s3_00_architecture.png)")
    w("")
    w("Dependencies are one-directional: `profiles` → `automata_models` → `classifier` → `visualizer`. Nothing in Stage 3 imports Stages 1 or 2; the contract with them is only the *list of canonical tokens*. The scripts and the two user-facing front ends (Streamlit and the local web API) are consumers.")
    w("")
    w("| File | Responsibility |")
    w("|---|---|")
    w("| `src/stage3_classifier/profiles.py` | Declarative definition of the profiles: categories, canonical order, alphabet Σ, mandatory requirement groups |")
    w("| `src/stage3_classifier/automata_models.py` | Builds one total DFA per profile with `pyformlang`; exposes the formal 5-tuple |")
    w("| `src/stage3_classifier/classifier.py` | Executes a word step by step, produces the trace and the diagnosis; classifies a candidate against all profiles |")
    w("| `src/stage3_classifier/visualizer.py` | Graphviz and Mermaid diagrams derived from the real transition table, optionally highlighting a trace |")
    w("| `src/stage3_classifier/__init__.py` | Public API of the package |")
    w("| `scripts/export_diagrams.py` | Writes `docs/diagrams/<profile>.{dot,svg,png}` and the HTML viewer |")
    w("| `scripts/export_formalization.py` | Writes `docs/stage3_formalization.md` from the DFAs |")
    w("")

    # ---------------------------------------------------------------- module reference
    w("## 3. Module reference (functions, inputs and outputs)")
    w("")
    w("### 3.1 `profiles.py`")
    w("")
    w("| Element | Signature | Input | Output |")
    w("|---|---|---|---|")
    w("| `Category` | frozen dataclass `(name, description, skills)` | — | one qualification category and its set of tokens |")
    w(f"| `ProfileDefinition` | frozen dataclass `(profile_id, title, domain, canonical_categories)` | — | a profile: ordered list of categories |")
    w(f"| `ProfileDefinition.required_groups` | property | — | `Dict[str, Set[str]]`: requirement name → categories that can satisfy it |")
    w(f"| `ProfileDefinition.alphabet` | property | — | `Set[str]` = Σ, the union of all category token sets |")
    w(f"| `ProfileDefinition.get_category_for_skill` | `{sig(P.ProfileDefinition.get_category_for_skill)}` | a token | name of its category, or `None` |")
    w("| `PROFILES_REGISTRY` | `Dict[str, ProfileDefinition]` | — | the four profiles keyed by `profile_id` |")
    w("")
    w("### 3.2 `automata_models.py`")
    w("")
    w("| Element | Signature | Input | Output |")
    w("|---|---|---|---|")
    w("| `FormalTuple` | dataclass | — | M = (Q, Σ, δ, q0, F) as plain Python sets and a dict |")
    w(f"| `FormalTuple.to_markdown` | `{sig(A.FormalTuple.to_markdown)}` | — | the tuple rendered as Markdown |")
    w(f"| `ProfileAutomaton.__init__` | `{sig(A.ProfileAutomaton.__init__)}` | a `ProfileDefinition` | builds the DFA, then completes δ with `q_trap` |")
    w(f"| `ProfileAutomaton._build_automaton` | `{sig(A.ProfileAutomaton._build_automaton)}` | — | strict linear chain: one state per category, self-loop on the category, forward edge to the next |")
    w(f"| `ProfileAutomaton._build_fullstack_automaton` | `{sig(A.ProfileAutomaton._build_fullstack_automaton)}` | — | chain with optional categories and bypass edges (see §6.1) |")
    w(f"| `ProfileAutomaton._complete_with_trap` | `{sig(A.ProfileAutomaton._complete_with_trap)}` | — | adds absorbing `q_trap` so that δ is total on Q × Σ |")
    w(f"| `ProfileAutomaton.accepts` | `{sig(A.ProfileAutomaton.accepts)}` | a word (list of tokens) | `bool`, using pyformlang's own `accepts` |")
    w(f"| `ProfileAutomaton.get_formal_tuple` | `{sig(A.ProfileAutomaton.get_formal_tuple)}` | — | `FormalTuple` extracted from the pyformlang object |")
    w(f"| `build_all_automata` | `{sig(A.build_all_automata)}` | — | `Dict[profile_id, ProfileAutomaton]` |")
    w("")
    w("### 3.3 `classifier.py`")
    w("")
    w("| Element | Signature | Input | Output |")
    w("|---|---|---|---|")
    w("| `ClassificationStatus` | `str` enum | — | `ACCEPTED` / `REJECTED` |")
    w(f"| `ResumeClassifier.__init__` | `{sig(C.ResumeClassifier.__init__)}` | — | builds all four automata once |")
    w(f"| `ResumeClassifier.evaluate_profile` | `{sig(C.ResumeClassifier.evaluate_profile)}` | profile id, token list (**strict**: no filtering, no sorting) | `ProfileEvaluationResult`; raises `ValueError` for an unknown profile id |")
    w(f"| `ResumeClassifier.classify` | `{sig(C.ResumeClassifier.classify)}` | token list; `prepare_input` (default `True`) | `ResumeClassificationReport` for the four profiles |")
    w("")
    w("### 3.4 `visualizer.py`")
    w("")
    w("| Function | Signature | Output |")
    w("|---|---|---|")
    w(f"| `build_graphviz_diagram` | `{sig(V.build_graphviz_diagram)}` | a `graphviz.Digraph`; with a result, the visited states/edges are highlighted (green accepted, red trap) |")
    w(f"| `generate_graphviz_dot` | `{sig(V.generate_graphviz_dot)}` | DOT source string |")
    w(f"| `generate_mermaid_diagram` | `{sig(V.generate_mermaid_diagram)}` | Mermaid `stateDiagram-v2` with one explicit line per pair of δ |")
    w("")
    w("### 3.5 Data structures returned by the classifier")
    w("")
    w("**`StepTransition`**")
    w("")
    w(fields_table(C.StepTransition)); w("")
    w("**`ProfileEvaluationResult`**")
    w("")
    w(fields_table(C.ProfileEvaluationResult)); w("")
    w("**`ResumeClassificationReport`**")
    w("")
    w(fields_table(C.ResumeClassificationReport)); w("")
    w("**`FormalTuple`**")
    w("")
    w(fields_table(A.FormalTuple)); w("")

    # ---------------------------------------------------------------- flow
    w("## 4. How a candidate is classified")
    w("")
    w("![Flow of classify](diagrams/stage3/s3_01_classify_flow.png)")
    w("")
    w("**`classify(tokens, prepare_input=True)`**")
    w("")
    w("1. For each profile P in the registry compute `rank`, the position of each of its tokens in the canonical order.")
    w("2. *Preparation* (only when `prepare_input=True`): keep the tokens that belong to Σ_P and sort them by rank (stable sort). The rest go to `ignored_tokens`. This is an integration step, **not** a DFA transition.")
    w("3. Call `evaluate_profile(P, word)`.")
    w("4. Collect accepted and rejected profile titles into the report.")
    w("")
    w("**`evaluate_profile(profile_id, tokens)`**, pseudocode:")
    w("")
    w("```text")
    w("state ← q0 ; trapped ← false")
    w("for i, token in enumerate(tokens, 1):")
    w("    category ← category of token in the profile (None if outside Σ)")
    w("    if trapped: record (q_trap, token, q_trap, invalid) ; continue")
    w("    next ← δ(state, token)                 # pyformlang lookup; absent or q_trap means violation")
    w("    if next is a real state: record the valid step ; state ← next")
    w("    else: trapped ← true ; record (state, token, q_trap, invalid)")
    w("          reason ← 'token not in alphabet'  if token ∉ Σ  else  'canonical-order violation at step i'")
    w("accepted ← not trapped and state = the accepting state")
    w("observed ← categories of all tokens ; satisfied ← observed in canonical order")
    w("missing ← mandatory requirement groups with no observed category")
    w("if rejected and no reason yet: reason ← 'empty sequence'  or  'missing: …'")
    w("```")
    w("")
    w("Cost: O(n) per profile for recognition (one dictionary lookup per token, after an O(1) amortised category lookup per token over a fixed vocabulary), O(n log n) for the preparation sort.")
    w("")
    w("### Why two modes?")
    w("")
    w("| Mode | Call | What it proves |")
    w("|---|---|---|")
    w("| Prepared (default) | `classify(tokens)` | Candidate-level question: *does this candidate cover the profile?* Order and foreign skills are irrelevant to the candidate, so they are normalised away per profile. |")
    w("| Strict | `classify(tokens, prepare_input=False)` or `evaluate_profile` | Language-level question: *is this exact word in L(M)?* Used by the tests, the demo without Stage 2 and the web API in `tokens` mode. |")
    w("")

    # ---------------------------------------------------------------- profiles
    w("## 5. Profiles in plain language")
    w("")
    w("A profile is a **pattern of categories in a fixed order**: first the core language, then the libraries built on top of it, then storage, and finally version control. A résumé matches when it names at least one skill from every mandatory category, in that order, and nothing in between breaks the order. Each category is a *block*: once the automaton moves to a later block it cannot go back (a database followed by a language is rejected in strict mode).")
    w("")
    w("| Profile | Domain | Σ size | States (with trap) | Transitions in δ (total / to trap) | Accepting state |")
    w("|---|---|---|---|---|---|")
    for pid, a in autos.items():
        f = a.get_formal_tuple()
        tot = len(f.transitions); trap = sum(1 for v in f.transitions.values() if v == "q_trap")
        w(f"| {a.profile.title} | {a.profile.domain} | {len(f.alphabet)} | {len(f.states)} | {tot} / {trap} | `{sorted(f.final_states)[0]}` |")
    w("")
    w("The number of transitions is |Q| × |Σ| because δ is total (every pair has exactly one target).")
    w("")

    prof_text = {
        "full_stack": ("a developer who can build both sides of a web application.",
                       "Optionally a reported number of years, then at least one frontend language (HTML/CSS/JavaScript/TypeScript), optionally frontend frameworks, then a backend (a language **or** a framework), optionally API technologies, then a database (SQL **or** NoSQL, or both), optionally cloud/DevOps tools, and finally at least one version-control tool."),
        "machine_learning": ("an engineer who trains and ships machine-learning models.",
                             "A core language, then data-processing libraries, then at least one ML framework, then a database, then version control. All five blocks are mandatory."),
        "cloud_devops": ("an engineer who automates, containerises and deploys infrastructure.",
                         "Scripting/OS skills, then CI/CD tools, then containers/orchestration, then cloud/IaC, then version control. All five blocks are mandatory."),
        "data_scientist": ("an analyst who explores data, visualises it and fits models.",
                           "A data language, then analysis/statistics libraries, then visualisation tools, then machine-learning libraries, then version control. All five blocks are mandatory."),
    }
    words = {
        "full_stack": dict(
            minimal=["JAVASCRIPT", "PYTHON", "POSTGRESQL", "GIT"],
            extended=["EXPERIENCE_PRESENT", "HTML", "JAVASCRIPT", "REACT", "NODE_JS", "EXPRESS", "REST", "POSTGRESQL", "MONGODB", "DOCKER", "GIT", "GITHUB"],
            extra=("Backend by framework only", ["TYPESCRIPT", "DJANGO", "MONGODB", "GITLAB"]),
            missing={"no frontend language": ["PYTHON", "POSTGRESQL", "GIT"],
                     "no backend": ["JAVASCRIPT", "POSTGRESQL", "GIT"],
                     "no database": ["JAVASCRIPT", "PYTHON", "GIT"],
                     "no version control": ["JAVASCRIPT", "PYTHON", "POSTGRESQL"]},
            swap=["PYTHON", "JAVASCRIPT", "POSTGRESQL", "GIT"]),
        "machine_learning": dict(
            minimal=["PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT"],
            extended=["PYTHON", "NUMPY", "PANDAS", "SCIKIT_LEARN", "PYTORCH", "MYSQL", "GITHUB"],
            extra=None,
            missing={"no core language": ["PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT"],
                     "no data processing": ["PYTHON", "TENSORFLOW", "POSTGRESQL", "GIT"],
                     "no ML framework": ["PYTHON", "PANDAS", "POSTGRESQL", "GIT"],
                     "no database": ["PYTHON", "PANDAS", "TENSORFLOW", "GIT"],
                     "no version control": ["PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL"]},
            swap=["PANDAS", "PYTHON", "TENSORFLOW", "POSTGRESQL", "GIT"]),
        "cloud_devops": dict(
            minimal=["BASH", "JENKINS", "DOCKER", "AWS", "GIT"],
            extended=["LINUX", "PYTHON", "GITHUB_ACTIONS", "GITLAB_CI", "DOCKER", "KUBERNETES", "TERRAFORM", "AWS", "GITHUB"],
            extra=None,
            missing={"no scripting/OS": ["JENKINS", "DOCKER", "AWS", "GIT"],
                     "no CI/CD": ["BASH", "DOCKER", "AWS", "GIT"],
                     "no containers": ["BASH", "JENKINS", "AWS", "GIT"],
                     "no cloud/IaC": ["BASH", "JENKINS", "DOCKER", "GIT"],
                     "no version control": ["BASH", "JENKINS", "DOCKER", "AWS"]},
            swap=["JENKINS", "BASH", "DOCKER", "AWS", "GIT"]),
        "data_scientist": dict(
            minimal=["PYTHON", "PANDAS", "MATPLOTLIB", "SCIKIT_LEARN", "GIT"],
            extended=["PYTHON", "R", "NUMPY", "PANDAS", "SEABORN", "PLOTLY", "XGBOOST", "LIGHTGBM", "GITHUB"],
            extra=None,
            missing={"no data language": ["PANDAS", "MATPLOTLIB", "SCIKIT_LEARN", "GIT"],
                     "no analysis/statistics": ["PYTHON", "MATPLOTLIB", "SCIKIT_LEARN", "GIT"],
                     "no visualisation": ["PYTHON", "PANDAS", "SCIKIT_LEARN", "GIT"],
                     "no machine learning": ["PYTHON", "PANDAS", "MATPLOTLIB", "GIT"],
                     "no version control": ["PYTHON", "PANDAS", "MATPLOTLIB", "SCIKIT_LEARN"]},
            swap=["PANDAS", "PYTHON", "MATPLOTLIB", "SCIKIT_LEARN", "GIT"]),
    }
    FOREIGN = "COBOL"
    for n, (pid, a) in enumerate(autos.items(), 1):
        p = a.profile; who, pat = prof_text[pid]
        w(f"### 5.{n} {p.title}")
        w("")
        w(f"**What it models:** {who}")
        w("")
        w(f"**Pattern in words:** {pat}")
        w("")
        if pid == "full_stack":
            pattern = ("EXPERIENCE* FE_LANGUAGE+ FE_FRAMEWORK* (BE_LANGUAGE+ BE_FRAMEWORK* | BE_FRAMEWORK+) "
                       "API_COMMUNICATION* (DATABASE_SQL+ DATABASE_NOSQL* | DATABASE_NOSQL+) DEVOPS_CLOUD* VERSION_CONTROL+")
        else:
            pattern = " ".join(c.name + "+" for c in p.canonical_categories)
        w(f"**Pattern as a regular expression over categories:** `{pattern}`")
        w("")
        w("| # | Category | Mandatory? | Tokens |")
        w("|---|---|---|---|")
        groups = p.required_groups
        for i, c in enumerate(p.canonical_categories, 1):
            grp = [g for g, alts in groups.items() if c.name in alts]
            if not grp:
                m = "optional"
            elif len(groups[grp[0]]) > 1:
                m = f"one of {' / '.join(sorted(groups[grp[0]]))} (group {grp[0]})"
            else:
                m = "mandatory"
            w(f"| {i} | {c.name} | {m} | {', '.join(sorted(c.skills))} |")
        w("")
        w(f"The complete transition diagram and the δ table of this profile are in Part II, section *{p.title}*.")
        w("")
        d = words[pid]
        w("**Examples (strict evaluation, executed by the generator):**")
        w("")
        w("| Case | Word | Verdict | Reason / final state |")
        w("|---|---|---|---|")
        w(row("Minimal accepted word", pid, d["minimal"]))
        w(row("Extended accepted word", pid, d["extended"]))
        if d["extra"]:
            w(row(d["extra"][0], pid, d["extra"][1]))
        for k, v in d["missing"].items():
            w(row(f"Requirement omitted: {k}", pid, v))
        w(row("Out of canonical order", pid, d["swap"]))
        w(row("Foreign token appended", pid, d["minimal"] + [FOREIGN]))
        w(row("Empty sequence", pid, []))
        w("")
        # verify claims
        assert run(pid, d["minimal"]).is_accepted and run(pid, d["extended"]).is_accepted
        assert not run(pid, d["swap"]).is_accepted
        for v in d["missing"].values():
            assert not run(pid, v).is_accepted
        if pid == "full_stack":
            assert run(pid, d["extra"][1]).is_accepted

    w("### 5.5 Reading the rejection messages")
    w("")
    w("`rejection_reason` has three forms:")
    w("")
    w("| Situation | Message |")
    w("|---|---|")
    w("| Token outside Σ | *Token 'X' does not belong to the alphabet of profile P.* |")
    w("| Token inside Σ but not allowed from the current state | *Canonical-order violation at step i: Token 'X' (category C) is not valid from state q.* |")
    w("| No violation but the word ends outside F | *Mandatory competencies are missing to complete the profile: …* or, for an empty input, *Empty sequence. No competencies provided.* |")
    w("")
    w("When the input is **prepared**, a missing mandatory block usually shows up as an *order violation* at the first token of the following block (the automaton cannot skip it). The field `missing_categories` always states the real cause, which is why both are shown together in the UI.")
    w("")

    # ---------------------------------------------------------------- worked traces
    w("## 6. Design notes on the automata")
    w("")
    w("### 6.1 Full Stack: optional blocks and bypass edges")
    w("")
    fs = autos["full_stack"].get_formal_tuple()
    w("Full Stack is the only profile with optional categories, so it is the only one that is not a strict chain. Its DFA has 11 real states plus the trap. The bypass edges implement the regular expression above:")
    w("")
    w("- `q0` accepts `EXPERIENCE_PRESENT` (→ `q_experience`) or goes straight to a frontend language.")
    w("- `q_fe_language` / `q_fe_framework` can jump directly to a backend language or framework (a frontend framework is optional).")
    w("- Any backend state (`q_be_language`, `q_be_framework`) can jump over `API_COMMUNICATION` to a database; a backend framework alone is enough (`BE_FRAMEWORK+`).")
    w("- `q_database_sql` can be followed by NoSQL or DevOps/Cloud or version control; `q_database_nosql` can go directly to DevOps/Cloud or version control.")
    w("- Only `q_version_control` is accepting. Everything else (skipping the frontend language, the backend, the database or the version control) ends in a non-accepting state.")
    w("")
    w("### 6.2 The other three profiles: strict chains")
    w("")
    w("Machine Learning, Cloud & DevOps and Data Scientist have five categories, all mandatory. Each state loops on its own category (several tools of the same block) and has exactly one forward edge, so every accepted word matches `C1+ C2+ C3+ C4+ C5+`.")
    w("")
    w("### 6.3 Why a total δ with an explicit trap state?")
    w("")
    w("A partial DFA would be enough for acceptance, but the project must **show the path of a rejection**. With an explicit `q_trap` every (state, symbol) pair has one target, the trace of a rejected résumé is a legal run of the automaton, and the diagrams and tables are complete.")
    w("")

    w("## 7. Worked examples")
    w("")
    w("### 7.1 The statement's example (Machine Learning)")
    w("")
    ml = clf.evaluate_profile("machine_learning", ["PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT"])
    w("Word: `PYTHON, PANDAS, TENSORFLOW, POSTGRESQL, GIT` evaluated by the Machine Learning DFA.")
    w("")
    w("| Step | Source state | Symbol | Category | Target state | Valid |")
    w("|---|---|---|---|---|---|")
    for s in ml.trace:
        w(f"| {s.step_number} | `{s.source_state}` | {s.symbol} | {s.category} | `{s.target_state}` | {'yes' if s.is_valid_transition else 'no'} |")
    w("")
    w(f"Final state `{ml.final_state}` = F, so the word is **{ml.status.value}**.")
    w("")
    render_trace(autos["machine_learning"], ml, "s3_02_trace_ml_accepted")
    w("![Trace ML accepted](diagrams/stage3/s3_02_trace_ml_accepted.png)")
    w("")
    w("The same skills without the ML framework (`PYTHON, PANDAS, POSTGRESQL, GIT`) are rejected: the machine cannot move from `q_data_processing` to `q_database`.")
    w("")
    bad = clf.evaluate_profile("machine_learning", ["PYTHON", "PANDAS", "POSTGRESQL", "GIT"])
    w("| Field | Value |")
    w("|---|---|")
    w(f"| `status` | {bad.status.value} |")
    w(f"| `final_state` | `{bad.final_state}` |")
    w(f"| `missing_categories` | {bad.missing_categories} |")
    w(f"| `rejection_reason` | {bad.rejection_reason} |")
    w("")


    def pipeline(fname, pid):
        txt = open(f"tests/data/resumes/{fname}.txt", encoding="utf-8").read()
        e = extract_qualifications(txt)
        n = normalize_and_sort(e.raw_tokens, pid, years_of_experience=e.years_of_experience)
        rep = clf.classify(n.normalized_tokens)
        return txt, e, n, rep


    for k, (fname, pid, title) in enumerate([("wednesday_addams", "full_stack", "Wednesday Addams"),
                                             ("mary_jane_watson", "machine_learning", "Mary Jane Watson")], 2):
        txt, e, n, rep = pipeline(fname, pid)
        w(f"### 7.{k} End to end: {title}")
        w("")
        w("Résumé (`tests/data/resumes/" + fname + ".txt`):")
        w("")
        w("```text"); w(txt.strip()); w("```")
        w("")
        w(f"1. **Stage 1** (regular expressions): raw tokens `{e.raw_tokens}`, years of experience `{e.years_of_experience}`.")
        w(f"2. **Stage 2** (transducers): normalized and sorted tokens `{n.normalized_tokens}`.")
        w(f"3. **Stage 3** (this stage): accepted profiles → **{', '.join(rep.accepted_profiles) or 'none'}**.")
        w("")
        w("| Profile | Verdict | Word read by the DFA | Ignored tokens | Missing mandatory groups |")
        w("|---|---|---|---|---|")
        for q, r in rep.results_by_profile.items():
            w(f"| {r.profile_title} | {r.status.value} | {', '.join(r.evaluated_tokens)} | {', '.join(r.ignored_tokens) or '—'} | {', '.join(r.missing_categories) or '—'} |")
        w("")
        if k == 3:
            r = rep.results_by_profile["data_scientist"]
            render_trace(autos["data_scientist"], r, "s3_03_trace_ds_rejected")
            w("Mary Jane is **rejected** as a Data Scientist: she lists no visualisation tool, so the run stops at `SCIKIT_LEARN` (red state in the diagram). Note how `TENSORFLOW` is ignored because it is not in the Data Scientist alphabet.")
            w("")
            w("![Trace DS rejected](diagrams/stage3/s3_03_trace_ds_rejected.png)")
            w("")

    w("## 8. Integration with the other stages")
    w("")
    w("| Boundary | Contract |")
    w("|---|---|")
    w("| Stage 1 → Stage 2 | `ExtractionResult.raw_tokens` (list of strings) and `years_of_experience` |")
    w("| Stage 2 → Stage 3 | `NormalizationResult.normalized_tokens`: canonical tokens in Σ of the profiles; `EXPERIENCE_PRESENT` is the only numeric-derived symbol |")
    w("| Stage 3 → UI (`src/ui/app.py`) | `classify(tokens, prepare_input=…)`; the trace feeds `build_graphviz_diagram(auto, result)` |")
    w("| Stage 3 → web API (`src/web_api/server.py`) | `classify(tokens, prepare_input=(mode == 'resume'))`; fields of the result are serialised into JSON |")
    w("| Stage 3 → Stage 4 (DSL, pending) | the report (`accepted_profiles`, `results_by_profile`, `missing_categories`) is the data the textX rules and the HTML visualisation will consume |")
    w("")
    w("Stage 2 already sorts tokens into the canonical order of one profile (`normalize_and_sort(..., profile_id)`); Stage 3 re-sorts per profile in `prepare_input` mode. The two sorts use the same category order, so they are compatible, and Stage 3 does not depend on Stage 2 having sorted.")
    w("")
    w("## 9. Design decisions")
    w("")
    w("| Decision | Rationale |")
    w("|---|---|")
    w("| One DFA per profile, not one global automaton | Each profile has its own alphabet and order; independent verdicts allow a candidate to match several profiles. |")
    w("| DFA instead of NFA/ε-NFA | There is exactly one possible reaction to each token in each state; no ε-moves are needed. Determinism gives O(n) recognition and unambiguous traces. |")
    w("| Categories are disjoint inside a profile | A token determines its block without ambiguity (`PYTHON` is in a different category in each profile, never twice in the same one). |")
    w("| Total δ with `q_trap` | Rejections are legal runs; the trace and diagrams show where the word broke. |")
    w("| `EXPERIENCE_PRESENT` as one finite symbol | A DFA cannot read an unbounded set of numbers; the exact number stays as Stage 1 metadata. |")
    w("| Preparation outside the DFA | Filtering and sorting is an operation on the input, not part of the language; keeping it separate preserves the formal definition and allows a strict mode. |")
    w("| `required_groups` separate from the DFA | The automaton decides acceptance; the groups only explain *why* something is missing. |")
    w("| Presence, not proficiency | A token only says the skill was named; no level is inferred. |")
    w("")
    w("## 10. Limitations")
    w("")
    w("- The four patterns are **team decisions** derived from the examples in the assignment; the detailed requirements that the instructor said would be provided separately are not in the repository and must be checked against them.")
    w("- Machine Learning, Cloud & DevOps and Data Scientist require **all five** categories (strict chains). A candidate lacking, for example, a database is not a Machine Learning Engineer for this model.")
    w("- Σ is limited to the 79 canonical tokens of Stage 2; a skill outside it cannot satisfy any requirement.")
    w("- In prepared mode, a missing block is reported as an order violation by `rejection_reason`; read it together with `missing_categories`.")
    w("- There is no scoring or partial credit: the verdict is binary per profile.")
    w("")
    w("## 11. How to run and regenerate")
    w("")
    w("```bash")
    w("python -m pytest -q                         # all tests")
    w("python scripts/export_diagrams.py           # docs/diagrams/<profile>.{dot,svg,png}")
    w("python scripts/export_formalization.py      # docs/stage3_formalization.md")
    w("```")
    w("")
    w("Minimal usage:")
    w("")
    w("```python")
    w("from src.stage3_classifier import ResumeClassifier")
    w("clf = ResumeClassifier()")
    w("report = clf.classify([\"PYTHON\", \"PANDAS\", \"TENSORFLOW\", \"POSTGRESQL\", \"GIT\"])")
    w("report.accepted_profiles                    # ['Machine Learning Engineer']")
    w("report.results_by_profile[\"machine_learning\"].trace   # list of StepTransition")
    w("```")
    w("")
    rep = clf.classify(["PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT"])
    assert rep.accepted_profiles == ["Machine Learning Engineer"], rep.accepted_profiles
    w("## 12. References")
    w("")
    w("- Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006). *Introduction to Automata Theory, Languages, and Computation* (3rd ed.). Pearson. (DFA definition, extended transition function, total transition function, dead/trap state.)")
    w("- Sipser, M. (2012). *Introduction to the Theory of Computation* (3rd ed.). Cengage. (Formal definition of a DFA, regular expressions and their equivalence with finite automata.)")
    w("- Kozen, D. C. (1997). *Automata and Computability*. Springer. (Myhill–Nerode theorem, minimization.)")
    w("- Kleene, S. C. (1956). Representation of events in nerve nets and finite automata. In C. E. Shannon & J. McCarthy (Eds.), *Automata Studies* (pp. 3–41). Princeton University Press. (Regular events.)")
    w("- Rabin, M. O., & Scott, D. (1959). Finite automata and their decision problems. *IBM Journal of Research and Development, 3*(2), 114–125. (Deterministic and nondeterministic automata.)")
    w("- Moore, E. F. (1956). Gedanken-experiments on sequential machines. In C. E. Shannon & J. McCarthy (Eds.), *Automata Studies* (pp. 129–153). Princeton University Press. (Partition-refinement algorithm used in Theorem 4.)")
    w("- Nerode, A. (1958). Linear automaton transformations. *Proceedings of the American Mathematical Society, 9*(4), 541–544. (Nerode equivalence.)")
    w("- Hopcroft, J. E. (1971). An n log n algorithm for minimizing states in a finite automaton. In Z. Kohavi & A. Paz (Eds.), *Theory of Machines and Computations* (pp. 189–196). Academic Press.")
    w("- pyformlang documentation: <https://pyformlang.readthedocs.io/> (`DeterministicFiniteAutomaton`, `Symbol`, `State`).")
    w("- Graphviz documentation: <https://graphviz.org/documentation/> (DOT language).")
    w("- Course assignment *Integrative Task 1 – 2026-2*, item 3 (qualification pattern recognition), and `docs/Initial Doc.md`.")
    w("")
    return out
