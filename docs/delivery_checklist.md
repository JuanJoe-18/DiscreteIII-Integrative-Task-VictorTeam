# Matriz de entrega y verificaciones externas

Base: enunciado suministrado en PDF y su transcripción `Initial Doc.md`.
Revisión técnica del 11 de octubre de 2026. Esta matriz distingue archivos
preparados de trámites, anexos y demostraciones que requieren al equipo.

| Requisito | Evidencia en el repositorio | Estado técnico |
|---|---|---|
| Extracción con `re`, explicación y persistencia | `stage1_regex.md`, `stage1_tests.md`, `src/stage1_regex/storage.py` | Implementado y probado |
| Transductores pyformlang, 7-tuplas y diagramas | `stage2_fst.md`, `stage2_tests.md`, `docs/diagrams/stage2/` | Implementado y probado |
| Cuatro perfiles, DFA, 5-tuplas, patrones y trazas | `stage3_formalization.md`, `src/stage3_classifier/` | Implementado y probado |
| EBNF con terminales, no terminales y repeticiones | `stage4_grammar.md`, `candidate.tx` | Documentado e implementado |
| Información personal, contacto, experiencia, formación y perfiles múltiples | `models.py`, ejemplo `wednesday.resume` | Representable; extracción conserva información parcial |
| Generación automática y validación textX antes de visualizar | `generator.py`, `renderer.py`, `src/pipeline.py` | Integrado y probado |
| Rechazo léxico/sintáctico y diagnóstico | Parser, CLI, endpoint de validación | Probado; no emite HTML inválido |
| Interfaz Python e integración web | Streamlit; API Python + React | Implementado |
| Diseño modular y documentación de pruebas | `architecture.md`, `stage4_tests.md` y documentos previos | Preparado |
| Revisión de literatura | `literature_review.md` | Preparada con fuentes primarias |
| Póster de investigación en inglés | `output/pdf/resumelens-poster.pdf` | Preparado |
| Presentación técnica de 10 minutos en inglés | Póster y ejemplos del repositorio | Ensayo y exposición a cargo del equipo |
| Registro de interacción con IAG e insumos propios | Sin archivo en el repositorio | Pendiente a cargo del equipo |

## Comprobaciones que corresponden al equipo

Las diapositivas y el guion son apoyo opcional para preparar la exposición. Se
conservan fuera del repositorio y no forman parte de sus archivos de entrega.

- Contrastar las categorías con cualquier anexo de requisitos que el profesor
  haya entregado por separado: no estaba en la carpeta revisada.
- Confirmar integrantes, nombres completos y registro del equipo. Los materiales
  usan el nombre existente «Víctor Team» sin inventar una lista de autores.
- Revisar todos los documentos, entender y ensayar el código, y practicar el guion
  en inglés con el póster. La asignación de tiempos suma 10 minutos; la duración
  real depende del ensayo.
- Ejecutar los scripts de commits y el push. Revisar los requisitos del historial
  (incluido el intervalo solicitado por el enunciado). Los scripts conservan fechas
  reales; no fabrican intervalos ni alteran commits anteriores.
- Entregar los enlaces/archivos por el canal de la asignatura. No se ha realizado
  una entrega ni se han enviado mensajes en nombre del equipo.

## Límite de las afirmaciones

La suite verifica comportamiento programado. No hay métricas de contratación,
dataset de currículos anotado ni evaluación de precisión/recall. La DSL permite
registros detallados, pero el extractor no vincula de forma fiable empleadores,
instituciones y periodos. El editor permite completar esos datos explícitamente.
