"""ResumeLens - Interactive UI built with Streamlit.

Features:
- Live candidate technical qualification screening.
- Step-by-step DFA state trace visualization with Graphviz.
- Mathematical formalization viewer (5-tuples, transition tables, Mermaid diagrams).
- Pre-configured test resumes and custom token input.
- Real-time unit test suite execution.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import graphviz
from src.stage1_regex import extract_qualifications
from src.stage2_fst import normalize_and_sort
from src.stage3_classifier.automata_models import build_all_automata
from src.stage3_classifier.classifier import ResumeClassifier, ClassificationStatus
from src.stage3_classifier.profiles import PROFILES_REGISTRY
from src.stage3_classifier.visualizer import build_graphviz_diagram

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="ResumeLens | Motor de Lógica & Autómatas",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .badge-accepted {
        background-color: #dcfce7;
        color: #15803d;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-rejected {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Classifier and Automata
@st.cache_resource
def get_classifier():
    return ResumeClassifier()

@st.cache_resource
def get_automata():
    return build_all_automata()

classifier = get_classifier()
automata = get_automata()

# ============================================================================
# Sample Resumes Dictionary
# ============================================================================
SAMPLE_RESUMES = {
    "Wednesday Addams (Full Stack - Aceptado)": [
        "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"
    ],
    "Wednesday Addams (Full Stack - Con 3 años exp)": [
        "3", "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"
    ],
    "Mary Jane Watson (Machine Learning - Aceptado)": [
        "PYTHON", "PANDAS", "NUMPY", "SCIKIT_LEARN", "TENSORFLOW", "SQL", "GIT"
    ],
    "Alex Murphy (Cloud & DevOps - Aceptado)": [
        "BASH", "LINUX", "GITHUB_ACTIONS", "DOCKER", "KUBERNETES", "AWS", "TERRAFORM", "GIT"
    ],
    "Ada Lovelace (Data Scientist - Aceptado)": [
        "PYTHON", "PANDAS", "NUMPY", "SEABORN", "PLOTLY", "SCIKIT_LEARN", "GIT"
    ],
    "Candidato Incompleto (Rechazado - Falta Backend y VCS)": [
        "JAVASCRIPT", "REACT", "POSTGRESQL"
    ],
    "Candidato Desordenado (Rechazado - Git antes de Backend)": [
        "JAVASCRIPT", "GIT", "NODE_JS", "POSTGRESQL"
    ],
    "Candidato Mixto Incompatible (Rechazado - Token foráneo)": [
        "JAVASCRIPT", "NODE_JS", "SCIKIT_LEARN", "GIT"
    ],
}

SAMPLE_RAW_CVS = {
    "Wednesday Addams (Full Stack - Enunciado)": (
        "Wednesday Addams 3 years of experience developing web applications. "
        "Technical Skills: JS, React.js, NodeJS, Postgres, Git."
    ),
    "Mary Jane Watson (Machine Learning - Enunciado)": (
        "Mary Jane Watson 2 years of experience developing predictive models and data-processing pipelines. "
        "Technical Skills: Python, Pandas, NumPy, Scikit-learn, TensorFlow, SQL, Git."
    ),
    "Alex Murphy (Cloud & DevOps)": (
        "Alex Murphy 4 years of infrastructure engineering. "
        "Technical Skills: Bash, Linux, GitHub Actions, Docker, Kubernetes, AWS, Terraform, Git."
    ),
    "Ada Lovelace (Data Scientist)": (
        "Ada Lovelace 3 years of data analysis and machine learning. "
        "Technical Skills: Python, Pandas, NumPy, Seaborn, Plotly, Scikit-learn, Git."
    ),
    "Candidato Sin Normalizar (Prueba de Rechazo si se salta Etapa 2)": (
        "Junior Web Developer. Technical Skills: JS, React.js, Postgres."
    ),
}

# ============================================================================
# Sidebar
# ============================================================================
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python-Dark.svg",
        width=50,
    )
    st.title("ResumeLens")
    st.caption("Estructuras Discretas III — Tarea Integradora")
    st.divider()

    st.subheader("📌 Rol del Sistema")
    st.markdown(
        """
        - **Integrante 2:** Motor de Lógica (Etapa 3) & Frontend
        - **Modelo Formal:** Autómatas Finitos Deterministas (DFA)
        - **Librería Formal:** `pyformlang`
        - **Perfiles Soportados:** 4 (2 de Software, 2 de AI/Data)
        """
    )
    st.divider()

    st.subheader("👤 Equipo")
    st.info("Víctor Team — Integrante 2 (Motor de Lógica)")


# ============================================================================
# Main Header
# ============================================================================
st.markdown('<div class="main-header">🔍 ResumeLens: Motor de Clasificación Formal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Reconocimiento de patrones de cualificación profesional mediante Autómatas Finitos Deterministas (DFA) en <code>pyformlang</code>.</div>',
    unsafe_allow_html=True,
)

# Tabs
tab_eval, tab_formal, tab_tests, tab_about = st.tabs([
    "🚀 Evaluador de Currículums",
    "📐 Formalización Matemática (5-Tuplas)",
    "🧪 Suite de Pruebas Unitarias",
    "📖 Sobre el Proyecto",
])

# ============================================================================
# Tab 1: Live Candidate Screening
# ============================================================================
with tab_eval:
    eval_mode = st.radio(
        "Modo de Evaluación:",
        [
            "🔗 Pipeline Completo End-to-End (CV Texto Crudo ➔ Etapa 1 Regex ➔ Etapa 2 FST ➔ Etapa 3 DFA)",
            "🎯 Modo Directo (Tokens de Entrada para Etapa 3)",
        ],
        horizontal=True,
    )

    if "Pipeline Completo" in eval_mode:
        st.subheader("1. Procesamiento End-to-End desde Texto de Currículum")
        col_cv_preset, col_profile_target = st.columns([2, 1])
        with col_cv_preset:
            selected_raw_cv = st.selectbox(
                "Cargar Currículum de Prueba:",
                list(SAMPLE_RAW_CVS.keys()),
            )
        with col_profile_target:
            target_profile_pipeline = st.selectbox(
                "Perfil Objetivo para Orden Canónico:",
                list(PROFILES_REGISTRY.keys()),
                format_func=lambda x: PROFILES_REGISTRY[x].title,
            )

        cv_input_text = st.text_area(
            "Texto del Currículum Vitae (Lenguaje Natural):",
            value=SAMPLE_RAW_CVS[selected_raw_cv],
            height=90,
        )

        # Checkbox to demonstrate why Stage 3 REQUIRES Stage 2
        skip_stage2 = st.checkbox(
            "⚠️ Demostración: Omitir Etapa 2 (Enviar tokens crudos sin normalizar directamente al Autómata)",
            value=False,
            help="Al activar esta casilla, los tokens crudos como 'JS' o 'React.js' entrarán directamente a tu autómata, provocando un rechazo inmediato hacia q_trap porque no pertenecen al alfabeto formal Sigma.",
        )

        # Stage 1: Extraction
        extraction = extract_qualifications(cv_input_text)
        
        # Stage 2: Normalization & Canonical Sorting
        normalization = normalize_and_sort(extraction.raw_tokens, profile_id=target_profile_pipeline)

        if skip_stage2:
            cleaned_tokens = extraction.raw_tokens
        else:
            cleaned_tokens = normalization.normalized_tokens

        # Visual Pipeline Cards
        pipe_c1, pipe_c2, pipe_c3 = st.columns(3)
        with pipe_c1:
            st.markdown("##### 📌 Etapa 1: Extracción (Regex)")
            st.caption("A cargo de Integrante 1 (Patrones en texto)")
            st.code(f"Tokens crudos:\n{extraction.raw_tokens}", language="python")
            if extraction.years_of_experience:
                st.caption(f"Experiencia detectada: {extraction.years_of_experience} años")

        with pipe_c2:
            st.markdown("##### 🔄 Etapa 2: Normalización (FST)")
            st.caption("A cargo de Integrante 1 (Transductores)")
            if skip_stage2:
                st.warning("⚠️ OMITIDA: Los tokens no fueron normalizados ni ordenados.")
            else:
                st.code(f"Tokens ordenados canónicamente:\n{normalization.normalized_tokens}", language="python")
                if normalization.transformations_applied:
                    st.caption(f"Transducciones: {normalization.transformations_applied}")

        with pipe_c3:
            st.markdown("##### 🎯 Etapa 3: Autómata DFA")
            st.caption("A cargo de Integrante 2 (Tu rol - pyformlang)")
            st.code(f"Secuencia evaluada:\n{cleaned_tokens}", language="python")

    else:
        st.subheader("1. Selección o Ingreso Directo de Tokens Normalizados")
        col_input_mode, col_tokens = st.columns([1, 2])

        with col_input_mode:
            selected_sample = st.selectbox(
                "Cargar Ejemplo Preconfigurado:",
                ["(Personalizado)"] + list(SAMPLE_RESUMES.keys()),
            )

            if selected_sample != "(Personalizado)":
                default_token_str = ", ".join(SAMPLE_RESUMES[selected_sample])
            else:
                default_token_str = "JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT"

        with col_tokens:
            input_text = st.text_area(
                "Secuencia de Tokens Normalizados (separados por coma o espacio):",
                value=default_token_str,
                help="Ingresa tokens en mayúscula según el orden canónico generado en la Etapa 2.",
                height=100,
            )

        # Clean and split tokens
        raw_tokens = [t.strip().upper() for t in input_text.replace("\n", " ").split(",") if t.strip()]
        cleaned_tokens: list[str] = []
        for chunk in raw_tokens:
            cleaned_tokens.extend([t for t in chunk.split() if t])

        st.write(f"**Tokens a evaluar ({len(cleaned_tokens)}):** `{cleaned_tokens}`")

    st.divider()

    # Classification Report
    st.subheader("2. Veredicto del Motor de Autómatas por Perfil")
    report = classifier.classify(cleaned_tokens)

    cols = st.columns(4)
    for idx, (pid, pdef) in enumerate(PROFILES_REGISTRY.items()):
        result = report.results_by_profile[pid]
        with cols[idx]:
            st.markdown(f"#### {pdef.title}")
            st.caption(f"Dominio: {pdef.domain}")
            if result.is_accepted:
                st.markdown('<span class="badge-accepted">✅ ACCEPTED</span>', unsafe_allow_html=True)
                st.success(f"Estado final: `{result.final_state}`")
            else:
                st.markdown('<span class="badge-rejected">❌ REJECTED</span>', unsafe_allow_html=True)
                st.error(f"Estado: `{result.final_state}`")
            
            with st.expander("Ver diagnóstico"):
                if result.is_accepted:
                    st.write("🎉 Cumple con todas las categorías obligatorias en orden canónico.")
                    st.write(f"**Categorías satisfechas:** {', '.join(result.satisfied_categories)}")
                else:
                    st.write(f"**Causa:** {result.rejection_reason}")
                    if result.missing_categories:
                        st.write(f"**Faltan:** {', '.join(result.missing_categories)}")

    st.divider()

    # Detailed DFA Inspector
    st.subheader("3. Trazabilidad de Estados y Diagnóstico (Trace)")
    selected_inspect_pid = st.selectbox(
        "Seleccionar perfil para inspeccionar la traza de estados en su DFA:",
        list(PROFILES_REGISTRY.keys()),
        format_func=lambda x: PROFILES_REGISTRY[x].title,
    )

    inspected_result = report.results_by_profile[selected_inspect_pid]
    inspected_auto = automata[selected_inspect_pid]

    # Status summary
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Estado Inicial", "q0")
    with col_stat2:
        st.metric("Estado Final Alcanzado", inspected_result.final_state)
    with col_stat3:
        st.metric("Estado de Aceptación Esperado", inspected_result.expected_final_state)

    col_chart, col_trace = st.columns([1.3, 1])
    with col_chart:
        st.markdown("##### Diagrama de Transición Interactivo (Graphviz)")
        st.caption("Verde = Ruta activa del candidato | Azul = Estados del DFA | Rojo = Estado trampa q_trap")
        chart_digraph = build_graphviz_diagram(inspected_auto, inspected_result)
        st.graphviz_chart(chart_digraph)

    with col_trace:
        st.markdown("##### Tabla de Ejecución Paso a Paso")
        if inspected_result.trace:
            trace_data = [
                {
                    "Paso": step.step_number,
                    "Estado Origen": step.source_state,
                    "Token Consumido": step.symbol,
                    "Estado Destino": step.target_state,
                    "Categoría": step.category or "N/A",
                    "¿Transición Válida?": "✅ Válida" if step.is_valid_transition else "❌ Violación (q_trap)",
                }
                for step in inspected_result.trace
            ]
            st.dataframe(trace_data, hide_index=True)
        else:
            st.warning("No se procesaron tokens (secuencia vacía).")

    # Optional Excalidraw diagram viewer
    diagram_path = PROJECT_ROOT / "docs" / "diagrams" / f"{selected_inspect_pid}.png"
    if diagram_path.exists():
        st.markdown("##### Diagrama Manual Adjunto (Excalidraw)")
        st.image(str(diagram_path), caption=f"Diagrama de {inspected_auto.profile.title}")


# ============================================================================
# Tab 2: Mathematical Formalization (5-Tuples)
# ============================================================================
with tab_formal:
    st.subheader("Formalización Matemática Rigurosa de los Autómatas")
    st.markdown(
        """
        Cada autómata está formalizado como un **Autómata Finito Determinista (DFA)**:
        $$\\mathcal{M} = (Q, \\Sigma, \\delta, q_0, F)$$
        Cumpliendo con los requerimientos teóricos de la **Etapa 3**.
        """
    )

    selected_formal_pid = st.selectbox(
        "Ver Formalización del Perfil:",
        list(PROFILES_REGISTRY.keys()),
        format_func=lambda x: f"{PROFILES_REGISTRY[x].title} ({PROFILES_REGISTRY[x].domain})",
        key="formal_selector",
    )

    f_auto = automata[selected_formal_pid]
    f_def = f_auto.profile
    f_tuple = f_auto.get_formal_tuple()

    c1, c2 = st.columns([1, 1.2])

    with c1:
        st.markdown(f"### {f_def.title}")
        st.write(f"**Dominio:** {f_def.domain}")
        st.write(
            f"**Orden Canónico:** "
            + " $\\to$ ".join([f"`{c.name}`" for c in f_def.canonical_categories])
        )

        st.markdown("#### 1. Conjunto de Estados ($Q$)")
        st.write(f"Total estados: **{len(f_tuple.states)}**")
        st.write(f"`{sorted(list(f_tuple.states))}`")

        st.markdown("#### 2. Alfabeto de Entrada ($\\Sigma$)")
        st.write(f"Contiene **{len(f_tuple.alphabet)}** símbolos terminales:")
        st.write(f"`{sorted(list(f_tuple.alphabet))}`")

        st.markdown("#### 3. Estado Inicial ($q_0$) y Aceptación ($F$)")
        st.write(f"- **Estado Inicial $q_0$:** `{f_tuple.initial_state}`")
        st.write(f"- **Estados de Aceptación $F$:** `{f_tuple.final_states}`")

    with c2:
        st.markdown("#### 4. Diagrama del Autómata (Graphviz)")
        formal_digraph = build_graphviz_diagram(f_auto, None)
        st.graphviz_chart(formal_digraph)

        diag_file = PROJECT_ROOT / "docs" / "diagrams" / f"{selected_formal_pid}.png"
        if diag_file.exists():
            st.markdown("#### Diagrama Manual (Excalidraw)")
            st.image(str(diag_file), caption=f"Diagrama Excalidraw - {f_def.title}")

    st.divider()
    st.markdown("#### 5. Tabla de Transiciones Formales $\\delta(q, s)$")
    trans_table = [
        {"Estado Origen (q)": src, "Símbolo (s)": sym, "Estado Destino (δ)": dst}
        for (src, sym), dst in sorted(f_tuple.transitions.items())
    ]
    st.dataframe(trans_table, hide_index=True)


# ============================================================================
# Tab 3: Unit Test Suite
# ============================================================================
with tab_tests:
    st.subheader("🧪 Ejecución de Pruebas Automatizadas (Pytest)")
    st.markdown(
        "Ejecuta en tiempo real la suite completa de pruebas unitarias (`tests/test_stage3.py`) "
        "para validar los casos de aceptación, rechazo, orden canónico y 5-tuplas."
    )

    if st.button("▶️ Ejecutar Pruebas con Pytest", type="primary"):
        import subprocess

        with st.spinner("Ejecutando pytest tests/test_stage3.py..."):
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_stage3.py", "-v"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )

        if proc.returncode == 0:
            st.success("✅ ¡Todas las pruebas pasaron satisfactoriamente!")
        else:
            st.error("❌ Se encontraron errores en la ejecución de pruebas.")

        st.code(proc.stdout, language="bash")


# ============================================================================
# Tab 4: About
# ============================================================================
with tab_about:
    st.subheader("ResumeLens: Formal Language-Based Resume Screening")
    st.markdown(
        """
        ### Resultados de Aprendizaje Evaluados (RAA):
        - **RAA1:** Aplicar expresiones regulares y teoría de autómatas en la solución de problemas de procesamiento de lenguaje y reconocimiento de patrones.
        - **RAA2:** Aplicar conceptos de gramáticas generativas en la implementación de sistemas de procesamiento de lenguajes especializados.
        - **RAA3:** Simplificar gramáticas mediante formas normales para el procesamiento y análisis eficiente de lenguajes.
        - **RAA6:** Comunicar con vocabulario y lenguaje especializado las ideas principales sobre los modelos computacionales estudiados y sus aplicaciones.

        ---
        ### Arquitectura del Pipeline:
        1. **Etapa 1:** Extracción con Expresiones Regulares (`re`).
        2. **Etapa 2:** Normalización y Orden Canónico con Transductores Finitos (FST).
        3. **Etapa 3:** **Reconocimiento de Patrones de Cualificación con Autómatas Finitos (`pyformlang`)**.
        4. **Etapa 4:** Lenguaje DSL de Especificación con Gramáticas Libres de Contexto (`textX`) y renderizado HTML.
        """
    )
