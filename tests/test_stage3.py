"""Comprehensive test suite for Stage 3 (Qualification Pattern Recognition with DFAs)."""

import pytest
from src.stage3_classifier.automata_models import build_all_automata
from src.stage3_classifier.classifier import ResumeClassifier, ClassificationStatus
from src.stage3_classifier.visualizer import generate_mermaid_diagram, generate_graphviz_dot


@pytest.fixture
def classifier():
    return ResumeClassifier()


@pytest.fixture
def automata():
    return build_all_automata()


# ============================================================================
# 1. Tests for Full Stack Developer Automaton (M_FS)
# ============================================================================
def test_full_stack_minimal_accepted(classifier):
    """Minimal sequence fulfilling each category exactly once in canonical order."""
    tokens = ["JAVASCRIPT", "NODE_JS", "POSTGRESQL", "GIT"]
    res = classifier.evaluate_profile("full_stack", tokens)
    assert res.is_accepted is True
    assert res.status == ClassificationStatus.ACCEPTED
    assert res.final_state == "q_version_control"


def test_full_stack_multiple_skills_accepted(classifier):
    """Multiple skills per category exercising self-loops."""
    tokens = [
        "JAVASCRIPT", "REACT",        # Frontend
        "NODE_JS", "FASTAPI",         # Backend
        "POSTGRESQL", "MONGODB",      # Database
        "GIT", "GITHUB",              # VCS
    ]
    res = classifier.evaluate_profile("full_stack", tokens)
    assert res.is_accepted is True
    assert res.status == ClassificationStatus.ACCEPTED


