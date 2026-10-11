"""Tests of the Stage 2 public API: normalization, canonical sorting and the pipeline contracts."""

import itertools
import random
from pathlib import Path

import pytest

from src.stage1_regex import extract_qualifications
from src.stage1_regex import patterns as stage1_patterns
from src.stage1_regex.models import TECH_CATEGORIES
from src.stage2_fst import (
    NormalizationResult,
    normalize_and_sort,
    normalize_qualifications,
    sort_to_canonical_order,
)
from src.stage3_classifier import ResumeClassifier
from src.stage3_classifier.profiles import PROFILES_REGISTRY
from tests.test_stage1_contract import SURFACE_FORMS

RESUMES = Path(__file__).parent / "data" / "resumes"


def _norm(*raw):
    return normalize_qualifications(list(raw)).normalized_tokens


# --------------------------------------------------------------------------- the assignment's examples
@pytest.mark.parametrize("raw, canonical", [
    ("JS", "JAVASCRIPT"), ("Javascript", "JAVASCRIPT"), ("React.js", "REACT"), ("ReactJS", "REACT"),
    ("NodeJS", "NODE_JS"), ("Node.js", "NODE_JS"), ("Postgres", "POSTGRESQL"), ("PostgreSQL", "POSTGRESQL"),
    ("pandas", "PANDAS"), ("sklearn", "SCIKIT_LEARN"), ("scikit learn", "SCIKIT_LEARN"),
    ("Scikit-learn", "SCIKIT_LEARN"), ("Tensor Flow", "TENSORFLOW"), ("TensorFlow", "TENSORFLOW"),
    ("Py Torch", "PYTORCH"), ("PyTorch", "PYTORCH"),
])
def test_examples_of_the_statement(raw, canonical):
    assert _norm(raw) == [canonical]


@pytest.mark.parametrize("raw, canonical", [
    ("C#", "CSHARP"), ("C++", "CPP"), ("Go", "GO"), ("Golang", "GO"), ("Java", "JAVA"),
    ("Amazon Web Services", "AWS"), ("Google Cloud Platform", "GCP"), ("K8s", "KUBERNETES"),
    ("GitLab CI/CD", "GITLAB_CI"), ("GitHub Actions", "GITHUB_ACTIONS"), ("Argo CD", "ARGO_CD"),
    ("SQL Server", "SQL_SERVER"), ("Mongo", "MONGODB"), ("RESTful APIs", "REST"), ("Rest API", "REST"),
    ("WebSockets", "WEBSOCKET"), ("Subversion", "SVN"), ("Spring Boot", "SPRING_BOOT"),
    ("Power BI", "POWER_BI"), ("Next.js", "NEXTJS"),
])
def test_forms_that_the_old_dictionary_missed(raw, canonical):
    assert _norm(raw) == [canonical]


def test_capitalisation_and_separators_do_not_matter():
    for spelling in ["NODE.JS", "node.js", "Node.Js", "node js", "node-js", "node_js", "NODEJS"]:
        assert _norm(spelling) == ["NODE_JS"]


# --------------------------------------------------------------------------- result object
def test_result_reports_transformations_and_unrecognized_tokens():
    result = normalize_qualifications(["JS", "JAVASCRIPT", "Brainfuck", "Rust Lang"])
    assert isinstance(result, NormalizationResult)
    assert result.normalized_tokens == ["JAVASCRIPT", "JAVASCRIPT", "BRAINFUCK", "RUST_LANG"]
    assert result.transformations_applied == {"JS": "JAVASCRIPT"}      # JAVASCRIPT is already canonical
    assert result.unrecognized_tokens == ["Brainfuck", "Rust Lang"]


def test_trace_describes_the_cascade_of_every_token():
    result = normalize_qualifications(["Node.js", "Foo-Bar"])
    first, second = result.traces
    assert (first.raw, first.clean, first.canonical, first.recognized) == ("Node.js", "nodejs", "NODE_JS", True)
    assert (second.raw, second.clean, second.canonical, second.recognized) == ("Foo-Bar", "foobar", "FOO_BAR", False)


def test_unknown_skill_keeps_the_old_fallback_form():
    assert _norm("Foo-Bar", "my tool") == ["FOO_BAR", "MY_TOOL"]


