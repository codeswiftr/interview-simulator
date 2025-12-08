import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add correlation ID for tracing
    if (!config.headers['X-Correlation-ID']) {
      config.headers['X-Correlation-ID'] = crypto.randomUUID();
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
let isRefreshing = false;
let failedQueue: { resolve: (token: string) => void; reject: (error: any) => void }[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });

  failedQueue = [];
};

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

    // Handle 401 Unauthorized errors - try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't retry the refresh endpoint itself OR the login endpoint
      if (originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/users/login')) {
        if (originalRequest.url?.includes('/auth/refresh')) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');

      if (!refreshToken) {
        // No refresh token, redirect to login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        // Try to refresh the token
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: newRefreshToken } = response.data;

        // Store new tokens
        localStorage.setItem('access_token', access_token);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }

        // Update header for retry
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }

        processQueue(null, access_token);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        // Refresh failed, clear tokens and redirect
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
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

  register: (email: string, password: string, full_name: string, experience_level?: string) =>
    api.post('/users/register', { email, password, full_name, experience_level }),

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: () => api.get('/users/me'),

  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }),

  resetPassword: (token: string, newPassword: string) =>
    api.post('/auth/reset-password', { token, new_password: newPassword }),
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

  getComparison: (sessionId: string) =>
    api.get<{
      session_score: number;
      average_score: number | null;
      improvement_percent: number | null;
      sessions_compared: number;
    }>(`/feedback/session/${sessionId}/comparison`),

  generateForSession: (sessionId: string) =>
    api.post(`/feedback/generate/session/${sessionId}`),

  generateForResponse: (responseId: string) =>
    api.post(`/feedback/generate/response/${responseId}`),
};

// Upload API for audio files
export const uploadAPI = {
  uploadAudio: (
    file: File,
    sessionId: string | null,
    questionId: string | null,
    preparationId?: string | null
  ) => {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }
    if (questionId) {
      formData.append('question_id', questionId);
    }
    if (preparationId) {
      formData.append('preparation_id', preparationId);
    }

    return api.post('/upload/audio', formData, {
      timeout: 60000, // 60 seconds for large audio files
      headers: {
        'Content-Type': undefined, // Remove default JSON content type, let browser set multipart/form-data with boundary
      },
    });
  },
};

// Subscriptions API
export const subscriptionsAPI = {
  getStatus: () => api.get('/subscriptions/status'),

  getPricing: () => api.get<{ pro_monthly_price_id: string | null; pro_annual_price_id: string | null }>('/subscriptions/pricing'),

  createCheckout: (priceId: string) =>
    api.post('/subscriptions/checkout', { price_id: priceId }),

  createPortalSession: () =>
    api.post<{ url: string }>('/subscriptions/portal'),

  cancel: () => api.post('/subscriptions/cancel'),
};

// User API
export const preparationAPI = {
  start: (questionId: string) =>
    api.post<{ preparation_id: string; stage: string; message: string }>('/preparation/start', {
      question_id: questionId,
    }),
  getDetectiveQuestion: (preparationId: string) =>
    api.post<{ question: string; order: number; is_complete: boolean }>(
      `/preparation/${preparationId}/detective/question`
    ),
  submitDetectiveAnswer: (preparationId: string, answer: string) =>
    api.post<{ next_question: string | null; stage: string; is_complete: boolean }>(
      `/preparation/${preparationId}/detective/answer`,
      { answer }
    ),
  generateDraft: (preparationId: string) =>
    api.post<{ draft_answer: string; stage: string }>(`/preparation/${preparationId}/generate-draft`),
  getDraft: (preparationId: string) =>
    api.get<{ draft_answer: string; stage: string }>(`/preparation/${preparationId}/draft`),
  startPractice: (preparationId: string) =>
    api.post<{ attempt_id: string; stage: string }>(
      `/preparation/${preparationId}/practice/start`
    ),
  submitPractice: (preparationId: string, audioUrl: string) =>
    api.post<{ attempt_id: string; transcript: string; stage: string }>(
      `/preparation/${preparationId}/practice/submit`,
      { audio_url: audioUrl }
    ),
  getAttempts: (preparationId: string) =>
    api.get<{
      attempts: Array<{
        id: string;
        preparation_id: string;
        audio_url: string | null;
        transcript: string | null;
        delivery_score: number | null;
        comparison_feedback: string | null;
        created_at: string;
      }>;
    }>(`/preparation/${preparationId}/attempts`),
  rateDelivery: (preparationId: string, attemptId: string) =>
    api.post<{
      delivery_score: number;
      content_coverage: number;
      key_points: number;
      flow_structure: number;
      comparison_feedback: string;
      strengths: string[];
      improvements: string[];
      stage: string;
    }>(`/preparation/${preparationId}/rate-delivery`, {
      attempt_id: attemptId,
    }),
  getComparison: (preparationId: string, attemptId: string) =>
    api.get<{
      draft: string;
      delivery: string;
      delivery_score: number | null;
      comparison_feedback: string | null;
      strengths: string[];
      improvements: string[];
    }>(`/preparation/${preparationId}/comparison?attempt_id=${attemptId}`),
};

export const userAPI = {
  getStats: () => api.get('/users/me/stats'),

  getProgress: () => api.get('/users/me/progress'),

  getReadinessScore: () => api.get('/users/me/readiness-score'),

  updateProfile: (data: { full_name?: string; email?: string; experience_level?: string }) =>
    api.patch('/users/me', data),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  deleteAccount: () => api.delete('/users/me'),
};

export default api;