def test_full_stack_with_numeric_experience_accepted(classifier):
    """Candidate starts with numeric years of experience range \\d."""
    # With numeric digit (e.g. Wednesday Addams: 3 years of experience)
    tokens_digit = ["3", "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]
    res1 = classifier.evaluate_profile("full_stack", tokens_digit)
    assert res1.is_accepted is True
    assert res1.status == ClassificationStatus.ACCEPTED
    assert res1.final_state == "q_version_control"

    # With range token \d
    tokens_range = [r"\d", "TYPESCRIPT", "ANGULAR", "DJANGO", "MYSQL", "GITHUB"]
    res2 = classifier.evaluate_profile("full_stack", tokens_range)
    assert res2.is_accepted is True
    assert res2.status == ClassificationStatus.ACCEPTED


def test_full_stack_missing_vcs_rejected(classifier):
    """Candidate has Frontend, Backend, DB, but lacks Version Control."""
    tokens = ["TYPESCRIPT", "REACT", "DJANGO", "SQL"]
    res = classifier.evaluate_profile("full_stack", tokens)
    assert res.is_accepted is False
    assert res.status == ClassificationStatus.REJECTED
    assert "VERSION_CONTROL" in res.missing_categories


def test_full_stack_out_of_order_rejected(classifier):
    """Candidate listed Git before Backend (violates canonical order)."""
    tokens = ["JAVASCRIPT", "GIT", "NODE_JS", "POSTGRESQL"]
    res = classifier.evaluate_profile("full_stack", tokens)
    assert res.is_accepted is False
    assert res.status == ClassificationStatus.REJECTED
    assert res.final_state == "q_trap"


def test_full_stack_foreign_token_rejected(classifier):
    """Candidate has skills from another domain not in Full Stack alphabet."""
    tokens = ["JAVASCRIPT", "NODE_JS", "SCIKIT_LEARN", "GIT"]
    res = classifier.evaluate_profile("full_stack", tokens)
    assert res.is_accepted is False
    assert res.status == ClassificationStatus.REJECTED
    assert res.final_state == "q_trap"


# ============================================================================
# 2. Tests for Machine Learning Engineer Automaton (M_ML)
# ============================================================================
def test_machine_learning_minimal_accepted(classifier):
    tokens = ["PYTHON", "PANDAS", "TENSORFLOW", "SQL", "GIT"]
    res = classifier.evaluate_profile("machine_learning", tokens)
    assert res.is_accepted is True
    assert res.status == ClassificationStatus.ACCEPTED
    assert res.final_state == "q_version_control"


def test_machine_learning_extended_accepted(classifier):
    tokens = [
        "PYTHON",
        "PANDAS", "NUMPY",
        "SCIKIT_LEARN", "PYTORCH",
        "SQL", "POSTGRESQL",
        "GIT",
    ]
    res = classifier.evaluate_profile("machine_learning", tokens)
    assert res.is_accepted is True
    assert res.status == ClassificationStatus.ACCEPTED


def test_machine_learning_missing_ml_framework_rejected(classifier):
    """Knows Python, Pandas, SQL, Git, but no ML/DL framework."""
    tokens = ["PYTHON", "PANDAS", "SQL", "GIT"]
    res = classifier.evaluate_profile("machine_learning", tokens)
    assert res.is_accepted is False
    assert res.status == ClassificationStatus.REJECTED
    assert "ML_FRAMEWORKS" in res.missing_categories


# ============================================================================
# 3. Tests for Cloud & DevOps Engineer Automaton (M_DEVOPS)
# ============================================================================
def test_devops_minimal_accepted(classifier):
    tokens = ["BASH", "GITHUB_ACTIONS", "DOCKER", "AWS", "GIT"]
    res = classifier.evaluate_profile("cloud_devops", tokens)
    assert res.is_accepted is True
    assert res.status == ClassificationStatus.ACCEPTED


def test_devops_extended_accepted(classifier):
    tokens = [
        "LINUX", "BASH",
        "JENKINS", "GITHUB_ACTIONS",
        "DOCKER", "KUBERNETES",
        "AWS", "TERRAFORM",
        "GIT", "GITHUB",
    ]
    res = classifier.evaluate_profile("cloud_devops", tokens)
    assert res.is_accepted is True
    assert res.status == ClassificationStatus.ACCEPTED


def test_devops_missing_containers_rejected(classifier):
    tokens = ["BASH", "JENKINS", "AWS", "GIT"]
    res = classifier.evaluate_profile("cloud_devops", tokens)
    assert res.is_accepted is False
    assert "CONTAINERS_ORCHESTRATION" in res.missing_categories


# ============================================================================
# 4. Tests for Data Scientist Automaton (M_DS)
# ============================================================================
def test_data_scientist_minimal_accepted(classifier):
    tokens = ["PYTHON", "PANDAS", "MATPLOTLIB", "SCIKIT_LEARN", "GIT"]
    res = classifier.evaluate_profile("data_scientist", tokens)
    assert res.is_accepted is True
    assert res.status == ClassificationStatus.ACCEPTED
    assert res.final_state == "q_version_control"


def test_data_scientist_extended_accepted(classifier):
    tokens = [
        "PYTHON", "SQL",                     # Language
        "PANDAS", "NUMPY",                   # Analysis & Stats
        "SEABORN", "PLOTLY", "TABLEAU",      # Data Visualization
        "SCIKIT_LEARN", "XGBOOST",           # Machine Learning
        "GIT", "GITHUB",                     # VCS
    ]
    res = classifier.evaluate_profile("data_scientist", tokens)
    assert res.is_accepted is True
    assert res.status == ClassificationStatus.ACCEPTED


def test_data_scientist_missing_visualization_rejected(classifier):
    """Candidate lacks Data Visualization skills."""
    tokens = ["PYTHON", "PANDAS", "SCIKIT_LEARN", "GIT"]
    res = classifier.evaluate_profile("data_scientist", tokens)
    assert res.is_accepted is False
    assert "DATA_VISUALIZATION" in res.missing_categories


def test_data_scientist_out_of_order_rejected(classifier):
    """Candidate listed ML before Visualization."""
    tokens = ["PYTHON", "PANDAS", "SCIKIT_LEARN", "MATPLOTLIB", "GIT"]
    res = classifier.evaluate_profile("data_scientist", tokens)
    assert res.is_accepted is False
    assert res.final_state == "q_trap"


# ============================================================================
# 5. General & Edge Case Tests
# ============================================================================
def test_empty_tokens_rejected(classifier):
    """Empty token list should be rejected by all profiles."""
    report = classifier.classify([])
    assert len(report.accepted_profiles) == 0
    assert len(report.rejected_profiles) == 4


def test_formal_tuples_structure(automata):
    """Verifies that all 4 automata produce valid 5-tuples."""
    for pid, auto in automata.items():
        t = auto.get_formal_tuple()
        assert "q0" == t.initial_state
        assert len(t.final_states) == 1
        assert len(t.states) >= 5
        assert len(t.alphabet) >= 10
        assert len(t.transitions) > 0
        md = t.to_markdown()
        assert "5-Tupla Formal" in md


def test_visualization_generators(automata):
    """Verifies that Mermaid and Graphviz strings are generated correctly."""
    for pid, auto in automata.items():
        mermaid_str = generate_mermaid_diagram(auto)
        assert "stateDiagram-v2" in mermaid_str
        assert "q0" in mermaid_str

        dot_str = generate_graphviz_dot(auto)
        assert "digraph DFA" in dot_str
        assert "q0" in dot_str