def test_symbols_outside_the_alphabet_are_unrecognized_not_a_crash():
    result = normalize_qualifications(["Café", "R&D", "日本"])
    assert result.unrecognized_tokens == ["Café", "R&D", "日本"]
    assert len(result.normalized_tokens) == 3


def test_empty_and_blank_tokens_are_skipped():
    assert normalize_qualifications([]).normalized_tokens == []
    assert normalize_qualifications(["", "  ", "\t"]).normalized_tokens == []


def test_tokens_are_stripped_before_the_cascade():
    result = normalize_qualifications(["  Node.js\t", " 3 "])
    assert result.normalized_tokens == ["NODE_JS", "EXPERIENCE_PRESENT"]
    assert [t.raw for t in result.traces] == ["Node.js", "3"]
    assert result.transformations_applied == {"Node.js": "NODE_JS", "3": "EXPERIENCE_PRESENT"}


def test_single_token_api_used_by_the_web_server():
    assert normalize_qualifications(["Postgres"]).normalized_tokens[0] == "POSTGRESQL"


def test_digit_tokens_still_become_the_experience_symbol():
    result = normalize_qualifications(["3"])
    assert result.normalized_tokens == ["EXPERIENCE_PRESENT"]
    assert result.transformations_applied == {"3": "EXPERIENCE_PRESENT"}


# --------------------------------------------------------------------------- years
def test_years_from_stage_1_become_experience_present_first():
    result = normalize_qualifications(["Git"], years_of_experience=7)
    assert result.normalized_tokens == ["EXPERIENCE_PRESENT", "GIT"]


@pytest.mark.parametrize("years", [None, 0, -1])
def test_no_experience_symbol_without_positive_years(years):
    assert normalize_qualifications(["Git"], years_of_experience=years).normalized_tokens == ["GIT"]


def test_experience_symbol_is_kept_for_profiles_that_have_the_category_and_dropped_otherwise():
    with_cat = normalize_and_sort(["Git", "JS"], "full_stack", years_of_experience=3).normalized_tokens
    assert with_cat[0] == "EXPERIENCE_PRESENT"
    for pid in ("machine_learning", "cloud_devops", "data_scientist"):
        assert "EXPERIENCE_PRESENT" not in normalize_and_sort(["Git"], pid, years_of_experience=3).normalized_tokens


# --------------------------------------------------------------------------- sorting
def test_statement_example_for_full_stack():
    result = normalize_and_sort(["Git", "NodeJS", "JS", "Postgres", "React.js"], "full_stack")
    assert result.normalized_tokens == ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]


def test_sorting_follows_the_category_order_of_each_profile():
    cases = {
        "machine_learning": (["Git", "SQL", "PyTorch", "Pandas", "Python"],
                             ["PYTHON", "PANDAS", "PYTORCH", "SQL", "GIT"]),
        "cloud_devops": (["GitHub", "Terraform", "Docker", "Jenkins", "Linux"],
                         ["LINUX", "JENKINS", "DOCKER", "TERRAFORM", "GITHUB"]),
        "data_scientist": (["Git", "Scikit-learn", "Tableau", "NumPy", "R"],
                           ["R", "NUMPY", "TABLEAU", "SCIKIT_LEARN", "GIT"]),
    }
    for pid, (raw, expected) in cases.items():
        assert normalize_and_sort(raw, pid).normalized_tokens == expected


def test_tokens_outside_the_profile_go_last_in_their_original_order():
    result = normalize_and_sort(["Rust", "Git", "Kotlin", "JS"], "full_stack")
    assert result.normalized_tokens == ["JAVASCRIPT", "GIT", "RUST", "KOTLIN"]


def test_order_inside_a_category_is_the_order_written_in_the_resume():
    assert sort_to_canonical_order(["REACT", "VUE"], "full_stack") == ["REACT", "VUE"]
    assert sort_to_canonical_order(["VUE", "REACT"], "full_stack") == ["VUE", "REACT"]


