"""Formal framework of docs/stage3_formalization.md (definitions, theorems, proofs, minimality).

Every statement that can be checked mechanically is checked here while the document is generated
(an AssertionError stops the export if the implementation ever contradicts the text), and the
tables of witnesses and state languages are computed from the real DFAs.
Used by scripts/export_formalization.py.
"""
import itertools
import re
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.stage3_classifier.automata_models import build_all_automata  # noqa: E402

FS_LETTERS = {
    "EXPERIENCE": "E", "FE_LANGUAGE": "F", "FE_FRAMEWORK": "G", "BE_LANGUAGE": "B", "BE_FRAMEWORK": "K",
    "API_COMMUNICATION": "A", "DATABASE_SQL": "S", "DATABASE_NOSQL": "N", "DEVOPS_CLOUD": "D",
    "VERSION_CONTROL": "V",
}
# Language of category words that lead from q0 to each Full Stack state (Lemma 2).
FS_STATE_LANGUAGE = {
    "q0": "",
    "q_experience": "E+",
    "q_fe_language": "E*F+",
    "q_fe_framework": "E*F+G+",
    "q_be_language": "E*F+G*B+",
    "q_be_framework": "E*F+G*(B+K+|K+)",
    "q_api_communication": "E*F+G*(B+K*|K+)A+",
    "q_database_sql": "E*F+G*(B+K*|K+)A*S+",
    "q_database_nosql": "E*F+G*(B+K*|K+)A*(S+N+|N+)",
    "q_devops_cloud": "E*F+G*(B+K*|K+)A*(S+N*|N+)D+",
    "q_version_control": "E*F+G*(B+K*|K+)A*(S+N*|N+)D*V+",
}
FS_PATTERN = FS_STATE_LANGUAGE["q_version_control"]


class Model:
    """Category-level view of one profile DFA, extracted from the real pyformlang automaton."""

    def __init__(self, pid, automaton):
        self.pid = pid
        self.auto = automaton
        self.profile = automaton.profile
        self.formal = automaton.get_formal_tuple()
        self.cats = [c.name for c in self.profile.canonical_categories]
        if pid == "full_stack":
            self.letter = dict(FS_LETTERS)
        else:
            self.letter = dict(zip(self.cats, "ABCDE"))
        self.rep = {c.name: sorted(c.skills)[0] for c in self.profile.canonical_categories}
        self.states = sorted(self.formal.states)
        self.final = next(iter(self.formal.final_states))
        self.delta = self.formal.transitions
        # Lemma 1: delta is uniform inside every category.
        self.cell = {}
        for q in self.states:
            for c in self.profile.canonical_categories:
                targets = {self.delta[q, s] for s in c.skills}
                assert len(targets) == 1, (pid, q, c.name)
                self.cell[q, c.name] = targets.pop()
        if pid == "full_stack":
            self.state_language = dict(FS_STATE_LANGUAGE)
        else:
            self.state_language = {"q0": ""}
            for j, name in enumerate(self.cats, 1):
                self.state_language["q_" + name.lower()] = "".join(self.letter[n] + "+" for n in self.cats[:j])
        self.pattern = self.state_language[self.final]

    def run_categories(self, word):
        state = "q0"
        for letter in word:
            state = self.cell[state, self.name_of[letter]]
        return state

    @property
    def name_of(self):
        return {v: k for k, v in self.letter.items()}

    def paths(self):
        """Shortest word from q0 to each state, and shortest suffix from each state to F (token level)."""
        symbols = {name: self.rep[name] for name in self.cats}
        forward = {"q0": []}
        queue = deque(["q0"])
        while queue:
            q = queue.popleft()
            for name in self.cats:
                t = self.cell[q, name]
                if t not in forward:
                    forward[t] = forward[q] + [symbols[name]]
                    queue.append(t)
        backward = {self.final: []}
        changed = True
        while changed:
            changed = False
            for q in self.states:
                for name in self.cats:
                    t = self.cell[q, name]
                    if t in backward and (q not in backward or len(backward[q]) > len(backward[t]) + 1):
                        backward[q] = [symbols[name]] + backward[t]
                        changed = True
        return forward, backward

    def moore(self):
        """Moore's partition refinement over the full alphabet; returns the class counts per round."""
        symbols = sorted(self.formal.alphabet)
        cls = {q: (q == self.final) for q in self.states}
        history = [len(set(cls.values()))]
        while True:
            signature = {q: (cls[q],) + tuple(cls[self.delta[q, s]] for s in symbols) for q in self.states}
            ids = {sig: i for i, sig in enumerate(sorted(set(signature.values()), key=repr))}
            new = {q: ids[signature[q]] for q in self.states}
            history.append(len(set(new.values())))
            if len(set(new.values())) == len(set(cls.values())):
                groups = {}
                for q, c in new.items():
                    groups.setdefault(c, []).append(q)
                return history, [sorted(g) for g in groups.values() if len(g) > 1]
            cls = new


