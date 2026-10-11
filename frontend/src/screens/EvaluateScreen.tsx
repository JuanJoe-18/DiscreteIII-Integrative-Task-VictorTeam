import { useState } from 'react'
import { EXAMPLES } from '../data/examples'
import { PROFILES } from '../data/profiles'
import { stateName, type Evaluation, type ProfileResult } from '../services/engine'
import { Button, Card, Chip, EngineNotice, StatusBadge } from '../components/ui'
import Icon from '../components/Icon'

export type Mode = 'resume' | 'tokens'
type Props = {
  mode: Mode; setMode: (m: Mode) => void
  resumeText: string; setResumeText: (s: string) => void
  tokenText: string; setTokenText: (s: string) => void
  status: 'idle' | 'loading' | 'done' | 'error'; error?: string; evaluation?: Evaluation
  onEvaluate: () => void; onLoadExample: (id: string) => void
  selectedProfile: string; onSelectProfile: (id: string) => void; onOpenAutomaton: (id: string) => void
}

export default function EvaluateScreen(p: Props) {
  const tabs: { id: Mode; label: string }[] = [{ id: 'resume', label: 'Hoja de vida' }, { id: 'tokens', label: 'Tokens normalizados' }]
  return (
    <div className="space-y-3">
      <Card>
        <div className="px-5 pt-4">
          <h1 className="text-[20px] font-semibold text-[#1d1d1d]">Evaluar currículo</h1>
          <p className="mt-0.5 text-[14px] text-[#666]">Reconoce si las habilidades explícitas cumplen patrones profesionales. No asigna puntuaciones ni recomienda candidatos.</p>
        </div>
        <div role="tablist" aria-label="Modo de entrada" className="mt-3 flex border-b border-[#e0dfdc] px-3">
          {tabs.map((t) => (
            <button key={t.id} role="tab" aria-selected={p.mode === t.id} aria-controls={`panel-${t.id}`} id={`tab-${t.id}`} onClick={() => p.setMode(t.id)}
              className={`-mb-px border-b-2 px-3 py-2.5 text-[14px] font-semibold ${p.mode === t.id ? 'border-[#0a66c2] text-[#0a66c2]' : 'border-transparent text-[#666] hover:text-[#1d1d1d]'}`}>
              {t.label}
            </button>
          ))}
        </div>
        <form className="p-5" onSubmit={(e) => { e.preventDefault(); p.onEvaluate() }}>
          {p.mode === 'resume' ? (
            <div id="panel-resume" role="tabpanel" aria-labelledby="tab-resume" className="space-y-3">
              <div className="flex flex-wrap items-end justify-between gap-2">
                <label htmlFor="resume" className="text-[14px] font-semibold text-[#1d1d1d]">Texto de la hoja de vida</label>
                <label className="flex items-center gap-2 text-[13px] text-[#666]">
                  Ejemplo
                  <select className="rounded-md border border-[#8c8c8c] bg-white px-2 py-1 text-[13px] text-[#1d1d1d]" value="" onChange={(e) => e.target.value && p.onLoadExample(e.target.value)}>
                    <option value="">Elegir…</option>
                    {EXAMPLES.filter((e) => e.mode === 'resume').map((e) => <option key={e.id} value={e.id}>{e.title}</option>)}
                  </select>
                </label>
              </div>
              <textarea id="resume" value={p.resumeText} onChange={(e) => p.setResumeText(e.target.value)} rows={11}
                placeholder="Pega aquí el texto del currículo: perfil, experiencia y habilidades…"
                className="w-full resize-y rounded-md border border-[#8c8c8c] p-3 text-[15px] leading-relaxed text-[#1d1d1d] placeholder:text-[#8c8c8c]" aria-describedby="resume-help" />
              <p id="resume-help" className="text-[13px] text-[#666]">
                Se analizan solo las habilidades técnicas explícitas (lenguajes, frameworks, bases de datos, herramientas). El nombre y la descripción se usan únicamente para la tarjeta del candidato si aparecen como <span className="font-mono">Nombre:</span> y <span className="font-mono">Descripción:</span>.
              </p>
            </div>
          ) : (
            <div id="panel-tokens" role="tabpanel" aria-labelledby="tab-tokens" className="space-y-3">
              <label htmlFor="tokens" className="text-[14px] font-semibold text-[#1d1d1d]">Secuencia de símbolos separados por comas</label>
              <input id="tokens" value={p.tokenText} onChange={(e) => p.setTokenText(e.target.value)} placeholder="JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT"
                className="w-full rounded-md border border-[#8c8c8c] px-3 py-2 font-mono text-[14px] text-[#1d1d1d]" aria-describedby="tokens-help" />
              <div id="tokens-help" className="rounded-md bg-[#f3f2ef] p-3 text-[13px] text-[#404040]">
                <p><strong>Importante:</strong> este modo evalúa la secuencia exactamente como se escribe; no corrige su orden. Un símbolo fuera de orden o ajeno al alfabeto del perfil provoca el rechazo.</p>
                <p className="mt-1">Ejemplo: <button type="button" className="font-mono font-semibold text-[#0a66c2] hover:underline" onClick={() => p.setTokenText('JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT')}>JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT</button></p>
              </div>
            </div>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={p.status === 'loading'}>
              {p.status === 'loading' ? <><span className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white" aria-hidden="true" /> Evaluando…</> : <><Icon name="play" className="size-4" /> Evaluar currículo</>}
            </Button>
            <EngineNotice />
          </div>
        </form>
      </Card>
      <Results {...p} />
    </div>
  )
}

function Results(p: Props) {
  if (p.status === 'loading')
    return (
      <Card className="p-5" aria-label="Procesando">
        <p className="text-[14px] font-semibold text-[#1d1d1d]" role="status">Procesando: extracción → normalización → reconocimiento…</p>
        <div className="mt-4 space-y-3" aria-hidden="true">{[0, 1, 2].map((i) => <div key={i} className="h-16 animate-pulse rounded-md bg-[#f3f2ef]" />)}</div>
      </Card>
    )
  if (p.status === 'error')
    return (
      <Card className="flex gap-3 border-[#b24020]/50 p-5" aria-label="Error">
        <Icon name="alert" className="size-6 shrink-0 text-[#b24020]" />
        <div role="alert"><p className="font-semibold text-[#8f2f12]">No se pudo evaluar</p><p className="mt-0.5 text-[14px] text-[#404040]">{p.error}</p></div>
      </Card>
    )
  if (!p.evaluation)
    return (
      <Card className="px-5 py-10 text-center" aria-label="Sin resultados">
        <Icon name="doc" className="mx-auto size-9 text-[#8c8c8c]" />
        <p className="mt-2 font-semibold text-[#1d1d1d]">Aún no hay resultados</p>
        <p className="mx-auto mt-1 max-w-md text-[14px] text-[#666]">Pega una hoja de vida o elige un ejemplo y pulsa “Evaluar currículo”. Verás los cuatro perfiles y el recorrido de cada autómata.</p>
      </Card>
    )
  const ev = p.evaluation
  const ok = ev.results.filter((r) => r.accepted)
  return (
    <>
      <Card className="p-5" aria-labelledby="sum-title">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 id="sum-title" className="text-[18px] font-semibold">Resumen</h2>
          <EngineNotice />
        </div>
        <p className="mt-1 text-[15px] text-[#404040]">
          {ok.length ? <>Patrones cumplidos: <strong>{ok.map((r) => PROFILES.find((x) => x.id === r.profileId)!.name).join(', ')}</strong>.</> : 'Ningún patrón profesional se cumple con esta entrada.'}
          {ok.length > 1 && ' Un candidato puede cumplir varios perfiles a la vez.'}
        </p>
        <p className="mt-1 text-[13px] text-[#666]">Modo: {ev.mode === 'resume' ? 'hoja de vida (orden canónico por perfil)' : 'tokens directos (orden tal como se escribió)'}.</p>
      </Card>
      <div className="space-y-3">
        {ev.results.map((r) => <ResultCard key={r.profileId} r={r} selected={p.selectedProfile === r.profileId} onSelect={() => p.onSelectProfile(r.profileId)} onOpen={() => p.onOpenAutomaton(r.profileId)} />)}
      </div>
      <Processing ev={ev} />
    </>
  )
}

function ResultCard({ r, selected, onSelect, onOpen }: { r: ProfileResult; selected: boolean; onSelect: () => void; onOpen: () => void }) {
  const [open, setOpen] = useState(false)
  const prof = PROFILES.find((x) => x.id === r.profileId)!
  return (
    <Card as="article" className={`p-5 ${selected ? 'ring-2 ring-[#0a66c2]' : ''}`} aria-label={prof.name}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-[16px] font-semibold text-[#1d1d1d]">
            <button className="text-left hover:text-[#0a66c2] hover:underline" onClick={onSelect} aria-pressed={selected}>{prof.name}</button>
          </h3>
          <p className="text-[13px] text-[#666]">Estado final: <span className="font-mono">{stateName(r.finalState)}</span></p>
        </div>
        <StatusBadge accepted={r.accepted} />
      </div>
      <div className="mt-3 space-y-2 text-[14px]">
        <div>
          <p className="text-[13px] font-semibold text-[#404040]">Competencias observadas</p>
          <div className="mt-1 flex flex-wrap gap-1.5">{r.observed.length ? r.observed.flatMap((o) => o.tokens).map((t) => <Chip key={t}>{t}</Chip>) : <span className="text-[#666]">Ninguna</span>}</div>
        </div>
        {r.missing.length > 0 && (
          <div>
            <p className="text-[13px] font-semibold text-[#404040]">Requisitos obligatorios faltantes</p>
            <div className="mt-1 flex flex-wrap gap-1.5">{r.missing.map((m) => <Chip key={m} tone="warn">Falta: {m}</Chip>)}</div>
          </div>
        )}
        {r.reason && <p className="rounded-md bg-[#f3f2ef] px-3 py-2 text-[#404040]"><strong>Motivo de rechazo:</strong> {r.reason}</p>}
      </div>
      <button className="mt-3 inline-flex items-center gap-1 text-[14px] font-semibold text-[#0a66c2] hover:underline" aria-expanded={open} onClick={() => setOpen(!open)}>
        Ver detalles <Icon name="chevron" className={`size-4 transition ${open ? 'rotate-90' : ''}`} />
      </button>
      {open && (
        <div className="mt-3 space-y-3 border-t border-[#e0dfdc] pt-3 text-[14px]">
          <div>
            <p className="text-[13px] font-semibold text-[#404040]">Secuencia evaluada</p>
            <p className="mt-1 break-words rounded-md bg-[#f3f2ef] px-3 py-2 font-mono text-[13px]">{r.sequence.length ? r.sequence.join(' · ') : 'ε (vacía)'}</p>
          </div>
          <details className="rounded-md border border-[#e0dfdc] px-3 py-2">
            <summary className="cursor-pointer text-[13px] font-semibold text-[#404040]">Habilidades ajenas a este perfil ({r.foreign.length})</summary>
            <div className="mt-2 flex flex-wrap gap-1.5">{r.foreign.length ? r.foreign.map((t) => <Chip key={t}>{t}</Chip>) : <span className="text-[#666]">Ninguna</span>}</div>
          </details>
          <Button variant="secondary" onClick={onOpen}><Icon name="graph" className="size-4" /> Ver recorrido en el autómata</Button>
        </div>
      )}
    </Card>
  )
}

function Processing({ ev }: { ev: Evaluation }) {
  return (
    <Card>
      <details className="group">
        <summary className="flex cursor-pointer items-center justify-between px-5 py-4 text-[16px] font-semibold">
          <span className="flex items-center gap-2"><Icon name="list" /> Ver procesamiento</span>
          <Icon name="chevron" className="size-5 transition group-open:rotate-90" />
        </summary>
        <ol className="space-y-4 border-t border-[#e0dfdc] px-5 py-4 text-[14px]">
          <li>
            <p className="font-semibold">1. Fragmentos extraídos</p>
            {ev.mode === 'tokens' ? <p className="text-[#666]">No aplica: el modo directo recibe símbolos ya normalizados.</p> : (
              <div className="mt-1 flex flex-wrap gap-1.5">{ev.fragments.map((f, i) => <span key={i} className="rounded border border-[#e0dfdc] px-2 py-0.5 text-[13px]">“{f.text}” → <span className="font-mono">{f.token}</span></span>)}</div>
            )}
          </li>
          <li>
            <p className="font-semibold">2. Habilidades normalizadas</p>
            <p className="mt-1 break-words font-mono text-[13px]">{ev.normalized.join(', ')}</p>
          </li>
          <li>
            <p className="font-semibold">3. Secuencia preparada para cada perfil</p>
            <ul className="mt-1 space-y-1">{ev.results.map((r) => <li key={r.profileId}><span className="text-[#666]">{PROFILES.find((x) => x.id === r.profileId)!.name}:</span> <span className="font-mono text-[13px]">{r.sequence.join(' · ') || 'ε'}</span></li>)}</ul>
          </li>
          <li>
            <p className="font-semibold">4. Resultado del reconocimiento</p>
            <ul className="mt-1 space-y-1">{ev.results.map((r) => <li key={r.profileId}>{PROFILES.find((x) => x.id === r.profileId)!.name}: <strong>{r.accepted ? 'aceptada' : 'rechazada'}</strong> en <span className="font-mono">{stateName(r.finalState)}</span></li>)}</ul>
          </li>
        </ol>
      </details>
    </Card>
  )
}
