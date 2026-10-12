import type { Evaluation, ProfileDocument } from './engine'
import type { Profile } from '../data/profiles'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15000)
  try {
    const response = await fetch(path, { ...options, signal: controller.signal })
    const body = await response.json()
    if (!response.ok) throw new Error(body.error ?? 'The request could not be completed.')
    return body as T
  } catch (error) {
    if (error instanceof TypeError || (error instanceof DOMException && error.name === 'AbortError'))
      throw new Error('Could not connect to the Python engine. Check that the server is running.')
    throw error
  } finally { clearTimeout(timeout) }
}
export const loadProfiles = () => request<Profile[]>('/api/profiles')
const evaluate = (mode: 'resume' | 'tokens', text: string) => request<Evaluation>('/api/evaluate', {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({mode, text}),
})
export const resumeService = {
  validateProfile: (text: string) => request<ProfileDocument>('/api/validate-profile', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }),
  }),
  evaluateResume: (text: string) => evaluate('resume', text),
  evaluateTokens: (text: string) => evaluate('tokens', text),
}
