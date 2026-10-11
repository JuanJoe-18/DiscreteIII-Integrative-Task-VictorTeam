import json
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
    assert devops['missing'] == ['Control de versiones']


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
