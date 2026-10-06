"""Automata models implementation for ResumeLens using pyformlang.

This module formalizes and instantiates the 4 DFAs:
- Full Stack Developer (M_FS)
- Machine Learning Engineer (M_ML)
- Cloud & DevOps Engineer (M_DEVOPS)
- Data Scientist (M_DS)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from pyformlang.finite_automaton import DeterministicFiniteAutomaton, State, Symbol

from src.stage3_classifier.profiles import (
    ProfileDefinition,
    FULL_STACK_PROFILE,
    MACHINE_LEARNING_PROFILE,
    DEVOPS_PROFILE,
    DATA_SCIENTIST_PROFILE,
    PROFILES_REGISTRY,
)


@dataclass
class FormalTuple:
    """Represents the formal 5-tuple M = (Q, Sigma, delta, q0, F)."""
    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[Tuple[str, str], str]
    initial_state: str
    final_states: Set[str]

    def to_markdown(self) -> str:
        """Renders the 5-tuple into formatted Markdown."""
        delta_lines = [
            f"  - δ({src}, {sym}) = {dst}"
            for (src, sym), dst in sorted(self.transitions.items())
        ]
        return (
            f"**5-Tupla Formal M = (Q, Σ, δ, q₀, F):**\n\n"
            f"- **Q (Estados):** {{{', '.join(sorted(self.states))}}}\n"
            f"- **Σ (Alfabeto):** {{{', '.join(sorted(self.alphabet))}}}\n"
            f"- **q₀ (Estado Inicial):** {self.initial_state}\n"
            f"- **F (Estados de Aceptación):** {{{', '.join(sorted(self.final_states))}}}\n"
            f"- **δ (Transiciones de Avance y Bucles):**\n"
            + "\n".join(delta_lines[:15])
            + (f"\n  - ... ({len(delta_lines)} transiciones en total)" if len(delta_lines) > 15 else "")
        )


class ProfileAutomaton:
    """Wraps a pyformlang DeterministicFiniteAutomaton corresponding to a ProfileDefinition."""

    def __init__(self, profile: ProfileDefinition):
        self.profile = profile
        self.dfa = DeterministicFiniteAutomaton()
        self.state_names: List[str] = []
        self._build_automaton()

    def _build_automaton(self) -> None:
        """Constructs the DFA states and transitions according to canonical categories."""
        categories = self.profile.canonical_categories
        k = len(categories)

        # 1. Define states
        # q0 is the initial state (no categories satisfied)
        # q1, ..., qk represent satisfaction of categories 1..k
        self.state_names = ["q0"] + [f"q_{cat.name.lower()}" for cat in categories]
        self.state_objects = {name: State(name) for name in self.state_names}

        # Set start state and final state
        q0 = self.state_objects["q0"]
        q_final = self.state_objects[self.state_names[-1]]

        self.dfa.add_start_state(q0)
        self.dfa.add_final_state(q_final)

        # 2. Build transitions
        # From q0: tokens in Category 1 advance to state q1
        first_cat = categories[0]
        q1 = self.state_objects[self.state_names[1]]
        for skill in first_cat.skills:
            self.dfa.add_transition(q0, Symbol(skill), q1)

        # For intermediate and final states
        for i in range(1, k + 1):
            curr_state = self.state_objects[self.state_names[i]]
            curr_cat = categories[i - 1]

            # Self-loops: multiple skills within the current category stay in the current state
            for skill in curr_cat.skills:
                self.dfa.add_transition(curr_state, Symbol(skill), curr_state)

            # Advance transition to the next category (if not the last state)
            if i < k:
                next_state = self.state_objects[self.state_names[i + 1]]
                next_cat = categories[i]
                for skill in next_cat.skills:
                    self.dfa.add_transition(curr_state, Symbol(skill), next_state)

    def accepts(self, word: List[str]) -> bool:
        """Evaluates whether the sequence of normalized tokens is accepted by the DFA."""
        symbols = [Symbol(token) for token in word]
        return self.dfa.accepts(symbols)

    def get_formal_tuple(self) -> FormalTuple:
        """Returns the formal mathematical 5-tuple M = (Q, Sigma, delta, q0, F)."""
        states_set = set(self.state_names)
        alphabet_set = self.profile.alphabet
        trans_dict: Dict[Tuple[str, str], str] = {}

        # Extract transitions from pyformlang DFA
        for src_state, sym_dict in self.dfa._transition_function._transitions.items():
            src_name = str(src_state.value)
            for sym, dest in sym_dict.items():
                sym_name = str(sym.value)
                trans_dict[(src_name, sym_name)] = str(dest.value)

        return FormalTuple(
            states=states_set,
            alphabet=alphabet_set,
            transitions=trans_dict,
            initial_state="q0",
            final_states={self.state_names[-1]},
        )


def build_all_automata() -> Dict[str, ProfileAutomaton]:
    """Constructs and returns the DFA instances for all 4 profiles."""
    return {
        pid: ProfileAutomaton(profile)
        for pid, profile in PROFILES_REGISTRY.items()
    }
