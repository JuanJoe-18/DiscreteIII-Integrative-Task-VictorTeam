import pytest

from src.stage2_fst import normalize_and_sort
from src.stage3_classifier import ResumeClassifier
from src.stage3_classifier.visualizer import generate_mermaid_diagram, generate_graphviz_dot


def test_classification_prepares_each_profile_and_preserves_input():
    tokens = ['GIT', 'SQL', 'MATPLOTLIB', 'SCIKIT_LEARN', 'PANDAS', 'PYTHON', 'UNKNOWN']
    report = ResumeClassifier().classify(tokens)
    assert set(report.accepted_profiles) == {'Machine Learning Engineer', 'Data Scientist'}
    ml = report.results_by_profile['machine_learning']
    assert ml.evaluated_tokens == ['PYTHON', 'PANDAS', 'SCIKIT_LEARN', 'SQL', 'GIT']
    assert ml.ignored_tokens == ['MATPLOTLIB', 'UNKNOWN']
    assert tokens == report.input_tokens


def test_optional_categories_are_not_invented_or_required():
    c = ResumeClassifier()
    tokens = ['JAVASCRIPT', 'NODE_JS', 'POSTGRESQL']
    rejected = c.evaluate_profile('full_stack', tokens)
    assert rejected.satisfied_categories == ['FE_LANGUAGE', 'BE_LANGUAGE', 'DATABASE_SQL']
    assert rejected.missing_categories == ['VERSION_CONTROL']
    accepted = c.evaluate_profile('full_stack', tokens + ['GIT'])
    assert accepted.satisfied_categories == rejected.satisfied_categories + ['VERSION_CONTROL']
    assert accepted.missing_categories == []


def test_missing_means_absent_not_unreachable_after_trap():
    r = ResumeClassifier().evaluate_profile('machine_learning', ['PYTHON', 'PANDAS', 'SQL', 'GIT'])
    assert r.missing_categories == ['ML_FRAMEWORKS']
    assert r.satisfied_categories == ['CORE_LANGUAGE', 'DATA_PROCESSING', 'DATABASE', 'VERSION_CONTROL']
    assert not r.is_accepted


@pytest.mark.parametrize('years', ['0', '3', '10', '25'])
def test_experience_is_a_finite_optional_symbol(years):
    tokens = normalize_and_sort([years, 'JS', 'NodeJS', 'Postgres', 'Git'], 'full_stack').normalized_tokens
    assert tokens[0] == 'EXPERIENCE_PRESENT'
    assert ResumeClassifier().evaluate_profile('full_stack', tokens).is_accepted


def test_formal_models_are_total_and_match_evaluator_and_diagrams():
    c = ResumeClassifier()
    for pid, auto in c.automata.items():
        formal = auto.get_formal_tuple()
        assert 'q_trap' in formal.states
        assert len(formal.transitions) == len(formal.states) * len(formal.alphabet)
        mermaid = generate_mermaid_diagram(auto)
        dot = generate_graphviz_dot(auto)
        assert 'q_trap' in dot
        for (source, symbol), target in formal.transitions.items():
            assert f'{source} --> {target} : {symbol}' in mermaid
        words = [[], ['UNKNOWN'], list(formal.alphabet), ['GIT', 'PYTHON']]
        for word in words:
            assert auto.accepts(word) == c.evaluate_profile(pid, word).is_accepted


def test_mermaid_fullstack_contains_direct_entry_and_bypass():
    auto = ResumeClassifier().automata['full_stack']
    mermaid = generate_mermaid_diagram(auto)
    assert 'q0 --> q_fe_language : JAVASCRIPT' in mermaid
    assert 'q_fe_language --> q_be_language : NODE_JS' in mermaid
    assert 'q_database_sql --> q_version_control : GIT' in mermaid


def test_strict_classification_does_not_repair_invalid_words():
    report = ResumeClassifier().classify(['GIT', 'JAVASCRIPT', 'NODE_JS', 'SQL'], prepare_input=False)
    assert not report.accepted_profiles
    assert report.results_by_profile['full_stack'].final_state == 'q_trap'


def test_fullstack_all_category_combinations_match_defined_requirements():
    from itertools import product
    c = ResumeClassifier()
    profile = c.automata['full_stack'].profile
    for presence in product([False, True], repeat=10):
        word = [sorted(cat.skills)[0] for cat, present in zip(profile.canonical_categories, presence) if present]
        expected = presence[1] and (presence[3] or presence[4]) and (presence[6] or presence[7]) and presence[9]
        assert c.evaluate_profile('full_stack', word).is_accepted == expected


def test_all_profiles_require_each_mandatory_group():
    c = ResumeClassifier()
    for pid, auto in c.automata.items():
        categories = auto.profile.canonical_categories
        assert sum(len(cat.skills) for cat in categories) == len(auto.profile.alphabet)
        full = [sorted(cat.skills)[0] for cat in categories]
        assert auto.accepts(full)
        for name, alternatives in auto.profile.required_groups.items():
            incomplete = [token for token in full if auto.profile.get_category_for_skill(token) not in alternatives]
            result = c.evaluate_profile(pid, incomplete)
            assert not result.is_accepted
            assert result.missing_categories == [name]
