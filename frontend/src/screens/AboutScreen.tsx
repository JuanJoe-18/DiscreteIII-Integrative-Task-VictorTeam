import { Card } from '../components/ui'

const PIPE = [
  { n: 'Regex', d: 'Extrae fragmentos de habilidades del texto libre.', s: 'Catálogo Regex integrado' },
  { n: 'FST', d: 'Transductores pyformlang normalizan variantes y ordenan por perfil.', s: 'Implementado' },
  { n: 'DFA', d: 'Un autómata por perfil reconoce la secuencia canónica de habilidades.', s: 'Implementado' },
  { n: 'EBNF / textX', d: 'DSL validada antes de generar y descargar el perfil HTML.', s: 'Implementado' },
]

export default function AboutScreen() {
  return (
    <div className="space-y-3">
      <Card className="p-6">
        <h1 className="text-[20px] font-semibold">Acerca del proyecto</h1>
        <p className="mt-2 max-w-prose text-[15px] leading-relaxed text-[#404040]">
          ResumeLens es un proyecto académico de <strong>Estructuras Discretas III</strong> que analiza hojas de vida mediante lenguajes formales. Reconoce si las habilidades explícitas de un candidato cumplen patrones profesionales. <strong>No</strong> asigna puntuaciones, no ordena candidatos y no toma decisiones de contratación. Un candidato puede cumplir varios perfiles al mismo tiempo.
        </p>
      </Card>
      <Card className="p-6" aria-labelledby="pipe">
        <h2 id="pipe" className="text-[18px] font-semibold">Pipeline integrado</h2>
        <ol className="mt-4 grid gap-3 md:grid-cols-4">
          {PIPE.map((p, i) => (
            <li key={p.n} className="rounded-lg border border-[#e0dfdc] p-4">
              <p className="text-[12px] font-semibold text-[#666]">Etapa {i + 1}</p>
              <p className="mt-0.5 text-[16px] font-semibold text-[#0a66c2]">{p.n}</p>
              <p className="mt-1 text-[14px] text-[#404040]">{p.d}</p>
              <p className="mt-2 text-[12px] font-semibold text-[#1d1d1d]">Estado: {p.s}</p>
            </li>
          ))}
        </ol>
      </Card>
      <Card className="p-6">
        <h2 className="text-[18px] font-semibold">Estado actual</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-[15px] text-[#404040]">
          <li>Los DFA de los cuatro perfiles están implementados.</li>
          <li>Regex y FST comparten la misma implementación en las interfaces.</li>
          <li>La etapa 4 conserva información personal, contacto, experiencia, formación y múltiples perfiles aceptados.</li>
          <li>El editor de DSL informa errores y habilita la salida HTML únicamente después de validar.</li>
          <li>Esta interfaz se conecta a la API Python local. Los resultados, las trazas y las definiciones formales provienen de los DFA reales de pyformlang; no se simula la clasificación en el navegador.</li>
        </ul>
      </Card>
    </div>
  )
}
