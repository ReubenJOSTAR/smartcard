// Phone number entry (+91 prefix, E.164 format).
// See progress.md → Mobile — Auth Screens and mobile/CLAUDE.md → Screen Map.

import { useRouter } from 'expo-router'
import { useState } from 'react'
import { ActivityIndicator, Pressable, Text, TextInput, View } from 'react-native'
import { getApiErrorCode, getApiErrorMessage, sendOtp } from '../../services/authService'

const LOCAL_NUMBER_PATTERN = /^\d{10}$/

export default function LoginScreen(): JSX.Element {
  const router = useRouter()
  const [localNumber, setLocalNumber] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isValid = LOCAL_NUMBER_PATTERN.test(localNumber)

  async function handleSubmit(): Promise<void> {
    if (!isValid || isSubmitting) return
    setError(null)
    setIsSubmitting(true)
    const phone = `+91${localNumber}`

    try {
      await sendOtp(phone)
      // PostHog wrapper is R2 (mobile/CLAUDE.md) — console.log stands in for it in MVP.
      console.log('[analytics] otp_requested', { method: 'sms' })
      router.push({ pathname: '/otp', params: { phone } })
    } catch (err) {
      if (getApiErrorCode(err) === 'OTP_RATE_LIMITED') {
        setError('Too many OTP requests — try again later')
      } else {
        setError(getApiErrorMessage(err))
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <View className="flex-1 justify-center bg-white px-6">
      <Text className="mb-2 text-2xl font-semibold">Enter your phone number</Text>
      <Text className="mb-6 text-sm text-gray-500">
        We'll send you a one-time code to verify it's you.
      </Text>

      <View className="mb-4 flex-row items-center rounded-lg border border-gray-300 px-4 py-3">
        <Text className="mr-2 text-base font-medium text-gray-700">+91</Text>
        <TextInput
          className="flex-1 text-base"
          value={localNumber}
          onChangeText={(text) => setLocalNumber(text.replace(/\D/g, '').slice(0, 10))}
          keyboardType="number-pad"
          placeholder="98765 43210"
          maxLength={10}
          autoFocus
        />
      </View>

      {error ? <Text className="mb-4 text-sm text-red-600">{error}</Text> : null}

      <Pressable
        onPress={handleSubmit}
        disabled={!isValid || isSubmitting}
        className={`items-center rounded-lg py-3 ${isValid && !isSubmitting ? 'bg-blue-600' : 'bg-gray-300'}`}
      >
        {isSubmitting ? (
          <ActivityIndicator color="white" />
        ) : (
          <Text className="text-base font-semibold text-white">Send code</Text>
        )}
      </Pressable>
    </View>
  )
}
