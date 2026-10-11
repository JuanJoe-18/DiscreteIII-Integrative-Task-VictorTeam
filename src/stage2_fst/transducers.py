"""The finite-state transducers of Stage 2, defined as complete 7-tuples and run with pyformlang.

Every transducer is a deterministic FST  M = (Q, Σ, Γ, δ, ω, q0, F)  where

* ``δ : Q × Σ → Q`` is the transition function,
* ``ω : Q × Σ → Γ ∪ {λ}`` is the output function (``None`` stands for λ, the empty output),
* ``q0`` is the start state and ``F ⊆ Q`` the set of accepting states.

The class :class:`Transducer` keeps the tuple explicit (so it can be printed in the documentation
and checked by the tests), converts it to a ``pyformlang.fst.FST`` and has a tiny reference
simulator that is used to cross-check pyformlang.

The transducers are combined in a cascade (the output of one is the input of the next):

    raw token ──CLEAN──▶ clean word + ⊣ ──ALIAS──▶ canonical token
    years      ──EXPERIENCE──▶ EXPERIENCE_PRESENT
    tokens     ──FILTER(c1), FILTER(c2), ... ──▶ tokens grouped by category (canonical order)
"""

import string
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from pyformlang.fst import FST

from src.stage2_fst.aliases import ALIAS_FAMILIES, EXPERIENCE_TOKEN

#: End-of-word marker. The alias transducer reads it after the last letter, so that a word which is
#: a prefix of another one ("git" / "github") is not confused with it.
END = "⊣"

LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
DIGITS = string.digits
#: Characters kept by the cleaning transducer (besides letters and digits).
KEPT_SYMBOLS = "#+"
#: Separators removed by the cleaning transducer (they produce λ).
SEPARATORS = " .-_/"


