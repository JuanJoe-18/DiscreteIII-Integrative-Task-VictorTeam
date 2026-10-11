"""Stage 4: lexical/syntactic rejection, domain checks and structured output."""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from src.stage2_fst.aliases import all_canonical_tokens
from src.stage3_classifier.profiles import PROFILES_REGISTRY
from src.stage4_grammar import CandidateProfile, ProfileValidationError, parse_profile, parse_profile_file
from src.stage4_grammar.__main__ import main

EXAMPLES = Path(__file__).resolve().parents[1] / 'docs' / 'examples'


def document(*, personal='', contact='', experience='', education='', skills='', classification=''):
    return f'''candidate {{
  personal {{ {personal} }}
  contact {{ {contact} }}
  experience {{ {experience} }}
  education {{ {education} }}
  skills {{ {skills} }}
  classification {{ {classification} }}
}}'''


def test_documented_example_retains_repeated_records_and_missing_values():
    profile = parse_profile_file(EXAMPLES / 'wednesday.resume')
    assert profile.name == 'Wednesday Addams'
    assert profile.location == 'Jericho'
    assert profile.contacts[0].kind == 'email'
    assert profile.contacts[0].value == 'wednesday.addams@example.com'
    assert profile.years_of_experience == 3
    assert len(profile.experiences) == len(profile.education) == 2
    assert profile.experiences[0].organization == 'Nevermore Academy'
    assert profile.experiences[1].period is None
    assert profile.education[0].institution == 'Example University'
    assert profile.education[1].institution is None
    assert profile.skills == ('JAVASCRIPT', 'REACT', 'NODE_JS', 'POSTGRESQL', 'GIT')
    assert profile.unrecognized_skills == ('Figma',)
    assert profile.accepted_profiles == ('full_stack',)


def test_missing_information_is_not_invented_and_zero_is_not_missing():
    assert parse_profile(document()) == CandidateProfile()
    assert parse_profile(document(experience='total_years 0;')).years_of_experience == 0
    assert parse_profile(document(experience='total_years 125;')).years_of_experience == 125


def test_all_normalized_skills_and_profile_identifiers_are_representable():
    tokens = all_canonical_tokens()
    source = document(skills=' '.join(f'skill {t};' for t in tokens),
                      classification=' '.join(f'accepted {p};' for p in PROFILES_REGISTRY))
    profile = parse_profile(source)
    assert profile.skills == tuple(tokens)
    assert profile.accepted_profiles == tuple(PROFILES_REGISTRY)


def test_repeated_contacts_of_the_same_kind_are_allowed():
    profile = parse_profile(document(contact='email "first@example.com"; email "second@example.com";'))
    assert [c.value for c in profile.contacts] == ['first@example.com', 'second@example.com']


def test_text_preserves_unicode_quotes_backslashes_newlines_and_dsl_punctuation():
    name = 'Ana María 😀'
    summary = 'She wrote "candidate { accepted full_stack; }".\nPath: C:\\notes\tDone.'
    source = document(personal=f'name {json.dumps(name)}; summary {json.dumps(summary)};')
    profile = parse_profile(source)
    assert profile.name == name
    assert profile.summary == summary
    assert profile.accepted_profiles == ()


def test_line_comments_do_not_consume_urls_or_strings():
    source = '// profile\n' + document(
        personal='name "Ana // Pérez"; // comment\n',
        contact='linkedin "https://www.linkedin.com/in/ana";',
    ) + '\n// end'
    profile = parse_profile(source)
    assert profile.name == 'Ana // Pérez'
    assert profile.contacts[0].value == 'https://www.linkedin.com/in/ana'


@pytest.mark.parametrize('source', [
    '',
    'candidate {}',
    document().replace('candidate', 'candidate_extra', 1),
    document().replace('personal {  }', ''),
    document().replace('contact {  }', 'contact {} contact {}'),
    document().replace('personal {  }\n  contact {  }', 'contact {}\n  personal {}'),
    document()[:-1],
    document() + ' unexpected',
    document(personal='name "Ana"'),
    document(personal='name Ana;'),
    document(personal="name 'Ana';"),
    document(personal='name "Ana"; name "Other";'),
    document(personal='location "Cali"; name "Ana";'),
    document(personal=r'name "bad\q";'),
    document(personal='name "first\nsecond";'),
    document(personal='age 20;'),
    document(contact='fax "1234567890";'),
    document(experience='total_years -1;'),
    document(experience='total_years 1.5;'),
    document(experience='total_years 01;'),
    document(experience='total_years "3";'),
    document(experience='entry { organization "Example"; }'),
    document(education='entry { institution "Example"; }'),
    document(skills='skill javascript;'),
    document(skills='skill NODE.JS;'),
    document(skills='skill "PYTHON";'),
    document(classification='accepted unknown_profile;'),
    document(classification='accepted full_stack_extra;'),
    document(classification='accepted FULL_STACK;'),
])
def test_lexical_and_syntactic_violations_are_rejected(source):
    with pytest.raises(ProfileValidationError) as exc:
        parse_profile(source)
    assert exc.value.kind == 'syntax'
    assert exc.value.line >= 1
    assert exc.value.column >= 1


