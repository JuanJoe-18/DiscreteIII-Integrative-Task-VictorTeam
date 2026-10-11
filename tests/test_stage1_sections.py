"""Stage 1 - tests of section detection and skill-list splitting."""

from src.stage1_regex.sections import find_section, section_spans, split_sections, split_skill_items


def test_heading_on_its_own_line():
    text = "Jane Doe\n\nSkills\nPython, Git\n\nEducation\nBSc in Physics\n"
    names = [s.name for s in split_sections(text)]
    assert names == ["skills", "education"]


def test_inline_heading_in_a_one_line_resume():
    text = "Wednesday Addams 3 years of experience. Technical Skills: JS, React.js, Git."
    section = find_section(text, "skills")
    assert section is not None
    assert section.body(text).strip() == "JS, React.js, Git."


def test_skills_on_the_line_after_the_heading():
    text = "Name\nTechnical Skills:\nJS, React.js, NodeJS, Postgres, Git."
    section = find_section(text, "skills")
    assert section.body(text).strip() == "JS, React.js, NodeJS, Postgres, Git."


def test_skills_section_stops_at_blank_line():
    text = "Skills:\nPython, Git\n\nThis is a paragraph, not skills."
    (start, end), = section_spans(text, "skills")
    assert text[start:end].strip() == "Python, Git"


def test_skills_section_stops_at_next_heading():
    text = "Technical Skills: Python, Git Education: BSc in Physics"
    (start, end), = section_spans(text, "skills")
    assert text[start:end].strip() == "Python, Git"


def test_soft_skills_is_not_a_skills_section():
    assert section_spans("Soft skills: communication, teamwork", "skills") == []


def test_spanish_headings():
    text = "Habilidades:\nPython, SQL\n\nEducación\nIngeniería de Sistemas"
    assert [s.name for s in split_sections(text)] == ["skills", "education"]


def test_no_headings():
    assert split_sections("Just a paragraph with no headings at all.") == []


def test_split_skill_items_handles_bullets_labels_and_trailing_dot():
    text = "Frontend: JavaScript, React\n- Docker (2 years); Linux, Notion."
    items = [item for item, _, _ in split_skill_items(text, 0, len(text))]
    assert items == ["JavaScript", "React", "Docker (2 years)", "Linux", "Notion"]


def test_split_skill_items_positions_point_into_the_text():
    text = "Skills: Python, Git"
    start = text.index(":") + 1
    for item, s, e in split_skill_items(text, start, len(text)):
        assert text[s:e] == item