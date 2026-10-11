import { useEffect, useRef, useState } from 'react'
import { EXAMPLES } from './data/examples'
import { PROFILES, setProfiles } from './data/profiles'
import type { Evaluation } from './services/engine'
import { resumeService, loadProfiles } from './services/resumeService'
import { Card, Chip } from './components/ui'
import Icon from './components/Icon'
import EvaluateScreen, { type Mode } from './screens/EvaluateScreen'
import ExploreScreen from './screens/ExploreScreen'
import AboutScreen from './screens/AboutScreen'

type Section = 'evaluate' | 'explore' | 'about'
const NAV: { id: Section; label: string; short: string; icon: string }[] = [
  { id: 'evaluate', label: 'Evaluar currículo', short: 'Evaluar', icon: 'doc' },
  { id: 'explore', label: 'Explorar autómatas', short: 'Autómatas', icon: 'graph' },
  { id: 'about', label: 'Acerca del proyecto', short: 'Acerca', icon: 'info' },
]

export default function App() {
  const [section, setSection] = useState<Section>('evaluate')
  const [mode, setMode] = useState<Mode>('resume')
  const [resumeText, setResumeText] = useState('')
  const [tokenText, setTokenText] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [error, setError] = useState<string>()
  const [evaluation, setEvaluation] = useState<Evaluation>()
  const [profileId, setProfileId] = useState('full_stack')
  const [expanded, setExpanded] = useState(false)
  const [exampleId, setExampleId] = useState<string>()

  const [ready, setReady] = useState(false)
  const [connectionError, setConnectionError] = useState<string>()
  const [attempt, setAttempt] = useState(0)
  const requestId = useRef(0)
  useEffect(() => {
    let disposed = false
    setConnectionError(undefined)
    loadProfiles().then((profiles) => {
      if (!disposed) { setProfiles(profiles); setReady(true) }
    }).catch((error: Error) => { if (!disposed) setConnectionError(error.message) })
    return () => { disposed = true }
  }, [attempt])
  function resetEvaluation() {
    requestId.current++; setStatus('idle'); setEvaluation(undefined); setError(undefined)
  }
  async function evaluate() {
    const id = ++requestId.current
    setStatus('loading'); setError(undefined)
    try {
      const ev = mode === 'resume' ? await resumeService.evaluateResume(resumeText) : await resumeService.evaluateTokens(tokenText)
      if (id === requestId.current) { setEvaluation(ev); setStatus('done') }
    } catch (e) {
      if (id === requestId.current) { setEvaluation(undefined); setError((e as Error).message); setStatus('error') }
    }
  }
  function loadExample(id: string) {
    const ex = EXAMPLES.find((e) => e.id === id)!
    setExampleId(id); setMode(ex.mode); setSection('evaluate')
    if (ex.mode === 'resume') setResumeText(ex.content); else setTokenText(ex.content)
    resetEvaluation()
  }
  if (!ready) return <div className="min-h-screen bg-[#f3f2ef] p-8 text-[#1d1d1d]">
    <Card className="mx-auto max-w-xl p-6"><h1 className="text-xl font-semibold text-[#0a66c2]">ResumeLens</h1>
      <p className="mt-3" role={connectionError ? 'alert' : 'status'}>{connectionError ?? 'Conectando con los autómatas Python…'}</p>
      {connectionError && <button className="mt-4 rounded-full bg-[#0a66c2] px-4 py-2 text-white" onClick={() => setAttempt(attempt + 1)}>Reintentar conexión</button>}
    </Card></div>
  const sides = !(section === 'explore' && expanded) && section !== 'about'
  const profile = PROFILES.find((p) => p.id === profileId)!

  return (
    <div className="min-h-screen bg-[#f3f2ef] pb-16 text-[#1d1d1d] md:pb-0">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2">Saltar al contenido</a>
      <header className="sticky top-0 z-30 border-b border-[#e0dfdc] bg-white">
        <div className="mx-auto flex h-[52px] max-w-[1128px] items-center justify-between px-4">
          <button onClick={() => setSection('evaluate')} className="flex items-center gap-2 rounded" aria-label="ResumeLens, inicio">
            <span className="grid size-8 place-items-center rounded bg-[#0a66c2] text-[14px] font-bold text-white" aria-hidden="true">RL</span>
            <span className="text-[18px] font-bold tracking-tight text-[#0a66c2]">ResumeLens</span>
          </button>
          <nav aria-label="Principal" className="hidden md:block">
            <ul className="flex">
              {NAV.map((n) => (
                <li key={n.id}>
                  <button onClick={() => setSection(n.id)} aria-current={section === n.id ? 'page' : undefined}
                    className={`flex h-[52px] w-[120px] flex-col items-center justify-center border-b-2 text-[12px] ${section === n.id ? 'border-[#1d1d1d] text-[#1d1d1d]' : 'border-transparent text-[#666] hover:text-[#1d1d1d]'}`}>
                    <Icon name={n.icon} className="size-6" />{n.label}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      <div className={`mx-auto grid max-w-[1128px] gap-6 px-4 py-6 ${sides ? 'lg:grid-cols-[225px_minmax(0,1fr)_300px]' : ''} ${section === 'explore' && expanded ? 'max-w-[1400px]' : ''}`}>
        {sides && (
          <aside className="space-y-3" aria-label="Candidato y ejemplos">
            <CandidateCard evaluation={evaluation} />
            <Card className="p-4" aria-labelledby="ex-title">
              <h2 id="ex-title" className="text-[14px] font-semibold">Ejemplos demostrativos</h2>
              <ul className="mt-2 space-y-1">
                {EXAMPLES.map((e) => (
                  <li key={e.id}>
                    <button onClick={() => loadExample(e.id)} aria-pressed={exampleId === e.id}
                      className={`w-full rounded-md px-2 py-1.5 text-left text-[14px] ${exampleId === e.id ? 'bg-[#eaf3fc] font-semibold text-[#004182]' : 'text-[#404040] hover:bg-[#f3f2ef]'}`}>
                      {e.title}
                      <span className="block text-[12px] font-normal text-[#666]">{e.mode === 'resume' ? 'Hoja de vida' : 'Tokens directos'}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </Card>
          </aside>
        )}

        <main id="main" className="order-first min-w-0 lg:order-none">
          {section === 'evaluate' && (
            <EvaluateScreen mode={mode} setMode={(value) => { setMode(value); resetEvaluation() }} resumeText={resumeText} setResumeText={(value) => { setResumeText(value); resetEvaluation() }} tokenText={tokenText} setTokenText={(value) => { setTokenText(value); resetEvaluation() }}
              status={status} error={error} evaluation={evaluation} onEvaluate={evaluate} onLoadExample={loadExample}
              selectedProfile={profileId} onSelectProfile={setProfileId} onOpenAutomaton={(id) => { setProfileId(id); setSection('explore') }} />
          )}
          {section === 'explore' && <ExploreScreen profileId={profileId} onSelectProfile={setProfileId} evaluation={evaluation} expanded={expanded} onToggleExpand={() => setExpanded(!expanded)} />}
          {section === 'about' && <AboutScreen />}
        </main>

        {sides && (
          <aside className="space-y-3" aria-label="Explicación y requisitos">
            <Card className="p-4" aria-labelledby="how">
              <h2 id="how" className="text-[14px] font-semibold">Cómo se procesa</h2>
              <ol className="mt-2 space-y-2 text-[13px] text-[#404040]">
                <li><strong>1. Extracción.</strong> Expresiones regulares localizan habilidades explícitas.</li>
                <li><strong>2. Normalización.</strong> La tabla de referencia convierte cada variante en un símbolo (p. ej. NODE_JS).</li>
                <li><strong>3. Orden canónico.</strong> En hoja de vida, cada perfil recibe solo sus símbolos, ordenados por categoría. Los demás no lo invalidan.</li>
                <li><strong>4. Reconocimiento.</strong> El DFA del perfil acepta o rechaza la secuencia.</li>
              </ol>
              <p className="mt-3 text-[12px] text-[#666]">En modo directo la secuencia se evalúa tal cual: desorden o símbolos externos llevan al estado trampa.</p>
            </Card>
            <Card className="p-4" aria-labelledby="req">
              <h2 id="req" className="text-[14px] font-semibold">Requisitos · {profile.name}</h2>
              <label className="sr-only" htmlFor="req-sel">Perfil</label>
              <select id="req-sel" value={profileId} onChange={(e) => setProfileId(e.target.value)} className="mt-2 w-full rounded-md border border-[#8c8c8c] bg-white px-2 py-1 text-[13px]">
                {PROFILES.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <ol className="mt-3 space-y-2">
                {profile.categories.map((c) => (
                  <li key={c.id} className="text-[13px]">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-[#1d1d1d]">{c.label}</span>
                      <span className={`max-w-[110px] text-right text-[10px] font-semibold uppercase ${c.required ? 'text-[#0a66c2]' : 'text-[#666]'}`}>{c.requirement}</span>
                    </div>
                    <p className="font-mono text-[11px] text-[#666]">{c.tokens.join(', ')}</p>
                  </li>
                ))}
              </ol>
            </Card>
          </aside>
        )}
      </div>

      <nav aria-label="Principal móvil" className="fixed inset-x-0 bottom-0 z-30 border-t border-[#e0dfdc] bg-white md:hidden">
        <ul className="grid grid-cols-3">
          {NAV.map((n) => (
            <li key={n.id}>
              <button onClick={() => setSection(n.id)} aria-current={section === n.id ? 'page' : undefined}
                className={`flex w-full flex-col items-center py-2 text-[11px] ${section === n.id ? 'text-[#0a66c2] font-semibold' : 'text-[#666]'}`}>
                <Icon name={n.icon} className="size-6" />{n.short}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}

function CandidateCard({ evaluation }: { evaluation?: Evaluation }) {
  const c = evaluation?.candidate ?? {}
  const initials = c.name ? c.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase() : ''
  return (
    <Card className="overflow-hidden" aria-label="Resumen del candidato">
      <div className="h-14 bg-[#a0b4c8]" aria-hidden="true" />
      <div className="-mt-8 px-4 pb-4">
        <div className="grid size-16 place-items-center rounded-full border-2 border-white bg-[#dce6f1] text-[20px] font-semibold text-[#004182]" aria-hidden="true">
          {initials || <svg viewBox="0 0 24 24" className="size-9 text-[#8ea6bf]" fill="currentColor"><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7z" /></svg>}
        </div>
        <p className={`mt-2 text-[16px] font-semibold ${c.name ? '' : 'text-[#8c8c8c]'}`}>{c.name ?? 'Nombre no indicado'}</p>
        <p className={`text-[13px] ${c.description ? 'text-[#404040]' : 'text-[#8c8c8c]'}`}>{c.description ?? (evaluation?.mode === 'tokens' ? 'Modo tokens: sin datos personales.' : 'Descripción no indicada')}</p>
        <div className="mt-3 border-t border-[#e0dfdc] pt-3">
          <p className="text-[12px] font-semibold text-[#666]">Habilidades detectadas</p>
          <div className="mt-1.5 flex flex-wrap gap-1">{evaluation?.normalized.length ? evaluation.normalized.map((t) => <Chip key={t}>{t}</Chip>) : <span className="text-[13px] text-[#8c8c8c]">—</span>}</div>
        </div>
      </div>
    </Card>
  )
}
