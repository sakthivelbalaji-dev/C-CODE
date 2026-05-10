const API_BASE = '/api'
export const API_BASE_URL = import.meta.env.VITE_API_URL || API_BASE

export function apiUrl(path) {
  return `${API_BASE_URL}${path}`
}
