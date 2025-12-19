import axios from 'axios'
import { supabase } from './supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 添加请求拦截器，自动添加 token
api.interceptors.request.use(async (config) => {
  // 优先从 Supabase SDK 获取最新的 session (自动处理刷新)
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 类型定义
export interface AuthResponse {
  user_id: string
  email: string
  access_token: string
  refresh_token: string
}

export interface UploadResponse {
  upload_id: string
  type: string
  status: string
  message: string
}

export interface AnalyzeResponse {
  task_id: string
  status: string
  message: string
}

export interface TaskStatus {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  result?: any
  error?: string
}

export interface AnalysisDetail {
  id: string
  upload_id: string
  visual_description?: string
  extracted_text?: string
  intent_analysis?: any
  full_context?: any
  status: string
  created_at: string
  original_content?: {
    type: 'image' | 'url' | 'text'
    content: string
  }
}

export interface RecommendationTile {
  id: string
  title: string
  description: string
  url?: string
  image_url?: string
  source: string
  relevance_score: number
  tile_type: string
  user_action?: 'keep' | 'discard' | null
  display_order: number
  article_html?: string
}

export interface ArticleResponse {
  id: string
  article_html: string
}

export interface RecommendationsResponse {
  analysis_id: string
  recommendations: RecommendationTile[]
  total: number
}

export interface HistoryItem {
  id: string
  type: string
  content_preview: string
  analysis_id?: string
  analysis_summary?: string
  recommendation_count: number
  created_at: string
  full_context?: any
}

export interface HistoryResponse {
  items: HistoryItem[]
  total: number
  page: number
  page_size: number
}

// API 方法
export const authAPI = {
  signup: (email: string, password: string, username?: string) =>
    api.post<AuthResponse>('/api/auth/signup', { email, password, username }),

  signin: (email: string, password: string) =>
    api.post<AuthResponse>('/api/auth/signin', { email, password }),

  signout: () => api.post('/api/auth/signout'),

  me: () => api.get('/api/auth/me'),
}

export const uploadAPI = {
  image: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<UploadResponse>('/api/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  url: (url: string, userId: string) =>
    api.post<UploadResponse>('/api/upload/url', {
      type: 'url',
      content: url,
      user_id: userId,
    }),

  text: (text: string, userId: string) =>
    api.post<UploadResponse>('/api/upload/text', {
      type: 'text',
      content: text,
      user_id: userId,
    }),
}

export const analysisAPI = {
  analyze: (uploadId: string) =>
    api.post<AnalyzeResponse>('/api/analysis/analyze', { upload_id: uploadId }),

  getTaskStatus: (taskId: string) =>
    api.get<TaskStatus>(`/api/analysis/task/${taskId}`),

  getDetails: (analysisId: string) =>
    api.get<AnalysisDetail>(`/api/analysis/${analysisId}`),
}

export const recommendationsAPI = {
  get: (analysisId: string) =>
    api.get<RecommendationsResponse>(`/api/recommendations/analysis/${analysisId}`),

  feedback: (recommendationId: string, action: 'keep' | 'discard') =>
    api.post('/api/recommendations/feedback', {
      recommendation_id: recommendationId,
      action,
    }),

  getArticle: (recommendationId: string, regenerate = false) =>
    api.get<ArticleResponse>(`/api/recommendations/${recommendationId}/article`, {
      params: { regenerate }
    }),
}

export const historyAPI = {
  list: (page = 1, pageSize = 20) =>
    api.get<HistoryResponse>('/api/history/', { params: { page, page_size: pageSize } }),

  delete: (uploadId: string) => api.delete(`/api/history/${uploadId}`),
}

export default api