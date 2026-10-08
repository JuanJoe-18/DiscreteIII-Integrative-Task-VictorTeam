"""Tests for the interface contracts connecting Stage 1, Stage 2, and Stage 3."""

import pytest

from src.stage1_regex import extract_qualifications
from src.stage2_fst import normalize_and_sort
from src.stage3_classifier import ResumeClassifier


@pytest.fixture
def classifier():
    return ResumeClassifier()


def test_wednesday_addams_end_to_end_pipeline(classifier):
    """Verifies that Wednesday Addams' CV text traverses Stages 1, 2, and 3 successfully."""
    cv_text = (
        "Wednesday Addams 3 years of experience developing web applications. "
        "Technical Skills: JS, React.js, NodeJS, Postgres, Git."
    )

    # 1. Stage 1: Extraction
    extraction = extract_qualifications(cv_text)
    assert "3" in extraction.raw_tokens
    assert any("JS" in t for t in extraction.raw_tokens)
    assert any("React.js" in t for t in extraction.raw_tokens)

    # 2. Stage 2: FST Normalization and Canonical Sorting
    normalization = normalize_and_sort(extraction.raw_tokens, profile_id="full_stack")
    normalized_tokens = normalization.normalized_tokens

    # Verify transformations
    assert "JAVASCRIPT" in normalized_tokens
    assert "REACT" in normalized_tokens
    assert "NODE_JS" in normalized_tokens
    assert "POSTGRESQL" in normalized_tokens
    assert "GIT" in normalized_tokens

    # 3. Stage 3: DFA Classification (Your stage)
    report = classifier.classify(normalized_tokens)
    fs_result = report.results_by_profile["full_stack"]

    assert fs_result.is_accepted, f"Expected accepted, got: {fs_result.rejection_reason}"
    assert fs_result.final_state == "q_version_control"


def test_stage3_rejects_raw_tokens_without_stage2(classifier):
    """Proves that Stage 3 strictly REQUIRES Stage 2.
    
    If unnormalized tokens (e.g. 'JS', 'React.js', 'Postgres') bypass Stage 2,
    Stage 3 DFA rejects them immediately because they are not in Sigma_FS.
    """
    raw_tokens = ["JS", "React.js", "NodeJS", "Postgres", "Git"]

    # Passing raw tokens directly to Stage 3 without Stage 2 FST normalization
    report = classifier.classify(raw_tokens)
    fs_result = report.results_by_profile["full_stack"]

    # Must be rejected because 'JS' and 'React.js' are not in the formal alphabet
    assert not fs_result.is_accepted
    assert fs_result.final_state == "q_trap"
    assert "no pertenece al alfabeto" in fs_result.rejection_reason


def test_mary_jane_watson_ml_engineer_pipeline(classifier):
    """Verifies that Mary Jane Watson's ML Engineer CV traverses Stages 1, 2, and 3."""
    cv_text = (
        "Mary Jane Watson 2 years of experience developing predictive models. "
        "Technical Skills: Python, Pandas, NumPy, Scikit-learn, TensorFlow, SQL, Git."
    )

    # 1. Stage 1
    extraction = extract_qualifications(cv_text)

    # 2. Stage 2
    normalization = normalize_and_sort(extraction.raw_tokens, profile_id="machine_learning")
    tokens = normalization.normalized_tokens

    assert "SCIKIT_LEARN" in tokens
    assert "TENSORFLOW" in tokens

    # 3. Stage 3
    report = classifier.classify(tokens)
    ml_result = report.results_by_profile["machine_learning"]

    assert ml_result.is_accepted, f"Expected accepted, got: {ml_result.rejection_reason}"