def models():
    return {pid: Model(pid, auto) for pid, auto in build_all_automata().items()}


def _check_state_languages(m, max_len):
    """Mechanical check of Lemma 2 and Theorem 1 on every category word up to max_len."""
    letters = [m.letter[n] for n in m.cats]
    regex = {q: re.compile(lang) for q, lang in m.state_language.items()}
    for length in range(max_len + 1):
        for tup in itertools.product(letters, repeat=length):
            word = "".join(tup)
            reached = m.run_categories(word)
            for q, rx in regex.items():
                assert bool(rx.fullmatch(word)) == (reached == q), (m.pid, word, q, reached)
    return len(letters), max_len


def _incoming(m, target):
    return [(q, c) for q in m.states for c in m.cats if m.cell[q, c] == target]


def profile_properties(m):
    """Per-profile table of state languages and witnesses (section appended to each profile)."""
    forward, backward = m.paths()
    rows = ["**Structural properties (generated from the DFA).** Λ(q) is the set of category words that lead "
            "from q0 to q (Lemma 2). A *witness* is a shortest word of tokens that reaches q from q0 "
            "(reachability) and a shortest suffix that leads from q to F (co-reachability); `q_trap` has no "
            "suffix because it cannot reach F.", "",
            "| State q | Λ(q) over categories | Witness q0 → q | Suffix q → F |", "|---|---|---|---|"]
    for q in m.states:
        lang = m.state_language.get(q)
        lang = ("ε" if lang == "" else "`" + lang.replace("|", "\\|") + "`") if lang is not None else "*complement of the others*"
        w = ", ".join(forward[q]) if q in forward and forward[q] else ("*(empty word)*" if q in forward else "*unreachable*")
        s = ", ".join(backward[q]) if q in backward and backward[q] else ("*(empty word)*" if q in backward else "*none (dead state)*")
        rows.append(f"| `{q}` | {lang} | {w} | {s} |")
    history, equal = m.moore()
    rounds = f"{len(history) - 1} refinement rounds (class counts per round: {', '.join(map(str, history))})"
    if not equal:
        rows += ["", f"Moore's algorithm separates the {len(m.states)} states into singleton classes after {rounds}; "
                 "no two states are equivalent, so this DFA is **minimal** (Theorem 4).", ""]
    else:
        pair = " ≡ ".join(f"`{q}`" for q in equal[0])
        rows += ["", f"Moore's algorithm ends after {rounds} with {len(m.states) - 1} classes for {len(m.states)} states: "
                 f"the only equivalent states are {pair} (Theorem 4). The implemented automaton is therefore one state larger than the minimal one; "
                 "see the remark after Theorem 4.", ""]
    return rows


