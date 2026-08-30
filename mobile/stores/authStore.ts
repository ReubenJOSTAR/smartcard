// Auth state — placeholder. JWT lives in expo-secure-store, NOT in this store.
// See progress.md → Mobile — Foundation and mobile/CLAUDE.md → State Architecture.

export type AuthUser = {
  id: string
  phone: string
}

export type AuthState = {
  user: AuthUser | null
  isAuthenticated: boolean
  login: (phone: string, token: string, refreshToken: string) => void
  logout: () => void
}
