"""Generate the Stage 3 definition from the executable DFA models."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.stage3_classifier.automata_models import build_all_automata


def export_formalization():
    lines = [
        '# Etapa 3 — Reconocimiento de patrones de cualificación',
        '',
        'Documento generado con `python scripts/export_formalization.py` desde los modelos ejecutables.',
        '',
        '## Contrato y criterios de diseño',
        '',
        'La entrada contiene tokens canónicos de la etapa 2, no texto de una hoja de vida. '
        'Se reconocen cuatro patrones mediante una misma solución basada en `pyformlang`. '
        'Un candidato puede cumplir cero, uno o varios perfiles; no se generan rankings ni decisiones de contratación.',
        '',
        '`classify(tokens)` prepara una secuencia por perfil: conserva los símbolos de su alfabeto '
        'y los ordena por categoría. Las habilidades ajenas se conservan en `ignored_tokens` para auditoría '
        'y no satisfacen requisitos. `evaluated_tokens` contiene la secuencia efectivamente reconocida. '
        'Esta preparación es una operación de integración, no una transición del DFA. '
        '`evaluate_profile(id, tokens)` y `classify(tokens, prepare_input=False)` reconocen la palabra '
        'estrictamente, sin filtrarla ni reordenarla. El modo directo y la demostración sin etapa 2 usan esta evaluación estricta.',
        '',
        'Cada símbolo representa una competencia identificada explícitamente; no certifica el nivel de dominio. '
        '`EXPERIENCE_PRESENT` representa un número de años reportado, incluido cero. La experiencia es opcional '
        'y no tiene umbral mínimo en este patrón. Los años exactos permanecen como metadatos de la etapa 1. '
        'No se usa el símbolo literal `\\d` ni un alfabeto infinito de números.',
        '',
        '## Tipo de autómata y semántica formal',
        '',
        'Para cada perfil, M = (Q, Σ, δ, q0, F). Las categorías del alfabeto son disjuntas dentro '
        'de un perfil. δ: Q × Σ → Q es total, con un único destino por par. No hay transiciones ε '
        'ni decisiones alternativas para un mismo símbolo: los cuatro modelos son DFA. '
        '`q_trap` pertenece a Q, no pertenece a F y satisface δ(q_trap, s) = q_trap para todo s ∈ Σ. '
        'Un token externo a Σ se rechaza antes de aplicar δ; su paso a trampa en la traza es una convención '
        'de diagnóstico, no una extensión del dominio de δ.',
        '',
        'Los estados `q_<categoría>` indican el último bloque consumido. En Full Stack no implican '
        'que se hayan observado todas las categorías anteriores, porque existen saltos. '
        '`satisfied_categories` enumera categorías observadas en la entrada; `missing_categories` '
        'enumera requisitos obligatorios ausentes. Una palabra con todos los requisitos puede rechazarse '
        'por desorden en la evaluación estricta.',
        '',
        'Reconocer una palabra cuesta O(n), dado un modelo construido. Preparar cada perfil mediante '
        'ordenamiento cuesta O(n log n). En las expresiones siguientes, C+ significa una o más '
        'habilidades de la categoría y C* permite cero o más; | representa alternativas.',
        '',
    ]
    for pid, auto in build_all_automata().items():
        formal = auto.get_formal_tuple()
        profile = auto.profile
        lines += [f'## {profile.title}', '', f'Dominio: {profile.domain}.', '',
                  f'**Q** = {{{", ".join(sorted(formal.states))}}}', '',
                  '**q0** = `q0`.', '',
                  f'**F** = {{{", ".join(sorted(formal.final_states))}}}', '',
                  '**Σ** es la unión de las siguientes categorías:', '',
                  '| Categoría | Símbolos |', '|---|---|']
        for cat in profile.canonical_categories:
            lines.append(f'| {cat.name} | {", ".join(sorted(cat.skills))} |')
        if pid == 'full_stack':
            pattern = ('EXPERIENCE* FE_LANGUAGE+ FE_FRAMEWORK* '
                       '(BE_LANGUAGE+ BE_FRAMEWORK* | BE_FRAMEWORK+) API_COMMUNICATION* '
                       '(DATABASE_SQL+ DATABASE_NOSQL* | DATABASE_NOSQL+) DEVOPS_CLOUD* VERSION_CONTROL+')
        else:
            pattern = ' '.join(cat.name + '+' for cat in profile.canonical_categories)
        lines += ['', '**Patrón reconocido:**', '', f'`{pattern}`', '',
                  '**Requisitos mínimos:** ' + '; '.join(
                      name + ' (' + ' o '.join(sorted(alts)) + ')'
                      for name, alts in profile.required_groups.items()) + '.', '',
                  '**δ completa por categorías:** cada celda se aplica a todos los símbolos de su columna.', '',
                  '| Estado | ' + ' | '.join(cat.name for cat in profile.canonical_categories) + ' |',
                  '|---|' + '---|' * len(profile.canonical_categories)]
        for state in sorted(formal.states):
            targets = []
            for cat in profile.canonical_categories:
                destinations = {formal.transitions[state, skill] for skill in cat.skills}
                assert len(destinations) == 1
                targets.append(destinations.pop())
            lines.append('| ' + state + ' | ' + ' | '.join(targets) + ' |')
        lines += ['', f'![DFA {profile.title}](diagrams/{pid}.png)', '',
                  'En Graphviz, «otros símbolos de Σ» agrupa el complemento exacto de las aristas '
                  'sólidas del estado. Mermaid contiene una transición explícita por cada par de δ.', '']
    lines += [
        '## Verificación contra el enunciado del punto 3', '',
        '| Requisito | Evidencia |', '|---|---|',
        '| Cuatro perfiles con una solución general | Registro común y construcción/evaluación compartidas; Full Stack, ML, DevOps y Data Scientist |',
        '| Definición completa de Q, Σ, δ, q0 y F por autómata | Secciones anteriores y `get_formal_tuple()`; tabla total generada del DFA |',
        '| Explicar y justificar DFA/NFA/ε-NFA | Determinismo, totalidad y ausencia de ε explicados arriba |',
        '| Diagrama de transición | DOT/SVG/PNG y Mermaid derivados del modelo |',
        '| Explicar el patrón profesional | Expresión regular y requisitos mínimos de cada sección |',
        '| Implementar usando pyformlang | `ProfileAutomaton.dfa` es un `DeterministicFiniteAutomaton` |',
        '| Casos de prueba y escenarios | `tests/test_stage3.py`, `test_stage3_regressions.py` y `test_pipeline_contract.py` |', '',
        'El enunciado presenta tecnologías como ejemplos y solicita que el equipo defina los patrones. '
        'Por eso Full Stack admite backend por lenguaje/entorno o framework, SQL o NoSQL, y hace opcionales '
        'framework frontend, APIs y despliegue. ML exige una habilidad del grupo ML_FRAMEWORKS, '
        'sin exigir simultáneamente Scikit-learn y un framework de deep learning. '
        'Estas son decisiones explícitas del equipo, no requisitos textuales adicionales del docente.', '',
        'El enunciado menciona requisitos detallados que se proporcionarían por separado. '
        'Esta verificación se basa en `docs/Initial Doc.md`; debe contrastarse también con cualquier '
        'anexo del docente que no esté en el repositorio.', '',
        'La conformidad del punto 3 no implica que el proyecto completo esté terminado: la etapa 2 '
        'actual utiliza un diccionario de referencia (no un FST implementado), la etapa 1 es una '
        'extracción de referencia y la etapa 4 no contiene aún la DSL textX. '
        'Poster, revisión de literatura, registro de uso de IAG y presentación son entregables independientes.', '',
        'Ejecutar `python -m pytest -q` para verificar los escenarios. Las regresiones cubren '
        'clasificación simultánea, evaluación estricta, categorías opcionales, años 0/3/10/25, '
        'totalidad de δ, diagramas, omisión de cada requisito y las 1024 combinaciones de presencia '
        'de las diez categorías de Full Stack.', '',
    ]
    (ROOT / 'docs/stage3_formalization.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    export_formalization()