@dataclass(frozen=True)
class Transducer:
    """A deterministic finite-state transducer written as a 7-tuple."""

    name: str
    states: Tuple[str, ...]
    sigma: Tuple[str, ...]
    gamma: Tuple[str, ...]
    delta: Mapping[Tuple[str, str], str]
    omega: Mapping[Tuple[str, str], Optional[str]]
    q0: str
    finals: Tuple[str, ...]
    #: Optional human readable meaning of each state (used by the documentation).
    labels: Mapping[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------ checks
    def validate(self) -> None:
        """Checks that the tuple is a well-formed deterministic transducer."""
        states, sigma, gamma = set(self.states), set(self.sigma), set(self.gamma)
        assert self.q0 in states, f"{self.name}: q0 is not a state"
        assert set(self.finals) <= states and self.finals, f"{self.name}: F must be a non-empty subset of Q"
        assert set(self.delta) == set(self.omega), f"{self.name}: δ and ω must have the same domain"
        for (state, symbol), target in self.delta.items():
            assert state in states and target in states, f"{self.name}: unknown state in δ({state}, {symbol})"
            assert symbol in sigma, f"{self.name}: {symbol!r} is not in Σ"
            out = self.omega[(state, symbol)]
            assert out is None or out in gamma, f"{self.name}: {out!r} is not in Γ"

    # --------------------------------------------------------------- execution
    def simulate(self, symbols: Iterable[str]) -> Optional[List[str]]:
        """Reference simulation: output sequence, or ``None`` if the input is rejected."""
        state = self.q0
        output: List[str] = []
        for symbol in symbols:
            key = (state, symbol)
            if key not in self.delta:
                return None
            out = self.omega[key]
            if out is not None:
                output.append(out)
            state = self.delta[key]
        return output if state in self.finals else None

    def to_fst(self) -> FST:
        """The same transducer as a ``pyformlang.fst.FST`` object."""
        fst = FST()
        fst.add_transitions(
            [(src, sym, dst, [] if self.omega[(src, sym)] is None else [self.omega[(src, sym)]])
             for (src, sym), dst in self.delta.items()]
        )
        fst.add_start_state(self.q0)
        for final in self.finals:
            fst.add_final_state(final)
        return fst

    def translate(self, symbols: Sequence[str]) -> Optional[List[str]]:
        """Runs the transducer with pyformlang. ``None`` means that the input is rejected."""
        return run_fst(self.to_fst(), symbols)

    @property
    def number_of_transitions(self) -> int:
        return len(self.delta)


def run_fst(fst: FST, symbols: Sequence[str]) -> Optional[List[str]]:
    """Translates ``symbols`` with a deterministic pyformlang FST (``None`` = rejected)."""
    outputs = list(fst.translate(list(symbols)))
    if not outputs:
        return None
    return [symbol for symbol in outputs[0]]


# ============================================================================
# T1 — CLEAN: lower-cases the word and removes the separators
# ============================================================================
def build_clean_transducer() -> Transducer:
    """``Q={q0}``; letters/digits/#/+ are copied in lower case and separators are erased (λ)."""
    delta: Dict[Tuple[str, str], str] = {}
    omega: Dict[Tuple[str, str], Optional[str]] = {}
    for ch in LOWER + DIGITS + KEPT_SYMBOLS:
        delta[("q0", ch)], omega[("q0", ch)] = "q0", ch
    for upper, lower in zip(UPPER, LOWER):
        delta[("q0", upper)], omega[("q0", upper)] = "q0", lower
    for ch in SEPARATORS:
        delta[("q0", ch)], omega[("q0", ch)] = "q0", None
    sigma = tuple(LOWER + UPPER + DIGITS + KEPT_SYMBOLS + SEPARATORS)
    gamma = tuple(LOWER + DIGITS + KEPT_SYMBOLS)
    t = Transducer("CLEAN", ("q0",), sigma, gamma, delta, omega, "q0", ("q0",),
                   {"q0": "reading a word"})
    t.validate()
    return t


CLEAN = build_clean_transducer()


def clean_word(raw: str) -> Optional[str]:
    """Output of CLEAN for ``raw`` (``None`` if it contains a symbol outside Σ)."""
    out = CLEAN.simulate(raw)
    return None if out is None else "".join(out)


# ============================================================================
# T2 — ALIAS: clean word  ->  canonical token
# ============================================================================
def clean_aliases(aliases: Mapping[str, Sequence[str]]) -> Dict[str, str]:
    """``{clean word: canonical}`` for a table ``{canonical: [spellings]}``.

    Raises ``ValueError`` if a spelling cannot be cleaned or if two different canonical tokens
    would share the same clean word (the transducer would not be deterministic).
    """
    table: Dict[str, str] = {}
    for canonical, spellings in aliases.items():
        for spelling in list(spellings) + [canonical]:
            word = clean_word(spelling)
            if not word:
                raise ValueError(f"spelling {spelling!r} of {canonical} cannot be cleaned")
            if table.setdefault(word, canonical) != canonical:
                raise ValueError(f"{spelling!r} is ambiguous: {table[word]} and {canonical}")
    return table


def build_alias_transducer(aliases: Mapping[str, Sequence[str]], name: str = "ALIAS") -> Transducer:
    """Trie transducer: one path per clean word, the canonical token is written on the ``⊣`` edge.

    * ``Q``  = prefixes of the clean words ∪ {q_f}   (q0 is the empty prefix)
    * ``Σ``  = letters, digits, ``#``, ``+`` and ``⊣``
    * ``Γ``  = the canonical tokens
    * ``δ(p, a) = p·a`` and ``ω(p, a) = λ`` for a letter ``a``; ``δ(w, ⊣) = q_f`` and ``ω(w, ⊣) = canon(w)``
    """
    table = clean_aliases(aliases)
    prefix_state: Dict[str, str] = {"": "q0"}
    labels: Dict[str, str] = {"q0": "ε"}
    delta: Dict[Tuple[str, str], str] = {}
    omega: Dict[Tuple[str, str], Optional[str]] = {}
    for word in sorted(table):
        for i, ch in enumerate(word):
            prefix, longer = word[:i], word[: i + 1]
            if longer not in prefix_state:
                prefix_state[longer] = f"q{len(prefix_state)}"
                labels[prefix_state[longer]] = longer
                delta[(prefix_state[prefix], ch)] = prefix_state[longer]
                omega[(prefix_state[prefix], ch)] = None
        delta[(prefix_state[word], END)] = "qf"
        omega[(prefix_state[word], END)] = table[word]
    labels["qf"] = "word accepted"
    letters = sorted({sym for (_, sym) in delta if sym != END})
    t = Transducer(
        name,
        tuple(list(prefix_state.values()) + ["qf"]),
        tuple(letters + [END]),
        tuple(sorted(set(table.values()))),
        delta, omega, "q0", ("qf",), labels,
    )
    t.validate()
    return t


def build_family_transducers() -> Dict[str, Transducer]:
    """One alias transducer per family of ``ALIAS_FAMILIES``."""
    return {family: build_alias_transducer(aliases, f"ALIAS_{family}")
            for family, aliases in ALIAS_FAMILIES.items()}


def build_full_alias_transducer() -> Transducer:
    """Alias transducer of the whole vocabulary (the union of the family transducers)."""
    merged: Dict[str, List[str]] = {}
    for aliases in ALIAS_FAMILIES.values():
        for canonical, spellings in aliases.items():
            merged.setdefault(canonical, []).extend(spellings)
    return build_alias_transducer(merged, "ALIAS")


# ============================================================================
# T3 — EXPERIENCE: any number  ->  EXPERIENCE_PRESENT
# ============================================================================
def build_experience_transducer() -> Transducer:
    """Abstracts a (non-empty) sequence of digits into the single symbol ``EXPERIENCE_PRESENT``.

    The exact number of years is kept by Stage 1; Stage 3 only needs to know that experience exists.
    """
    delta: Dict[Tuple[str, str], str] = {}
    omega: Dict[Tuple[str, str], Optional[str]] = {}
    for d in DIGITS:
        delta[("q0", d)], omega[("q0", d)] = "q1", EXPERIENCE_TOKEN
        delta[("q1", d)], omega[("q1", d)] = "q1", None
    t = Transducer("EXPERIENCE", ("q0", "q1"), tuple(DIGITS), (EXPERIENCE_TOKEN,), delta, omega,
                   "q0", ("q1",), {"q0": "no digit read", "q1": "number read"})
    t.validate()
    return t


EXPERIENCE = build_experience_transducer()


# ============================================================================
# T4 — FILTER(C): keeps only the tokens of one category (used by the canonical sort)
# ============================================================================
def build_filter_transducer(keep: Set[str], alphabet: Iterable[str], name: str = "FILTER") -> Transducer:
    """``Q={q0}``; ``a:a`` for ``a`` in ``keep`` and ``a:λ`` for the other symbols of the alphabet."""
    sigma = sorted(set(alphabet) | set(keep))
    delta = {("q0", s): "q0" for s in sigma}
    omega = {("q0", s): (s if s in keep else None) for s in sigma}
    t = Transducer(name, ("q0",), tuple(sigma), tuple(sorted(keep)), delta, omega, "q0", ("q0",),
                   {"q0": "scanning the tokens"})
    t.validate()
    return t
