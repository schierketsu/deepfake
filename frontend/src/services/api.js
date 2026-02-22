import axios from 'axios'

// Бэкенд по умолчанию на порту 8000 (для dev и сборки без VITE_API_URL)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 минут для больших файлов
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})

export const analyzeImage = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/api/analyze/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  return response.data
}

export const analyzeVideo = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/api/analyze/video', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  return response.data
}

export const analyzeDocument = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/api/analyze/document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  return response.data
}

export const getReport = (reportUrl) => {
  return `${API_BASE_URL}${reportUrl}`
}

export default api
