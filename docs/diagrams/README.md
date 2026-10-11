# Diagramas de los DFA

Estos archivos se generan desde las transiciones reales de `pyformlang`, mediante:

```powershell
python scripts/export_diagrams.py
```

Cada perfil incluye DOT, SVG y PNG. `ver_diagramas.html` permite verlos sin conexión.
Las aristas sólidas muestran los símbolos individuales. Una arista discontinua
«otros símbolos de Σ» agrupa exactamente los símbolos del alfabeto que no figuran
en las aristas sólidas del estado de origen; todos llevan a `q_trap`.
En `q_trap`, el bucle Σ incluye todo el alfabeto. El estado aceptor tiene doble círculo.
El exportador actual utiliza QuickChart para renderizar SVG/PNG y requiere conexión
al regenerarlos; los diagramas ya exportados y el visor funcionan sin conexión.
