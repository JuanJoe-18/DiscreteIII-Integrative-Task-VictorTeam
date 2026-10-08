# ResumeLens — Formal Language-Based Resume Screening
> **Estructuras Discretas III (2026) — Tarea Integradora**  
> **Equipo:** Víctor Team  
> **Integrante 2 (Motor de Lógica):** Etapa 3 (Reconocimiento de Patrones con Autómatas) y Frontend

---

##  Descripción del Proyecto
**ResumeLens** es un sistema automatizado de preselección curricular basado en la teoría de lenguajes formales y modelos computacionales. El sistema procesa hojas de vida textuales, extrae competencias técnicas, las normaliza a un formato canónico y determina si el perfil del candidato satisface formalmente los requisitos de cualificación de un cargo profesional sin emitir juicios heurísticos o subjetivos.

### Pipeline de 4 Etapas:
1. **Etapa 1 — Extracción de Información:** Expresiones Regulares (`re`).
2. **Etapa 2 — Normalización y Orden Canónico:** Transductores Finitos (FST).
3. **Etapa 3 — Reconocimiento de Patrones de Cualificación:** Autómatas Finitos Deterministas (DFA) implementados con `pyformlang`.
4. **Etapa 4 — Lenguaje de Especificación del Candidato:** Gramáticas Libres de Contexto (CFG) con `textX` y visualización HTML.

---

##  Perfiles Profesionales Soportados (4 Perfiles)

| # | Perfil | Dominio | Orden Canónico de Categorías |
|---|---|---|---|
| **1** | **Full Stack Developer** *(Predefinido)* | Software Engineering | $\text{Frontend} \to \text{Backend} \to \text{Database} \to \text{Version Control}$ |
| **2** | **Machine Learning Engineer** *(Predefinido)* | AI / Data | $\text{Language} \to \text{Data Processing} \to \text{ML Framework} \to \text{Database} \to \text{Version Control}$ |
| **3** | **Cloud & DevOps Engineer** *(Propuesto)* | Software Engineering | $\text{Scripting/OS} \to \text{CI/CD} \to \text{Containers} \to \text{Cloud/IaC} \to \text{Version Control}$ |
| **4** | **Data Scientist** *(Propuesto)* | AI / Data | $\text{Language} \to \text{Data Analysis/Stats} \to \text{Data Visualization} \to \text{Machine Learning} \to \text{Version Control}$ |

---

##  Estructura del Repositorio

```
DiscreteIII-Integrative-Task-VictorTeam/
├── docs/
│   ├── Initial Doc.md                 # Enunciado y rúbrica oficial de la tarea
│   └── stage3_formalization.md        # Formalización matemática (5-tuplas, tablas y diagramas)
├── src/
│   ├── __init__.py
│   ├── stage1_regex/                  # Etapa 1: Extracción con Regex
│   ├── stage2_fst/                    # Etapa 2: Normalización con FST
│   ├── stage3_classifier/             # Etapa 3: Motor de Autómatas (pyformlang)
│   │   ├── profiles.py                # Definición de perfiles, categorías y alfabetos
│   │   ├── automata_models.py         # Modelos DFA y 5-tuplas en pyformlang
│   │   ├── classifier.py              # Motor de evaluación y trazabilidad
│   │   └── visualizer.py              # Generador de grafos (Mermaid y Graphviz)
│   ├── stage4_grammar/                # Etapa 4: DSL y CFG con textX
│   └── ui/                            # Frontend Interactivo
│       └── app.py                     # Aplicación Web Streamlit
├── tests/
│   ├── __init__.py
│   └── test_stage3.py                 # Suite de pruebas unitarias (Pytest)
├── requirements.txt                   # Dependencias del proyecto
└── README.md                          # Documentación principal
```

---

##  Instalación y Ejecución

### 1. Clonar el repositorio y preparar el entorno
```bash
git clone https://github.com/JuanJoe-18/DiscreteIII-Integrative-Task-VictorTeam.git
cd DiscreteIII-Integrative-Task-VictorTeam
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar las pruebas unitarias
```bash
python -m pytest tests/test_stage3.py -v
```

### 4. Lanzar la Interfaz Web (Streamlit)
```bash
python -m streamlit run src/ui/app.py
```

La interfaz se abrirá en `http://localhost:8501`, permitiendo:
- Evaluar candidatos en vivo o con ejemplos predefinidos.
- Visualizar el camino de estados recorrido en el grafo de cada DFA.
- Inspeccionar las 5-tuplas formales y diagramas Mermaid/Graphviz.
- Ejecutar la suite de pruebas unitarias desde la propia interfaz web.

---

##  Formalización Matemática (Resumen de la 5-Tupla)

Para cada autómata $i \in \{FS, ML, DEVOPS, DS\}$:
$$\mathcal{M}_i = (Q_i, \Sigma_i, \delta_i, q_0, F_i)$$

- **$Q$:** Estados secuenciales que certifican cada nivel de competencia más el estado trampa $q_{trap}$.
- **$\Sigma$:** Alfabeto de tecnologías normalizadas clasificadas por categorías disjuntas.
- **$\delta$:** Función de transición determinista con *self-loops* para múltiples tecnologías de una categoría y transiciones hacia adelante para avanzar al siguiente requisito.
- **$q_0$:** Estado inicial.
- **$F$:** Estado de aceptación final que certifica la posesión de todas las competencias obligatorias.

*Para ver la formalización matemática completa con tablas de transición y diagramas de estados, consultar [`docs/stage3_formalization.md`](docs/stage3_formalization.md).*
