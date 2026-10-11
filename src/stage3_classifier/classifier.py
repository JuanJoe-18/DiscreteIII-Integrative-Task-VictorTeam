"""Resume classification engine using pyformlang automata with detailed step traces.

This module executes the evaluation of candidate qualification sequences,
providing full execution trace, state transitions, acceptance/rejection status,
and human-readable diagnostic explanations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from pyformlang.finite_automaton import Symbol

from src.stage3_classifier.automata_models import build_all_automata
from src.stage3_classifier.profiles import PROFILES_REGISTRY


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
    evaluated_tokens: List[str] = field(default_factory=list)
    ignored_tokens: List[str] = field(default_factory=list)
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
            destinations = dfa(current_state_obj, sym)
            next_state_obj = destinations[0] if destinations else None
            next_state_name = str(next_state_obj.value) if next_state_obj else "q_trap"
            if next_state_name != "q_trap":
                trace.append(StepTransition(
                    step_idx, current_state_name, token, next_state_name, category, True
                ))
                current_state_obj = next_state_obj
                current_state_name = next_state_name
            else:
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
                        f"Token '{token}' does not belong to the alphabet of profile {profile_def.title}."
                    )
                else:
                    rejection_reason = (
                        f"Canonical-order violation at step {step_idx}: "
                        f"Token '{token}' (category {category}) is not valid from state {current_state_name}."
                    )
                current_state_name = "q_trap"

        # Determine acceptance
        is_accepted = (not is_trapped) and (current_state_name == final_state_name)
        status = ClassificationStatus.ACCEPTED if is_accepted else ClassificationStatus.REJECTED

        # Observed competencies are independent of execution order or optional bypasses.
        observed = {profile_def.get_category_for_skill(token) for token in tokens}
        satisfied = [cat.name for cat in profile_def.canonical_categories if cat.name in observed]
        missing = [name for name, alternatives in profile_def.required_groups.items()
                   if not alternatives.intersection(observed)]
        if not is_accepted and not rejection_reason:
            rejection_reason = (
                "Empty sequence. No competencies provided."
                if not tokens else
                f"Mandatory competencies are missing to complete the profile: {', '.join(missing)}."
            )

        return ProfileEvaluationResult(
            profile_id=profile_id,
            profile_title=profile_def.title,
            status=status,
            is_accepted=is_accepted,
            final_state=current_state_name,
            expected_final_state=final_state_name,
            trace=trace,
            evaluated_tokens=list(tokens),
            rejection_reason=rejection_reason,
            missing_categories=missing,
            satisfied_categories=satisfied,
        )

    def classify(self, tokens: List[str], *, prepare_input: bool = True) -> ResumeClassificationReport:
        """Classifies normalized skills using a separate projection/order per profile.

        Unrelated skills are reported, never used to satisfy a requirement.
        Set prepare_input=False for strict word recognition without preparation.
        """
        results: Dict[str, ProfileEvaluationResult] = {}
        accepted: List[str] = []
        rejected: List[str] = []

        for pid in PROFILES_REGISTRY.keys():
            profile = self.automata[pid].profile
            rank = {skill: index for index, cat in enumerate(profile.canonical_categories)
                    for skill in cat.skills}
            relevant = sorted((token for token in tokens if token in rank), key=rank.__getitem__)
            res = self.evaluate_profile(pid, relevant if prepare_input else tokens)
            if prepare_input:
                res.ignored_tokens = [token for token in tokens if token not in rank]
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
