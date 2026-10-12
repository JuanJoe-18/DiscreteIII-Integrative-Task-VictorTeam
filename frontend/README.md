# `frontend/` — React interface

A responsive React + TypeScript interface (built with Vite) recovered from the Figma Make design *Responsive web interface for ResumeLens*. It keeps the professional look of the design but replaces its TypeScript simulation with the real Python engine: **every result shown comes from the Python pipeline**, through the local JSON API in `src/web_api/server.py`. No Figma tools are needed to run it.

## Files

| Path | Contents |
|---|---|
| `index.html`, `src/main.tsx` | Entry point |
| `src/App.tsx` | Layout, navigation (Evaluate résumé · Explore automata · About), candidate card, examples, requirements panel |
| `src/screens/EvaluateScreen.tsx` | Résumé / token input, per-profile results, processing details |
| `src/screens/ExploreScreen.tsx` | DFA diagram, formal definition (Q, Σ, δ, q0, F), δ table and execution table |
| `src/screens/AboutScreen.tsx` | Project summary and pipeline status |
| `src/components/ProfileOutput.tsx` | Stage 4 panel: view/edit the DSL, validate it, preview and download the HTML |
| `src/components/Diagram.tsx` | SVG drawing of a DFA with the evaluated path highlighted |
| `src/components/ui.tsx`, `src/components/Icon.tsx` | Small UI components and icons |
| `src/services/resumeService.ts` | Calls to the API (`/api/profiles`, `/api/evaluate`, `/api/validate-profile`) |
| `src/services/engine.ts` | Types of the API responses and presentation helpers (no recognition logic) |
| `src/data/examples.ts` | Demonstration résumés (English, plus one Spanish résumé) and a direct-token example |
| `src/data/profiles.ts` | Profile catalog type; filled from `/api/profiles` |
| `vite.config.ts`, `tsconfig.json`, `package.json`, `pnpm-lock.yaml` | Build configuration |

## Running

Requirements: Python with the repository dependencies, Node.js 22.12+ or 24, and pnpm. From the repository root:

```powershell
python -m pip install -r requirements.txt
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
python -m src.web_api.server
```

Open `http://127.0.0.1:8000`. The Python server serves the built interface and the API from the same origin, so Vite does not need to run.

For development, keep the Python server running and start Vite in another terminal:

```powershell
pnpm --dir frontend dev
```

Vite serves `http://127.0.0.1:5173` and proxies `/api` to the Python engine on port 8000. The `--port` option of the Python server changes the port of the built version; for development with another port, update the proxy in `vite.config.ts` too.

## Integration contract

- `GET /api/profiles`: alphabets, states, initial state, accepting states, complete transitions and required/alternative requirements, taken from the Python models.
- `POST /api/evaluate` with JSON `{ "mode": "resume" | "tokens", "text": "..." }` returns, for the four profiles, the evaluated sequences, observed categories, missing requirements, foreign skills and traces with the real state names.
- In résumé mode the API runs Stage 1 (`extract_qualifications`), including section boundaries and the exclusion of technologies inside contact data; there is no second skill extractor. `candidate` keeps `name`, `contact` (lists of email, phone, linkedin and github), `education`, `job_titles` and `years_of_experience` (integer or null). The labels `Name:`/`Nombre:` and `Description:`/`Descripción:` fill the candidate card.
- Normalization and per-profile order run the Stage 2 FSTs. Each DFA receives the projection of the sorted sequence on its alphabet; foreign skills are kept in `foreign` and unknown ones remain visible in `normalized`.
- `profileDocument` contains `{validated: true, dsl, html, profile}`: the DSL generated from the extracted data and the real DFA results, validated by textX before the HTML is produced. In token mode this field is `null`.
- `POST /api/validate-profile` with JSON `{ "text": "candidate { ... }" }` returns the validated document, or HTTP 400 with `error`, `kind`, `line` and `column`. It checks structure and domain rules; it does not reclassify declarations.
- Editing the DSL invalidates the previous preview and disables the HTML download; only the response for the current revision can enable them again. The preview uses a sandboxed iframe, and the standalone HTML escapes all candidate text.
- In token mode the order and the symbols are evaluated strictly; they are not normalized or filtered.
- All classification runs in `pyformlang`. The frontend only presents results and draws the transition table it receives.

Résumés are processed in memory, are not stored and are not sent to Figma. The server listens on loopback and is meant for local use and demonstration.

## Verification

```powershell
python -m pytest -q
pnpm --dir frontend build
```

HTTP integration cases are in `tests/test_web_api.py` and `tests/test_web_stage4.py`. The Streamlit interface (`src/ui/app.py`) remains available with its usual command.
