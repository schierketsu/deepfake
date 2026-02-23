import axios from 'axios'

// Бэкенд: 127.0.0.1:8000 как в логе uvicorn (localhost на Windows иногда даёт 404)
const API_BASE_URL = import.meta.env.VITE_API_URL?.trim() || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : 'http://127.0.0.1:8000')

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 минут для больших файлов
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})

// При 404 показываем, куда ушёл запрос (для отладки)
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 404 && err.config) {
      const url = err.config.baseURL + err.config.url
      console.warn('[API] 404 по адресу:', url)
    }
    return Promise.reject(err)
  }
)

export const analyzeDocument = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await api.post('/api/analyze/document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      const fallbackResponse = await api.post('/api/analyze/document/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return fallbackResponse.data
    }
    throw error
  }
}

export const getReport = (reportUrl) => {
  return `${API_BASE_URL}${reportUrl}`
}

export default api
