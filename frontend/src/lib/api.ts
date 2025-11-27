import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
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
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      // Redirect to login page
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { username: email, password }),

  register: (email: string, password: string, full_name: string) =>
    api.post('/auth/register', { email, password, full_name }),

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: () => api.get('/auth/me'),
};

// Interview Sessions API
export const interviewsAPI = {
  getAll: () => api.get('/interviews'),

  getById: (id: string) => api.get(`/interviews/${id}`),

  create: (data: {
    interview_type: string;
    company_style?: string;
    question_count?: number;
  }) => api.post('/interviews', data),

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

export default api;
