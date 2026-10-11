"""Round-trip, injection boundaries and the validation-before-output contract."""

from dataclasses import replace
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.stage4_grammar import (
    CandidateProfile, Contact, Education, Experience, ProfileValidationError,
    generate_document, parse_profile, parse_profile_file, serialize_profile, validate_document,
)
from src.stage4_grammar.__main__ import main

EXAMPLE = Path(__file__).parents[1] / 'docs/examples/wednesday.resume'


@pytest.mark.parametrize('profile', [
    CandidateProfile(),
    CandidateProfile(name='María José', years_of_experience=0),
    CandidateProfile(name='A "quote" \\ slash', summary='Line one\nLine two\t\U0001f600'),
    CandidateProfile(experiences=(Experience('Developer'), Experience('Analyst', 'Acme', '2020–2022', 'Data')),
                     education=(Education('BSc', 'University', '2020'), Education('MSc'))),
    CandidateProfile(contacts=(Contact('email', 'person@example.com'), Contact('github', 'github.com/person')),
                     skills=('PYTHON', 'GIT'), unrecognized_skills=('Figma',),
                     accepted_profiles=('machine_learning', 'data_scientist')),
])
def test_generated_dsl_is_lossless_and_deterministic(profile):
    document = generate_document(profile)
    assert parse_profile(document.dsl) == profile
    assert serialize_profile(parse_profile(document.dsl)) == document.dsl
    assert document.to_dict()['validated'] is True
    assert '<!doctype html>' in document.html


def test_complete_example_round_trip():
    profile = parse_profile_file(EXAMPLE)
    assert parse_profile(serialize_profile(profile)) == profile
    assert len(profile.experiences) == len(profile.education) == 2


@pytest.mark.parametrize('field,value', [
    ('name', '<script>alert(1)</script>'),
    ('summary', '</style><img src=x onerror=alert(1)>'),
    ('location', '" onmouseover="alert(1)'),
])
def test_html_never_interprets_candidate_markup(field, value):
    document = generate_document(replace(CandidateProfile(), **{field: value}))
    assert value not in document.html
    assert '<script>' not in document.html
    assert '<img ' not in document.html
    assert getattr(document.profile, field) == value


def test_dsl_text_cannot_inject_classification():
    value = '"; } classification { accepted full_stack; } //'
    profile = CandidateProfile(name=value)
    assert generate_document(profile).profile == profile


@pytest.mark.parametrize('profile', [
    CandidateProfile(skills=('PYTHON; skill GIT',)),
    CandidateProfile(accepted_profiles=('full_stack; accepted data_scientist',)),
    CandidateProfile(contacts=(Contact('email "x"; github', 'person@example.com'),)),
    CandidateProfile(skills=('MADE_UP',)),
    CandidateProfile(skills=('EXPERIENCE_PRESENT',)),
    CandidateProfile(name=' '),
    CandidateProfile(name='\ud800'),
    CandidateProfile(skills=('PYTHON', 'PYTHON')),
    CandidateProfile(years_of_experience=True),
    CandidateProfile(years_of_experience=-1),
    CandidateProfile(years_of_experience=1.2),
])
def test_invalid_models_cannot_produce_documents(profile):
    with pytest.raises(ValueError):
        generate_document(profile)


def test_missing_years_are_not_rendered_as_zero():
    assert 'Total reported experience' not in generate_document(CandidateProfile()).html
    assert '<strong>0 years</strong>' in generate_document(CandidateProfile(years_of_experience=0)).html


def test_invalid_dsl_does_not_create_or_overwrite_html(tmp_path):
    source = tmp_path / 'broken.resume'
    target = tmp_path / 'profile.html'
    source.write_text('candidate {', encoding='utf-8')
    assert main([str(source), '--html', str(target)]) == 1
    assert not target.exists()
    target.write_text('previous validated output', encoding='utf-8')
    assert main([str(source), '--html', str(target)]) == 1
    assert target.read_text() == 'previous validated output'


def test_cli_exports_valid_example_and_preserves_input(tmp_path):
    target = tmp_path / 'profile.html'
    assert main([str(EXAMPLE), '--html', str(target)]) == 0
    assert target.read_text(encoding='utf-8') == validate_document(EXAMPLE.read_text(encoding='utf-8')).html
    source = tmp_path / 'same.resume'
    original = EXAMPLE.read_text(encoding='utf-8')
    source.write_text(original, encoding='utf-8')
    assert main([str(source), '--html', str(source)]) == 1
    assert source.read_text(encoding='utf-8') == original


def test_concurrent_validations_keep_profiles_separate():
    sources = [serialize_profile(CandidateProfile(name=f'Candidate {n}')) for n in range(12)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        profiles = list(pool.map(parse_profile, sources))
    assert [p.name for p in profiles] == [f'Candidate {n}' for n in range(12)]


@pytest.mark.parametrize('source', ['candidate {}', 'candidate {', '', 'garbage'])
def test_invalid_source_is_rejected_before_rendering(source):
    with pytest.raises(ProfileValidationError):
        validate_document(source)
