// Transient UI state — NOT persisted.
// See progress.md → Mobile — Foundation and mobile/CLAUDE.md → State Architecture.

import { create } from 'zustand'

export type UIState = {
  offlineBannerVisible: boolean
  forceUpdateRequired: boolean
  maintenanceMode: boolean
  setOfflineBannerVisible: (visible: boolean) => void
  setForceUpdateRequired: (required: boolean) => void
  setMaintenanceMode: (enabled: boolean) => void
}

export const useUIStore = create<UIState>((set) => ({
  offlineBannerVisible: false,
  forceUpdateRequired: false,
  maintenanceMode: false,
  setOfflineBannerVisible: (visible) => set({ offlineBannerVisible: visible }),
  setForceUpdateRequired: (required) => set({ forceUpdateRequired: required }),
  setMaintenanceMode: (enabled) => set({ maintenanceMode: enabled }),
}))
