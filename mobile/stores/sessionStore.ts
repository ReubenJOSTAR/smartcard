// Active shopping session — persisted to AsyncStorage for crash recovery. Placeholder.
// See progress.md → Mobile — Foundation and mobile/CLAUDE.md → State Architecture.

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
}