@pytest.mark.parametrize('fields, message', [
    ({'personal': 'name " ";'}, 'name must not be blank'),
    ({'personal': 'summary "";'}, 'summary must not be blank'),
    ({'experience': 'entry { title ""; }'}, 'title must not be blank'),
    ({'education': 'entry { qualification "  "; }'}, 'qualification must not be blank'),
    ({'contact': 'email "not-an-email";'}, 'Invalid email'),
    ({'contact': 'email "prefix user@example.com suffix";'}, 'Invalid email'),
    ({'contact': 'phone "abc";'}, 'Invalid phone'),
    ({'contact': 'linkedin "https://example.com/in/user";'}, 'Invalid linkedin'),
    ({'contact': 'github "https://example.com/user";'}, 'Invalid github'),
    ({'contact': 'email "a@example.com"; email "a@example.com";'}, 'Duplicate contact'),
    ({'skills': 'skill FIGMA;'}, 'Unknown canonical skill'),
    ({'skills': 'skill EXPERIENCE_PRESENT;'}, 'Unknown canonical skill'),
    ({'skills': 'skill PYTHON; skill PYTHON;'}, 'Duplicate skill'),
    ({'skills': 'unrecognized "";'}, 'value must not be blank'),
    ({'skills': 'unrecognized "Figma"; unrecognized "Figma";'}, 'Duplicate unrecognized'),
    ({'classification': 'accepted full_stack; accepted full_stack;'}, 'Duplicate accepted profile'),
])
def test_semantic_checks_report_domain_errors_separately(fields, message):
    with pytest.raises(ProfileValidationError, match=message) as exc:
        parse_profile(document(**fields))
    assert exc.value.kind == 'semantic'
    assert exc.value.line >= 1
    assert exc.value.column >= 1


def test_grammar_validation_does_not_claim_to_reclassify_the_candidate():
    # This is structurally valid. Only Stage 3 can substantiate the declaration.
    profile = parse_profile(document(classification='accepted full_stack;'))
    assert profile.accepted_profiles == ('full_stack',)
    assert profile.skills == ()


def test_parse_results_are_immutable_and_independent():
    first = parse_profile(document(personal='name "First Candidate";', skills='skill PYTHON;'))
    second = parse_profile(document())
    with pytest.raises(FrozenInstanceError):
        first.name = 'Changed'
    assert second == CandidateProfile()
    assert first.skills == ('PYTHON',)


def test_utf8_files_and_error_locations(tmp_path):
    path = tmp_path / 'candidate.resume'
    path.write_text(document(personal='name "Ana Pérez";'), encoding='utf-8')
    assert parse_profile_file(path).name == 'Ana Pérez'
    path.write_text(document(skills='skill python;'), encoding='utf-8')
    with pytest.raises(ProfileValidationError) as exc:
        parse_profile_file(path)
    assert exc.value.line == 6
    assert exc.value.column > 0
    assert exc.value.filename == str(path)


def test_parser_requires_text():
    with pytest.raises(TypeError, match='must be a string'):
        parse_profile(None)


def test_cli_valid_file_prints_structured_data(capsys):
    assert main([str(EXAMPLES / 'wednesday.resume')]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)['accepted_profiles'] == ['full_stack']
    assert captured.err == ''


def test_cli_invalid_file_has_nonzero_status_and_no_success_output(capsys):
    assert main([str(EXAMPLES / 'invalid_candidate.resume')]) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'syntax:' in captured.err
    assert 'invalid_candidate.resume' in captured.err


def test_cli_missing_file_is_reported_without_a_traceback(tmp_path, capsys):
    assert main([str(tmp_path / 'absent.resume')]) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'absent.resume' in captured.err
    assert 'Traceback' not in captured.err
