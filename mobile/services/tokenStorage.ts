// JWT + refresh token persistence via expo-secure-store.
// Never use AsyncStorage here — it's plaintext on disk. See root CLAUDE.md §22.

import * as SecureStore from 'expo-secure-store'

const ACCESS_TOKEN_KEY = 'smartcart_jwt_access_token'
const REFRESH_TOKEN_KEY = 'smartcart_jwt_refresh_token'

export async function setTokens(accessToken: string, refreshToken: string): Promise<void> {
  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken)
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken)
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY)
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY)
}

export async function clearTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY)
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY)
}
