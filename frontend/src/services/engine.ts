// Presentation types and lookups only. Recognition runs exclusively in Python.
import type { Profile } from '../data/profiles'
export const TRAP = 'q_trap'
export const START = 'q0'
export type Step = { index: number; from: string; symbol: string; to: string; explanation: string }
export type Fragment = { text: string; token: string }
export type ProfileResult = {
  profileId: string; accepted: boolean; sequence: string[]; steps: Step[]; finalState: string;
  observed: { category: string; tokens: string[] }[]; missing: string[]; foreign: string[]; reason?: string;
}
export type Evaluation = {
  mode: 'resume' | 'tokens'; fragments: Fragment[]; normalized: string[];
  results: ProfileResult[]; candidate: {
    name?: string; description?: string;
    contact?: { email: string[]; phone: string[]; linkedin: string[]; github: string[] };
    education?: string[]; job_titles?: string[]; years_of_experience?: number | null;
  }; simulated: false;
}
export const stateName = (state: string) => state
export const isFinal = (profile: Profile, state: string) => profile.finalStates.includes(state)
export const delta = (profile: Profile, state: string, category: number) =>
  profile.transitions[state]?.[profile.categories[category].tokens[0]] ?? TRAP
