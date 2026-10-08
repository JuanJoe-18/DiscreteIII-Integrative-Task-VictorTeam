"""Stage 3: Qualification Pattern Recognition using Finite Automata."""

from src.stage3_classifier.classifier import (
    ResumeClassifier,
    ResumeClassificationReport,
    ProfileEvaluationResult,
    StepTransition,
    ClassificationStatus,
)
from src.stage3_classifier.automata_models import (
    ProfileAutomaton,
    build_all_automata,
    FormalTuple,
)
from src.stage3_classifier.profiles import (
    ProfileDefinition,
    PROFILES_REGISTRY,
)

__all__ = [
    "ResumeClassifier",
    "ResumeClassificationReport",
    "ProfileEvaluationResult",
    "StepTransition",
    "ClassificationStatus",
    "ProfileAutomaton",
    "build_all_automata",
    "FormalTuple",
    "ProfileDefinition",
    "PROFILES_REGISTRY",
]
