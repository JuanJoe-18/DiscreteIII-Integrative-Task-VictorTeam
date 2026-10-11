"""Stage 1 - boundary and negative cases.

These scenarios were added after a mutation analysis of the suite (see ``docs/stage1_tests.md``):
each test kills a deliberate change of an expression or of the engine that the first version of the
suite did not notice.
"""

import pytest

from src.stage1_regex import extract_qualifications
from src.stage1_regex.patterns import SPECS_BY_NAME


def _search(spec_name, text):
    return SPECS_BY_NAME[spec_name].regex.search(text)


# ------------------------------------------------------------------ right boundary
@pytest.mark.parametrize(
    "spec_name, text",
    [
        ("PROGRAMMING_LANGUAGE", "a Python-based tool"),  # hyphen + word continues the word
        ("WEB_FRAMEWORK", "built with Node.jsx"),  # dot + word continues the name
        ("DATABASE", "SQL-like syntax"),
        ("DEVOPS_CLOUD_TOOL", "Docker-compose files"),
        ("DEVOPS_CLOUD_TOOL", "see Docker.com"),
    ],
)
def test_technology_followed_by_hyphen_or_dot_and_a_word_is_not_a_technology(spec_name, text):
    assert _search(spec_name, text) is None


@pytest.mark.parametrize("text", ["Knows Git.", "Knows Git, Docker", "Knows (Git)"])
def test_technology_followed_by_sentence_punctuation_is_still_found(text):
    assert _search("VERSION_CONTROL", text).group() == "Git"


# --------------------------------------------------------------- technologies vs contact
def test_technology_that_is_part_of_an_email_is_not_a_technology():
    result = extract_qualifications("Contact: git@acme.io")
    assert result.contact["email"] == ["git@acme.io"]
    assert result.raw_tokens == []


# ------------------------------------------------------------------------- degrees
def test_master_without_of_or_in_is_not_a_degree():
    result = extract_qualifications("Certified Scrum Master Training and Master Thesis")
    assert [i for i in result.items if i.spec_name == "DEGREE"] == []


@pytest.mark.parametrize("text", ["Ph.D. in Physics", "PhD", "Doctorate in Chemistry", "MSc in Machine Learning"])
def test_doctorates_and_abbreviations_are_degrees(text):
    result = extract_qualifications(text)
    assert [i.text for i in result.items if i.spec_name == "DEGREE"] == [text]


# ----------------------------------------------------------------- certifications
@pytest.mark.parametrize("text", ["GCP Certified Professional", "Azure Certified Administrator", "Certified Kubernetes Administrator"])
def test_certifications_of_every_provider(text):
    assert [i.text for i in extract_qualifications(text).items if i.spec_name == "CERTIFICATION"] == [text]


# ------------------------------------------------------------------------ job titles
@pytest.mark.parametrize("title", ["Principal Data Engineer", "Lead Machine Learning Engineer", "Junior Web Developer", "Cloud Engineer"])
def test_job_titles_with_every_seniority_word(title):
    assert extract_qualifications(f"{title} at Acme").job_titles == [title]


# ------------------------------------------------------------------------- names
def test_a_name_has_at_most_four_words():
    assert extract_qualifications("Anna Maria Louise Jane Smith\n3 years").candidate_name == "Anna Maria Louise Jane"


def test_a_heading_word_is_not_the_first_word_of_a_name():
    assert extract_qualifications("Technical Writer\nPython").candidate_name is None


def test_name_with_apostrophe():
    assert extract_qualifications("Conan O'Brien\n3 years").candidate_name == "Conan O'Brien"


# ----------------------------------------------------------------------- API protocols
@pytest.mark.parametrize("text", ["WebSocket", "websockets", "Web Sockets", "GraphQL", "RESTful APIs"])
def test_api_protocol_spellings(text):
    assert _search("API_PROTOCOL", text).group() == text


# -------------------------------------------------------------------- unknown skills
def test_long_unknown_skills_are_not_guessed():
    result = extract_qualifications("Skills: Python, Supercalifragilisticexpialidocious Pneumonoultramicroscopic")
    assert result.raw_tokens == ["Python"]


# ------------------------------------------------------------- Windows line endings
def test_skills_section_is_found_and_ends_at_a_blank_line_with_windows_line_endings():
    text = "Skills\r\nPython, Figma\r\n\r\nNotion\r\n"  # Figma is in the list (OTHER); Notion is outside it
    assert extract_qualifications(text).raw_tokens == ["Python", "Figma"]
    assert extract_qualifications(text.replace("\r\n", "\n")).raw_tokens == ["Python", "Figma"]
