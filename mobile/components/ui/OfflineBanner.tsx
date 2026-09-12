// Persistent top banner when offline — pure presentational, no state.
// See root CLAUDE.md §7 → Offline Behaviour Rules.

import { Text, View } from 'react-native'

export type OfflineBannerProps = {
  isOffline: boolean
}

export function OfflineBanner({ isOffline }: OfflineBannerProps): JSX.Element | null {
  if (!isOffline) return null

  return (
    <View className="bg-amber-500 px-4 py-2">
      <Text className="text-center text-sm font-medium text-white">
        Offline — using cached prices
      </Text>
    </View>
  )
}
