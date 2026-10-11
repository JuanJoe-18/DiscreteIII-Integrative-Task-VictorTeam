import { useState } from 'react'
import { PROFILES } from '../data/profiles'
import { delta, isFinal, stateName, START, TRAP, type Evaluation } from '../services/engine'
import { Card, StatusBadge } from '../components/ui'
import Diagram from '../components/Diagram'
import Icon from '../components/Icon'

type Props = { profileId: string; onSelectProfile: (id: string) => void; evaluation?: Evaluation; expanded: boolean; onToggleExpand: () => void }

export default function ExploreScreen({ profileId, onSelectProfile, evaluation, expanded, onToggleExpand }: Props) {
  const [view, setView] = useState<'diagram' | 'formal'>('diagram')
  const profile = PROFILES.find((p) => p.id === profileId)!
  const result = evaluation?.results.find((r) => r.profileId === profileId)
  const states = profile.states.filter((state) => state !== TRAP)

  return (
    <div className="space-y-3">
      <Card className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-[20px] font-semibold">Explorar autómatas</h1>
            <p className="mt-0.5 text-[14px] text-[#666]">Un DFA por perfil. Selecciona uno para ver su diagrama y su definición formal.</p>
          </div>
          <button onClick={onToggleExpand} aria-pressed={expanded} className="hidden items-center gap-1.5 rounded-full px-3 py-1.5 text-[14px] font-semibold text-[#0a66c2] ring-1 ring-[#0a66c2] hover:bg-[#eaf3fc] lg:inline-flex">
            <Icon name={expanded ? 'collapse' : 'expand'} className="size-4" /> {expanded ? 'Mostrar columnas' : 'Ampliar área'}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2" role="radiogroup" aria-label="Perfil">
          {PROFILES.map((p) => (
            <button key={p.id} role="radio" aria-checked={p.id === profileId} onClick={() => onSelectProfile(p.id)}
              className={`rounded-full px-3 py-1 text-[14px] font-semibold ring-1 ring-inset transition ${p.id === profileId ? 'bg-[#0a66c2] text-white ring-[#0a66c2]' : 'bg-white text-[#404040] ring-[#8c8c8c] hover:bg-[#f3f2ef]'}`}>
              {p.name}
            </button>
          ))}
        </div>
      </Card>

      <Card>
        <div role="tablist" aria-label="Vista" className="flex items-center justify-between border-b border-[#e0dfdc] px-3">
          <div className="flex">
            {(['diagram', 'formal'] as const).map((v) => (
              <button key={v} role="tab" aria-selected={view === v} onClick={() => setView(v)}
                className={`-mb-px border-b-2 px-3 py-2.5 text-[14px] font-semibold ${view === v ? 'border-[#0a66c2] text-[#0a66c2]' : 'border-transparent text-[#666] hover:text-[#1d1d1d]'}`}>
                {v === 'diagram' ? 'Diagrama' : 'Definición formal'}
              </button>
            ))}
          </div>
          {result && <div className="hidden sm:block"><StatusBadge accepted={result.accepted} /></div>}
        </div>
        {view === 'diagram' ? <Diagram key={profileId} profile={profile} steps={result?.steps} /> : (
          <div className="space-y-5 p-5 text-[14px]">
            <p className="font-mono text-[16px]">M<sub>{profile.id}</sub> = (Q, Σ, δ, q0, F)</p>
            <dl className="grid gap-3 sm:grid-cols-[120px_1fr]">
              <dt className="font-semibold">Q (estados)</dt><dd className="font-mono">{'{'}{[...states.map(stateName), TRAP].join(', ')}{'}'}</dd>
              <dt className="font-semibold">Σ (alfabeto)</dt>
              <dd><ul className="space-y-1">{profile.categories.map((c) => <li key={c.id}><span className="text-[#666]">{c.label}:</span> <span className="font-mono text-[13px]">{c.tokens.join(', ')}</span></li>)}</ul></dd>
              <dt className="font-semibold">q0 (inicial)</dt><dd className="font-mono">q0</dd>
              <dt className="font-semibold">F (finales)</dt><dd className="font-mono">{'{'}{states.filter((s) => isFinal(profile, s)).map(stateName).join(', ')}{'}'}</dd>
            </dl>
            <div>
              <h2 className="font-semibold">Tabla de transiciones δ</h2>
              <p className="text-[13px] text-[#666]">Cada columna representa los símbolos de esa categoría. Fuera de Σ se rechaza antes de aplicar δ. → inicial, * final.</p>
              <div className="mt-2 overflow-x-auto">
                <table className="w-full min-w-max border-collapse text-[13px]">
                  <thead><tr className="bg-[#f3f2ef]"><th className="border border-[#e0dfdc] px-2 py-1.5 text-left">Estado</th>{profile.categories.map((c) => <th key={c.id} className="border border-[#e0dfdc] px-2 py-1.5 text-left">{c.short}</th>)}<th className="border border-[#e0dfdc] px-2 py-1.5 text-left">Fuera de Σ</th></tr></thead>
                  <tbody className="font-mono">
                    {[...states, TRAP].map((s) => (
                      <tr key={s}>
                        <th scope="row" className="border border-[#e0dfdc] px-2 py-1.5 text-left">{s === START ? '→ ' : ''}{isFinal(profile, s) ? '* ' : ''}{stateName(s)}</th>
                        {profile.categories.map((_, c) => { const t = delta(profile, s, c); return <td key={c} className={`border border-[#e0dfdc] px-2 py-1.5 ${t === TRAP ? 'text-[#999]' : ''}`}>{stateName(t)}</td> })}
                        <td className="border border-[#e0dfdc] px-2 py-1.5 text-[#999]">{TRAP}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div>
              <h2 className="font-semibold">Patrón</h2>
              <p className="mt-1 text-[#404040]">{profile.description}</p>
              <p className="mt-1 text-[#404040]">Lenguaje reconocido por el modelo Python. + exige una o más habilidades; * permite omitir una categoría; | expresa alternativas.</p>
              <p className="mt-2 font-mono text-[13px]">{profile.pattern}</p>
            </div>
          </div>
        )}
      </Card>

      <Card aria-labelledby="exec-title">
        <div className="px-5 pt-4">
          <h2 id="exec-title" className="text-[16px] font-semibold">Tabla de ejecución</h2>
          <p className="text-[13px] text-[#666]">{result ? <>Secuencia: <span className="font-mono">{result.sequence.join(' · ') || 'ε'}</span></> : 'Evalúa un currículo o una secuencia para ver el recorrido paso a paso.'}</p>
        </div>
        {result && (
          <div className="mt-3 overflow-x-auto px-5 pb-5">
            <table className="w-full min-w-[560px] border-collapse text-[13px]">
              <thead><tr className="bg-[#f3f2ef] text-left">{['Paso', 'Origen', 'Símbolo', 'Destino', 'Explicación'].map((h) => <th key={h} className="border border-[#e0dfdc] px-2 py-1.5">{h}</th>)}</tr></thead>
              <tbody>
                {result.steps.map((s) => (
                  <tr key={s.index} className={s.to === TRAP ? 'bg-[#fdf1ec]' : ''}>
                    <td className="border border-[#e0dfdc] px-2 py-1.5">{s.index}</td>
                    <td className="border border-[#e0dfdc] px-2 py-1.5 font-mono">{stateName(s.from)}</td>
                    <td className="border border-[#e0dfdc] px-2 py-1.5 font-mono">{s.symbol}</td>
                    <td className="border border-[#e0dfdc] px-2 py-1.5 font-mono">{stateName(s.to)}{s.to === TRAP ? ' (trampa)' : ''}</td>
                    <td className="border border-[#e0dfdc] px-2 py-1.5">{s.explanation}</td>
                  </tr>
                ))}
                <tr><td colSpan={5} className="border border-[#e0dfdc] px-2 py-1.5 font-semibold">{result.accepted ? `✓ Termina en ${stateName(result.finalState)} ∈ F: aceptada.` : `✗ Rechazada. ${result.reason ?? ''}`}</td></tr>
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
