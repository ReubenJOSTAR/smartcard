// Single scanned item row with qty controls — placeholder.
// See progress.md → Mobile — Components.

import { View } from 'react-native'

export type SessionItemProps = {
  id: string
  barcode: string
  name: string
  qty: number
  pricePaise: number
}

export function SessionItem(props: SessionItemProps): JSX.Element {
  return <View />
}
