// Coloured progress bar (green/amber/red) — placeholder.
// See progress.md → Mobile — Components and mobile/CLAUDE.md → Component Structure.

import { View } from 'react-native'

export type BudgetBarProps = {
  spentPaise: number
  budgetPaise: number
}

export function BudgetBar(props: BudgetBarProps): JSX.Element {
  return <View />
}
