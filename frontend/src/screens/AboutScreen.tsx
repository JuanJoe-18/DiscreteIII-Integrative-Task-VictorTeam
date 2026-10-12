import { Card } from '../components/ui'

const PIPE = [
  { n: 'Regex', d: 'Extracts skill fragments from free text.', s: 'Integrated regex catalog' },
  { n: 'FST', d: 'pyformlang transducers normalize variants and sort them per profile.', s: 'Implemented' },
  { n: 'DFA', d: 'One automaton per profile recognizes the canonical sequence of skills.', s: 'Implemented' },
  { n: 'EBNF / textX', d: 'A DSL validated before the HTML profile is generated and downloaded.', s: 'Implemented' },
]

export default function AboutScreen() {
  return (
    <div className="space-y-3">
      <Card className="p-6">
        <h1 className="text-[20px] font-semibold">About the project</h1>
        <p className="mt-2 max-w-prose text-[15px] leading-relaxed text-[#404040]">
          ResumeLens is an academic project of <strong>Computación y Estructuras Discretas III</strong> that analyses résumés with formal languages. It recognizes whether a candidate's explicit skills satisfy professional patterns. It does <strong>not</strong> score or rank candidates and does not make hiring decisions. A candidate can satisfy several profiles at the same time.
        </p>
      </Card>
      <Card className="p-6" aria-labelledby="pipe">
        <h2 id="pipe" className="text-[18px] font-semibold">Integrated pipeline</h2>
        <ol className="mt-4 grid gap-3 md:grid-cols-4">
          {PIPE.map((p, i) => (
            <li key={p.n} className="rounded-lg border border-[#e0dfdc] p-4">
              <p className="text-[12px] font-semibold text-[#666]">Stage {i + 1}</p>
              <p className="mt-0.5 text-[16px] font-semibold text-[#0a66c2]">{p.n}</p>
              <p className="mt-1 text-[14px] text-[#404040]">{p.d}</p>
              <p className="mt-2 text-[12px] font-semibold text-[#1d1d1d]">Status: {p.s}</p>
            </li>
          ))}
        </ol>
      </Card>
      <Card className="p-6">
        <h2 className="text-[18px] font-semibold">Current status</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-[15px] text-[#404040]">
          <li>The DFAs of the four profiles are implemented.</li>
          <li>Both interfaces use the same regex and FST implementation.</li>
          <li>Stage 4 keeps personal information, contact data, experience, education and several accepted profiles.</li>
          <li>The DSL editor reports errors and enables the HTML output only after validation.</li>
          <li>This interface connects to the local Python API. Results, traces and formal definitions come from the real pyformlang DFAs; classification is never simulated in the browser.</li>
        </ul>
      </Card>
    </div>
  )
}