def test_unknown_profile_leaves_the_tokens_untouched_and_empty_input_is_empty():
    assert sort_to_canonical_order(["GIT", "JAVASCRIPT"], "nope") == ["GIT", "JAVASCRIPT"]
    assert sort_to_canonical_order([], "full_stack") == []


def test_duplicates_are_kept():
    assert sort_to_canonical_order(["GIT", "REACT", "GIT"], "full_stack") == ["REACT", "GIT", "GIT"]


@pytest.mark.parametrize("pid", list(PROFILES_REGISTRY))
def test_sort_equals_a_plain_stable_sort_by_category_rank(pid):
    """Differential test: the multi-pass FILTER construction == sorted(key=category rank)."""
    profile = PROFILES_REGISTRY[pid]
    rank = {s: i for i, c in enumerate(profile.canonical_categories) for s in c.skills}
    pool = sorted(profile.alphabet | {"RUST", "PHP"})
    rng = random.Random(7)
    for _ in range(60):
        tokens = [rng.choice(pool) for _ in range(rng.randint(0, 12))]
        has_exp = any(c.name == "EXPERIENCE" for c in profile.canonical_categories)
        expected = sorted((t for t in tokens if has_exp or t != "EXPERIENCE_PRESENT"),
                          key=lambda t: rank.get(t, 999))
        assert sort_to_canonical_order(tokens, pid) == expected


@pytest.mark.parametrize("pid", list(PROFILES_REGISTRY))
def test_result_does_not_depend_on_the_order_in_the_resume(pid):
    """Sorting is what the statement asks for: same set of skills, same category sequence."""
    profile = PROFILES_REGISTRY[pid]
    category_of = {s: c.name for c in profile.canonical_categories for s in c.skills}
    tokens = sorted(profile.alphabet - {"EXPERIENCE_PRESENT"})[:8]
    reference = None
    for perm in itertools.islice(itertools.permutations(tokens), 200):
        out = sort_to_canonical_order(list(perm), pid)
        sequence = [category_of[t] for t in out]
        reference = reference or sequence
        assert sequence == reference
        assert sorted(out) == sorted(tokens)


# --------------------------------------------------------------------------- Stage 1 -> 2 -> 3
def test_every_surface_form_of_the_stage_1_contract_reaches_its_canonical_token():
    for canonical, form in SURFACE_FORMS.items():
        assert _norm(form) == [canonical], form


def test_every_technology_example_of_stage_1_is_recognised_by_stage_2():
    for name, spec in vars(stage1_patterns).items():
        if hasattr(spec, "category") and hasattr(spec, "accepts") and spec.category in TECH_CATEGORIES:
            for example in spec.accepts:
                result = normalize_qualifications([example])
                assert not result.unrecognized_tokens, f"{spec.name}: {example}"


@pytest.mark.parametrize("name", ["wednesday_addams", "mary_jane_watson", "rich_resume"])
def test_resume_fixtures_go_through_the_three_stages(name):
    classifier = ResumeClassifier()
    extraction = extract_qualifications((RESUMES / f"{name}.txt").read_text(encoding="utf-8"))
    for pid in PROFILES_REGISTRY:
        result = normalize_and_sort(extraction.raw_tokens, pid, extraction.years_of_experience)
        unsorted = normalize_qualifications(extraction.raw_tokens, extraction.years_of_experience)
        # sorting only moves tokens (or drops EXPERIENCE_PRESENT where the profile has no such category)
        kept = [t for t in unsorted.normalized_tokens
                if t != "EXPERIENCE_PRESENT" or pid == "full_stack"]
        assert sorted(result.normalized_tokens) == sorted(kept)
        report = classifier.classify(result.normalized_tokens, prepare_input=False)
        assert pid in report.results_by_profile


def test_wednesday_addams_is_accepted_for_full_stack_with_experience():
    text = (RESUMES / "wednesday_addams.txt").read_text(encoding="utf-8")
    extraction = extract_qualifications(text)
    result = normalize_and_sort(extraction.raw_tokens, "full_stack", extraction.years_of_experience)
    assert result.normalized_tokens[0] == "EXPERIENCE_PRESENT"
    report = ResumeClassifier().classify(result.normalized_tokens, prepare_input=False)
    assert report.results_by_profile["full_stack"].is_accepted
