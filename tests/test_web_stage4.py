import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from src.stage4_grammar import CandidateProfile, serialize_profile
from src.web_api.server import create_server, evaluate, validate_profile


def test_resume_response_contains_validated_document_matching_dfa_results():
    result = evaluate({'mode': 'resume', 'text': 'Name: Ada\nSkills: Python, Pandas, Matplotlib, Scikit-learn, SQL, Git.'})
    document = result['profileDocument']
    assert document['validated'] is True
    assert set(document['profile']['accepted_profiles']) == {r['profileId'] for r in result['results'] if r['accepted']}
    assert document['profile']['name'] == 'Ada'
    assert validate_profile({'text': document['dsl']}) == document


def test_strict_tokens_do_not_invent_candidate_documents():
    assert evaluate({'mode': 'tokens', 'text': 'JAVASCRIPT,NODE_JS,SQL,GIT'})['profileDocument'] is None


@pytest.mark.parametrize('payload', [None, [], {}, {'text': 12}, {'text': ''}, {'text': ' '}, {'text': 'x' * 100_001}])
def test_dsl_endpoint_rejects_invalid_payloads(payload):
    with pytest.raises(ValueError):
        validate_profile(payload)


def test_http_dsl_validation_reports_location_and_never_returns_html_on_failure(tmp_path):
    server = create_server(port=0, static_dir=tmp_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}/api/validate-profile'

    def request(text):
        return urlopen(Request(url, data=json.dumps({'text': text}).encode(), headers={'Content-Type': 'application/json'}))

    try:
        valid = serialize_profile(CandidateProfile(name='Test'))
        with request(valid) as response:
            assert response.headers['Cache-Control'] == 'no-store'
            assert json.load(response)['profile']['name'] == 'Test'
        for source, kind in [(valid.replace('personal', 'person'), 'syntax'),
                             (valid.replace('name "Test";', 'name " ";'), 'semantic')]:
            with pytest.raises(HTTPError) as captured:
                request(source)
            assert captured.value.code == 400
            body = json.load(captured.value)
            assert body['kind'] == kind
            assert body['line'] > 0 and body['column'] > 0
            assert 'html' not in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
