// 6-digit OTP input, 30s resend cooldown, lockout UI.
// See progress.md → Mobile — Auth Screens and mobile/CLAUDE.md → Screen Map.

import { useLocalSearchParams, useRouter } from 'expo-router'
import { useEffect, useState } from 'react'
import { ActivityIndicator, Pressable, Text, TextInput, View } from 'react-native'
import { getApiErrorCode, getApiErrorMessage, sendOtp, verifyOtp } from '../../services/authService'
import { useAuthStore } from '../../stores/authStore'

const RESEND_COOLDOWN_SECONDS = 30
const OTP_PATTERN = /^\d{6}$/

export default function OtpScreen(): JSX.Element {
  const { phone }: { phone: string } = useLocalSearchParams()
  const router = useRouter()
  const login = useAuthStore((state) => state.login)

  const [code, setCode] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLockedOut, setIsLockedOut] = useState(false)
  const [cooldown, setCooldown] = useState(RESEND_COOLDOWN_SECONDS)

  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setInterval(() => setCooldown((seconds) => seconds - 1), 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  async function handleVerify(fullCode: string): Promise<void> {
    if (!OTP_PATTERN.test(fullCode) || isSubmitting || isLockedOut) return
    setError(null)
    setIsSubmitting(true)

    try {
      const { accessToken, refreshToken } = await verifyOtp(phone, fullCode)
      login(phone, accessToken, refreshToken)
      // PostHog wrapper is R2 (mobile/CLAUDE.md) — console.log stands in for it in MVP.
      console.log('[analytics] login_success')
      router.replace('/')
    } catch (err) {
      const errorCode = getApiErrorCode(err)
      if (errorCode === 'OTP_LOCKED_OUT') {
        setIsLockedOut(true)
        setError('Too many attempts — try again in 1 hour')
        console.log('[analytics] login_failed', { reason: 'locked_out' })
      } else if (errorCode === 'OTP_EXPIRED') {
        setError('Code expired — request a new one')
        console.log('[analytics] login_failed', { reason: 'expired' })
      } else if (errorCode === 'OTP_INVALID') {
        setError('Incorrect code')
        console.log('[analytics] login_failed', { reason: 'wrong_otp' })
      } else {
        setError(getApiErrorMessage(err))
      }
      setCode('')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleResend(): Promise<void> {
    if (cooldown > 0 || isResending || isLockedOut) return
    setError(null)
    setIsResending(true)

    try {
      await sendOtp(phone)
      setCooldown(RESEND_COOLDOWN_SECONDS)
    } catch (err) {
      if (getApiErrorCode(err) === 'OTP_RATE_LIMITED') {
        setError('Too many OTP requests — try again later')
      } else {
        setError(getApiErrorMessage(err))
      }
    } finally {
      setIsResending(false)
    }
  }

  return (
    <View className="flex-1 justify-center bg-white px-6">
      <Text className="mb-2 text-2xl font-semibold">Enter the code</Text>
      <Text className="mb-6 text-sm text-gray-500">We sent a 6-digit code to {phone}</Text>

      <TextInput
        className="mb-4 rounded-lg border border-gray-300 px-4 py-3 text-center text-2xl tracking-[8px]"
        value={code}
        onChangeText={(text) => {
          const digitsOnly = text.replace(/\D/g, '').slice(0, 6)
          setCode(digitsOnly)
          if (digitsOnly.length === 6) void handleVerify(digitsOnly)
        }}
        keyboardType="number-pad"
        maxLength={6}
        editable={!isSubmitting && !isLockedOut}
        autoFocus
      />

      {error ? <Text className="mb-4 text-sm text-red-600">{error}</Text> : null}
      {isSubmitting ? <ActivityIndicator className="mb-4" /> : null}

      <Pressable onPress={handleResend} disabled={cooldown > 0 || isResending || isLockedOut}>
        <Text className={`text-center text-sm ${cooldown > 0 || isLockedOut ? 'text-gray-400' : 'text-blue-600'}`}>
          {cooldown > 0 ? `Resend code in ${cooldown}s` : isResending ? 'Sending…' : 'Resend code'}
        </Text>
      </Pressable>
    </View>
  )
}
