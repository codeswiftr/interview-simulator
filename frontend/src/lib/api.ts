import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

// Get API base URL from environment or use default
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors and token refresh
api.interceptors.response.use(
  (response) => {
    // Minimal debug logging in development builds
    if (import.meta.env.DEV) {
      const requestId = response.headers['x-correlation-id'] || response.headers['X-Correlation-ID'];
      if (requestId) {
        console.debug(`[API] ${response.config.method?.toUpperCase()} ${response.config.url} - Request ID: ${requestId}`);
      }
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Minimal debug logging in development builds
    if (import.meta.env.DEV) {
      const requestId = error.response?.headers['x-correlation-id'] || error.response?.headers['X-Correlation-ID'];
      if (requestId) {
        console.warn(`[API Error] ${originalRequest?.method?.toUpperCase()} ${originalRequest?.url} - Request ID: ${requestId} - Status: ${error.response?.status}`);
      }
    }

    // Handle 401 Unauthorized errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      // Redirect to login page
      window.location.href = '/login';
    }

    // Handle 402 Payment Required (quota exceeded)
    // Don't redirect, let component handle it
    if (error.response?.status === 402) {
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/users/login', { email, password }),

  register: (email: string, password: string, full_name: string) =>
    api.post('/users/register', { email, password, full_name }),

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: () => api.get('/users/me'),
};

// Interview Sessions API
export const interviewsAPI = {
  getAll: () => api.get('/interviews'),

  getById: (id: string) => api.get(`/interviews/${id}`),

  create: (data: {
    interview_type: string;
    company_style?: string;
    question_count?: number;
    difficulty?: string;
  }) => api.post('/interviews', data),

  quickPractice: (questionId: string) =>
    api.post('/interviews/quick-practice', null, {
      params: { question_id: questionId },
    }),

  start: (id: string) => api.post(`/interviews/${id}/start`),

  end: (id: string) => api.post(`/interviews/${id}/end`),

  getQuestions: (id: string) => api.get(`/interviews/${id}/questions`),

  getResponses: (id: string) => api.get(`/interviews/${id}/responses`),

  delete: (id: string) => api.delete(`/interviews/${id}`),
};

// Questions API
export const questionsAPI = {
  getAll: (params?: { category?: string; difficulty?: string }) =>
    api.get('/questions', { params }),

  getById: (id: string) => api.get(`/questions/${id}`),

  getRandomQuestion: (category?: string, difficulty?: string) =>
    api.get('/questions/random', { params: { category, difficulty } }),
};

// Responses API
export const responsesAPI = {
  submit: (sessionId: string, data: {
    question_id: string;
    audio_url?: string;
    video_url?: string;
    transcript?: string;
    duration_seconds?: number;
  }) => api.post(`/interviews/${sessionId}/responses`, data),

  getBySessionId: (sessionId: string) =>
    api.get(`/interviews/${sessionId}/responses`),

  getById: (id: string) => api.get(`/responses/${id}`),
};

// Feedback API
export const feedbackAPI = {
  getByResponseId: (responseId: string) =>
    api.get(`/feedback/response/${responseId}`),

  getBySessionId: (sessionId: string) =>
    api.get(`/feedback/session/${sessionId}`),

  getAllBySessionId: (sessionId: string) =>
    api.get(`/feedback/session/${sessionId}/all`),

  getSessionStatus: (sessionId: string) =>
    api.get(`/feedback/session/${sessionId}/status`),

  generateForSession: (sessionId: string) =>
    api.post(`/feedback/generate/session/${sessionId}`),

  generateForResponse: (responseId: string) =>
    api.post(`/feedback/generate/response/${responseId}`),
};

// Upload API for audio files
export const uploadAPI = {
  uploadAudio: (file: File, sessionId: string, questionId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    formData.append('question_id', questionId);

    return api.post('/upload/audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 seconds for large audio files
    });
  },
};

// Subscriptions API
export const subscriptionsAPI = {
  getStatus: () => api.get('/subscriptions/status'),

  createCheckout: (priceId: string) =>
    api.post('/subscriptions/checkout', { price_id: priceId }),

  cancel: () => api.post('/subscriptions/cancel'),
};

// User API
export const userAPI = {
  getStats: () => api.get('/users/me/stats'),

  getProgress: () => api.get('/users/me/progress'),

  updateProfile: (data: { full_name?: string; email?: string }) =>
    api.patch('/users/me', data),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  deleteAccount: () => api.delete('/users/me'),
};

export default api;
