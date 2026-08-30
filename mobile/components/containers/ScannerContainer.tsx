// Barcode scan → lookup → add to session — placeholder, stateful logic, no styling.
// See mobile/CLAUDE.md → Component Structure and → Barcode Scanner.

import { ReactNode } from 'react'

export type ScannerContainerProps = {
  children?: ReactNode
}

export function ScannerContainer(props: ScannerContainerProps): JSX.Element {
  return <>{props.children}</>
}
