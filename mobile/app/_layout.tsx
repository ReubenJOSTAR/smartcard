// Root layout — SafeAreaProvider, StatusBar, NetInfo listener, app version check.
// See progress.md → Mobile — Foundation and mobile/CLAUDE.md → App Version Check.

import '../global.css'

import NetInfo from '@react-native-community/netinfo'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as Application from 'expo-application'
import { Stack, useRouter } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { useEffect, useState } from 'react'
import { Text } from 'react-native'
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context'

import { OfflineBanner } from '../components/ui/OfflineBanner'
import { api } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import { useSessionStore } from '../stores/sessionStore'
import { useUIStore } from '../stores/uiStore'
import { isVersionBelow } from '../utils/semver'

type ConfigResponse = {
  min_app_version: string
  latest_version: string
  force_update: boolean
  maintenance_mode: boolean
  maintenance_message: string | null
}

export default function RootLayout(): JSX.Element {
  const router = useRouter()
  const [queryClient] = useState(() => new QueryClient())
  const isOffline = useSessionStore((state) => state.isOffline)
  const setOffline = useSessionStore((state) => state.setOffline)
  const maintenanceMode = useUIStore((state) => state.maintenanceMode)
  const forceUpdateRequired = useUIStore((state) => state.forceUpdateRequired)
  const setMaintenanceMode = useUIStore((state) => state.setMaintenanceMode)
  const setForceUpdateRequired = useUIStore((state) => state.setForceUpdateRequired)
  const isHydrating = useAuthStore((state) => state.isHydrating)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hydrate = useAuthStore((state) => state.hydrate)

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setOffline(!state.isConnected)
    })
    return unsubscribe
  }, [setOffline])

  useEffect(() => {
    void hydrate()
  }, [hydrate])

  // Redirect once we know whether a stored session exists. Runs again whenever
  // isAuthenticated flips (login success, logout) — not on every navigation.
  useEffect(() => {
    if (isHydrating) return
    router.replace(isAuthenticated ? '/' : '/login')
  }, [isHydrating, isAuthenticated, router])

  useEffect(() => {
    let isMounted = true

    api
      .get<ConfigResponse>('/v1/config')
      .then(({ data: config }) => {
        if (!isMounted) return
        setMaintenanceMode(config.maintenance_mode)

        const currentVersion = Application.nativeApplicationVersion
        if (currentVersion && isVersionBelow(currentVersion, config.min_app_version)) {
          setForceUpdateRequired(true)
        }
      })
      .catch(() => {
        // Never block the app on a failed config check (e.g. offline on launch)
        // — root CLAUDE.md's offline-first rules apply here too.
      })

    return () => {
      isMounted = false
    }
  }, [setMaintenanceMode, setForceUpdateRequired])

  if (maintenanceMode) {
    return (
      <SafeAreaProvider>
        <SafeAreaView className="flex-1 items-center justify-center bg-white px-6">
          <Text className="text-center text-lg font-semibold">
            SmartCart is under maintenance — back soon
          </Text>
        </SafeAreaView>
      </SafeAreaProvider>
    )
  }

  if (forceUpdateRequired) {
    return (
      <SafeAreaProvider>
        <SafeAreaView className="flex-1 items-center justify-center bg-white px-6">
          <Text className="text-center text-lg font-semibold">
            Please update SmartCart to continue
          </Text>
        </SafeAreaView>
      </SafeAreaProvider>
    )
  }

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="auto" />
        <SafeAreaView edges={['top']} className="bg-white">
          <OfflineBanner isOffline={isOffline} />
        </SafeAreaView>
        <Stack />
      </QueryClientProvider>
    </SafeAreaProvider>
  )
}
