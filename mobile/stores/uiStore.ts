// Transient UI state — NOT persisted. Placeholder.
// See progress.md → Mobile — Foundation and mobile/CLAUDE.md → State Architecture.

export type UIState = {
  offlineBannerVisible: boolean
  forceUpdateRequired: boolean
  maintenanceMode: boolean
}
