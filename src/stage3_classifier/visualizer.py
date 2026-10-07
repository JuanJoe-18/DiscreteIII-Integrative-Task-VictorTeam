"""Automata visualization module for ResumeLens.

Generates:
1. Mermaid diagram syntax (for Markdown documentation and reports).
2. Graphviz DOT representations (for interactive rendering in Streamlit).
3. Path-highlighted Graphviz charts showing the exact trace traversed by a candidate.
"""

from typing import List, Optional
from src.stage3_classifier.automata_models import ProfileAutomaton
from src.stage3_classifier.classifier import ProfileEvaluationResult


def generate_mermaid_diagram(automaton: ProfileAutomaton) -> str:
    """Generates Mermaid stateDiagram-v2 representation for the given automaton."""
    lines = ["stateDiagram-v2", "    [*] --> q0"]
    categories = automaton.profile.canonical_categories

    # Transition from q0 to q1
    c1 = categories[0]
    c1_sample = ", ".join(sorted(list(c1.skills))[:3])
    lines.append(f"    q0 --> q_{c1.name.lower()} : {c1.name} ({c1_sample})")

    # Intermediate transitions
    for i, cat in enumerate(categories):
        curr_state = f"q_{cat.name.lower()}"
        lines.append(f"    {curr_state} --> {curr_state} : {cat.name} (self-loop)")

        if i + 1 < len(categories):
            next_cat = categories[i + 1]
            next_sample = ", ".join(sorted(list(next_cat.skills))[:3])
            lines.append(
                f"    {curr_state} --> q_{next_cat.name.lower()} : {next_cat.name} ({next_sample})"
            )

    # Final accept state
    final_state = f"q_{categories[-1].name.lower()}"
    lines.append(f"    {final_state} --> [*]")

    return "\n".join(lines)


def generate_graphviz_dot(
    automaton: ProfileAutomaton,
    result: Optional[ProfileEvaluationResult] = None,
) -> str:
    """Generates Graphviz DOT string for the automaton, optionally highlighting the evaluation trace."""
    profile = automaton.profile
    categories = profile.canonical_categories
    final_state_name = automaton.state_names[-1]

    # Collect visited states and transitions if result is provided
    visited_states = set()
    visited_transitions = set()  # (src, dst)
    trapped = False

    if result:
        visited_states.add("q0")
        for step in result.trace:
            visited_states.add(step.target_state)
            visited_transitions.add((step.source_state, step.target_state))
            if step.target_state == "q_trap":
                trapped = True

    dot = [
        "digraph DFA {",
        "    rankdir=LR;",
        '    node [fontname="Helvetica", fontsize=11, style=filled];',
        '    edge [fontname="Helvetica", fontsize=9];',
    ]

    # Invisible start arrow
    dot.append('    __start [shape=point, width=0.1, label=""];')
    dot.append('    __start -> q0 [color="#2563eb", penwidth=2.0];')

    # Draw states
    for sname in automaton.state_names:
        is_final = (sname == final_state_name)
        shape = "doublecircle" if is_final else "circle"

        # Node styling based on trace
        if result and sname in visited_states:
            if sname == final_state_name and result.is_accepted:
                # Accepted final state -> bright green
                fillcolor = "#86efac"
                color = "#16a34a"
                penwidth = "3.0"
            else:
                # Intermediate visited state -> soft blue
                fillcolor = "#bfdbfe"
                color = "#2563eb"
                penwidth = "2.0"
        else:
            fillcolor = "#f8fafc"
            color = "#64748b"
            penwidth = "1.5"

        dot.append(
            f'    {sname} [shape={shape}, fillcolor="{fillcolor}", color="{color}", penwidth={penwidth}];'
        )

    # Draw q_trap if visited
    if trapped:
        dot.append(
            '    q_trap [shape=circle, fillcolor="#fca5a5", color="#dc2626", penwidth=3.0, label="q_trap"];'
        )

    # Draw transitions by category to keep graph readable
    # 1. q0 -> first category
    c0 = categories[0]
    c0_label = f"{c0.name}\\n({', '.join(sorted(list(c0.skills))[:2])}...)"
    c0_active = ("q0", f"q_{c0.name.lower()}") in visited_transitions
    c0_color = "#16a34a" if c0_active else "#64748b"
    c0_width = "2.5" if c0_active else "1.0"
    dot.append(
        f'    q0 -> q_{c0.name.lower()} [label="{c0_label}", color="{c0_color}", penwidth={c0_width}];'
    )

    # 2. Category transitions & self-loops
    for i, cat in enumerate(categories):
        curr_state = f"q_{cat.name.lower()}"
        loop_active = (curr_state, curr_state) in visited_transitions
        loop_color = "#16a34a" if loop_active else "#94a3b8"
        loop_width = "2.5" if loop_active else "1.0"
        dot.append(
            f'    {curr_state} -> {curr_state} [label="{cat.name}*", color="{loop_color}", penwidth={loop_width}];'
        )

        if i + 1 < len(categories):
            next_cat = categories[i + 1]
            next_state = f"q_{next_cat.name.lower()}"
            next_label = f"{next_cat.name}\\n({', '.join(sorted(list(next_cat.skills))[:2])}...)"
            trans_active = (curr_state, next_state) in visited_transitions
            trans_color = "#16a34a" if trans_active else "#64748b"
            trans_width = "2.5" if trans_active else "1.0"
            dot.append(
                f'    {curr_state} -> {next_state} [label="{next_label}", color="{trans_color}", penwidth={trans_width}];'
            )

    # 3. If trapped, draw red transition into q_trap
    if trapped:
        for (src, dst) in visited_transitions:
            if dst == "q_trap":
                dot.append(
                    f'    {src} -> q_trap [label="REJECT (violation)", color="#dc2626", fontcolor="#dc2626", penwidth=2.5];'
                )

    dot.append("}")
    return "\n".join(dot)
