import axios from 'axios'
import { getToken } from '../auth/session'
import { API_URL } from './config'
import { UNAUTHORIZED_EVENT } from './events'

// The one Axios instance for the whole app.
export const http = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the signed-in user's token to every request.
http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// A 401 on any normal request means the session ended. A 401 from the sign-in
// form itself only means "wrong password", so that one is left alone.
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url ?? ''
    const isAuthForm = url.startsWith('/auth/')
    if (error.response?.status === 401 && !isAuthForm) {
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
    }
    return Promise.reject(error)
  },
)
