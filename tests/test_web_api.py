import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from threading import Thread

import pytest

from src.web_api.server import create_server, evaluate, profile_catalog
from src.stage3_classifier import ResumeClassifier


def test_catalog_is_the_actual_dfa_and_declares_alternatives():
    classifier = ResumeClassifier()
    for profile in profile_catalog():
        formal = classifier.automata[profile['id']].get_formal_tuple()
        assert set(profile['states']) == formal.states
        assert set(profile['finalStates']) == formal.final_states
        assert sum(len(row) for row in profile['transitions'].values()) == len(formal.transitions)
        for (source, symbol), target in formal.transitions.items():
            assert profile['transitions'][source][symbol] == target
    fs = profile_catalog()[0]
    assert fs['requiredGroups']['BACKEND'] == ['BE_FRAMEWORK', 'BE_LANGUAGE']


def test_resume_uses_catalog_regex_and_python_classifier():
    result = evaluate({'mode': 'resume', 'text': 'Nombre: Laura Gómez\nHabilidades:\nJavaScript y React. Node.js con Express. PostgreSQL, Docker y Git.\n10 años de experiencia.'})
    assert result['simulated'] is False
    assert result['candidate']['name'] == 'Laura Gómez'
    fs = next(r for r in result['results'] if r['profileId'] == 'full_stack')
    assert fs['accepted']
    assert fs['sequence'][0] == 'EXPERIENCE_PRESENT'
    assert fs['finalState'] == 'q_version_control'
    assert fs['missing'] == []


def test_resume_can_qualify_for_two_profiles():
    result = evaluate({'mode': 'resume', 'text': 'Habilidades: Python, Pandas, Matplotlib, Scikit-learn, SQL y Git.'})
    assert {r['profileId'] for r in result['results'] if r['accepted']} == {'machine_learning', 'data_scientist'}


def test_strict_words_are_not_sorted_or_filtered():
    word = 'GIT, JAVASCRIPT, NODE_JS, POSTGRESQL'
    result = evaluate({'mode': 'tokens', 'text': word})
    assert not any(r['accepted'] for r in result['results'])
    fs = result['results'][0]
    assert fs['steps'][0]['to'] == 'q_trap'
    assert fs['sequence'] == word.split(', ')


def test_overlapping_ci_tool_does_not_invent_version_control():
    result = evaluate({'mode': 'resume', 'text': 'Habilidades: Bash, GitHub Actions, Docker y AWS.'})
    devops = next(r for r in result['results'] if r['profileId'] == 'cloud_devops')
    assert 'GITHUB_ACTIONS' in result['normalized']
    assert 'GITHUB' not in result['normalized']
    assert not devops['accepted']
    assert devops['missing'] == ['Version control']


@pytest.mark.parametrize('contact', [
    'Contact: python@gmail.com',
    'Contact: github.com/python',
])
def test_contact_text_cannot_supply_a_missing_backend_skill(contact):
    result = evaluate({'mode': 'resume', 'text':
                       contact + '\nSkills: JavaScript, PostgreSQL, Git.'})
    assert result['normalized'] == ['JAVASCRIPT', 'POSTGRESQL', 'GIT']
    fs = next(r for r in result['results'] if r['profileId'] == 'full_stack')
    assert not fs['accepted']
    assert fs['missing'] == ['Backend (language / runtime or framework)']


@pytest.mark.parametrize('section_break', ['\nExperience\n', '\n\n'])
def test_ambiguous_words_after_skills_are_not_qualifications(section_break):
    text = ('Skills: JavaScript, PostgreSQL, Git.' + section_break
            + 'We react quickly and go the extra mile.')
    result = evaluate({'mode': 'resume', 'text': text})
    assert result['normalized'] == ['JAVASCRIPT', 'POSTGRESQL', 'GIT']
    assert not any(r['accepted'] for r in result['results'])


def test_candidate_metadata_and_unknown_skills_survive_the_web_pipeline():
    text = (Path(__file__).parent / 'data' / 'resumes' / 'rich_resume.txt').read_text(encoding='utf-8')
    result = evaluate({'mode': 'resume', 'text': text})
    candidate = result['candidate']
    assert candidate['name'] == 'WEDNESDAY ADDAMS'
    assert candidate['years_of_experience'] == 10
    assert candidate['contact'] == {
        'email': ['wednesday.addams@example.com'],
        'phone': ['+57 300 123 4567'],
        'linkedin': ['linkedin.com/in/wadd'],
        'github': ['github.com/wadd/notes'],
    }
    assert 'Bachelor of Science in Computer Science' in candidate['education']
    assert 'AWS Certified Solutions Architect' in candidate['education']
    assert 'Web Application Developer' in candidate['job_titles']
    assert {'FIGMA', 'NOTION'} <= set(result['normalized'])
    fs = next(r for r in result['results'] if r['profileId'] == 'full_stack')
    assert fs['accepted']
    assert {'FIGMA', 'NOTION'} <= set(fs['foreign'])
    assert not {'FIGMA', 'NOTION'}.intersection(fs['sequence'])


def test_zero_experience_is_preserved_without_inventing_experience_token():
    result = evaluate({'mode': 'resume', 'text':
                       'Wednesday Addams\n0 years of experience.\n'
                       'Skills: JS, NodeJS, Postgres, Git.'})
    assert result['candidate']['name'] == 'Wednesday Addams'
    assert result['candidate']['years_of_experience'] == 0
    assert 'EXPERIENCE_PRESENT' not in result['normalized']
    assert result['results'][0]['accepted']


def test_profile_preparation_preserves_category_order_and_foreign_evidence():
    result = evaluate({'mode': 'resume', 'text':
                       'Skills: Git, Postgres, NodeJS, TypeScript, JS, Figma, AWS.'})
    fs = next(r for r in result['results'] if r['profileId'] == 'full_stack')
    assert fs['accepted']
    assert fs['sequence'] == ['TYPESCRIPT', 'JAVASCRIPT', 'NODE_JS', 'POSTGRESQL', 'AWS', 'GIT']
    assert fs['foreign'] == ['FIGMA']


@pytest.mark.parametrize('payload', [{}, {'mode': 'bad', 'text': 'Python'}, {'mode': 'tokens', 'text': ''}, {'mode': 'resume', 'text': 123}, {'mode': 'resume', 'text': 'No hay habilidades técnicas'}, {'mode': 'tokens', 'text': 'JS?'}])
def test_invalid_requests_are_rejected(payload):
    with pytest.raises(ValueError):
        evaluate(payload)


def test_http_roundtrip_and_bad_json(tmp_path):
    (tmp_path / 'index.html').write_text('<h1>ResumeLens</h1>')
    server = create_server(port=0, static_dir=tmp_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with urlopen(base + '/api/profiles') as response:
            assert len(json.load(response)) == 4
        with urlopen(base) as response:
            assert b'ResumeLens' in response.read()
        req = Request(base + '/api/evaluate', data=json.dumps({'mode': 'tokens', 'text': 'JAVASCRIPT,NODE_JS,SQL,GIT'}).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(req) as response:
            assert json.load(response)['results'][0]['accepted']
        with pytest.raises(HTTPError) as error:
            urlopen(Request(base + '/api/evaluate', data=b'{invalid', headers={'Content-Type': 'application/json'}))
        assert error.value.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
