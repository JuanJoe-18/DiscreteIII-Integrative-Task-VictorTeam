# DFA Diagrams

These files are generated from the real `pyformlang` transitions with:

```bash
python scripts/export_diagrams.py
```

Each profile has a DOT, an SVG and a PNG file. `ver_diagramas.html` shows them offline.
Solid edges show individual symbols. A dashed edge labelled "other symbols of Σ" groups
exactly the alphabet symbols that do not appear on the solid edges of the source state;
all of them lead to `q_trap`. On `q_trap` the loop Σ includes the whole alphabet.
The accepting state is drawn with a double circle.
The exporter renders SVG/PNG with the local Graphviz `dot` binary and falls back to the
QuickChart web service when `dot` is not installed (which then requires a connection).
