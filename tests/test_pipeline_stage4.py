from pathlib import Path

import pytest

from src.pipeline import process_resume
from src.stage4_grammar import parse_profile


@pytest.mark.parametrize('skills,accepted', [
    ('Git, SQL, Node.js, JavaScript', {'full_stack'}),
    ('Git, SQL, Scikit-learn, Pandas, Python', {'machine_learning'}),
    ('Git, AWS, Docker, Jenkins, Bash', {'cloud_devops'}),
    ('Git, Scikit-learn, Matplotlib, Pandas, Python', {'data_scientist'}),
    ('Python, Pandas, Matplotlib, Scikit-learn, SQL, Git', {'machine_learning', 'data_scientist'}),
    ('JavaScript, SQL, Git', set()),
])
def test_all_four_stages_preserve_actual_acceptance(skills, accepted):
    result = process_resume('Name: Test Candidate\nSkills: ' + skills + '.')
    profile = parse_profile(result.document.dsl)
    assert set(profile.accepted_profiles) == accepted
    assert set(profile.accepted_profiles) == {pid for pid, r in result.classification.results_by_profile.items() if r.is_accepted}
    assert profile.name == 'Test Candidate'


def test_rich_resume_preserves_metadata_without_inventing_record_associations():
    text = (Path(__file__).parent / 'data/resumes/rich_resume.txt').read_text(encoding='utf-8')
    result = process_resume(text)
    profile = result.document.profile
    assert profile.years_of_experience == 10
    assert {c.value for c in profile.contacts} == {v for values in result.extraction.contact.values() for v in values}
    assert {e.title for e in profile.experiences} == set(result.extraction.job_titles)
    assert all(e.organization is None and e.period is None for e in profile.experiences)
    assert {e.qualification for e in profile.education} == set(result.extraction.education)
    assert {'Figma', 'Notion'} <= set(profile.unrecognized_skills)
    assert 'EXPERIENCE_PRESENT' not in profile.skills


def test_no_technical_skills_can_still_form_a_valid_rejected_document():
    result = process_resume('Name: Test Candidate\nContact: python@gmail.com')
    assert not result.document.profile.skills
    assert not result.document.profile.accepted_profiles
    assert all(not r.is_accepted for r in result.classification.results_by_profile.values())


@pytest.mark.parametrize('text', ['', '  ', None])
def test_empty_resume_rejected(text):
    with pytest.raises(ValueError):
        process_resume(text)
