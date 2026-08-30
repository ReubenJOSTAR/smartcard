// Bottom sheet for destructive confirmations (e.g. "Finish Shopping") — placeholder.
// See progress.md → Mobile — Components.

import { View } from 'react-native'

export type ConfirmSheetProps = {
  visible: boolean
  message: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmSheet(props: ConfirmSheetProps): JSX.Element | null {
  return null
}
