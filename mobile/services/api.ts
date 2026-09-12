// Axios instance — JWT injection, 401 handler, 8s timeout, backoff retry on network errors.
// No API calls in components — everything goes through this client. See root CLAUDE.md §15.

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { router } from 'expo-router'
import { clearTokens, getAccessToken } from './tokenStorage'

const MAX_RETRIES = 2
const RETRY_DELAY_MS = [500, 1000]

type RetryableConfig = InternalAxiosRequestConfig & { _retryCount?: number }

export const api: AxiosInstance = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL,
  timeout: 8000,
})

api.interceptors.request.use(async (config) => {
  const token = await getAccessToken()
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryableConfig | undefined

    if (error.response?.status === 401) {
      await clearTokens()
      router.replace('/login')
      return Promise.reject(error)
    }

    // Network error (no response at all) — retry with backoff, never on 4xx/5xx.
    if (!error.response && config) {
      const retryCount = config._retryCount ?? 0
      if (retryCount < MAX_RETRIES) {
        config._retryCount = retryCount + 1
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS[retryCount]))
        return api(config)
      }
    }

    return Promise.reject(error)
  }
)
