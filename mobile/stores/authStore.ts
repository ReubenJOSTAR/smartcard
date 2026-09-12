// Auth state. JWT lives in expo-secure-store, NOT in this store — only the
// decoded user identity (from the access token's payload) is kept here.
// See progress.md → Mobile — Foundation and mobile/CLAUDE.md → State Architecture.

import { create } from 'zustand'
import { clearTokens, getAccessToken, setTokens } from '../services/tokenStorage'

export type AuthUser = {
  id: string
  phone: string
}

export type AuthState = {
  user: AuthUser | null
  isAuthenticated: boolean
  // True until the stored-token check on app launch resolves — lets the root
  // layout avoid flashing the login screen before we know a session exists.
  isHydrating: boolean
  login: (phone: string, token: string, refreshToken: string) => void
  logout: () => void
  hydrate: () => Promise<void>
}

type AccessTokenPayload = { sub: string; phone: string; exp: number }

function decodeAccessToken(token: string): AccessTokenPayload {
  const payloadSegment = token.split('.')[1]
  const base64 = payloadSegment.replace(/-/g, '+').replace(/_/g, '/')
  return JSON.parse(atob(base64)) as AccessTokenPayload
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isHydrating: true,
  login: (phone, token, refreshToken) => {
    void setTokens(token, refreshToken)
    const payload = decodeAccessToken(token)
    set({ user: { id: payload.sub, phone: payload.phone }, isAuthenticated: true, isHydrating: false })
  },
  logout: () => {
    void clearTokens()
    set({ user: null, isAuthenticated: false, isHydrating: false })
  },
  hydrate: async () => {
    const token = await getAccessToken()
    if (token) {
      try {
        const payload = decodeAccessToken(token)
        // No refresh-token endpoint exists yet (api/CLAUDE.md's auth routes are
        // send-otp/verify-otp only) — an expired access token just means a full
        // re-login via OTP, same as the api.ts 401 interceptor's fallback.
        if (payload.exp * 1000 > Date.now()) {
          set({ user: { id: payload.sub, phone: payload.phone }, isAuthenticated: true, isHydrating: false })
          return
        }
      } catch {
        // Malformed/corrupt stored token — fall through and clear it.
      }
      await clearTokens()
    }
    set({ isHydrating: false })
  },
}))
