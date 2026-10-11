export type Category = {
  id: string; label: string; short: string; tokens: string[]; required: boolean;
  requirement: string; group?: string;
}
export type Profile = {
  id: string; name: string; description: string; pattern: string; categories: Category[];
  requiredGroups: Record<string, string[]>; states: string[]; initialState: string;
  finalStates: string[]; transitions: Record<string, Record<string, string>>;
}
// Populated exclusively from the Python model; no second profile registry.
export const PROFILES: Profile[] = []
export function setProfiles(profiles: Profile[]) { PROFILES.splice(0, PROFILES.length, ...profiles) }
