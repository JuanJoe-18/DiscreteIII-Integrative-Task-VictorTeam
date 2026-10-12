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
import streamlit.components.v1 as components
import graphviz
from src.pipeline import process_resume
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
    page_title="ResumeLens | Formal Language Engine",
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
    "Wednesday Addams (Full Stack - Accepted)": [
        "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"
    ],
    "Wednesday Addams (Full Stack - With 3 years of experience)": [
        "EXPERIENCE_PRESENT", "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"
    ],
    "Mary Jane Watson (Machine Learning - Accepted)": [
        "PYTHON", "PANDAS", "NUMPY", "SCIKIT_LEARN", "TENSORFLOW", "SQL", "GIT"
    ],
    "Alex Murphy (Cloud & DevOps - Accepted)": [
        "BASH", "LINUX", "GITHUB_ACTIONS", "DOCKER", "KUBERNETES", "AWS", "TERRAFORM", "GIT"
    ],
    "Ada Lovelace (Data Scientist - Accepted)": [
        "PYTHON", "PANDAS", "NUMPY", "SEABORN", "PLOTLY", "SCIKIT_LEARN", "GIT"
    ],
    "Incomplete candidate (Rejected - missing backend and VCS)": [
        "JAVASCRIPT", "REACT", "POSTGRESQL"
    ],
    "Out-of-order candidate (Rejected - Git before backend)": [
        "JAVASCRIPT", "GIT", "NODE_JS", "POSTGRESQL"
    ],
    "Mixed candidate (Rejected - foreign token)": [
        "JAVASCRIPT", "NODE_JS", "SCIKIT_LEARN", "GIT"
    ],
}

