"""Automata visualization module for ResumeLens using python-graphviz.

Generates:
1. graphviz.Digraph object with individual edges per symbol (except range \\d).
2. Graphviz DOT representations for Streamlit and documentation.
3. Path-highlighted execution traces showing active paths taken by candidates.
"""

from typing import Dict, List, Optional, Set, Tuple
import graphviz

from src.stage3_classifier.automata_models import ProfileAutomaton
from src.stage3_classifier.classifier import ProfileEvaluationResult


def build_graphviz_diagram(
    automaton: ProfileAutomaton,
    result: Optional[ProfileEvaluationResult] = None,
) -> graphviz.Digraph:
    """Builds a graphviz.Digraph with an edge for each symbol (except numeric range \\d)."""
    profile = automaton.profile
    pid = profile.profile_id
    final_state_name = automaton.state_names[-1]

    dot = graphviz.Digraph(
        name=f"DFA_{pid}",
        format="svg",
        engine="dot",
    )
    dot.attr(rankdir="LR")
    dot.attr("node", fontname="Helvetica", fontsize="11", style="filled")
    dot.attr("edge", fontname="Helvetica", fontsize="9")

    # Start indicator
    dot.node("__start", shape="point", width="0.1", label="")
    dot.edge("__start", "q0", color="#2563eb", penwidth="2.0")

    # Collect trace info
    visited_states: Set[str] = set()
    active_transitions: Set[Tuple[str, str, str]] = set()  # (src, sym, dst)
    trapped = False

    if result:
        visited_states.add("q0")
        for step in result.trace:
            visited_states.add(step.target_state)
            active_transitions.add((step.source_state, step.symbol, step.target_state))
            if step.target_state == "q_trap":
                trapped = True

    # Draw states
    for sname in automaton.state_names:
        is_final = (sname == final_state_name)
        shape = "doublecircle" if is_final else "circle"

        if result and sname in visited_states:
            if sname == final_state_name and result.is_accepted:
                fillcolor = "#86efac"
                color = "#16a34a"
                penwidth = "3.0"
            else:
                fillcolor = "#bfdbfe"
                color = "#2563eb"
                penwidth = "2.0"
        else:
            fillcolor = "#f8fafc"
            color = "#64748b"
            penwidth = "1.5"

        dot.node(sname, shape=shape, fillcolor=fillcolor, color=color, penwidth=penwidth)

    # Draw q_trap if reached
    if trapped:
        dot.node(
            "q_trap",
            shape="circle",
            fillcolor="#fca5a5",
            color="#dc2626",
            penwidth="3.0",
            label="q_trap",
        )

    # Group experience digits into single range edge \d to avoid 10 identical parallel lines
    exp_digits = {"\\d", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
    handled_ranges: Set[Tuple[str, str]] = set()

    # Draw transitions from pyformlang DFA: ONE EDGE PER SYMBOL
    for src_state_obj, sym_dict in automaton.dfa._transition_function._transitions.items():
        src_name = str(src_state_obj.value)
        for sym_obj, dst_state_obj in sym_dict.items():
            sym_name = str(sym_obj.value)
            dst_name = str(dst_state_obj.value)

            # Special case: Numeric range \d (group digits into single edge "\d (1..9 años)")
            if pid == "full_stack" and sym_name in exp_digits and (src_name, dst_name) in [
                ("q0", "q_experience"),
                ("q_experience", "q_experience"),
            ]:
                pair = (src_name, dst_name)
                if pair not in handled_ranges:
                    handled_ranges.add(pair)
                    # Check if any active step used this range
                    range_active = any(
                        (s, token, d) in active_transitions
                        for (s, token, d) in active_transitions
                        if s == src_name and d == dst_name and token in exp_digits
                    )
                    edge_color = "#16a34a" if range_active else "#64748b"
                    edge_width = "2.5" if range_active else "1.0"
                    lbl = r"\d (1..9 años exp)" if src_name != dst_name else r"\d*"
                    dot.edge(src_name, dst_name, label=lbl, color=edge_color, penwidth=edge_width)
                continue

            # Standard case: ONE EDGE PER SYMBOL
            is_active = (src_name, sym_name, dst_name) in active_transitions
            edge_color = "#16a34a" if is_active else "#94a3b8"
            edge_width = "2.2" if is_active else "1.0"
            font_color = "#15803d" if is_active else "#334155"

            dot.edge(
                src_name,
                dst_name,
                label=sym_name,
                color=edge_color,
                fontcolor=font_color,
                penwidth=edge_width,
            )

    # Draw trap transition if trapped
    if trapped and result:
        for step in result.trace:
            if step.target_state == "q_trap":
                dot.edge(
                    step.source_state,
                    "q_trap",
                    label=f"{step.symbol} (REJECT)",
                    color="#dc2626",
                    fontcolor="#dc2626",
                    penwidth="2.5",
                )

    return dot


def generate_graphviz_dot(
    automaton: ProfileAutomaton,
    result: Optional[ProfileEvaluationResult] = None,
) -> str:
    """Generates the DOT source code string from the Graphviz Digraph."""
    digraph = build_graphviz_diagram(automaton, result)
    return digraph.source


def generate_mermaid_diagram(automaton: ProfileAutomaton) -> str:
    """Generates Mermaid stateDiagram-v2 representation for the given automaton."""
    lines = ["stateDiagram-v2", "    [*] --> q0"]
    categories = automaton.profile.canonical_categories

    for i, cat in enumerate(categories):
        curr_state = f"q_{cat.name.lower()}"
        lines.append(f"    {curr_state} --> {curr_state} : {cat.name} (self-loop)")

        if i + 1 < len(categories):
            next_cat = categories[i + 1]
            lines.append(f"    {curr_state} --> q_{next_cat.name.lower()} : {next_cat.name}")

    final_state = f"q_{categories[-1].name.lower()}"
    lines.append(f"    {final_state} --> [*]")
    return "\n".join(lines)
