# ResumeLens — interfaz React recuperada de Figma Make

Diseño y componentes recuperados del archivo `Responsive web interface for ResumeLens.make`.
Se conserva la apariencia profesional de la interfaz, reemplazando su simulación TypeScript
por el motor Python existente. No se necesitan las herramientas internas de Figma para ejecutarla.

## Ejecutar la aplicación

Requisitos: Python con las dependencias del repositorio, Node.js 22.12+ o 24 y pnpm.
Desde la raíz del repositorio:

```powershell
python -m pip install -r requirements.txt
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
python -m src.web_api.server
```

Abrir `http://127.0.0.1:8000`. El servidor sirve la interfaz compilada y la API
desde el mismo origen. No hay que arrancar Vite para usar esta versión.

Para desarrollo, mantener el servidor Python anterior abierto y ejecutar en otra terminal:

```powershell
pnpm --dir frontend dev
```

Vite sirve `http://127.0.0.1:5173` y redirige `/api` al motor Python en el puerto 8000.
El parámetro `--port` del servidor Python permite cambiar el puerto de la versión compilada.
Para desarrollo con otro puerto, actualizar también el proxy en `vite.config.ts`.

## Contrato de integración

- `GET /api/profiles`: alfabetos, estados, estado inicial, estados finales, transiciones
  completas y requisitos obligatorios/alternativos, obtenidos de los modelos Python.
- `POST /api/evaluate`: JSON `{ "mode": "resume" | "tokens", "text": "..." }`.
  Devuelve resultados de los cuatro perfiles, secuencias, categorías observadas,
  requisitos faltantes, habilidades ajenas y trazas con los nombres reales de estados.
- En currículo, se ejecuta el catálogo compartido de expresiones regulares de la etapa 1;
  los términos ambiguos se restringen a la sección de habilidades y se conserva el match
  más largo en solapamientos (por ejemplo, GitHub Actions frente a GitHub).
- La normalización reutiliza la tabla de referencia de la etapa 2. El FST formal
  y la DSL de la etapa 4 siguen pendientes y la interfaz lo indica.
- En tokens, el orden y los símbolos se evalúan estrictamente; no se normalizan ni filtran.
- Toda la clasificación se ejecuta con `pyformlang`. El frontend solo presenta resultados
  y dibuja la tabla de transiciones recibida; no mantiene otro motor de reconocimiento.

Los currículos se procesan en memoria, no se guardan y no se envían a Figma.
El servidor escucha en loopback y está destinado a uso y demostración locales.

## Verificación

```powershell
python -m pytest -q
pnpm --dir frontend build
```

Los casos de integración HTTP están en `tests/test_web_api.py`.
La interfaz Streamlit anterior sigue disponible mediante su comando habitual.
