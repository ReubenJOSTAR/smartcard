// Price display — MVP: simple "~₹X" only, no confidence label (that's R2).
// See progress.md → Mobile — Components.

import { View } from 'react-native'

export type PriceTagProps = {
  pricePaise: number
}

export function PriceTag(props: PriceTagProps): JSX.Element {
  return <View />
}
