"""Stage 1 - tests of the regex catalog (one documented RegexSpec per type of information)."""

import re

import pytest

from src.stage1_regex.models import Category, Scope
from src.stage1_regex.patterns import DEFAULT_SPECS, SPECS_BY_NAME

SPEC_IDS = [spec.name for spec in DEFAULT_SPECS]


def test_catalog_has_unique_names():
    assert len(SPEC_IDS) == len(set(SPEC_IDS))


@pytest.mark.parametrize("spec", DEFAULT_SPECS, ids=SPEC_IDS)
def test_spec_is_fully_documented(spec):
    assert spec.description.strip(), "every spec must explain the language it recognises"
    assert len(spec.accepts) >= 1
    assert len(spec.rejects) >= 1
    assert spec.techniques, "list the regex techniques used (needed for the formal documentation)"


@pytest.mark.parametrize("spec", DEFAULT_SPECS, ids=SPEC_IDS)
def test_spec_compiles_and_honours_its_examples(spec):
    assert isinstance(spec.regex, re.Pattern)
    assert spec.example_failures() == []


@pytest.mark.parametrize("spec", DEFAULT_SPECS, ids=SPEC_IDS)
def test_group_exists_in_pattern(spec):
    assert spec.group <= spec.regex.groups


def test_ambiguous_specs_are_restricted_to_the_skills_section():
    ambiguous = [s for s in DEFAULT_SPECS if s.name.endswith("_AMBIGUOUS")]
    assert ambiguous, "the catalog must contain the context-sensitive specs"
    assert all(s.scope is Scope.SKILLS_SECTION for s in ambiguous)


def test_every_extraction_category_of_the_assignment_is_covered():
    covered = {spec.category for spec in DEFAULT_SPECS}
    for category in (
        Category.CONTACT,
        Category.PROGRAMMING_LANGUAGE,
        Category.FRAMEWORK_LIBRARY,
        Category.DATABASE,
        Category.EDUCATION,
        Category.EXPERIENCE,
        Category.TOOL_TECHNOLOGY,
    ):
        assert category in covered


# ----------------------------------------------------------- lookaround behaviour
def _search(spec_name, text):
    return SPECS_BY_NAME[spec_name].regex.search(text)


def test_js_is_not_found_inside_other_words():
    assert _search("PROGRAMMING_LANGUAGE", "JSON, main.js, JSX") is None
    assert _search("PROGRAMMING_LANGUAGE", "JS, React").group() == "JS"


def test_java_and_javascript_are_mutually_exclusive():
    spec = SPECS_BY_NAME["PROGRAMMING_LANGUAGE"].regex
    assert [m.group() for m in spec.finditer("Java Script and Java and JavaScript")] == [
        "Java Script",
        "Java",
        "JavaScript",
    ]


def test_sql_server_wins_over_sql():
    assert _search("DATABASE", "MS SQL Server").group() == "SQL Server"


def test_rest_is_case_sensitive_but_graphql_is_not():
    assert _search("API_PROTOCOL", "the rest of the team") is None
    assert _search("API_PROTOCOL", "REST APIs").group() == "REST APIs"
    assert _search("API_PROTOCOL", "graphql").group() == "graphql"


def test_phone_ignores_year_ranges_and_long_digit_runs():
    assert _search("PHONE", "Studied 2019-2023") is None
    assert _search("PHONE", "id 123456789012345") is None


def test_years_range_alternation():
    spec = SPECS_BY_NAME["YEARS_OF_EXPERIENCE"].regex
    for text, expected in [("9 years", "9"), ("10 years", "10"), ("49 years", "49"), ("07 years", "07")]:
        assert spec.search(text).group(1) == expected
    for text in ("50 years", "99 years", "1.5 years"):
        assert spec.search(text) is None, text