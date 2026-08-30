// axios instance — JWT injection, 401 handler, 8s timeout, offline sync queue integration.
// Placeholder. See progress.md → Mobile — Foundation and mobile/CLAUDE.md → API Client.

import axios, { AxiosInstance } from 'axios'

export const api: AxiosInstance = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL,
  timeout: 8000,
})
