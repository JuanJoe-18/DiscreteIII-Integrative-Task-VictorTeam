"""Script to export all DFA transition diagrams into Graphviz DOT files, SVG/PNG images, and an offline interactive HTML viewer."""

import sys
from pathlib import Path
import json
import urllib.request
import urllib.parse

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.stage3_classifier.automata_models import build_all_automata
from src.stage3_classifier.visualizer import build_graphviz_diagram


def export_diagrams() -> None:
    diagrams_dir = PROJECT_ROOT / "docs" / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)

    automata = build_all_automata()
    profiles_data = {}

    print("==================================================")
    print("Generando diagramas de autómatas con Graphviz...")
    print("==================================================")

    for pid, auto in automata.items():
        digraph = build_graphviz_diagram(auto, None)
        dot_path = diagrams_dir / f"{pid}.dot"
        dot_source = digraph.source
        dot_path.write_text(dot_source, encoding="utf-8")
        print(f" -> Generado archivo DOT: {dot_path.relative_to(PROJECT_ROOT)}")

        # Fetch / render SVG and PNG vector images
        svg_path = diagrams_dir / f"{pid}.svg"
        png_path = diagrams_dir / f"{pid}.png"

        try:
            # Download SVG
            svg_url = "https://quickchart.io/graphviz?format=svg&graph=" + urllib.parse.quote(dot_source)
            req_svg = urllib.request.Request(svg_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_svg, timeout=15) as resp:
                svg_content = resp.read().decode("utf-8")
                svg_path.write_text(svg_content, encoding="utf-8")
                print(f" -> Generado archivo SVG: {svg_path.relative_to(PROJECT_ROOT)}")

            # Download PNG
            png_url = "https://quickchart.io/graphviz?format=png&graph=" + urllib.parse.quote(dot_source)
            req_png = urllib.request.Request(png_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_png, timeout=15) as resp:
                png_path.write_bytes(resp.read())
                print(f" -> Generado archivo PNG: {png_path.relative_to(PROJECT_ROOT)}")
        except Exception as err:
            print(f" [!] Aviso: No se pudo renderizar imagen remota ({err}). El archivo .dot está disponible.")
            svg_content = ""

        profiles_data[pid] = {
            "title": auto.profile.title,
            "domain": auto.profile.domain,
            "dot": dot_source,
            "svg": svg_content if svg_path.exists() else "",
            "png_file": f"{pid}.png",
            "svg_file": f"{pid}.svg",
            "dot_file": f"{pid}.dot",
        }

    # Generate a 100% self-contained, offline HTML viewer (No external WASM/CORS issues)
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ResumeLens - Diagramas de Autómatas Finitos (DFA)</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header {{
      background: #1e293b;
      padding: 1.25rem 2rem;
      border-bottom: 1px solid #334155;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    h1 {{ font-size: 1.35rem; font-weight: 700; color: #38bdf8; }}
    .subtitle {{ font-size: 0.85rem; color: #94a3b8; }}
    .nav-tabs {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}
    .tab-btn {{
      background: #334155;
      color: #cbd5e1;
      border: 1px solid #475569;
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      font-size: 0.9rem;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s ease;
    }}
    .tab-btn:hover {{ background: #475569; color: #fff; }}
    .tab-btn.active {{
      background: #2563eb;
      color: #fff;
      border-color: #3b82f6;
      box-shadow: 0 0 10px rgba(37, 99, 235, 0.4);
    }}
    main {{
      flex: 1;
      padding: 1.5rem 2rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .info-bar {{
      background: #1e293b;
      padding: 0.75rem 1.25rem;
      border-radius: 0.5rem;
      border-left: 4px solid #38bdf8;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.9rem;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}
    .graph-container {{
      flex: 1;
      background: #ffffff;
      border-radius: 0.75rem;
      padding: 1.5rem;
      overflow: auto;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 550px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}
    .graph-container svg {{
      max-width: 100%;
      height: auto;
    }}
    .graph-container img {{
      max-width: 100%;
      height: auto;
      display: block;
    }}
    .footer-tools {{
      display: flex;
      gap: 0.75rem;
      align-items: center;
    }}
    .btn-action {{
      background: #1e293b;
      color: #94a3b8;
      border: 1px solid #334155;
      padding: 0.4rem 0.8rem;
      border-radius: 0.375rem;
      font-size: 0.8rem;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease;
    }}
    .btn-action:hover {{ background: #334155; color: #fff; }}
    .zoom-hint {{ font-size: 0.75rem; color: #64748b; margin-left: 0.5rem; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>ResumeLens - Visualizador de Autómatas Finitos (DFA)</h1>
      <p class="subtitle">Estructuras Discretas III - Etapa 3 (Motor de Lógica Formal)</p>
    </div>
    <div class="nav-tabs" id="tabButtons"></div>
  </header>

  <main>
    <div class="info-bar">
      <span id="profileTitle">Cargando autómata...</span>
      <div class="footer-tools">
        <a id="downloadPngLink" class="btn-action" href="#" download>Descargar PNG</a>
        <a id="downloadSvgLink" class="btn-action" href="#" download>Descargar SVG</a>
        <a id="downloadDotLink" class="btn-action" href="#" download>Descargar .DOT</a>
        <a id="onlineViewerLink" class="btn-action" href="https://dreampuf.github.io/GraphvizOnline/" target="_blank">Abrir en Graphviz Online</a>
      </div>
    </div>

    <div class="graph-container" id="graphContainer">
      <!-- El diagrama SVG o imagen se inyecta aquí -->
    </div>
  </main>

  <script>
    const data = {json.dumps(profiles_data, ensure_ascii=False)};
    const tabContainer = document.getElementById("tabButtons");
    const graphContainer = document.getElementById("graphContainer");
    const profileTitle = document.getElementById("profileTitle");
    const downloadPngLink = document.getElementById("downloadPngLink");
    const downloadSvgLink = document.getElementById("downloadSvgLink");
    const downloadDotLink = document.getElementById("downloadDotLink");
    const onlineViewerLink = document.getElementById("onlineViewerLink");

    let currentPid = Object.keys(data)[0];

    // Setup tabs
    Object.keys(data).forEach((pid, idx) => {{
      const btn = document.createElement("button");
      btn.className = "tab-btn" + (idx === 0 ? " active" : "");
      btn.textContent = data[pid].title;
      btn.onclick = () => switchProfile(pid);
      tabContainer.appendChild(btn);
    }});

    function renderCurrent() {{
      const info = data[currentPid];
      profileTitle.innerHTML = `<strong>${{info.title}}</strong> (${{info.domain}}) &bull; <em>Una arista por símbolo; rango numérico \\d colapsado</em>`;
      
      downloadPngLink.href = info.png_file;
      downloadPngLink.download = info.png_file;
      
      downloadSvgLink.href = info.svg_file;
      downloadSvgLink.download = info.svg_file;

      downloadDotLink.href = info.dot_file;
      downloadDotLink.download = info.dot_file;

      onlineViewerLink.href = "https://dreampuf.github.io/GraphvizOnline/#" + encodeURIComponent(info.dot);

      if (info.svg && info.svg.trim().length > 0) {{
        graphContainer.innerHTML = info.svg;
      }} else {{
        graphContainer.innerHTML = `<img src="${{info.png_file}}" alt="Diagrama de ${{info.title}}">`;
      }}
    }}

    function switchProfile(pid) {{
      currentPid = pid;
      Array.from(tabContainer.children).forEach((btn, idx) => {{
        btn.classList.toggle("active", Object.keys(data)[idx] === pid);
      }});
      renderCurrent();
    }}

    // Initial render
    renderCurrent();
  </script>
</body>
</html>
"""
    html_path = diagrams_dir / "ver_diagramas.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f" -> Generado visor interactivo HTML (100% autónomo y offline): {html_path.relative_to(PROJECT_ROOT)}")
    print("==================================================")


if __name__ == "__main__":
    export_diagrams()
