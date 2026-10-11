"""Shared four-stage orchestration for the web API, Streamlit and CLI clients."""

from dataclasses import dataclass
import re

from src.stage1_regex import extract_qualifications
from src.stage1_regex.models import ExtractionResult
from src.stage2_fst.normalizer import NormalizationResult, normalize_qualifications, sort_to_canonical_order
from src.stage3_classifier import ResumeClassifier
from src.stage3_classifier.classifier import ResumeClassificationReport
from src.stage4_grammar import candidate_from_results, generate_document, ProfileDocument


@dataclass
class PipelineResult:
    extraction: ExtractionResult
    normalization: NormalizationResult
    classification: ResumeClassificationReport
    document: ProfileDocument
    candidate: dict


def extract_and_normalize(text):
    extraction = extract_qualifications(text)
    normalization = normalize_qualifications(extraction.raw_tokens, extraction.years_of_experience)
    candidate = {
        'contact': extraction.contact, 'education': extraction.education,
        'job_titles': extraction.job_titles, 'years_of_experience': extraction.years_of_experience,
    }
    if extraction.candidate_name:
        candidate['name'] = extraction.candidate_name
    for key, pattern in [
        ('name', r'(?im)^[ \t]*(?:Name|Nombre)[ \t]*:[ \t]*([^\r\n]+)'),
        ('description', r'(?im)^[ \t]*(?:Description|Descripción|Descripcion|Perfil)[ \t]*:[ \t]*([^\r\n]+)'),
    ]:
        match = re.search(pattern, text)
        if match and match.group(1).strip():
            candidate[key] = match.group(1).strip()
    return extraction, normalization, candidate


def process_resume(text: str, *, classifier=None) -> PipelineResult:
    """Extract facts, normalize/order with FSTs, run four DFAs, validate then render.

    Unlike strict word recognition, each profile receives its own projection of
    the normalized sequence. Foreign tokens remain visible in ignored_tokens.
    A resume with no recognized skills still yields a valid, rejected profile.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError('The resume must contain nonblank text.')
    classifier = classifier if classifier is not None else ResumeClassifier()
    extraction, normalization, candidate = extract_and_normalize(text)
    tokens = list(dict.fromkeys(normalization.normalized_tokens))
    results = {}
    for pid, automaton in classifier.automata.items():
        ordered = sort_to_canonical_order(tokens, pid)
        sequence = [token for token in ordered if token in automaton.profile.alphabet]
        result = classifier.evaluate_profile(pid, sequence)
        result.ignored_tokens = [token for token in tokens if token not in automaton.profile.alphabet]
        results[pid] = result
    report = ResumeClassificationReport(
        tokens,
        [r.profile_title for r in results.values() if r.is_accepted],
        [r.profile_title for r in results.values() if not r.is_accepted],
        results,
    )
    profile = candidate_from_results(extraction, normalization, report,
                                     name=candidate.get('name'), summary=candidate.get('description'))
    return PipelineResult(extraction, normalization, report, generate_document(profile), candidate)