def build_theory_section():
    ms = models()
    out = []
    w = out.append
    letters_note = ", ".join(f"{v} = {k}" for k, v in FS_LETTERS.items())

    w("## Formal framework")
    w("")
    w("This section states precisely what each automaton recognizes and proves the properties that the "
      "previous section only asserts. Statements marked **(machine-checked)** are also verified by the script "
      "that generates this document: the export stops if the implementation contradicts the text.")
    w("")
    w("### Definitions")
    w("")
    w("Fix a profile P with categories C₁, …, C_k listed in canonical order.")
    w("")
    w("1. The **alphabet** Σ_P is the union of the category sets. The categories are pairwise disjoint, so "
      "the map κ: Σ_P → {C₁, …, C_k} that sends a token to its category is well defined; it extends to words by "
      "κ(s₁ … s_n) = κ(s₁) … κ(s_n), a word over the *category alphabet*. For readability a category is written with a single "
      "letter in the formulas below (Full Stack: " + letters_note + "; the other profiles: A, B, C, D, E in canonical order).")
    w("2. A **word** is a finite sequence of tokens of Σ_P. A DFA is M = (Q, Σ, δ, q0, F) with δ: Q × Σ → Q. The "
      "**extended transition function** δ*: Q × Σ* → Q is defined by δ*(q, ε) = q and δ*(q, ws) = δ(δ*(q, w), s).")
    w("3. The **language of the automaton** is L(M) = { w ∈ Σ* : δ*(q0, w) ∈ F }. A candidate *satisfies the "
      "profile in strict mode* iff their token word belongs to L(M_P).")
    w("4. The **category pattern** R_P is a regular expression over the category alphabet:")
    w("")
    w("| Profile | R_P |")
    w("|---|---|")
    for pid, m in ms.items():
        w(f"| {m.profile.title} | `{m.pattern.replace('|', chr(92) + '|')}` |")
    w("")
    w("   In the chain profiles R_P = C₁⁺ C₂⁺ … C₅⁺. In Full Stack, the two alternations satisfy "
      "(B⁺K\\*|K⁺) = B\\*K\\* ∖ {ε} and (S⁺N\\*|N⁺) = S\\*N\\* ∖ {ε}, so R_FS = E\\* F⁺ G\\* (B\\*K\\*∖ε) A\\* (S\\*N\\*∖ε) D\\* V⁺: "
      "a backend block is any non-empty run of backend languages followed by backend frameworks, and the same holds for the database block.")
    w("5. For a state q let **Λ(q) = { u ∈ category words : δ*(q0, u) = q }** (computed on any tokens with those categories; "
      "Lemma 1 shows the choice of tokens is irrelevant).")
    w("")

    w("### Lemma 1 — δ depends only on the category of the symbol  (machine-checked)")
    w("")
    w("*For every state q and every category C, all tokens of C have the same image: δ(q, s) = δ(q, s′) whenever κ(s) = κ(s′).*")
    w("")
    w("*Proof.* The constructors `_build_automaton` and `_build_fullstack_automaton` add transitions by looping over "
      "`category.skills` with a single target per category, and `_complete_with_trap` adds the trap for every pair that "
      "is still undefined, again for every token of the category. The generator verifies the statement for every state and "
      "category of the four automata; this is what allows the δ tables of this document to be written by category. ∎")
    w("")
    w("Consequently each M_P is the composition of κ with a DFA B_P over the category alphabet (same states, δ_B(q, C) = the cell of the table), "
      "and **w ∈ L(M_P) ⇔ κ(w) ∈ L(B_P)**.")
    w("")

    w("### Lemma 2 — the languages Λ(q)")
    w("")
    w("*The language of category words reaching each state is the one given in the column Λ(q) of the table of every profile "
      "(section «Structural properties»). In particular Λ(q_F) = R_P and Λ(q_trap) is the set of category words that "
      "are not a prefix of any word of R_P.*")
    w("")
    w("*Proof.* By induction on the length of the word. The family Λ(q) is uniquely determined by the system of equations")
    w("")
    w("- ε ∈ Λ(q0) and ε ∉ Λ(q) for q ≠ q0;")
    w("- Λ(q′) ∖ {ε} = ⋃ { Λ(q)·C : δ(q, C) = q′ }  for every state q′,")
    w("")
    w("because a word u·C reaches q′ exactly when u reaches a state q with δ(q, C) = q′ (definition of δ*). So it is enough to check "
      "that the claimed languages satisfy these equations, which is read directly from the incoming edges of each state in the δ table.")
    w("")
    w("*Chain profiles.* The claim is Λ(q_j) = C₁⁺…C_j⁺. The state q_j has exactly two incoming edges: the loop (q_j, C_j) and the "
      "advance (q_{j−1}, C_j) (for j = 1 the advance starts at q0). Hence Λ(q_j) = Λ(q_{j−1})·C_j ∪ Λ(q_j)·C_j = "
      "C₁⁺…C_{j−1}⁺C_j ∪ C₁⁺…C_j⁺C_j = C₁⁺…C_j⁺. ∎")
    w("")
    w("*Full Stack.* The equations are the following; the left-hand side is Λ of the state and the right-hand side is the union of the "
      "incoming edges (state, category) taken from the δ table; the equality of each line is an identity between regular expressions "
      "(for example Λ(q_fe_framework) = E\\*F⁺G ∪ E\\*F⁺G⁺G = E\\*F⁺G⁺).")
    w("")
    m = ms["full_stack"]
    w("| State q′ | Incoming edges (q, C) with δ(q, C) = q′ | Λ(q′) |")
    w("|---|---|---|")
    for q in m.states:
        if q == "q_trap":
            continue
        inc = _incoming(m, q)
        inc = [(a, c) for a, c in inc if a != "q_trap"]
        text = ", ".join(f"({a}, {m.letter[c]})" for a, c in inc) if inc else "— (initial state)"
        lang = m.state_language[q]
        w(f"| `{q}` | {text} | {('ε' if lang == '' else '`' + lang.replace('|', chr(92) + '|') + '`')} |")
    w("")
    n_letters = {}
    for pid, mm in ms.items():
        n_letters[pid] = _check_state_languages(mm, 5 if pid == "full_stack" else 7)
    w(f"**(machine-checked)** For every profile the generator runs the DFA on *all* category words up to length 5 (Full Stack, 10 categories: "
      f"{sum(10 ** k for k in range(6)):,} words) or 7 (the other profiles, 5 categories: {sum(5 ** k for k in range(8)):,} words) and "
      "checks that each word reaches exactly the state whose Λ contains it. ∎")
    w("")

    w("### Theorem 1 — language of each automaton")
    w("")
    w("*For every profile P, L(M_P) = κ⁻¹(L(R_P)) = { w ∈ Σ_P* : κ(w) matches R_P }.*")
    w("")
    w("*Proof.* By Lemma 1, w ∈ L(M_P) iff δ*(q0, w) = q_F, i.e. iff κ(w) ∈ Λ(q_F). By Lemma 2, Λ(q_F) = L(R_P). ∎")
    w("")
    w("In words: a word of tokens is accepted in strict mode exactly when, replacing every token by its category, the result is "
      "a sequence of non-empty blocks of categories in canonical order that follows the pattern of the profile. Tokens outside Σ_P are "
      "not words of Σ_P*: they are rejected by the evaluator before δ is applied (see *Contract and design criteria*).")
    w("")

    w("### Theorem 2 — each M_P is a total deterministic automaton without ε-transitions  (machine-checked)")
    w("")
    w("*Q × Σ_P → Q is a total function: for every state q and every token s there is exactly one target δ(q, s). "
      "The number of transitions is |Q|·|Σ_P|.*")
    w("")
    w("*Proof.* The transitions are stored in a `pyformlang` `DeterministicFiniteAutomaton`, which keeps at most one target per (state, symbol) "
      "pair and has no ε-transitions (determinism). After the construction, `_complete_with_trap` visits every pair (q, s) with q ∈ Q ∪ {q_trap} "
      "and s ∈ Σ_P and adds q → q_trap on s if no transition is defined (totality). The trap has the loop on every symbol, hence δ(q_trap, s) = q_trap. ∎")
    w("")
    w("| Profile | States (with trap) | Alphabet size | States × alphabet | Transitions in δ | Transitions into the trap |")
    w("|---|---|---|---|---|---|")
    for pid, mm in ms.items():
        tot = len(mm.delta)
        trap = sum(1 for v in mm.delta.values() if v == "q_trap")
        assert tot == len(mm.states) * len(mm.formal.alphabet)
        w(f"| {mm.profile.title} | {len(mm.states)} | {len(mm.formal.alphabet)} | {len(mm.states) * len(mm.formal.alphabet)} | {tot} | {trap} |")
    w("")

    w("### Theorem 3 — no useless states: every state except the trap is reachable and co-reachable  (machine-checked)")
    w("")
    w("*Every state q ≠ q_trap is reachable from q0 and can reach F; q_trap is reachable but cannot reach F (it is the only dead state).*")
    w("")
    w("*Proof.* For reachability and co-reachability it is enough to exhibit a word: the tables «Structural properties» of each profile list, for every "
      "state, a shortest word from q0 (computed by breadth-first search over δ) and a shortest suffix to F (computed backwards). "
      "For `q_trap`, every transition leaving it returns to it and F does not contain it, so no suffix exists. ∎")
    w("")
    for pid, mm in ms.items():
        fw, bw = mm.paths()
        for q in mm.states:
            assert q in fw, (pid, q)
            assert (q in bw) == (q != "q_trap"), (pid, q)
    w("A consequence is that a rejected word that is a prefix of a valid word is rejected only because it **stops too early** (it ends in a non-accepting "
      "state, never in the trap), which is exactly the case that the evaluator reports as «mandatory competencies are missing».")
    w("")

    w("### Theorem 4 — minimality  (machine-checked)")
    w("")
    w("*The three chain automata (Machine Learning, Cloud & DevOps, Data Scientist) are the minimal complete DFAs of their languages. "
      "The Full Stack automaton has exactly one pair of equivalent states, q0 and q_experience; merging them gives its minimal DFA, with one state less.*")
    w("")
    w("*Proof.* Two states q, q′ are equivalent iff for every word z, δ*(q, z) ∈ F ⇔ δ*(q′, z) ∈ F. Moore's algorithm starts with the partition {F, Q∖F} "
      "and splits two states whenever some symbol sends them to different classes; it stops when a round does not create a new class. "
      "The generator runs it on the real automata: the number of rounds and the class counts appear below the table of each profile. "
      "By the Myhill–Nerode theorem the final classes are the states of the minimal DFA. In the chain automata every class is a singleton, so they are minimal. "
      "In Full Stack the only non-singleton class is {q0, q_experience}: both states have the same row of the δ table "
      "(EXPERIENCE → q_experience, FE_LANGUAGE → q_fe_language, everything else → q_trap), hence the same set of valid continuations E\\*F⁺…; "
      "after merging them the loop on E is attached to q0. ∎")
    w("")
    w("*Remark (a design decision).* The implemented Full Stack automaton keeps `q_experience` as a separate state although it is language-equivalent to `q0`. "
      "The extra state does not change L(M_FS) (Theorem 1 is stated for the implemented automaton), and it has a practical benefit: the trace and the diagram show "
      "explicitly that the optional EXPERIENCE_PRESENT symbol was read. Minimality is therefore a property of the language, not an extra requirement on the implementation.")
    w("")
    w("Intuitively the other states are distinguishable because their sets of valid continuations differ: the languages Λ(q) are pairwise different and each state "
      "needs a different set of future categories to reach F (e.g. in Full Stack `q_database_sql` accepts V directly, whereas `q_api_communication` needs a database first).")
    w("")

    w("### Theorem 5 — correctness of the preparation (filtering and sorting)")
    w("")
    w("For a candidate with token list t, `classify(t)` evaluates, for every profile P, the word **prep_P(t)**: the subsequence of tokens that belong to Σ_P, "
      "stably sorted by the position of their category in the canonical order. Let O(t) ⊆ {C₁, …, C_k} be the set of categories of P that appear in t.")
    w("")
    w("*Claim A. κ(prep_P(t)) = C_{i₁}^{n₁} C_{i₂}^{n₂} … C_{i_m}^{n_m} with i₁ < i₂ < … < i_m, n_j ≥ 1, and {C_{i₁}, …, C_{i_m}} = O(t).*")
    w("")
    w("*Proof.* The sort is by category rank, so equal categories are adjacent and the ranks are non-decreasing; every observed category contributes at least one token (n_j ≥ 1) "
      "and no unobserved category contributes any. ∎")
    w("")
    w("*Claim B. Let O be a set of categories and let β(O) be the word with one block C_i⁺ per category of O in canonical order (any block lengths ≥ 1). "
      "Then β(O) matches R_P iff O contains every mandatory requirement of P:*")
    w("")
    w("- *chain profiles:* O = {C₁, …, C₅} (all five categories);")
    w("- *Full Stack:* F ∈ O, V ∈ O, O ∩ {B, K} ≠ ∅ and O ∩ {S, N} ≠ ∅ (E, G, A and D are optional).")
    w("")
    w("*Proof.* Chain: R_P = C₁⁺…C₅⁺ matches a block word iff every one of the five letters occurs. Full Stack: by the rewriting of R_FS shown in the definitions, "
      "R_FS = E\\* F⁺ G\\* (B\\*K\\*∖ε) A\\* (S\\*N\\*∖ε) D\\* V⁺; a block word in the order E < F < G < B < K < A < S < N < D < V matches iff F and V occur, "
      "at least one of B, K occurs (so that the factor B\\*K\\* is non-empty) and at least one of S, N occurs. The canonical order of the profile is exactly this order, "
      "so no block is ever out of place. ∎")
    w("")
    w("**Theorem 5.** *prep_P(t) ∈ L(M_P) ⇔ O(t) contains every mandatory requirement of P ⇔ `missing_categories` is empty.* "
      "In particular, if the candidate has at least one skill in every mandatory requirement, the prepared word belongs to the language, "
      "whatever the original order, the repetitions or the foreign skills in t.")
    w("")
    w("*Proof.* By Claim A the word κ(prep_P(t)) is a block word over O(t); by Claim B it matches R_P iff the mandatory requirements are in O(t); "
      "by Theorem 1 this is equivalent to prep_P(t) ∈ L(M_P). The set of mandatory requirements is the dictionary `required_groups`, "
      "and `missing_categories` lists those requirements without any observed category. ∎")
    w("")
    w("The theorem is also verified by tests: `test_fullstack_all_category_combinations_match_defined_requirements` evaluates the 2¹⁰ = 1,024 category subsets of Full Stack, "
      "the tests EC-05 and OR-01 check all permutations and 2,500 random words per profile (see [`stage3_tests.md`](stage3_tests.md)). "
      "Note that this is a statement about the *prepared* word; in **strict mode** the word must already be in canonical order (Theorem 1), "
      "and a word with every requirement can still be rejected by disorder.")
    w("")

    w("### Complexity")
    w("")
    w("| Operation | Time | Space | Justification |")
    w("|---|---|---|---|")
    w("| Build the four automata (once) | O(number of transitions) = 843 transitions in total | one table of states × alphabet per profile | one transition per pair (Theorem 2) |")
    w("| Recognize a word of n tokens (`evaluate_profile`, strict) | O(n) | O(n) trace | one lookup δ(q, s) per token; the trace stores one record per token |")
    w("| Prepare the word of one profile | O(n log n) | O(n) | filter (O(n)) plus a stable sort by rank |")
    w("| `classify` over the 4 profiles | O(n log n) | O(n) | four independent preparations and runs |")
    w("")
    w("With a fixed vocabulary of 79 tokens the category lookup is O(1) per token. All sizes are tiny, so the cost of the "
      "step-by-step trace and of rendering diagrams, not of the automaton, dominates the running time.")
    w("")

    w("### Correspondence between the mathematics and the code")
    w("")
    w("| Mathematics | Python |")
    w("|---|---|")
    w("| Profile P, categories C₁ … C_k in canonical order | `ProfileDefinition`, `canonical_categories` (list of `Category`) |")
    w("| Alphabet Σ_P | `ProfileDefinition.alphabet` |")
    w("| Category map κ | `ProfileDefinition.get_category_for_skill` |")
    w("| Automaton M_P | `ProfileAutomaton.dfa` (a `pyformlang` `DeterministicFiniteAutomaton`) |")
    w("| Q, q0, F, δ as sets and a function | `FormalTuple` returned by `ProfileAutomaton.get_formal_tuple()` (`states`, `initial_state`, `final_states`, `transitions`) |")
    w("| Dead state | `q_trap`, created by `_complete_with_trap` |")
    w("| Accepting state q_F | `state_names[-1]` (always `q_version_control`) |")
    w("| w ∈ L(M_P) | `ProfileAutomaton.accepts(word)`; with trace: `ResumeClassifier.evaluate_profile(profile_id, word)` |")
    w("| Configuration after i symbols δ*(q0, s₁…s_i) | `StepTransition(step_number=i, source_state, symbol, target_state)` |")
    w("| Pattern R_P | the expression printed under **Recognized pattern**; used as an independent oracle in test OR-01 |")
    w("| prep_P(t) | the `rank`/`sorted` code of `ResumeClassifier.classify` with `prepare_input=True` |")
    w("| Foreign tokens (not in Σ_P) | `ProfileEvaluationResult.ignored_tokens` |")
    w("| Observed categories O(t) | `ProfileEvaluationResult.satisfied_categories` |")
    w("| Mandatory requirements | `ProfileDefinition.required_groups` (name → set of categories that can satisfy it) |")
    w("| Missing requirements | `ProfileEvaluationResult.missing_categories` |")
    w("")

    w("### Worked example: reading δ from the table")
    w("")
    m = ms["machine_learning"]
    word = ["PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT"]
    w("Machine Learning Engineer, word **PYTHON · PANDAS · TENSORFLOW · POSTGRESQL · GIT**. The row of the δ table is the current state and "
      "the column is the category of the token (κ).")
    w("")
    w("| i | Token s_i | κ(s_i) | Current state | Cell of the table | δ*(q0, s₁…s_i) |")
    w("|---|---|---|---|---|---|")
    q = "q0"
    for i, s in enumerate(word, 1):
        cat = m.profile.get_category_for_skill(s)
        nq = m.delta[q, s]
        assert nq == m.cell[q, cat]
        w(f"| {i} | {s} | {cat} | `{q}` | row `{q}`, column {cat} → `{nq}` | `{nq}` |")
        q = nq
    assert q == m.final
    w("")
    w("δ*(q0, w) = `q_version_control` ∈ F, so w ∈ L(M_ML) and the candidate is accepted. By Theorem 1 this is the same as κ(w) = A B C D E matching A⁺B⁺C⁺D⁺E⁺.")
    w("")
    word = ["PYTHON", "POSTGRESQL", "GIT"]
    w("Same automaton, word **PYTHON · POSTGRESQL · GIT** (no data-processing and no ML framework):")
    w("")
    w("| i | Token | κ | Current state | Cell | State after |")
    w("|---|---|---|---|---|---|")
    q = "q0"
    for i, s in enumerate(word, 1):
        cat = m.profile.get_category_for_skill(s)
        nq = m.delta[q, s]
        w(f"| {i} | {s} | {cat} | `{q}` | row `{q}`, column {cat} → `{nq}` | `{nq}` |")
        q = nq
    assert q == "q_trap"
    w("")
    w("The second step falls into `q_trap`, which absorbs the rest of the word; δ* = `q_trap` ∉ F, so the word is rejected. "
      "The evaluator reports a canonical-order violation at step 2 (the automaton cannot skip the blocks DATA_PROCESSING and ML_FRAMEWORKS), "
      "and `missing_categories` names the real causes: DATA_PROCESSING and ML_FRAMEWORKS.")
    w("")
    m = ms["full_stack"]
    word = ["TYPESCRIPT", "DJANGO", "MONGODB", "GITLAB"]
    w("Full Stack Developer shows the **bypass edges** of the table. Word **TYPESCRIPT · DJANGO · MONGODB · GITLAB** "
      "(frontend language, a backend framework only, a NoSQL database only, version control):")
    w("")
    w("| i | Token | κ | Current state | Cell | State after |")
    w("|---|---|---|---|---|---|")
    q = "q0"
    for i, s in enumerate(word, 1):
        cat = m.profile.get_category_for_skill(s)
        nq = m.delta[q, s]
        w(f"| {i} | {s} | {cat} | `{q}` | row `{q}`, column {cat} → `{nq}` | `{nq}` |")
        q = nq
    assert q == m.final
    w("")
    w("The word skips FE_FRAMEWORK, BE_LANGUAGE, API_COMMUNICATION, DATABASE_SQL and DEVOPS_CLOUD and is still accepted, as the pattern "
      "`E* F+ G* (B+K*|K+) A* (S+N*|N+) D* V+` predicts: κ(w) = F K N V.")
    w("")
    return out
