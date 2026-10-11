"""Diagrams derived from the actual complete pyformlang transition table."""
from typing import Optional
import graphviz
from src.stage3_classifier.automata_models import ProfileAutomaton
from src.stage3_classifier.classifier import ProfileEvaluationResult


def build_graphviz_diagram(automaton: ProfileAutomaton,
                           result: Optional[ProfileEvaluationResult] = None) -> graphviz.Digraph:
    formal = automaton.get_formal_tuple()
    dot = graphviz.Digraph(name=f"DFA_{automaton.profile.profile_id}", format="svg")
    dot.attr(rankdir="LR")
    dot.attr("node", fontname="Helvetica", fontsize="11", style="filled")
    dot.attr("edge", fontname="Helvetica", fontsize="9")
    dot.node("__start", shape="point", label="")
    dot.edge("__start", formal.initial_state)
    active = {(step.source_state, step.symbol, step.target_state)
              for step in result.trace} if result else set()
    visited = {formal.initial_state} | {dst for _, _, dst in active}
    for state in sorted(formal.states):
        color = "#f8fafc"
        if result and state in visited:
            color = "#fca5a5" if state == "q_trap" else "#bfdbfe"
            if state in formal.final_states and result.is_accepted:
                color = "#86efac"
        dot.node(state, shape="doublecircle" if state in formal.final_states else "circle",
                 fillcolor=color)
    trap_sources = set()
    for (source, symbol), target in sorted(formal.transitions.items()):
        if target == "q_trap":
            trap_sources.add(source)
            continue
        highlighted = (source, symbol, target) in active
        dot.edge(source, target, label=symbol,
                 color="#16a34a" if highlighted else "#64748b",
                 penwidth="2.5" if highlighted else "1.0")
    # Exact complement of the outgoing non-trap symbols in Sigma.
    for source in sorted(trap_sources):
        highlighted = any(src == source and dst == "q_trap" for src, _, dst in active)
        dot.edge(source, "q_trap", label="Σ" if source == "q_trap" else "other symbols of Σ",
                 color="#dc2626" if highlighted else "#94a3b8", style="dashed")
    # External symbols are rejected before delta (they are outside its domain).
    for source, symbol, target in sorted(active):
        if symbol not in formal.alphabet:
            dot.edge(source, target, label=f"{symbol} (outside Σ)", color="#dc2626")
    return dot


def generate_graphviz_dot(automaton: ProfileAutomaton,
                          result: Optional[ProfileEvaluationResult] = None) -> str:
    return build_graphviz_diagram(automaton, result).source


def generate_mermaid_diagram(automaton: ProfileAutomaton) -> str:
    formal = automaton.get_formal_tuple()
    lines = ["stateDiagram-v2", f"    [*] --> {formal.initial_state}"]
    for (source, symbol), target in sorted(formal.transitions.items()):
        lines.append(f"    {source} --> {target} : {symbol}")
    for state in sorted(formal.final_states):
        lines.append(f"    {state} --> [*]")
    return "\n".join(lines)
