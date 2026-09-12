// Active shopping session — persisted to AsyncStorage for crash recovery.
// See progress.md → Mobile — Foundation, mobile/CLAUDE.md → State Architecture,
// and root CLAUDE.md §7 → Session Crash Recovery.

import AsyncStorage from '@react-native-async-storage/async-storage'
import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export type SyncQueueItem = {
  id: string
  method: 'POST' | 'PATCH' | 'DELETE'
  url: string
  body: object
  createdAt: string
}

export type SessionItemState = {
  id: string
  barcode: string
  name: string
  qty: number
  pricePaise: number
  confidence: number
  source: 'cache' | 'api' | 'manual'
}

export type ActiveSession = {
  id: string
  storeId: number | null
  storeName: string
  budgetPaise: number
  items: SessionItemState[]
  runningTotalPaise: number
  status: 'active' | 'finished'
  lastUpdatedAt: string
}

export type SessionState = {
  activeSession: ActiveSession | null
  isOffline: boolean
  syncQueue: SyncQueueItem[]
  resumeSession: (session: ActiveSession) => void
  addItem: (item: SessionItemState) => void
  updateQty: (itemId: string, qty: number) => void
  removeItem: (itemId: string) => void
  clearSession: () => void
  setOffline: (isOffline: boolean) => void
}

function recomputeTotal(items: SessionItemState[]): number {
  return items.reduce((sum, item) => sum + item.pricePaise * item.qty, 0)
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      activeSession: null,
      isOffline: false,
      syncQueue: [],
      resumeSession: (session) => set({ activeSession: session }),
      addItem: (item) =>
        set((state) => {
          if (!state.activeSession) return state
          const items = [...state.activeSession.items, item]
          return {
            activeSession: {
              ...state.activeSession,
              items,
              runningTotalPaise: recomputeTotal(items),
              lastUpdatedAt: new Date().toISOString(),
            },
          }
        }),
      updateQty: (itemId, qty) =>
        set((state) => {
          if (!state.activeSession) return state
          const items = state.activeSession.items.map((item) =>
            item.id === itemId ? { ...item, qty } : item
          )
          return {
            activeSession: {
              ...state.activeSession,
              items,
              runningTotalPaise: recomputeTotal(items),
              lastUpdatedAt: new Date().toISOString(),
            },
          }
        }),
      removeItem: (itemId) =>
        set((state) => {
          if (!state.activeSession) return state
          const items = state.activeSession.items.filter((item) => item.id !== itemId)
          return {
            activeSession: {
              ...state.activeSession,
              items,
              runningTotalPaise: recomputeTotal(items),
              lastUpdatedAt: new Date().toISOString(),
            },
          }
        }),
      clearSession: () => set({ activeSession: null }),
      setOffline: (isOffline) => set({ isOffline }),
    }),
    {
      name: 'smartcart_session_store',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({ activeSession: state.activeSession }),
    }
  )
)
