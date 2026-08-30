// Root layout — placeholder. See progress.md → Mobile — Foundation.
// Will own: SafeAreaProvider, StatusBar, NetInfo listener, app version check (GET /v1/config).

import { Stack } from 'expo-router'

export default function RootLayout(): JSX.Element {
  return <Stack />
}
