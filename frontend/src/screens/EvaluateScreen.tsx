import { useState } from 'react'
import { EXAMPLES } from '../data/examples'
import { PROFILES } from '../data/profiles'
import { stateName, type Evaluation, type ProfileResult } from '../services/engine'
import { Button, Card, Chip, EngineNotice, StatusBadge } from '../components/ui'
import Icon from '../components/Icon'
import ProfileOutput from '../components/ProfileOutput'

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
  const tabs: { id: Mode; label: string }[] = [{ id: 'resume', label: 'Résumé' }, { id: 'tokens', label: 'Normalized tokens' }]
  return (
    <div className="space-y-3">
      <Card>
        <div className="px-5 pt-4">
          <h1 className="text-[20px] font-semibold text-[#1d1d1d]">Evaluate résumé</h1>
          <p className="mt-0.5 text-[14px] text-[#666]">Recognizes whether the explicit skills satisfy professional patterns. It does not score or recommend candidates.</p>
        </div>
        <div role="tablist" aria-label="Input mode" className="mt-3 flex border-b border-[#e0dfdc] px-3">
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
                <label htmlFor="resume" className="text-[14px] font-semibold text-[#1d1d1d]">Résumé text</label>
                <label className="flex items-center gap-2 text-[13px] text-[#666]">
                  Example
                  <select className="rounded-md border border-[#8c8c8c] bg-white px-2 py-1 text-[13px] text-[#1d1d1d]" value="" onChange={(e) => e.target.value && p.onLoadExample(e.target.value)}>
                    <option value="">Choose…</option>
                    {EXAMPLES.filter((e) => e.mode === 'resume').map((e) => <option key={e.id} value={e.id}>{e.title}</option>)}
                  </select>
                </label>
              </div>
              <textarea id="resume" value={p.resumeText} onChange={(e) => p.setResumeText(e.target.value)} rows={11}
                placeholder="Paste the résumé text here: profile, experience and skills…"
                className="w-full resize-y rounded-md border border-[#8c8c8c] p-3 text-[15px] leading-relaxed text-[#1d1d1d] placeholder:text-[#8c8c8c]" aria-describedby="resume-help" />
              <p id="resume-help" className="text-[13px] text-[#666]">
                Only explicit technical skills are analysed. The name is recognized at the start of the résumé or after the label <span className="font-mono">Name:</span>. You can add <span className="font-mono">Description:</span> to complete the card; contact data never counts as a skill.
              </p>
            </div>
          ) : (
            <div id="panel-tokens" role="tabpanel" aria-labelledby="tab-tokens" className="space-y-3">
              <label htmlFor="tokens" className="text-[14px] font-semibold text-[#1d1d1d]">Sequence of symbols separated by commas</label>
              <input id="tokens" value={p.tokenText} onChange={(e) => p.setTokenText(e.target.value)} placeholder="JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT"
                className="w-full rounded-md border border-[#8c8c8c] px-3 py-2 font-mono text-[14px] text-[#1d1d1d]" aria-describedby="tokens-help" />
              <div id="tokens-help" className="rounded-md bg-[#f3f2ef] p-3 text-[13px] text-[#404040]">
                <p><strong>Important:</strong> this mode evaluates the sequence exactly as written; it does not fix its order. A symbol out of order or outside the profile alphabet causes a rejection.</p>
                <p className="mt-1">Example: <button type="button" className="font-mono font-semibold text-[#0a66c2] hover:underline" onClick={() => p.setTokenText('JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT')}>JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT</button></p>
              </div>
            </div>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={p.status === 'loading'}>
              {p.status === 'loading' ? <><span className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white" aria-hidden="true" /> Evaluating…</> : <><Icon name="play" className="size-4" /> Evaluate résumé</>}
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
      <Card className="p-5" aria-label="Processing">
        <p className="text-[14px] font-semibold text-[#1d1d1d]" role="status">Processing: extraction → normalization → recognition…</p>
        <div className="mt-4 space-y-3" aria-hidden="true">{[0, 1, 2].map((i) => <div key={i} className="h-16 animate-pulse rounded-md bg-[#f3f2ef]" />)}</div>
      </Card>
    )
  if (p.status === 'error')
    return (
      <Card className="flex gap-3 border-[#b24020]/50 p-5" aria-label="Error">
        <Icon name="alert" className="size-6 shrink-0 text-[#b24020]" />
        <div role="alert"><p className="font-semibold text-[#8f2f12]">The evaluation failed</p><p className="mt-0.5 text-[14px] text-[#404040]">{p.error}</p></div>
      </Card>
    )
  if (!p.evaluation)
    return (
      <Card className="px-5 py-10 text-center" aria-label="No results">
        <Icon name="doc" className="mx-auto size-9 text-[#8c8c8c]" />
        <p className="mt-2 font-semibold text-[#1d1d1d]">No results yet</p>
        <p className="mx-auto mt-1 max-w-md text-[14px] text-[#666]">Paste a résumé or choose an example and press “Evaluate résumé”. You will see the four profiles and the path through each automaton.</p>
      </Card>
    )
  const ev = p.evaluation
  const ok = ev.results.filter((r) => r.accepted)
  return (
    <>
      <Card className="p-5" aria-labelledby="sum-title">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 id="sum-title" className="text-[18px] font-semibold">Summary</h2>
          <EngineNotice />
        </div>
        <p className="mt-1 text-[15px] text-[#404040]">
          {ok.length ? <>Satisfied patterns: <strong>{ok.map((r) => PROFILES.find((x) => x.id === r.profileId)!.name).join(', ')}</strong>.</> : 'No professional pattern is satisfied by this input.'}
          {ok.length > 1 && ' A candidate can satisfy several profiles at the same time.'}
        </p>
        <p className="mt-1 text-[13px] text-[#666]">Mode: {ev.mode === 'resume' ? 'résumé (canonical order per profile)' : 'direct tokens (order as written)'}.</p>
      </Card>
      <div className="space-y-3">
        {ev.results.map((r) => <ResultCard key={r.profileId} r={r} selected={p.selectedProfile === r.profileId} onSelect={() => p.onSelectProfile(r.profileId)} onOpen={() => p.onOpenAutomaton(r.profileId)} />)}
      </div>
      <Processing ev={ev} />
      {ev.profileDocument && <ProfileOutput key={ev.profileDocument.dsl} document={ev.profileDocument} />}
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
          <p className="text-[13px] text-[#666]">Final state: <span className="font-mono">{stateName(r.finalState)}</span></p>
        </div>
        <StatusBadge accepted={r.accepted} />
      </div>
      <div className="mt-3 space-y-2 text-[14px]">
        <div>
          <p className="text-[13px] font-semibold text-[#404040]">Observed skills</p>
          <div className="mt-1 flex flex-wrap gap-1.5">{r.observed.length ? r.observed.flatMap((o) => o.tokens).map((t) => <Chip key={t}>{t}</Chip>) : <span className="text-[#666]">None</span>}</div>
        </div>
        {r.missing.length > 0 && (
          <div>
            <p className="text-[13px] font-semibold text-[#404040]">Missing mandatory requirements</p>
            <div className="mt-1 flex flex-wrap gap-1.5">{r.missing.map((m) => <Chip key={m} tone="warn">Missing: {m}</Chip>)}</div>
          </div>
        )}
        {r.reason && <p className="rounded-md bg-[#f3f2ef] px-3 py-2 text-[#404040]"><strong>Rejection reason:</strong> {r.reason}</p>}
      </div>
      <button className="mt-3 inline-flex items-center gap-1 text-[14px] font-semibold text-[#0a66c2] hover:underline" aria-expanded={open} onClick={() => setOpen(!open)}>
        Show details <Icon name="chevron" className={`size-4 transition ${open ? 'rotate-90' : ''}`} />
      </button>
      {open && (
        <div className="mt-3 space-y-3 border-t border-[#e0dfdc] pt-3 text-[14px]">
          <div>
            <p className="text-[13px] font-semibold text-[#404040]">Evaluated sequence</p>
            <p className="mt-1 break-words rounded-md bg-[#f3f2ef] px-3 py-2 font-mono text-[13px]">{r.sequence.length ? r.sequence.join(' · ') : 'ε (empty)'}</p>
          </div>
          <details className="rounded-md border border-[#e0dfdc] px-3 py-2">
            <summary className="cursor-pointer text-[13px] font-semibold text-[#404040]">Skills outside this profile ({r.foreign.length})</summary>
            <div className="mt-2 flex flex-wrap gap-1.5">{r.foreign.length ? r.foreign.map((t) => <Chip key={t}>{t}</Chip>) : <span className="text-[#666]">None</span>}</div>
          </details>
          <Button variant="secondary" onClick={onOpen}><Icon name="graph" className="size-4" /> Show the path in the automaton</Button>
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
          <span className="flex items-center gap-2"><Icon name="list" /> Show processing</span>
          <Icon name="chevron" className="size-5 transition group-open:rotate-90" />
        </summary>
        <ol className="space-y-4 border-t border-[#e0dfdc] px-5 py-4 text-[14px]">
          <li>
            <p className="font-semibold">1. Extracted fragments</p>
            {ev.mode === 'tokens' ? <p className="text-[#666]">Not applicable: direct mode receives symbols that are already normalized.</p> : (
              <div className="mt-1 flex flex-wrap gap-1.5">{ev.fragments.map((f, i) => <span key={i} className="rounded border border-[#e0dfdc] px-2 py-0.5 text-[13px]">“{f.text}” → <span className="font-mono">{f.token}</span></span>)}</div>
            )}
          </li>
          <li>
            <p className="font-semibold">2. Normalized skills</p>
            <p className="mt-1 break-words font-mono text-[13px]">{ev.normalized.join(', ')}</p>
          </li>
          <li>
            <p className="font-semibold">3. Sequence prepared for each profile</p>
            <ul className="mt-1 space-y-1">{ev.results.map((r) => <li key={r.profileId}><span className="text-[#666]">{PROFILES.find((x) => x.id === r.profileId)!.name}:</span> <span className="font-mono text-[13px]">{r.sequence.join(' · ') || 'ε'}</span></li>)}</ul>
          </li>
          <li>
            <p className="font-semibold">4. Recognition result</p>
            <ul className="mt-1 space-y-1">{ev.results.map((r) => <li key={r.profileId}>{PROFILES.find((x) => x.id === r.profileId)!.name}: <strong>{r.accepted ? 'accepted' : 'rejected'}</strong> in <span className="font-mono">{stateName(r.finalState)}</span></li>)}</ul>
          </li>
        </ol>
      </details>
    </Card>
  )
}
