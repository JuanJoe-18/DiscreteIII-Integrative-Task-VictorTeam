import { useRef, useState } from 'react'
import type { Profile } from '../data/profiles'
import { delta, isFinal, stateName, START, TRAP, type Step } from '../services/engine'
import Icon from './Icon'

const GAP = 190, R = 40, Y = 230, X0 = 70

export default function Diagram({ profile, steps }: { profile: Profile; steps?: Step[] }) {
  const [scale, setScale] = useState(1)
  const container = useRef<HTMLDivElement>(null)
  const states = profile.states.filter((state) => state !== TRAP)
  const n = profile.categories.length
  const x = (state: string) => X0 + states.indexOf(state) * GAP
  const width = x(states[states.length - 1]) + 80
  const trapX = width / 2, trapY = 400
  const used = new Set(steps?.map((s) => `${s.from}>${s.to}`))
  const visited = new Set(steps?.flatMap((s) => [s.from, s.to]) ?? [])
  const last = steps?.length ? steps[steps.length - 1].to : steps ? START : undefined

  const edges: { from: string; to: string; label: string }[] = []
  for (const j of states) for (let c = 0; c < n; c++) {
    const to = delta(profile, j, c)
    if (to !== TRAP) edges.push({ from: j, to, label: profile.categories[c].short })
  }
  const color = (k: string) => (used.has(k) ? '#0a66c2' : '#8c8c8c')

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e0dfdc] px-4 py-2">
        <p className="text-[13px] text-[#666]">{steps ? 'Recorrido de la evaluación resaltado en azul.' : 'Sin evaluación seleccionada: no hay recorrido que resaltar.'}</p>
        <div className="flex items-center gap-1" role="group" aria-label="Controles de zoom">
          <button className="rounded-full p-1.5 text-[#404040] hover:bg-[#ebebeb]" onClick={() => setScale((s) => Math.max(0.5, s - 0.25))} aria-label="Alejar"><Icon name="minus" /></button>
          <span className="w-12 text-center text-[13px] tabular-nums text-[#404040]" aria-live="polite">{Math.round(scale * 100)}%</span>
          <button className="rounded-full p-1.5 text-[#404040] hover:bg-[#ebebeb]" onClick={() => setScale((s) => Math.min(2.5, s + 0.25))} aria-label="Acercar"><Icon name="plus" /></button>
          <button className="ml-1 inline-flex items-center gap-1 rounded-full px-3 py-1 text-[13px] font-semibold text-[#404040] hover:bg-[#ebebeb]" onClick={() => setScale(Math.min(1, (container.current?.clientWidth ?? width) / width))}><Icon name="fit" className="size-4" /> Ajustar</button>
        </div>
      </div>
      <div ref={container} className="overflow-auto bg-[#fafafa]" style={{ maxHeight: 520 }}>
        <svg viewBox={`0 0 ${width} 470`} style={{ width: width * scale, maxWidth: 'none' }} role="img" aria-label={`Diagrama del DFA de ${profile.name}`} className="block">
          <defs>
            {['#8c8c8c', '#0a66c2', '#b24020'].map((c) => (
              <marker key={c} id={`a${c.slice(1)}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M0 0L10 5L0 10z" fill={c} />
              </marker>
            ))}
          </defs>
          {/* flecha de inicio */}
          <line x1={x(START) - 60} y1={Y} x2={x(START) - R - 2} y2={Y} stroke="#1d1d1d" strokeWidth={1.6} markerEnd="url(#a8c8c8c)" />
          <text x={x(START) - 62} y={Y - 8} fontSize="12" fill="#404040">inicio</text>
          {/* transiciones a trampa */}
          {states.map((s) => {
            const k = `${s}>${TRAP}`
            return <line key={k} x1={x(s)} y1={Y + R} x2={trapX + (x(s) - trapX) * 0.12} y2={trapY - R - 2} stroke={used.has(k) ? '#b24020' : '#d0cfcc'} strokeDasharray="4 4" strokeWidth={used.has(k) ? 2 : 1.2} markerEnd={`url(#a${used.has(k) ? 'b24020' : '8c8c8c'})`} />
          })}
          <text x={trapX + 40} y={trapY - 52} fontSize="12" fill="#8c8c8c">otros símbolos de Σ / fuera de orden</text>
          {edges.map(({ from, to, label }) => {
            const k = `${from}>${to}`, c = color(k), w = used.has(k) ? 2.6 : 1.4
            if (from === to) {
              const cx = x(from)
              return (
                <g key={k + label}>
                  <path d={`M${cx - 12} ${Y - R + 3} C ${cx - 30} ${Y - 80}, ${cx + 30} ${Y - 80}, ${cx + 12} ${Y - R + 3}`} fill="none" stroke={c} strokeWidth={w} markerEnd={`url(#a${c.slice(1)})`} />
                  <text x={cx} y={Y - 72} textAnchor="middle" fontSize="12" fill={c} fontWeight={used.has(k) ? 700 : 500}>{label}</text>
                </g>
              )
            }
            const x1 = x(from) + R, x2 = x(to) - R, d = states.indexOf(to) - states.indexOf(from)
            if (d === 1) return (
              <g key={k}>
                <line x1={x1} y1={Y} x2={x2 - 2} y2={Y} stroke={c} strokeWidth={w} markerEnd={`url(#a${c.slice(1)})`} />
                <text x={(x1 + x2) / 2} y={Y + 18} textAnchor="middle" fontSize="12" fill={c} fontWeight={used.has(k) ? 700 : 500}>{label}</text>
              </g>
            )
            const h = 60 + d * 28, mx = (x(from) + x(to)) / 2
            return (
              <g key={k}>
                <path d={`M${x(from) + 10} ${Y - R + 4} Q ${mx} ${Y - h * 2}, ${x(to) - 10} ${Y - R + 4}`} fill="none" stroke={c} strokeWidth={w} markerEnd={`url(#a${c.slice(1)})`} />
                <rect x={mx - 34} y={Y - h - 9} width={68} height={17} rx={4} fill="#fafafa" />
                <text x={mx} y={Y - h + 4} textAnchor="middle" fontSize="12" fill={c} fontWeight={used.has(k) ? 700 : 500}>{label}</text>
              </g>
            )
          })}
          {states.map((s) => {
            const fin = isFinal(profile, s), on = visited.has(s), cur = last === s
            return (
              <g key={s}>
                <circle cx={x(s)} cy={Y} r={R} fill={cur ? '#0a66c2' : on ? '#eaf3fc' : '#fff'} stroke={on ? '#0a66c2' : '#404040'} strokeWidth={on ? 2.2 : 1.5} />
                {fin && <circle cx={x(s)} cy={Y} r={R - 5} fill="none" stroke={cur ? '#fff' : on ? '#0a66c2' : '#404040'} strokeWidth={1.5} />}
                <text x={x(s)} y={Y + 5} textAnchor="middle" fontSize="9" fontWeight="600" fill={cur ? '#fff' : '#1d1d1d'}>{stateName(s)}</text>
                <text x={x(s)} y={Y + R + 34} textAnchor="middle" fontSize="11" fill="#666">{s === START ? 'inicial' : profile.categories[states.indexOf(s) - 1].short}</text>
              </g>
            )
          })}
          <g>
            <path d={`M${trapX - 12} ${trapY - R + 3} C ${trapX - 32} ${trapY - 95}, ${trapX + 32} ${trapY - 95}, ${trapX + 12} ${trapY - R + 3}`} fill="none" stroke="#b24020" strokeWidth="1.5" markerEnd="url(#ab24020)" />
            <text x={trapX} y={trapY - 80} textAnchor="middle" fontSize="12" fill="#8f2f12">Σ</text>
            <circle cx={trapX} cy={trapY} r={R} fill={last === TRAP ? '#fdf1ec' : '#fff'} stroke="#b24020" strokeWidth={last === TRAP ? 2.4 : 1.5} strokeDasharray="5 3" />
            <text x={trapX} y={trapY + 5} textAnchor="middle" fontSize="14" fontWeight="600" fill="#8f2f12">q_trap</text>
            <text x={trapX + R + 8} y={trapY + 4} fontSize="12" fill="#8f2f12">trampa (Σ)</text>
          </g>
        </svg>
      </div>
      <ul className="flex flex-wrap gap-x-5 gap-y-2 border-t border-[#e0dfdc] px-4 py-3 text-[13px] text-[#404040]" aria-label="Leyenda">
        <li className="flex items-center gap-2"><svg width="26" height="12" aria-hidden="true"><line x1="0" y1="6" x2="24" y2="6" stroke="#1d1d1d" strokeWidth="1.6" /></svg>Flecha de inicio → q0</li>
        <li className="flex items-center gap-2"><svg width="22" height="22" aria-hidden="true"><circle cx="11" cy="11" r="9" fill="#fff" stroke="#404040" strokeWidth="1.5" /><circle cx="11" cy="11" r="5.5" fill="none" stroke="#404040" strokeWidth="1.5" /></svg>Doble círculo: aceptación</li>
        <li className="flex items-center gap-2"><svg width="22" height="22" aria-hidden="true"><circle cx="11" cy="11" r="9" fill="#fff" stroke="#b24020" strokeWidth="1.5" strokeDasharray="4 2" /></svg>Discontinuo: trampa q_trap</li>
        <li className="flex items-center gap-2"><svg width="22" height="22" aria-hidden="true"><circle cx="11" cy="11" r="9" fill="#0a66c2" /></svg>Estado final del recorrido</li>
        <li>Las etiquetas agrupan símbolos por categoría. Las aristas discontinuas llevan los otros símbolos de Σ a trampa; símbolos externos se rechazan antes de δ.</li>
      </ul>
    </div>
  )
}
