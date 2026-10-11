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

from src.stage1_regex import extract_qualifications
from src.stage2_fst.normalizer import normalize_qualifications, sort_to_canonical_order
from src.stage3_classifier import ResumeClassifier

ROOT = Path(__file__).resolve().parents[2]
MAX_TEXT = 100_000
CLASSIFIER = ResumeClassifier()
LABELS = {
    'EXPERIENCE': 'Experiencia reportada', 'FE_LANGUAGE': 'Lenguaje frontend',
    'FE_FRAMEWORK': 'Framework frontend', 'BE_LANGUAGE': 'Lenguaje / entorno backend',
    'BE_FRAMEWORK': 'Framework backend', 'API_COMMUNICATION': 'Comunicación API',
    'DATABASE_SQL': 'Base de datos SQL', 'DATABASE_NOSQL': 'Base de datos NoSQL',
    'DEVOPS_CLOUD': 'Despliegue y nube', 'VERSION_CONTROL': 'Control de versiones',
    'CORE_LANGUAGE': 'Lenguaje', 'DATA_PROCESSING': 'Procesamiento de datos',
    'ML_FRAMEWORKS': 'Framework ML', 'DATABASE': 'Base de datos',
    'SCRIPTING_OS': 'Scripting / sistema operativo', 'CICD': 'CI/CD',
    'CONTAINERS_ORCHESTRATION': 'Contenedores', 'CLOUD_IAC': 'Cloud / IaC',
    'DATA_LANGUAGE': 'Lenguaje analítico', 'DATA_ANALYSIS_STATS': 'Análisis / estadística',
    'DATA_VISUALIZATION': 'Visualización', 'MACHINE_LEARNING': 'Machine Learning',
    'BACKEND': 'Backend (lenguaje / entorno o framework)',
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
                'requirement': 'Obligatorio' if required else 'Alternativa obligatoria' if group else 'Opcional',
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
    extraction = extract_qualifications(text)
    normalization = normalize_qualifications(
        extraction.raw_tokens, extraction.years_of_experience,
    )
    fragments = [{'text': trace.raw, 'token': trace.canonical}
                 for trace in normalization.traces]
    normalized = list(dict.fromkeys(normalization.normalized_tokens))
    candidate = {
        'contact': extraction.contact,
        'education': extraction.education,
        'job_titles': extraction.job_titles,
        'years_of_experience': extraction.years_of_experience,
    }
    if extraction.candidate_name:
        candidate['name'] = extraction.candidate_name
    # Keep the explicit labels used by existing UI examples. Technical extraction
    # and section boundaries are handled exclusively by the shared extractor.
    for key, pattern in [('name', r'(?im)^[ \t]*(?:Name|Nombre)[ \t]*:[ \t]*([^\r\n]+)'),
                         ('description', r'(?im)^[ \t]*(?:Description|Descripción|Descripcion|Perfil)[ \t]*:[ \t]*([^\r\n]+)')]:
        match = re.search(pattern, text)
        if match:
            candidate[key] = match.group(1).strip()
    return fragments, normalized, candidate


def evaluate(payload):
    if not isinstance(payload, dict):
        raise ValueError('La solicitud debe ser un objeto JSON.')
    mode, text = payload.get('mode'), payload.get('text')
    if mode not in ('resume', 'tokens') or not isinstance(text, str):
        raise ValueError('Indica un modo válido y una entrada de texto.')
    if not text.strip() or len(text) > MAX_TEXT:
        raise ValueError('La entrada está vacía o supera los 100 000 caracteres.')
    if mode == 'resume':
        fragments, tokens, candidate = extract_resume(text)
        known = set().union(*(a.profile.alphabet for a in CLASSIFIER.automata.values())) - {'EXPERIENCE_PRESENT'}
        if not known.intersection(tokens):
            raise ValueError('No se reconocieron habilidades técnicas del catálogo en el texto.')
    else:
        fragments, candidate = [], {}
        tokens = [token for token in re.split(r'[,\s]+', text.strip()) if token]
        if any(not re.fullmatch(r'[A-Z][A-Z0-9_]*', token) for token in tokens):
            raise ValueError('Usa símbolos canónicos en MAYÚSCULAS, separados por comas o espacios.')
    results = []
    for pid, automaton in CLASSIFIER.automata.items():
        profile = automaton.profile
        if mode == 'resume':
            # Stage 2 orders each profile with its FILTER transducers. Project
            # onto the profile alphabet before strict Stage 3 recognition;
            # unrelated skills remain visible as ignored evidence.
            ordered = sort_to_canonical_order(tokens, pid)
            sequence = [token for token in ordered if token in profile.alphabet]
            result = CLASSIFIER.evaluate_profile(pid, sequence)
            result.ignored_tokens = [token for token in tokens if token not in profile.alphabet]
        else:
            result = CLASSIFIER.evaluate_profile(pid, tokens)
        observed = [{'category': LABELS[cat.name], 'tokens': sorted(cat.skills.intersection(result.evaluated_tokens))}
                    for cat in profile.canonical_categories if cat.name in result.satisfied_categories]
        results.append({
            'profileId': pid, 'accepted': result.is_accepted, 'sequence': result.evaluated_tokens,
            'steps': [{'index': step.step_number, 'from': step.source_state, 'to': step.target_state,
                       'symbol': step.symbol, 'explanation':
                       'El estado trampa absorbe la entrada.' if step.source_state == 'q_trap' else
                       result.rejection_reason if not step.is_valid_transition else
                       f'Lee {step.symbol} ({LABELS.get(step.category, step.category)}).'} for step in result.trace],
            'finalState': result.final_state, 'observed': observed,
            'missing': [LABELS.get(name, name) for name in result.missing_categories],
            'foreign': result.ignored_tokens, 'reason': result.rejection_reason,
        })
    return {'mode': mode, 'fragments': fragments, 'normalized': tokens, 'results': results,
            'candidate': candidate, 'simulated': False}


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
        if urlsplit(self.path).path != '/api/evaluate':
            self.send_json({'error': 'Ruta no encontrada.'}, 404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 500_000:
                raise ValueError('Tamaño de solicitud inválido.')
            if self.headers.get_content_type() != 'application/json':
                raise ValueError('Se requiere Content-Type: application/json.')
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            self.send_json(evaluate(payload))
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
