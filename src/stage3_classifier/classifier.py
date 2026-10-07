"""Resume classification engine using pyformlang automata with detailed step traces.

This module executes the evaluation of candidate qualification sequences,
providing full execution trace, state transitions, acceptance/rejection status,
and human-readable diagnostic explanations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pyformlang.finite_automaton import State, Symbol

from src.stage3_classifier.automata_models import ProfileAutomaton, build_all_automata
from src.stage3_classifier.profiles import PROFILES_REGISTRY, ProfileDefinition


class ClassificationStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass
class StepTransition:
    """Represents a single step in the automaton execution trace."""
    step_number: int
    source_state: str
    symbol: str
    target_state: str
    category: Optional[str]
    is_valid_transition: bool


@dataclass
class ProfileEvaluationResult:
    """Contains the evaluation result of a candidate sequence against a specific profile."""
    profile_id: str
    profile_title: str
    status: ClassificationStatus
    is_accepted: bool
    final_state: str
    expected_final_state: str
    trace: List[StepTransition]
    rejection_reason: Optional[str] = None
    missing_categories: List[str] = field(default_factory=list)
    satisfied_categories: List[str] = field(default_factory=list)


@dataclass
class ResumeClassificationReport:
    """Overall classification report across all four profiles for a candidate."""
    input_tokens: List[str]
    accepted_profiles: List[str]
    rejected_profiles: List[str]
    results_by_profile: Dict[str, ProfileEvaluationResult]


class ResumeClassifier:
    """Evaluates candidate technical skills against the 4 formal profile automata."""

    def __init__(self):
        self.automata = build_all_automata()

    def evaluate_profile(
        self, profile_id: str, tokens: List[str]
    ) -> ProfileEvaluationResult:
        """Evaluates a list of normalized tokens against a specific profile's DFA."""
        if profile_id not in self.automata:
            raise ValueError(f"Unknown profile ID: {profile_id}")

        profile_auto = self.automata[profile_id]
        profile_def = profile_auto.profile
        dfa = profile_auto.dfa

        # State tracking
        current_state_obj = list(dfa.start_states)[0]
        current_state_name = str(current_state_obj.value)
        final_state_name = profile_auto.state_names[-1]

        trace: List[StepTransition] = []
        is_trapped = False
        rejection_reason = None

        for step_idx, token in enumerate(tokens, start=1):
            category = profile_def.get_category_for_skill(token)

            if is_trapped:
                # Once trapped, stay trapped
                trace.append(
                    StepTransition(
                        step_number=step_idx,
                        source_state="q_trap",
                        symbol=token,
                        target_state="q_trap",
                        category=category,
                        is_valid_transition=False,
                    )
                )
                continue

            # Look up pyformlang transition for (current_state, Symbol(token))
            sym = Symbol(token)
            next_state_obj = dfa._transition_function._transitions.get(
                current_state_obj, {}
            ).get(sym, None)

            if next_state_obj is not None:
                next_state_name = str(next_state_obj.value)

                trace.append(
                    StepTransition(
                        step_number=step_idx,
                        source_state=current_state_name,
                        symbol=token,
                        target_state=next_state_name,
                        category=category,
                        is_valid_transition=True,
                    )
                )
                current_state_obj = next_state_obj
                current_state_name = next_state_name
            else:
                # Transition not defined: move to q_trap
                is_trapped = True
                trace.append(
                    StepTransition(
                        step_number=step_idx,
                        source_state=current_state_name,
                        symbol=token,
                        target_state="q_trap",
                        category=category,
                        is_valid_transition=False,
                    )
                )
                if token not in profile_def.alphabet:
                    rejection_reason = (
                        f"El token '{token}' no pertenece al alfabeto del perfil {profile_def.title}."
                    )
                else:
                    rejection_reason = (
                        f"Violación del orden canónico en el paso {step_idx}: "
                        f"El token '{token}' (categoría {category}) no es válido desde el estado {current_state_name}."
                    )
                current_state_name = "q_trap"

        # Determine acceptance
        is_accepted = (not is_trapped) and (current_state_name == final_state_name)
        status = ClassificationStatus.ACCEPTED if is_accepted else ClassificationStatus.REJECTED

        # Determine satisfied and missing categories
        categories = profile_def.canonical_categories
        satisfied: List[str] = []
        missing: List[str] = []

        if is_accepted:
            satisfied = [cat.name for cat in categories]
        else:
            # Find how far the candidate got
            if current_state_name in profile_auto.state_names:
                state_idx = profile_auto.state_names.index(current_state_name)
                satisfied = [cat.name for cat in categories[:state_idx]]
                missing = [cat.name for cat in categories[state_idx:]]
            else:
                # If trapped, examine last valid state in trace
                last_valid_state = "q0"
                for step in trace:
                    if step.is_valid_transition:
                        last_valid_state = step.target_state
                state_idx = (
                    profile_auto.state_names.index(last_valid_state)
                    if last_valid_state in profile_auto.state_names
                    else 0
                )
                satisfied = [cat.name for cat in categories[:state_idx]]
                missing = [cat.name for cat in categories[state_idx:]]

            if not rejection_reason:
                if len(tokens) == 0:
                    rejection_reason = "Secuencia de calificaciones vacía. Ninguna competencia provista."
                else:
                    rejection_reason = (
                        f"Faltan competencias obligatorias para completar el perfil: {', '.join(missing)}."
                    )

        return ProfileEvaluationResult(
            profile_id=profile_id,
            profile_title=profile_def.title,
            status=status,
            is_accepted=is_accepted,
            final_state=current_state_name,
            expected_final_state=final_state_name,
            trace=trace,
            rejection_reason=rejection_reason,
            missing_categories=missing,
            satisfied_categories=satisfied,
        )

    def classify(self, tokens: List[str]) -> ResumeClassificationReport:
        """Evaluates tokens against all 4 profiles and compiles a comprehensive report."""
        results: Dict[str, ProfileEvaluationResult] = {}
        accepted: List[str] = []
        rejected: List[str] = []

        for pid in PROFILES_REGISTRY.keys():
            res = self.evaluate_profile(pid, tokens)
            results[pid] = res
            if res.is_accepted:
                accepted.append(res.profile_title)
            else:
                rejected.append(res.profile_title)

        return ResumeClassificationReport(
            input_tokens=tokens,
            accepted_profiles=accepted,
            rejected_profiles=rejected,
            results_by_profile=results,
        )
