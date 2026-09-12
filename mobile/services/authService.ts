// OTP send/verify API calls + typed error helpers. See api/CLAUDE.md → OTP & Auth Flow
// for the exact error codes this wraps.

import { AxiosError } from 'axios'
import { api } from './api'

type ApiErrorBody = {
  error: { code: string; message: string; details: Record<string, unknown> }
}

type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export function getApiErrorCode(error: unknown): string | null {
  const axiosError = error as AxiosError<ApiErrorBody>
  return axiosError.response?.data?.error?.code ?? null
}

export function getApiErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<ApiErrorBody>
  return axiosError.response?.data?.error?.message ?? "Couldn't reach the server — check your connection"
}

export async function sendOtp(phone: string): Promise<void> {
  await api.post('/v1/auth/send-otp', { phone })
}

export async function verifyOtp(
  phone: string,
  otp: string
): Promise<{ accessToken: string; refreshToken: string }> {
  const { data } = await api.post<TokenResponse>('/v1/auth/verify-otp', { phone, otp })
  return { accessToken: data.access_token, refreshToken: data.refresh_token }
}
