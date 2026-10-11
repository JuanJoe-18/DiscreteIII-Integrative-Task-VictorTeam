"""Stage 2: qualification normalization and canonical sorting with finite-state transducers.

``normalize_qualifications`` turns every raw token written by Stage 1 ("React.js", "JS",
"Postgres") into one canonical token ("REACT", "JAVASCRIPT", "POSTGRESQL") by running a cascade of
pyformlang transducers (see ``transducers.py``):

    raw token ──CLEAN──▶ clean word ⊣ ──ALIAS──▶ canonical token

``sort_to_canonical_order`` groups the canonical tokens in the category order of the selected
profile with one FILTER transducer per category, and ``normalize_and_sort`` runs both steps.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional

from pyformlang.fst import FST

from src.stage2_fst.aliases import EXPERIENCE_TOKEN
from src.stage2_fst.transducers import (
    END,
    EXPERIENCE,
    build_filter_transducer,
    build_full_alias_transducer,
    clean_word,
    run_fst,
)
from src.stage3_classifier.profiles import PROFILES_REGISTRY


@dataclass
class TokenTrace:
    """What the cascade did with one raw token (used by the interface and the documentation)."""
    raw: str
    clean: Optional[str]
    canonical: str
    recognized: bool


@dataclass
class NormalizationResult:
    """Represents the output of Stage 2 normalization."""
    normalized_tokens: List[str]
    transformations_applied: Dict[str, str] = field(default_factory=dict)
    unrecognized_tokens: List[str] = field(default_factory=list)
    traces: List[TokenTrace] = field(default_factory=list)


@lru_cache(maxsize=1)
def _alias_fst() -> FST:
    return build_full_alias_transducer().to_fst()


@lru_cache(maxsize=1)
def _experience_fst() -> FST:
    return EXPERIENCE.to_fst()


def _fallback(clean: str) -> str:
    """Canonical-looking token for a skill that is not in the vocabulary (Stage 1 category OTHER)."""
    return clean.upper().replace("-", "_").replace(" ", "_")


def normalize_token(raw: str) -> TokenTrace:
    """Runs the cascade CLEAN → ALIAS (or EXPERIENCE for a number) on one raw token."""
    text = raw.strip()
    if text.isdigit():
        out = run_fst(_experience_fst(), list(text))
        return TokenTrace(text, text, out[0] if out else EXPERIENCE_TOKEN, True)

    word = clean_word(text)
    if word:
        out = run_fst(_alias_fst(), list(word) + [END])
        if out:
            return TokenTrace(text, word, out[0], True)
    return TokenTrace(text, word, _fallback(text), False)


def normalize_qualifications(
    raw_tokens: List[str],
    years_of_experience: Optional[int] = None,
) -> NormalizationResult:
    """STAGE 2A: raw token → canonical token, one transducer run per token.

    ``years_of_experience`` is the integer found by Stage 1 (it is not part of ``raw_tokens``).
    When it is positive, the EXPERIENCE transducer abstracts it into ``EXPERIENCE_PRESENT``,
    which is placed first.
    """
    normalized: List[str] = []
    transformations: Dict[str, str] = {}
    unrecognized: List[str] = []
    traces: List[TokenTrace] = []

    inputs = list(raw_tokens)
    if years_of_experience is not None and years_of_experience > 0:
        inputs.insert(0, str(years_of_experience))

    for token in inputs:
        if not token.strip():
            continue
        trace = normalize_token(token)
        traces.append(trace)
        normalized.append(trace.canonical)
        if trace.recognized:
            if trace.raw != trace.canonical:
                transformations[trace.raw] = trace.canonical
        else:
            unrecognized.append(trace.raw)

    return NormalizationResult(normalized, transformations, unrecognized, traces)


def sort_to_canonical_order(
    normalized_tokens: List[str],
    profile_id: str = "full_stack",
) -> List[str]:
    """STAGE 2B: groups the tokens in the category order of the profile.

    One FILTER transducer per category copies only the tokens of that category; the outputs of the
    passes are concatenated in the canonical order of the profile. A last pass copies the tokens
    that do not belong to the profile. ``EXPERIENCE_PRESENT`` is erased when the profile has no
    EXPERIENCE category. The order inside a category is the order of the input (stable).
    """
    if profile_id not in PROFILES_REGISTRY or not normalized_tokens:
        return list(normalized_tokens)

    profile = PROFILES_REGISTRY[profile_id]
    alphabet = set(normalized_tokens)
    in_profile = profile.alphabet
    has_experience = any(cat.name == "EXPERIENCE" for cat in profile.canonical_categories)

    ordered: List[str] = []
    for category in profile.canonical_categories:
        keep = set(category.skills) & alphabet
        if keep:
            ordered += _run_filter(keep, alphabet, f"FILTER_{category.name}", normalized_tokens)

    keep_rest = {t for t in alphabet if t not in in_profile}
    if not has_experience:
        keep_rest.discard(EXPERIENCE_TOKEN)
    if keep_rest:
        ordered += _run_filter(keep_rest, alphabet, "FILTER_REST", normalized_tokens)
    return ordered


def _run_filter(keep, alphabet, name: str, tokens: List[str]) -> List[str]:
    out = run_fst(build_filter_transducer(keep, alphabet, name).to_fst(), tokens)
    return out or []


def normalize_and_sort(
    raw_tokens: List[str],
    profile_id: str = "full_stack",
    years_of_experience: Optional[int] = None,
) -> NormalizationResult:
    """STAGE 2 complete: normalizes the tokens and sorts them for the Stage 3 automaton."""
    result = normalize_qualifications(raw_tokens, years_of_experience)
    result.normalized_tokens = sort_to_canonical_order(result.normalized_tokens, profile_id)
    return result
