"""Comprehensive test suite for Stage 3 (Qualification Pattern Recognition with DFAs).

Sections 1-7 are the original example-based tests. Section 8 holds the scenario, equivalence-class,
boundary, specification-table, oracle and structural tests (identifiers SC-xx, EC-xx, BV-xx, SP-xx,
OR-xx, ST-xx) that are catalogued in docs/stage3_tests.md.
"""

import itertools
import random
import re
from pathlib import Path

import pytest

from src.stage1_regex import extract_qualifications
from src.stage2_fst import normalize_and_sort
from src.stage3_classifier import PROFILES_REGISTRY
from src.stage3_classifier.automata_models import build_all_automata
from src.stage3_classifier.classifier import ResumeClassifier, ClassificationStatus
from src.stage3_classifier.visualizer import (
    build_graphviz_diagram,
    generate_graphviz_dot,
    generate_mermaid_diagram,
)


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
    """Candidate starts with the canonical optional experience symbol."""
    # Normalized experience; exact years are metadata.
    tokens_digit = ["EXPERIENCE_PRESENT", "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]
    res1 = classifier.evaluate_profile("full_stack", tokens_digit)
    assert res1.is_accepted is True
    assert res1.status == ClassificationStatus.ACCEPTED
    assert res1.final_state == "q_version_control"

    # Same token with another valid skill path.
    tokens_range = ["EXPERIENCE_PRESENT", "TYPESCRIPT", "ANGULAR", "DJANGO", "MYSQL", "GITHUB"]
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
        assert "Formal 5-tuple" in md


def test_visualization_generators(automata):
    """Verifies that Mermaid and Graphviz strings are generated correctly."""
    for pid, auto in automata.items():
        mermaid_str = generate_mermaid_diagram(auto)
        assert "stateDiagram-v2" in mermaid_str
        assert "q0" in mermaid_str

        dot_str = generate_graphviz_dot(auto)
        assert "digraph DFA" in dot_str
        assert "q0" in dot_str


# ============================================================================
# 8. Scenario, equivalence-class, boundary, oracle and structural tests
# ============================================================================
RESUMES = Path(__file__).parent / "data" / "resumes"
PIDS = list(PROFILES_REGISTRY)
FULL = {
    "full_stack": ["JAVASCRIPT", "PYTHON", "POSTGRESQL", "GIT"],
    "machine_learning": ["PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT"],
    "cloud_devops": ["BASH", "JENKINS", "DOCKER", "AWS", "GIT"],
    "data_scientist": ["PYTHON", "PANDAS", "MATPLOTLIB", "SCIKIT_LEARN", "GIT"],
}
TITLES = {pid: PROFILES_REGISTRY[pid].title for pid in PIDS}


@pytest.fixture(scope="module")
def clf():
    return ResumeClassifier()


@pytest.fixture(scope="module")
def autos():
    return build_all_automata()


def pipeline(name, clf, profile="full_stack"):
    text = (RESUMES / f"{name}.txt").read_text(encoding="utf-8")
    extraction = extract_qualifications(text)
    normalized = normalize_and_sort(
        extraction.raw_tokens, profile, years_of_experience=extraction.years_of_experience
    )
    return normalized, clf.classify(normalized.normalized_tokens)


# --------------------------------------------------------------------------- SC
def test_sc01_wednesday_addams_is_only_full_stack(clf):
    _, report = pipeline("wednesday_addams", clf)
    assert report.accepted_profiles == ["Full Stack Developer"]


def test_sc02_mary_jane_is_only_machine_learning(clf):
    _, report = pipeline("mary_jane_watson", clf)
    assert report.accepted_profiles == ["Machine Learning Engineer"]
    ds = report.results_by_profile["data_scientist"]
    assert "DATA_VISUALIZATION" in ds.missing_categories
    assert "TENSORFLOW" in ds.ignored_tokens


def test_sc03_rich_resume_matches_two_profiles(clf):
    normalized, report = pipeline("rich_resume", clf)
    assert set(report.accepted_profiles) == {"Full Stack Developer", "Cloud & DevOps Engineer"}
    assert normalized.unrecognized_tokens  # Figma and Notion are not in the vocabulary
    assert "FIGMA" in report.results_by_profile["full_stack"].ignored_tokens


def test_sc04_spanish_resume_is_machine_learning(clf):
    _, report = pipeline("spanish_resume", clf)
    assert report.accepted_profiles == ["Machine Learning Engineer"]


def test_sc05_candidate_with_no_matching_profile(clf):
    report = clf.classify(["HTML", "CSS", "FIGMA", "NOTION"])
    assert report.accepted_profiles == []
    assert sorted(report.rejected_profiles) == sorted(TITLES.values())


def test_sc06_one_candidate_can_satisfy_all_four_profiles(clf):
    tokens = FULL["full_stack"] + FULL["machine_learning"] + FULL["cloud_devops"] + FULL["data_scientist"]
    report = clf.classify(tokens)
    assert sorted(report.accepted_profiles) == sorted(TITLES.values())


def test_sc07_statement_example_trace(clf):
    result = clf.evaluate_profile("machine_learning", FULL["machine_learning"])
    assert result.is_accepted and result.final_state == "q_version_control"
    assert [s.target_state for s in result.trace] == [
        "q_core_language", "q_data_processing", "q_ml_frameworks", "q_database", "q_version_control"]
    assert all(s.is_valid_transition for s in result.trace)


def test_sc08_raw_tokens_without_stage2_are_rejected_by_every_profile(clf):
    report = clf.classify(["JS", "React.js", "Postgres", "Git"], prepare_input=False)
    assert report.accepted_profiles == []
    for result in report.results_by_profile.values():
        assert result.final_state == "q_trap"
        assert "does not belong to the alphabet" in result.rejection_reason


# --------------------------------------------------------------------------- EC
@pytest.mark.parametrize("pid", PIDS)
def test_ec01_every_mandatory_group_is_necessary(clf, pid):
    profile = PROFILES_REGISTRY[pid]
    for name, alternatives in profile.required_groups.items():
        word = [t for t in FULL[pid]
                if profile.get_category_for_skill(t) not in alternatives]
        result = clf.evaluate_profile(pid, word)
        assert not result.is_accepted, name
        assert name in result.missing_categories


@pytest.mark.parametrize("pid", PIDS)
def test_ec02_repetition_inside_a_block_is_accepted(clf, pid):
    word = [t for t in FULL[pid] for _ in range(3)]
    assert clf.evaluate_profile(pid, word).is_accepted


@pytest.mark.parametrize("pid", PIDS)
def test_ec03_every_category_alternative_is_accepted(clf, pid):
    """Replacing one token by ANY other token of its category keeps the word accepted."""
    profile = PROFILES_REGISTRY[pid]
    for index, token in enumerate(FULL[pid]):
        category = next(c for c in profile.canonical_categories if token in c.skills)
        for alternative in category.skills:
            word = FULL[pid][:index] + [alternative] + FULL[pid][index + 1:]
            assert clf.evaluate_profile(pid, word).is_accepted, (pid, alternative)


@pytest.mark.parametrize("pid", PIDS)
def test_ec04_adjacent_swap_of_different_blocks_is_rejected_in_strict_mode(clf, pid):
    word = FULL[pid]
    profile = PROFILES_REGISTRY[pid]
    for i in range(len(word) - 1):
        if profile.get_category_for_skill(word[i]) == profile.get_category_for_skill(word[i + 1]):
            continue
        swapped = word[:i] + [word[i + 1], word[i]] + word[i + 2:]
        assert not clf.evaluate_profile(pid, swapped).is_accepted, (pid, i)


@pytest.mark.parametrize("pid", PIDS)
def test_ec05_prepared_mode_accepts_every_permutation(clf, pid):
    for permutation in itertools.permutations(FULL[pid]):
        report = clf.classify(list(permutation))
        assert report.results_by_profile[pid].is_accepted, permutation


@pytest.mark.parametrize("pid", PIDS)
def test_ec06_foreign_token_anywhere_is_rejected_strictly_and_ignored_when_prepared(clf, pid):
    word = FULL[pid]
    for position in range(len(word) + 1):
        polluted = word[:position] + ["COBOL"] + word[position:]
        strict = clf.evaluate_profile(pid, polluted)
        assert not strict.is_accepted and "does not belong to the alphabet" in strict.rejection_reason
        prepared = clf.classify(polluted).results_by_profile[pid]
        assert prepared.is_accepted and prepared.ignored_tokens == ["COBOL"]


def test_ec07_tokens_of_other_profiles_do_not_satisfy_requirements(clf):
    # DOCKER/AWS belong to Full Stack's optional block but cannot replace a database.
    result = clf.classify(["JAVASCRIPT", "PYTHON", "DOCKER", "AWS", "GIT"]).results_by_profile["full_stack"]
    assert not result.is_accepted and result.missing_categories == ["DATABASE"]


def test_ec08_full_stack_alternatives(clf):
    accepted = [
        ["HTML", "DJANGO", "REDIS", "GITHUB"],            # backend by framework only, NoSQL only
        ["CSS", "JAVA", "SPRING_BOOT", "MYSQL", "REDIS", "GIT"],
        ["EXPERIENCE_PRESENT", "TYPESCRIPT", "VUE", "GO", "GRAPHQL", "SQLITE", "KUBERNETES", "GITLAB"],
    ]
    for word in accepted:
        assert clf.evaluate_profile("full_stack", word).is_accepted, word


# --------------------------------------------------------------------------- BV
@pytest.mark.parametrize("pid", PIDS)
def test_bv01_empty_and_single_token_words(clf, pid):
    empty = clf.evaluate_profile(pid, [])
    assert not empty.is_accepted and empty.final_state == "q0"
    assert "Empty sequence" in empty.rejection_reason
    for token in PROFILES_REGISTRY[pid].alphabet:
        assert not clf.evaluate_profile(pid, [token]).is_accepted


@pytest.mark.parametrize("pid", PIDS)
def test_bv02_prefixes_of_a_valid_word_are_rejected_and_the_full_word_accepted(clf, pid):
    word = FULL[pid]
    for cut in range(len(word)):
        assert not clf.evaluate_profile(pid, word[:cut]).is_accepted
    assert clf.evaluate_profile(pid, word).is_accepted


@pytest.mark.parametrize("pid", PIDS)
def test_bv03_very_long_word_is_linear_and_accepted(clf, pid):
    word = [t for t in FULL[pid] for _ in range(2000)]
    result = clf.evaluate_profile(pid, word)
    assert result.is_accepted and len(result.trace) == len(word)


@pytest.mark.parametrize("pid", PIDS)
def test_bv04_trap_is_absorbing_and_trace_is_consistent(clf, pid):
    word = FULL[pid][::-1] + FULL[pid]   # starts with a violation
    result = clf.evaluate_profile(pid, word)
    assert not result.is_accepted and result.final_state == "q_trap"
    assert [s.step_number for s in result.trace] == list(range(1, len(word) + 1))
    first_bad = next(i for i, s in enumerate(result.trace) if not s.is_valid_transition)
    assert all(s.target_state == "q_trap" and not s.is_valid_transition for s in result.trace[first_bad:])
    for before, after in zip(result.trace, result.trace[1:]):
        assert before.target_state == after.source_state


@pytest.mark.parametrize("pid", PIDS)
def test_bv05_unknown_profile_and_input_not_mutated(clf, pid):
    with pytest.raises(ValueError):
        clf.evaluate_profile("astronaut", ["PYTHON"])
    tokens = list(reversed(FULL[pid]))
    snapshot = list(tokens)
    clf.classify(tokens)
    clf.classify(tokens, prepare_input=False)
    clf.evaluate_profile(pid, tokens)
    assert tokens == snapshot


def test_bv06_experience_only_matters_in_full_stack(clf):
    for pid in PIDS:
        word = ["EXPERIENCE_PRESENT"] + FULL[pid]
        strict = clf.evaluate_profile(pid, word)
        assert strict.is_accepted == (pid == "full_stack")
        prepared = clf.classify(word).results_by_profile[pid]
        assert prepared.is_accepted


# --------------------------------------------------------------------------- OR
LETTERS = "EFGBKASNDV"
FS_ORDER = ["EXPERIENCE", "FE_LANGUAGE", "FE_FRAMEWORK", "BE_LANGUAGE", "BE_FRAMEWORK",
            "API_COMMUNICATION", "DATABASE_SQL", "DATABASE_NOSQL", "DEVOPS_CLOUD", "VERSION_CONTROL"]
FS_REGEX = re.compile(r"E*F+G*(B+K*|K+)A*(S+N*|N+)D*V+")


def _category_regex(pid):
    """Independent oracle: the regular expression of each profile, over category letters."""
    if pid == "full_stack":
        return FS_REGEX, dict(zip(FS_ORDER, "EFGBKASNDV"))
    names = [c.name for c in PROFILES_REGISTRY[pid].canonical_categories]
    letters = "ABCDE"
    return re.compile("".join(f"{letter}+" for letter in letters)), dict(zip(names, letters))


@pytest.mark.parametrize("pid", PIDS)
def test_or01_dfa_agrees_with_independent_regular_expression(clf, autos, pid):
    """2,500 random words over Sigma: pyformlang DFA == evaluator == Python `re` oracle."""
    rng = random.Random(20261011)
    profile = PROFILES_REGISTRY[pid]
    regex, letter = _category_regex(pid)
    categories = profile.canonical_categories
    accepted_seen = 0
    for _ in range(2500):
        # bias towards ordered words so that both outcomes are frequent
        length = rng.randint(0, 9)
        cats = sorted(rng.choices(categories, k=length), key=categories.index) if rng.random() < 0.7 \
            else rng.choices(categories, k=length)
        word = [rng.choice(sorted(c.skills)) for c in cats]
        expected = bool(regex.fullmatch("".join(letter[c.name] for c in cats)))
        assert autos[pid].accepts(word) == expected, word
        assert clf.evaluate_profile(pid, word).is_accepted == expected, word
        accepted_seen += expected
    assert 100 < accepted_seen < 2400   # the sample exercises both classes


@pytest.mark.parametrize("pid", PIDS)
def test_or02_missing_categories_match_a_direct_computation(clf, pid):
    profile = PROFILES_REGISTRY[pid]
    rng = random.Random(7)
    for _ in range(300):
        word = rng.sample(sorted(profile.alphabet), k=rng.randint(0, 8))
        observed = {profile.get_category_for_skill(t) for t in word}
        expected = [g for g, alts in profile.required_groups.items() if not alts & observed]
        result = clf.evaluate_profile(pid, word)
        assert result.missing_categories == expected
        assert result.satisfied_categories == [c.name for c in profile.canonical_categories if c.name in observed]


def test_or03_prepared_and_strict_agree_on_already_prepared_words(clf):
    rng = random.Random(3)
    for pid in PIDS:
        profile = PROFILES_REGISTRY[pid]
        rank = {t: i for i, c in enumerate(profile.canonical_categories) for t in c.skills}
        for _ in range(200):
            word = sorted(rng.choices(sorted(profile.alphabet), k=rng.randint(0, 8)), key=rank.__getitem__)
            prepared = clf.classify(word).results_by_profile[pid]
            assert prepared.is_accepted == clf.evaluate_profile(pid, word).is_accepted


# --------------------------------------------------------------------------- ST
@pytest.mark.parametrize("pid", PIDS)
def test_st01_formal_model_properties(autos, pid):
    auto = autos[pid]
    formal = auto.get_formal_tuple()
    assert len(formal.final_states) == 1 and formal.initial_state == "q0"
    assert len(formal.transitions) == len(formal.states) * len(formal.alphabet)  # total delta
    assert all(formal.transitions["q_trap", s] == "q_trap" for s in formal.alphabet)
    assert "q_trap" not in formal.final_states
    accepting = next(iter(formal.final_states))
    # every state except the trap can still reach F (no hidden dead states)
    graph = {}
    for (src, _), dst in formal.transitions.items():
        graph.setdefault(src, set()).add(dst)
    for state in formal.states - {"q_trap"}:
        seen, stack = set(), [state]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(graph.get(current, ()))
        assert accepting in seen, state
    # the alphabet is partitioned by the categories
    sizes = [len(c.skills) for c in PROFILES_REGISTRY[pid].canonical_categories]
    assert sum(sizes) == len(formal.alphabet)


@pytest.mark.parametrize("pid", PIDS)
def test_st02_diagrams_follow_the_model(autos, clf, pid):
    auto = autos[pid]
    formal = auto.get_formal_tuple()
    mermaid = generate_mermaid_diagram(auto).splitlines()
    assert mermaid[0] == "stateDiagram-v2"
    assert len(mermaid) == 2 + len(formal.transitions) + len(formal.final_states)
    plain = build_graphviz_diagram(auto).source
    result = clf.evaluate_profile(pid, FULL[pid])
    highlighted = build_graphviz_diagram(auto, result).source
    assert "#16a34a" in highlighted and "#16a34a" not in plain
    assert "#86efac" in highlighted   # accepting state painted green
    rejected = clf.evaluate_profile(pid, FULL[pid][::-1])
    assert "#fca5a5" in build_graphviz_diagram(auto, rejected).source   # trap painted red


def test_st03_foreign_symbol_is_drawn_outside_sigma(autos, clf):
    auto = autos["machine_learning"]
    result = clf.evaluate_profile("machine_learning", ["PYTHON", "COBOL"])
    assert "COBOL (outside Σ)" in build_graphviz_diagram(auto, result).source


def test_st04_report_partitions_the_profiles(clf):
    rng = random.Random(11)
    universe = sorted(set().union(*(p.alphabet for p in PROFILES_REGISTRY.values()))) + ["COBOL"]
    for _ in range(200):
        report = clf.classify(rng.choices(universe, k=rng.randint(0, 14)))
        assert set(report.accepted_profiles).isdisjoint(report.rejected_profiles)
        assert sorted(report.accepted_profiles + report.rejected_profiles) == sorted(TITLES.values())
        for pid, result in report.results_by_profile.items():
            assert result.status == (ClassificationStatus.ACCEPTED if result.is_accepted
                                     else ClassificationStatus.REJECTED)
            assert (result.rejection_reason is None) == result.is_accepted
            assert result.expected_final_state == "q_version_control"


# ----------------------------------------------------------- specification table
SPEC = {
    "full_stack": {
        "EXPERIENCE": "EXPERIENCE_PRESENT",
        "FE_LANGUAGE": "CSS HTML JAVASCRIPT TYPESCRIPT",
        "FE_FRAMEWORK": "ANGULAR NEXTJS REACT SVELTE VUE",
        "BE_LANGUAGE": "CSHARP GO JAVA NODE_JS PYTHON",
        "BE_FRAMEWORK": "DJANGO EXPRESS FASTAPI NESTJS SPRING_BOOT",
        "API_COMMUNICATION": "GRAPHQL REST WEBSOCKET",
        "DATABASE_SQL": "MYSQL ORACLE POSTGRESQL SQL SQLITE",
        "DATABASE_NOSQL": "FIREBASE MONGODB REDIS",
        "DEVOPS_CLOUD": "AWS DOCKER KUBERNETES",
        "VERSION_CONTROL": "GIT GITHUB GITLAB",
    },
    "machine_learning": {
        "CORE_LANGUAGE": "JULIA PYTHON R",
        "DATA_PROCESSING": "NUMPY PANDAS SCIPY",
        "ML_FRAMEWORKS": "KERAS PYTORCH SCIKIT_LEARN TENSORFLOW XGBOOST",
        "DATABASE": "MYSQL POSTGRESQL SQL",
        "VERSION_CONTROL": "GIT GITHUB GITLAB",
    },
    "cloud_devops": {
        "SCRIPTING_OS": "BASH LINUX POWERSHELL PYTHON",
        "CICD": "ARGO_CD GITHUB_ACTIONS GITLAB_CI JENKINS",
        "CONTAINERS_ORCHESTRATION": "DOCKER HELM KUBERNETES PODMAN",
        "CLOUD_IAC": "ANSIBLE AWS AZURE GCP TERRAFORM",
        "VERSION_CONTROL": "GIT GITHUB GITLAB",
    },
    "data_scientist": {
        "DATA_LANGUAGE": "JULIA PYTHON R SQL",
        "DATA_ANALYSIS_STATS": "NUMPY PANDAS SCIPY STATSMODELS",
        "DATA_VISUALIZATION": "MATPLOTLIB PLOTLY POWER_BI SEABORN TABLEAU",
        "MACHINE_LEARNING": "CATBOOST LIGHTGBM SCIKIT_LEARN XGBOOST",
        "VERSION_CONTROL": "GIT GITHUB GITLAB",
    },
}


@pytest.mark.parametrize("pid", PIDS)
def test_sp01_profile_definitions_match_the_specification_table(pid):
    profile = PROFILES_REGISTRY[pid]
    actual = {c.name: set(c.skills) for c in profile.canonical_categories}
    assert actual == {name: set(tokens.split()) for name, tokens in SPEC[pid].items()}
    assert [c.name for c in profile.canonical_categories] == list(SPEC[pid])   # canonical order


@pytest.mark.parametrize("pid", PIDS)
def test_sp02_every_token_of_the_alphabet_is_accepted_in_its_block(clf, autos, pid):
    """Each token, put in its own block of an otherwise minimal word, gives an accepted word."""
    profile = PROFILES_REGISTRY[pid]
    for index, category in enumerate(profile.canonical_categories):
        for token in category.skills:
            if pid == "full_stack":
                base = {c: FULL[pid][i] for i, c in enumerate(["FE_LANGUAGE", "BE_LANGUAGE", "DATABASE_SQL", "VERSION_CONTROL"])}
                base[category.name] = token
                if category.name in {"EXPERIENCE", "FE_FRAMEWORK", "BE_FRAMEWORK", "API_COMMUNICATION",
                                     "DATABASE_NOSQL", "DEVOPS_CLOUD"}:
                    base[category.name + "_x"] = token
                word = sorted(base.values(), key=lambda t: [c.name for c in profile.canonical_categories].index(
                    profile.get_category_for_skill(t)))
            else:
                word = list(FULL[pid])
                word[index] = token
            assert autos[pid].accepts(word), (pid, token)


def test_sp03_required_groups(autos):
    for pid in PIDS:
        groups = PROFILES_REGISTRY[pid].required_groups
        assert "VERSION_CONTROL" in groups
        if pid != "full_stack":
            assert set(groups) == {c.name for c in PROFILES_REGISTRY[pid].canonical_categories}
    assert PROFILES_REGISTRY["full_stack"].required_groups == {
        "FE_LANGUAGE": {"FE_LANGUAGE"}, "BACKEND": {"BE_LANGUAGE", "BE_FRAMEWORK"},
        "DATABASE": {"DATABASE_SQL", "DATABASE_NOSQL"}, "VERSION_CONTROL": {"VERSION_CONTROL"}}


def _node_fill(source, node):
    line = next(l for l in source.splitlines() if l.strip().startswith(node + " [fillcolor"))
    return re.search(r'fillcolor="(#[0-9a-f]+)"', line).group(1)


def test_st05_diagram_colours_and_edges(autos, clf):
    auto = autos["machine_learning"]
    plain = build_graphviz_diagram(auto).source
    # un-highlighted diagram: every node neutral; edges to the trap are grouped, never per symbol
    assert {_node_fill(plain, s) for s in ("q0", "q_trap", "q_database")} == {"#f8fafc"}
    trap_edges = [l for l in plain.splitlines() if "-> q_trap" in l]
    assert trap_edges and all("other symbols of Σ" in l or 'label="Σ"' in l for l in trap_edges)
    rejected = build_graphviz_diagram(auto, clf.evaluate_profile("machine_learning", ["PYTHON", "GIT"])).source
    assert _node_fill(rejected, "q_trap") == "#fca5a5"
    assert _node_fill(rejected, "q_core_language") == "#bfdbfe"
    assert _node_fill(rejected, "q_database") == "#f8fafc"     # not visited
    assert generate_mermaid_diagram(auto).splitlines()[1] == "    [*] --> q0"


# ----------------------------------------------------------- theory (docs/stage3_formalization.md)
def test_st06_minimality_theorem():
    """Theorem 4: chain automata are minimal; Full Stack has exactly one equivalent pair (q0, q_experience)."""
    from scripts.stage3_theory_section import models
    for pid, model in models().items():
        _, equivalent = model.moore()
        if pid == "full_stack":
            assert equivalent == [["q0", "q_experience"]]
        else:
            assert equivalent == []


def test_st07_every_state_is_reachable_and_only_the_trap_is_dead():
    """Theorem 3: witnesses exist for reachability and co-reachability."""
    from scripts.stage3_theory_section import models
    for pid, model in models().items():
        forward, backward = model.paths()
        assert set(forward) == set(model.states)
        assert set(backward) == set(model.states) - {"q_trap"}
        for state, word in forward.items():           # the witnesses really lead to the state
            current = "q0"
            for token in word:
                current = model.delta[current, token]
            assert current == state
        for state, word in backward.items():          # the suffixes really lead to F
            current = state
            for token in word:
                current = model.delta[current, token]
            assert current == model.final


def test_st08_theory_section_is_consistent_with_the_implementation():
    """Lemma 1/2 and Theorems 1-5 are re-checked mechanically while the section is generated."""
    from scripts.stage3_theory_section import build_theory_section
    text = "\n".join(build_theory_section())
    for heading in ("Lemma 1", "Lemma 2", "Theorem 1", "Theorem 2", "Theorem 3", "Theorem 4", "Theorem 5"):
        assert heading in text
