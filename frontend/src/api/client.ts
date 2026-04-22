import axios from 'axios'
import { useAuthStore } from '../store/auth'

const API_URL = import.meta.env.VITE_API_URL || ''

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const { data } = await apiClient.post('/auth/login', { email, password })
    return data
  },
  register: async (email: string, password: string, name: string) => {
    const { data } = await apiClient.post('/auth/register', { email, password, name })
    return data
  },
  logout: async () => {
    const { data } = await apiClient.post('/auth/logout')
    return data
  },
  me: async () => {
    const { data } = await apiClient.get('/auth/me')
    return data
  },
}

// Patients API
export const patientsApi = {
  list: async (params?: { skip?: number; limit?: number }) => {
    const { data } = await apiClient.get('/patients', { params })
    return data
  },
  get: async (id: string) => {
    const { data } = await apiClient.get(`/patients/${id}`)
    return data
  },
  create: async (patient: {
    first_name: string
    last_name: string
    date_of_birth?: string
    gender?: string
    phone?: string
    email?: string
  }) => {
    const { data } = await apiClient.post('/patients', patient)
    return data
  },
  update: async (id: string, patient: Partial<{
    first_name: string
    last_name: string
    date_of_birth: string
    gender: string
    phone: string
    email: string
  }>) => {
    const { data } = await apiClient.put(`/patients/${id}`, patient)
    return data
  },
}

// Triage API
export const triageApi = {
  createThread: async (patientId: string, chiefComplaint?: string) => {
    const { data } = await apiClient.post('/triage/threads', {
      patient_id: patientId,
      chief_complaint: chiefComplaint,
    })
    return data
  },
  getThread: async (threadId: string) => {
    const { data } = await apiClient.get(`/triage/threads/${threadId}`)
    return data
  },
  listThreads: async (params?: { patient_id?: string; status?: string }) => {
    const { data } = await apiClient.get('/triage/threads', { params })
    return data
  },
  sendMessage: async (threadId: string, content: string) => {
    const { data } = await apiClient.post(`/triage/threads/${threadId}/messages`, {
      content,
    })
    return data
  },
  getMessages: async (threadId: string) => {
    const { data } = await apiClient.get(`/triage/threads/${threadId}/messages`)
    return data
  },
  getArtifacts: async (threadId: string) => {
    const { data } = await apiClient.get(`/triage/threads/${threadId}/artifacts`)
    return data
  },
}

// Dashboard API
export const dashboardApi = {
  getSummary: async () => {
    const { data } = await apiClient.get('/dashboard/summary')
    return data
  },
  getPatients: async (params?: { skip?: number; limit?: number }) => {
    const { data } = await apiClient.get('/dashboard/patients', { params })
    return data
  },
}

