// Session detail: item list, qty controls, finish button + ConfirmSheet — placeholder.
// See progress.md → Mobile — Core Screens.

import { View } from 'react-native'
import { useLocalSearchParams } from 'expo-router'

export default function SessionDetailScreen(): JSX.Element {
  const { id }: { id: string } = useLocalSearchParams()
  return <View />
}
