"""Stage 1 - tests of the extraction engine on whole resumes."""

from pathlib import Path

import pytest

from src.stage1_regex import Category, ResumeExtractor, extract_qualifications

DATA = Path(__file__).parent / "data" / "resumes"


def read(name: str) -> str:
    return (DATA / name).read_text(encoding="utf-8")


# ------------------------------------------------- the two resumes of the assignment
def test_wednesday_addams_from_the_assignment():
    result = extract_qualifications(read("wednesday_addams.txt"))
    assert result.raw_tokens == ["JS", "React.js", "NodeJS", "Postgres", "Git"]
    assert result.candidate_name == "Wednesday Addams"
    assert result.years_of_experience == 3


def test_wednesday_addams_written_on_a_single_line():
    text = (
        "Wednesday Addams 3 years of experience developing web applications. "
        "Technical Skills: JS, React.js, NodeJS, Postgres, Git."
    )
    result = extract_qualifications(text)
    assert result.raw_tokens == ["JS", "React.js", "NodeJS", "Postgres", "Git"]
    assert result.candidate_name == "Wednesday Addams"
    assert result.years_of_experience == 3


def test_mary_jane_watson_from_the_assignment():
    result = extract_qualifications(read("mary_jane_watson.txt"))
    assert result.raw_tokens == ["Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "SQL", "Git"]
    assert result.candidate_name == "Mary Jane Watson"
    assert result.years_of_experience == 2


def test_years_are_not_mixed_with_the_raw_tokens():
    result = extract_qualifications(read("wednesday_addams.txt"))
    assert "3" not in result.raw_tokens


# ---------------------------------------------------------------- years of experience
@pytest.mark.parametrize(
    "text, expected",
    [
        ("10 years of experience", 10),
        ("12+ years building APIs", 12),
        ("two years of experience", 2),
        ("5 años de experiencia", 5),
        ("2 years at A and 7 years at B", 7),  # the maximum is reported
        ("0 years", 0),
    ],
)
def test_years_of_experience_values(text, expected):
    assert extract_qualifications(text).years_of_experience == expected


@pytest.mark.parametrize("text", ["99 years of experience", "2020 years", "years of experience", "I like to travel"])
def test_incoherent_or_missing_years_are_not_reported(text):
    assert extract_qualifications(text).years_of_experience is None


# --------------------------------------------------------------- a rich resume
def test_rich_resume_contact_information():
    result = extract_qualifications(read("rich_resume.txt"))
    assert result.contact == {
        "email": ["wednesday.addams@example.com"],
        "phone": ["+57 300 123 4567"],
        "linkedin": ["linkedin.com/in/wadd"],
        "github": ["github.com/wadd/notes"],
    }


def test_rich_resume_identity_experience_and_education():
    result = extract_qualifications(read("rich_resume.txt"))
    assert result.candidate_name == "WEDNESDAY ADDAMS"
    assert result.years_of_experience == 10
    assert result.job_titles == ["Senior Full Stack Developer", "Web Application Developer"]
    assert result.education == ["Bachelor of Science in Computer Science", "AWS Certified Solutions Architect"]


def test_rich_resume_technologies_by_category():
    by_category = extract_qualifications(read("rich_resume.txt")).by_category()
    assert by_category[Category.PROGRAMMING_LANGUAGE] == ["JavaScript", "Go"]
    assert by_category[Category.DATABASE] == ["PostgreSQL"]
    assert "Node.js" in by_category[Category.FRAMEWORK_LIBRARY]
    assert "Express.js" in by_category[Category.FRAMEWORK_LIBRARY]
    assert "GitHub Actions" in by_category[Category.TOOL_TECHNOLOGY]
    assert "Docker" in by_category[Category.TOOL_TECHNOLOGY]


def test_longest_technology_wins_over_overlapping_one():
    result = extract_qualifications(read("rich_resume.txt"))
    texts = [i.text for i in result.items if i.spec_name in ("VERSION_CONTROL", "DEVOPS_CLOUD_TOOL")]
    assert "GitHub Actions" in texts
    assert "GitHub" not in texts


def test_spanish_resume():
    result = extract_qualifications(read("spanish_resume.txt"))
    assert result.candidate_name == "Juan Pérez Gómez"
    assert result.years_of_experience == 5
    assert result.contact["email"] == ["juan.perez@correo.icesi.edu.co"]
    assert result.contact["phone"] == ["3001234567"]
    assert result.education == ["Ingeniería de Sistemas", "Maestría en Ciencia de Datos"]
    assert result.raw_tokens == ["Python", "SQL", "Git", "Pandas", "Scikit-learn"]


# ------------------------------------------------------- context-sensitive words
def test_ambiguous_words_in_prose_are_not_technologies():
    text = "We react quickly, express interest and go the extra mile. Worked at Oracle with the rest of the team."
    assert extract_qualifications(text).raw_tokens == []


def test_ambiguous_words_inside_the_skills_section_are_technologies():
    result = extract_qualifications("Skills: Python, R, Go, Rust, Julia, React, Node, Express, Oracle")
    assert result.raw_tokens == ["Python", "R", "Go", "Rust", "Julia", "React", "Node", "Express", "Oracle"]


def test_technologies_are_not_found_inside_other_words_or_emails():
    text = "Contact: dev.git@example.com. Knows JSON, main.js and Dockerfile."
    result = extract_qualifications(text)
    assert result.raw_tokens == []
    assert result.contact["email"] == ["dev.git@example.com"]


# --------------------------------------------------------------- unknown skills
def test_unknown_skills_in_the_skills_section_become_other():
    result = extract_qualifications("Skills: Python, Figma, Notion (2 years), Git")
    assert result.raw_tokens == ["Python", "Figma", "Notion", "Git"]
    others = [i for i in result.items if i.category is Category.OTHER]
    assert [i.text for i in others] == ["Figma", "Notion"]


def test_no_skills_section_means_no_unknown_skills_are_guessed():
    result = extract_qualifications("I enjoy painting and cooking. Python is my favourite language.")
    assert result.raw_tokens == ["Python"]


def test_sentences_in_the_skills_section_are_not_unknown_skills():
    result = extract_qualifications("Skills: Python, passionate about building scalable distributed systems")
    assert result.raw_tokens == ["Python"]


# ------------------------------------------------------------------- edge cases
@pytest.mark.parametrize("text", ["", "   ", "\n\n"])
def test_empty_resume(text):
    result = extract_qualifications(text)
    assert result.raw_tokens == []
    assert result.years_of_experience is None
    assert result.candidate_name is None
    assert result.items == []


def test_tokens_are_deduplicated_case_insensitively_keeping_the_first_spelling():
    result = extract_qualifications("Skills: Python, python, PYTHON, Git, git")
    assert result.raw_tokens == ["Python", "Git"]


def test_windows_line_endings():
    result = extract_qualifications(read("wednesday_addams.txt").replace("\n", "\r\n"))
    assert result.raw_tokens == ["JS", "React.js", "NodeJS", "Postgres", "Git"]


def test_item_positions_point_to_the_original_text():
    text = read("rich_resume.txt")
    for item in extract_qualifications(text).items:
        assert " ".join(text[item.start : item.end].split()) == item.text


def test_extractor_runs_a_custom_catalog():
    from src.stage1_regex.patterns import SPECS_BY_NAME

    only_email = ResumeExtractor([SPECS_BY_NAME["EMAIL"]])
    result = only_email.extract("Python dev, mail: a@b.co")
    assert result.raw_tokens == []
    assert result.contact["email"] == ["a@b.co"]