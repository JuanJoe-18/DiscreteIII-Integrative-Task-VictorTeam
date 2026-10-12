"""Serve the built frontend and a same-origin JSON API on loopback.

Run: python -m src.web_api.server
This is a local demonstration server, not an Internet deployment server.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from src.pipeline import extract_and_normalize, process_resume
from src.stage3_classifier import ResumeClassifier
from src.stage4_grammar import ProfileValidationError, validate_document

ROOT = Path(__file__).resolve().parents[2]
MAX_TEXT = 100_000
CLASSIFIER = ResumeClassifier()
LABELS = {
    'EXPERIENCE': 'Reported experience', 'FE_LANGUAGE': 'Frontend language',
    'FE_FRAMEWORK': 'Frontend framework', 'BE_LANGUAGE': 'Backend language / runtime',
    'BE_FRAMEWORK': 'Backend framework', 'API_COMMUNICATION': 'API communication',
    'DATABASE_SQL': 'SQL database', 'DATABASE_NOSQL': 'NoSQL database',
    'DEVOPS_CLOUD': 'Deployment and cloud', 'VERSION_CONTROL': 'Version control',
    'CORE_LANGUAGE': 'Language', 'DATA_PROCESSING': 'Data processing',
    'ML_FRAMEWORKS': 'ML framework', 'DATABASE': 'Database',
    'SCRIPTING_OS': 'Scripting / operating system', 'CICD': 'CI/CD',
    'CONTAINERS_ORCHESTRATION': 'Containers', 'CLOUD_IAC': 'Cloud / IaC',
    'DATA_LANGUAGE': 'Analytical language', 'DATA_ANALYSIS_STATS': 'Analysis / statistics',
    'DATA_VISUALIZATION': 'Visualization', 'MACHINE_LEARNING': 'Machine Learning',
    'BACKEND': 'Backend (language / runtime or framework)',
}


def profile_catalog():
    profiles = []
    for pid, auto in CLASSIFIER.automata.items():
        profile, formal = auto.profile, auto.get_formal_tuple()
        groups = profile.required_groups
        categories = []
        for cat in profile.canonical_categories:
            group = next((name for name, choices in groups.items() if cat.name in choices), None)
            required = group is not None and len(groups[group]) == 1
            categories.append({
                'id': cat.name, 'label': LABELS[cat.name], 'short': LABELS[cat.name],
                'tokens': sorted(cat.skills), 'required': required,
                'requirement': 'Required' if required else 'Required alternative' if group else 'Optional',
                'group': LABELS.get(group, group),
            })
        transitions = {state: {} for state in sorted(formal.states)}
        for (source, symbol), target in sorted(formal.transitions.items()):
            transitions[source][symbol] = target
        pattern = ('EXPERIENCE* FE_LANGUAGE+ FE_FRAMEWORK* (BE_LANGUAGE+ BE_FRAMEWORK* | BE_FRAMEWORK+) '
                   'API_COMMUNICATION* (DATABASE_SQL+ DATABASE_NOSQL* | DATABASE_NOSQL+) '
                   'DEVOPS_CLOUD* VERSION_CONTROL+' if pid == 'full_stack' else
                   ' · '.join(cat.name + '+' for cat in profile.canonical_categories))
        profiles.append({
            'id': pid, 'name': profile.title, 'description': ' → '.join(c['label'] for c in categories),
            'categories': categories, 'requiredGroups': {name: sorted(choices) for name, choices in groups.items()},
            'states': ['q0'] + auto.state_names[1:] + ['q_trap'],
            'initialState': formal.initial_state, 'finalStates': sorted(formal.final_states),
            'transitions': transitions, 'pattern': pattern,
        })
    return profiles


def extract_resume(text):
    """Adapt the complete Stage 1/2 results to the web response contract."""
    _, normalization, candidate = extract_and_normalize(text)
    fragments = [{'text': trace.raw, 'token': trace.canonical}
                 for trace in normalization.traces]
    normalized = list(dict.fromkeys(normalization.normalized_tokens))
    return fragments, normalized, candidate


def evaluate(payload):
    if not isinstance(payload, dict):
        raise ValueError('The request must be a JSON object.')
    mode, text = payload.get('mode'), payload.get('text')
    if mode not in ('resume', 'tokens') or not isinstance(text, str):
        raise ValueError('Provide a valid mode and a text input.')
    if not text.strip() or len(text) > MAX_TEXT:
        raise ValueError('The input is empty or exceeds 100,000 characters.')
    if mode == 'resume':
        pipeline = process_resume(text, classifier=CLASSIFIER)
        fragments = [{'text': t.raw, 'token': t.canonical} for t in pipeline.normalization.traces]
        tokens, candidate = pipeline.classification.input_tokens, pipeline.candidate
        known = set().union(*(a.profile.alphabet for a in CLASSIFIER.automata.values())) - {'EXPERIENCE_PRESENT'}
        if not known.intersection(tokens):
            raise ValueError('No technical skills from the catalog were recognized in the text.')
    else:
        fragments, candidate = [], {}
        tokens = [token for token in re.split(r'[,\s]+', text.strip()) if token]
        if any(not re.fullmatch(r'[A-Z][A-Z0-9_]*', token) for token in tokens):
            raise ValueError('Use canonical UPPERCASE symbols separated by commas or spaces.')
    results = []
    for pid, automaton in CLASSIFIER.automata.items():
        profile = automaton.profile
        if mode == 'resume':
            result = pipeline.classification.results_by_profile[pid]
        else:
            result = CLASSIFIER.evaluate_profile(pid, tokens)
        observed = [{'category': LABELS[cat.name], 'tokens': sorted(cat.skills.intersection(result.evaluated_tokens))}
                    for cat in profile.canonical_categories if cat.name in result.satisfied_categories]
        results.append({
            'profileId': pid, 'accepted': result.is_accepted, 'sequence': result.evaluated_tokens,
            'steps': [{'index': step.step_number, 'from': step.source_state, 'to': step.target_state,
                       'symbol': step.symbol, 'explanation':
                       'The trap state absorbs the input.' if step.source_state == 'q_trap' else
                       result.rejection_reason if not step.is_valid_transition else
                       f'Reads {step.symbol} ({LABELS.get(step.category, step.category)}).'} for step in result.trace],
            'finalState': result.final_state, 'observed': observed,
            'missing': [LABELS.get(name, name) for name in result.missing_categories],
            'foreign': result.ignored_tokens, 'reason': result.rejection_reason,
        })
    return {'mode': mode, 'fragments': fragments, 'normalized': tokens, 'results': results,
            'candidate': candidate, 'simulated': False,
            'profileDocument': pipeline.document.to_dict() if mode == 'resume' else None}


def validate_profile(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('text'), str):
        raise ValueError('Provide the DSL in the text field.')
    if not payload['text'].strip() or len(payload['text']) > MAX_TEXT:
        raise ValueError('The DSL is empty or exceeds 100,000 characters.')
    return validate_document(payload['text']).to_dict()


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Do not write submitted resume content to logs.
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlsplit(self.path).path == '/api/profiles':
            self.send_json(profile_catalog())
        elif urlsplit(self.path).path.startswith('/api/'):
            self.send_json({'error': 'Ruta no encontrada.'}, 404)
        else:
            super().do_GET()

    def do_POST(self):
        route = urlsplit(self.path).path
        if route not in ('/api/evaluate', '/api/validate-profile'):
            self.send_json({'error': 'Ruta no encontrada.'}, 404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 500_000:
                raise ValueError('Invalid request size.')
            if self.headers.get_content_type() != 'application/json':
                raise ValueError('Se requiere Content-Type: application/json.')
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            self.send_json(evaluate(payload) if route == '/api/evaluate' else validate_profile(payload))
        except ProfileValidationError as exc:
            self.send_json({'error': str(exc), 'kind': exc.kind, 'line': exc.line, 'column': exc.column}, 400)
        except (ValueError, UnicodeError) as exc:
            self.send_json({'error': str(exc)}, 400)


def create_server(port=8000, static_dir=None):
    directory = Path(static_dir) if static_dir else ROOT / 'frontend' / 'dist'
    return ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=str(directory)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    with create_server(port=args.port) as server:
        print(f'ResumeLens: http://127.0.0.1:{server.server_port}', flush=True)
        if not (ROOT / 'frontend/dist/index.html').exists():
            print('Frontend sin compilar: ejecuta pnpm build en frontend o usa Vite.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