SAMPLE_RAW_CVS = {
    "Wednesday Addams (Full Stack - assignment example)": (
        "Wednesday Addams 3 years of experience developing web applications. "
        "Technical Skills: JS, React.js, NodeJS, Postgres, Git."
    ),
    "Mary Jane Watson (Machine Learning - assignment example)": (
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
    "Unnormalized candidate (rejected if Stage 2 is skipped)": (
        "Junior Web Developer. Technical Skills: JS, React.js, Postgres."
    ),
}

# ============================================================================
# Sidebar
# ============================================================================
with st.sidebar:
    st.title("ResumeLens")
    st.caption("Computación y Estructuras Discretas III — Integrative Task")
    st.divider()

    st.subheader("📌 System overview")
    st.markdown(
        """
        - **Stage 1:** regular expressions (`re`)
        - **Stage 2:** finite-state transducers (`pyformlang`)
        - **Stage 3:** deterministic finite automata (`pyformlang`)
        - **Stage 4:** context-free grammar / DSL (`textX`)
        - **Supported profiles:** 4 (2 software, 2 AI/data)
        """
    )
    st.divider()

    st.subheader("👤 Team")
    st.info("Víctor Team — Víctor Cardona, Juan José Aponza, Juancho31g")


# ============================================================================
# Main Header
# ============================================================================
st.markdown('<div class="main-header">🔍 ResumeLens: Formal Classification Engine</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Recognition of professional qualification patterns with deterministic finite automata (DFA) in <code>pyformlang</code>.</div>',
    unsafe_allow_html=True,
)

# Tabs
tab_eval, tab_formal, tab_tests, tab_about = st.tabs([
    "🚀 Résumé evaluator",
    "📐 Mathematical formalization (5-tuples)",
    "🧪 Test suite",
    "📖 About the project",
])

# ============================================================================
# Tab 1: Live Candidate Screening
# ============================================================================
with tab_eval:
    eval_mode = st.radio(
        "Evaluation mode:",
        [
            "🔗 Full pipeline (résumé ➔ Regex ➔ FST ➔ DFA ➔ DSL / HTML)",
            "🎯 Direct mode (input tokens for Stage 3)",
        ],
        horizontal=True,
    )

    skip_stage2 = False
    if "Full pipeline" in eval_mode:
        st.subheader("1. End-to-end processing of résumé text")
        col_cv_preset, col_profile_target = st.columns([2, 1])
        with col_cv_preset:
            selected_raw_cv = st.selectbox(
                "Load a sample résumé:",
                list(SAMPLE_RAW_CVS.keys()),
            )
        with col_profile_target:
            target_profile_pipeline = st.selectbox(
                "Target profile for the canonical order:",
                list(PROFILES_REGISTRY.keys()),
                format_func=lambda x: PROFILES_REGISTRY[x].title,
            )

        cv_input_text = st.text_area(
            "Résumé text (natural language):",
            value=SAMPLE_RAW_CVS[selected_raw_cv],
            height=90,
        )
        if not cv_input_text.strip():
            st.info("Write a résumé to run the pipeline.")
            st.stop()

        # Checkbox to demonstrate why Stage 3 REQUIRES Stage 2
        skip_stage2 = st.checkbox(
            "⚠️ Demonstration: skip Stage 2 (send raw, unnormalized tokens directly to the automata)",
            value=False,
            help="When checked, raw tokens such as 'JS' or 'React.js' go directly into the automata and are rejected immediately (q_trap) because they do not belong to the alphabet Sigma.",
        )

        # Stage 1: Extraction
        extraction = extract_qualifications(cv_input_text)
        
        # Stage 2: Normalization & Canonical Sorting
        normalization = normalize_and_sort(
            extraction.raw_tokens,
            profile_id=target_profile_pipeline,
            years_of_experience=extraction.years_of_experience,
        )

        if skip_stage2:
            cleaned_tokens = extraction.raw_tokens
        else:
            cleaned_tokens = normalization.normalized_tokens

        # Visual Pipeline Cards
        pipe_c1, pipe_c2, pipe_c3 = st.columns(3)
        with pipe_c1:
            st.markdown("##### 📌 Stage 1: Extraction (Regex)")
            st.caption("Patterns and section boundaries")
            st.code(f"Raw tokens:\n{extraction.raw_tokens}", language="python")
            if extraction.years_of_experience is not None:
                st.caption(f"Detected experience: {extraction.years_of_experience} years")

        with pipe_c2:
            st.markdown("##### 🔄 Stage 2: Normalization (FST)")
            st.caption("Cascade of pyformlang transducers")
            if skip_stage2:
                st.warning("⚠️ SKIPPED: the tokens were neither normalized nor sorted.")
            else:
                st.code(f"Canonically sorted tokens:\n{normalization.normalized_tokens}", language="python")
                if normalization.transformations_applied:
                    st.caption(f"Transductions: {normalization.transformations_applied}")

        with pipe_c3:
            st.markdown("##### 🎯 Stage 3: DFA")
            st.caption("Each profile receives its own projection and canonical order")
            preview = cleaned_tokens if skip_stage2 else [t for t in cleaned_tokens if t in automata[target_profile_pipeline].profile.alphabet]
            st.code(f"Sequence for the selected profile:\n{preview}", language="python")

    else:
        st.subheader("1. Select or type normalized tokens")
        col_input_mode, col_tokens = st.columns([1, 2])

        with col_input_mode:
            selected_sample = st.selectbox(
                "Load a preset example:",
                ["(Custom)"] + list(SAMPLE_RESUMES.keys()),
            )

            if selected_sample != "(Custom)":
                default_token_str = ", ".join(SAMPLE_RESUMES[selected_sample])
            else:
                default_token_str = "JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT"

        with col_tokens:
            input_text = st.text_area(
                "Sequence of normalized tokens (separated by commas or spaces):",
                value=default_token_str,
                help="Type uppercase tokens in the canonical order produced by Stage 2.",
                height=100,
            )

        # Clean and split tokens
        raw_tokens = [t.strip() for t in input_text.replace("\n", " ").split(",") if t.strip()]
        cleaned_tokens: list[str] = []
        for chunk in raw_tokens:
            cleaned_tokens.extend([t for t in chunk.split() if t])

        st.write(f"**Tokens to evaluate ({len(cleaned_tokens)}):** `{cleaned_tokens}`")

    st.divider()

    # Classification Report
    st.subheader("2. Verdict of the automata per profile")
    pipeline_result = None
    if "Full pipeline" in eval_mode and not skip_stage2:
        try:
            pipeline_result = process_resume(cv_input_text, classifier=classifier)
        except ValueError as error:
            st.error(str(error))
            st.stop()
        report = pipeline_result.classification
    else:
        report = classifier.classify(cleaned_tokens, prepare_input=False)

    cols = st.columns(4)
    for idx, (pid, pdef) in enumerate(PROFILES_REGISTRY.items()):
        result = report.results_by_profile[pid]
        with cols[idx]:
            st.markdown(f"#### {pdef.title}")
            st.caption(f"Domain: {pdef.domain}")
            if result.is_accepted:
                st.markdown('<span class="badge-accepted">✅ ACCEPTED</span>', unsafe_allow_html=True)
                st.success(f"Final state: `{result.final_state}`")
            else:
                st.markdown('<span class="badge-rejected">❌ REJECTED</span>', unsafe_allow_html=True)
                st.error(f"State: `{result.final_state}`")
            
            with st.expander("Show diagnosis"):
                st.write(f"**Profile sequence:** {result.evaluated_tokens}")
                if result.ignored_tokens:
                    st.write(f"**Skills outside this profile:** {result.ignored_tokens}")
                if result.is_accepted:
                    st.write("🎉 Meets every mandatory category in canonical order.")
                    st.write(f"**Observed categories:** {', '.join(result.satisfied_categories)}")
                else:
                    st.write(f"**Reason:** {result.rejection_reason}")
                    if result.missing_categories:
                        st.write(f"**Missing requirements:** {', '.join(result.missing_categories)}")

    st.divider()

    # Detailed DFA Inspector
    st.subheader("3. State trace and diagnosis")
    selected_inspect_pid = st.selectbox(
        "Select a profile to inspect the state trace in its DFA:",
        list(PROFILES_REGISTRY.keys()),
        format_func=lambda x: PROFILES_REGISTRY[x].title,
    )

    inspected_result = report.results_by_profile[selected_inspect_pid]
    inspected_auto = automata[selected_inspect_pid]

    # Status summary
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Initial state", "q0")
    with col_stat2:
        st.metric("Final state reached", inspected_result.final_state)
    with col_stat3:
        st.metric("Expected accepting state", inspected_result.expected_final_state)

    col_chart, col_trace = st.columns([1.3, 1])
    with col_chart:
        st.markdown("##### Transition diagram (Graphviz)")
        st.caption("Green = candidate path | Blue = DFA states | Red = trap state q_trap")
        chart_digraph = build_graphviz_diagram(inspected_auto, inspected_result)
        st.graphviz_chart(chart_digraph)

    with col_trace:
        st.markdown("##### Step-by-step execution table")
        if inspected_result.trace:
            trace_data = [
                {
                    "Step": step.step_number,
                    "Source state": step.source_state,
                    "Token read": step.symbol,
                    "Target state": step.target_state,
                    "Category": step.category or "N/A",
                    "Valid transition?": "✅ Valid" if step.is_valid_transition else "❌ Violation (q_trap)",
                }
                for step in inspected_result.trace
            ]
            st.dataframe(trace_data, hide_index=True)
        else:
            st.warning("No tokens were processed (empty sequence).")

    # Optional Excalidraw diagram viewer
    diagram_path = PROJECT_ROOT / "docs" / "diagrams" / f"{selected_inspect_pid}.png"
    if diagram_path.exists():
        st.markdown("##### Diagram exported from the DFA")
        st.image(str(diagram_path), caption=f"Diagram of {inspected_auto.profile.title}")


    if pipeline_result is not None:
        st.divider()
        st.subheader("4. Structured profile validated with textX")
        document = pipeline_result.document
        st.caption("Missing data is omitted. Job titles are not used to infer employers or dates.")
        with st.expander("Show the generated DSL"):
            st.code(document.dsl, language="text")
        col_dsl, col_html = st.columns(2)
        with col_dsl:
            st.download_button("Download DSL", document.dsl, file_name="candidate.resume", mime="text/plain")
        with col_html:
            st.download_button("Download validated HTML", document.html, file_name="candidate.html", mime="text/html")
        if hasattr(st, 'iframe'):
            st.iframe(document.html, height=620, alt="Validated candidate profile")
        else:
            # Compatibility with the older Streamlit versions allowed by requirements.
            components.html(document.html, height=620, scrolling=True)


# ============================================================================
# Tab 2: Mathematical Formalization (5-Tuples)
# ============================================================================
with tab_formal:
    st.subheader("Mathematical formalization of the automata")
    st.markdown(
        """
        Each automaton is formalized as a **deterministic finite automaton (DFA)**:
        $$\\mathcal{M} = (Q, \\Sigma, \\delta, q_0, F)$$
        as required by **Stage 3** of the assignment.
        """
    )

    selected_formal_pid = st.selectbox(
        "Show the formalization of profile:",
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
        st.write(f"**Domain:** {f_def.domain}")
        st.write(
            f"**Canonical order:** "
            + " $\\to$ ".join([f"`{c.name}`" for c in f_def.canonical_categories])
        )

        st.markdown("#### 1. Set of states ($Q$)")
        st.write(f"Number of states: **{len(f_tuple.states)}**")
        st.write(f"`{sorted(list(f_tuple.states))}`")

        st.markdown("#### 2. Input alphabet ($\\Sigma$)")
        st.write(f"It contains **{len(f_tuple.alphabet)}** symbols:")
        st.write(f"`{sorted(list(f_tuple.alphabet))}`")

        st.markdown("#### 3. Initial state ($q_0$) and accepting states ($F$)")
        st.write(f"- **Initial state $q_0$:** `{f_tuple.initial_state}`")
        st.write(f"- **Accepting states $F$:** `{f_tuple.final_states}`")

    with c2:
        st.markdown("#### 4. Diagram of the automaton (Graphviz)")
        formal_digraph = build_graphviz_diagram(f_auto, None)
        st.graphviz_chart(formal_digraph)

        diag_file = PROJECT_ROOT / "docs" / "diagrams" / f"{selected_formal_pid}.png"
        if diag_file.exists():
            st.markdown("#### Diagram exported from the DFA")
            st.image(str(diag_file), caption=f"DFA diagram - {f_def.title}")

    st.divider()
    st.markdown("#### 5. Transition table $\\delta(q, s)$")
    trans_table = [
        {"Source state (q)": src, "Symbol (s)": sym, "Target state (δ)": dst}
        for (src, sym), dst in sorted(f_tuple.transitions.items())
    ]
    st.dataframe(trans_table, hide_index=True)


# ============================================================================
# Tab 3: Unit Test Suite
# ============================================================================
with tab_tests:
    st.subheader("🧪 Automated tests (pytest)")
    st.markdown(
        "Runs the complete test suite (`tests`) in real time: acceptance, rejection, "
        "canonical order, formal tuples, grammar and end-to-end scenarios."
    )

    if st.button("▶️ Run the tests with pytest", type="primary"):
        import subprocess

        with st.spinner("Running pytest tests..."):
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "tests", "-v"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )

        if proc.returncode == 0:
            st.success("✅ All tests passed.")
        else:
            st.error("❌ Some tests failed.")

        st.code(proc.stdout, language="bash")


# ============================================================================
# Tab 4: About
# ============================================================================
with tab_about:
    st.subheader("ResumeLens: Formal Language-Based Resume Screening")
    st.markdown(
        """
        ### Learning outcomes assessed (RAA)
        - **RAA1:** Apply regular expressions and automata theory to solve language-processing and pattern-recognition problems.
        - **RAA2:** Apply generative-grammar concepts to implement specialized language-processing systems.
        - **RAA3:** Simplify grammars with normal forms for efficient language processing and analysis.
        - **RAA6:** Communicate, with specialized vocabulary, the main ideas of the computational models studied and their applications.

        ---
        ### Pipeline architecture
        1. **Stage 1:** extraction with regular expressions (`re`).
        2. **Stage 2:** normalization and canonical order with finite-state transducers (FST).
        3. **Stage 3:** **qualification-pattern recognition with finite automata (`pyformlang`)**.
        4. **Stage 4:** candidate specification DSL with a context-free grammar (`textX`) and HTML rendering.
        """
    )
