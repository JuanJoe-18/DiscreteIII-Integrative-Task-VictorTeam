import { useRef, useState } from 'react'
import type { ProfileDocument } from '../services/engine'
import { resumeService } from '../services/resumeService'
import { Button, Card } from './ui'

function download(text: string, name: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export default function ProfileOutput({ document: original }: { document: ProfileDocument }) {
  const [source, setSource] = useState(original.dsl)
  const [validated, setValidated] = useState<ProfileDocument | null>(original)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const revision = useRef(0)

  function edit(value: string) {
    revision.current += 1
    setSource(value)
    setValidated(null)
    setError('')
    setLoading(false)
  }

  async function validate() {
    const current = ++revision.current
    setLoading(true)
    setError('')
    setValidated(null)
    try {
      const result = await resumeService.validateProfile(source)
      if (revision.current === current) setValidated(result)
    } catch (cause) {
      if (revision.current === current) setError(cause instanceof Error ? cause.message : 'No se pudo validar la DSL.')
    } finally {
      if (revision.current === current) setLoading(false)
    }
  }

  return <Card className="space-y-4 p-5" aria-labelledby="document-title">
    <div>
      <h2 id="document-title" className="text-[18px] font-semibold">Perfil estructurado · Etapa 4</h2>
      <p className="mt-1 text-[14px] text-[#666]">La DSL conserva los datos extraídos y los perfiles aceptados. Puedes completar empleadores, fechas y formación; cada cambio requiere una nueva validación.</p>
    </div>
    <details>
      <summary className="cursor-pointer font-semibold text-[#0a66c2]">Ver o editar la DSL</summary>
      <label htmlFor="profile-dsl" className="mt-3 block text-[13px] font-semibold">Documento del candidato (.resume)</label>
      <textarea id="profile-dsl" value={source} onChange={e => edit(e.target.value)} rows={18} spellCheck={false}
        className="mt-1 w-full rounded-md border border-[#8c8c8c] p-3 font-mono text-[13px]" />
      <p className="text-[13px] text-[#666]">Validar comprueba sintaxis y reglas de datos; no vuelve a clasificar los perfiles declarados en una DSL editada.</p>
    </details>
    <div className="flex flex-wrap gap-2">
      <Button onClick={validate} disabled={loading || !source.trim()}>{loading ? 'Validando…' : 'Validar DSL y generar HTML'}</Button>
      <Button variant="secondary" onClick={() => download(source, 'candidate.resume', 'text/plain;charset=utf-8')}>Descargar DSL</Button>
      <Button variant="secondary" disabled={!validated} onClick={() => validated && download(validated.html, 'candidate.html', 'text/html;charset=utf-8')}>Descargar HTML</Button>
      <Button variant="secondary" onClick={() => { edit(original.dsl); setValidated(original) }}>Restaurar resultado</Button>
    </div>
    <p role="status" className={`text-[13px] ${validated ? 'text-[#26723d]' : 'text-[#666]'}`}>
      {validated ? 'DSL válida. El HTML corresponde al documento validado.' : loading ? 'Comprobando el documento con textX…' : 'Documento modificado: valida la DSL para generar la vista y habilitar el HTML.'}
    </p>
    {error && <p role="alert" className="rounded-md bg-[#fff1ec] p-3 text-[14px] text-[#8f2f12]">{error}</p>}
    {validated && <iframe title="Vista previa del perfil validado" sandbox="" srcDoc={validated.html}
      className="h-[640px] w-full rounded-md border border-[#e0dfdc] bg-white" />}
  </Card>
}
