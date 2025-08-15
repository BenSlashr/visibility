import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios'

// Types pour les réponses API standard
export interface ApiResponse<T = any> {
  data: T
  message?: string
  success?: boolean
}

export interface ApiError {
  detail: string
  status_code: number
  type?: string
}

export interface PaginationParams {
  skip?: number
  limit?: number
}

// Configuration de l'instance Axios
// Vite injecte import.meta.env en runtime; casting pour TS
const envAny = (import.meta as any)?.env || {}
const API_BASE_URL = envAny.VITE_API_URL || 'http://localhost:8021'
const API_TIMEOUT = Number(envAny.VITE_API_TIMEOUT) || 30000
const DEV_MODE = envAny.VITE_DEV_MODE === 'true'

// Base URL pour les appels API en production (avec base path)
const getApiBaseUrl = () => {
  if (import.meta.env.PROD) {
    // En production, utiliser le chemin relatif avec le base path
    return '/nom-outil/api/v1'
  }
  // En développement, utiliser l'URL complète
  return `${API_BASE_URL}/api/v1`
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Intercepteur de requête pour les logs en dev
apiClient.interceptors.request.use(
  (config) => {
    if (DEV_MODE) {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
        data: config.data,
        params: config.params,
      })
    }
    return config
  },
  (error) => {
    if (DEV_MODE) {
      console.error('❌ API Request Error:', error)
    }
    return Promise.reject(error)
  }
)

// Intercepteur de réponse pour gestion d'erreurs globales
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    if (DEV_MODE) {
      console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data,
      })
    }
    return response
  },
  (error: AxiosError<ApiError>) => {
    if (DEV_MODE) {
      console.error('❌ API Response Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        data: error.response?.data,
      })
    }

    // Gestion des erreurs communes
    const status = error.response?.status
    if (status === 401) {
      console.warn('🔒 Non autorisé - Redirection vers login nécessaire')
      // TODO: Redirection vers page de login si implémentée
    } else if (status === 404) {
      console.warn('🔍 Ressource non trouvée')
    } else if (typeof status === 'number' && status >= 500) {
      console.error('🔥 Erreur serveur - Vérifier le backend')
    } else if (error.code === 'ECONNABORTED') {
      console.error('⏱️ Timeout - Requête trop lente')
    } else if (error.code === 'ERR_NETWORK') {
      console.error('🌐 Erreur réseau - Backend inaccessible')
    }

    return Promise.reject(error)
  }
)

// Client API avec méthodes utilitaires
export class ApiClient {
  static async get<T>(url: string, params?: any): Promise<T> {
    const response = await apiClient.get<T>(url, { params })
    return response.data
  }

  static async post<T>(url: string, data?: any): Promise<T> {
    const response = await apiClient.post<T>(url, data)
    return response.data
  }

  static async put<T>(url: string, data?: any): Promise<T> {
    const response = await apiClient.put<T>(url, data)
    return response.data
  }

  static async patch<T>(url: string, data?: any): Promise<T> {
    const response = await apiClient.patch<T>(url, data)
    return response.data
  }

  static async delete<T>(url: string): Promise<T> {
    const response = await apiClient.delete<T>(url)
    return response.data
  }

  // Méthode utilitaire pour tester la connexion
  static async testConnection(): Promise<boolean> {
    try {
      await apiClient.get('/health', { timeout: 5000 })
      return true
    } catch (error) {
      console.error('❌ Test de connexion API échoué:', error)
      return false
    }
  }
}

// Export du client axios pour les cas spéciaux
export { apiClient as default } 