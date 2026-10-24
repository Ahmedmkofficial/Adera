// One switch between the built-in demo data and the real backend.
// Set VITE_USE_MOCK=false (and VITE_API_URL) in a .env file to use the real API.
export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
