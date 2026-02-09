import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { getReferralCode } from '../hooks/useAffiliateTracking';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Token expiry check - refresh if less than 5 minutes remaining
const TOKEN_REFRESH_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

// Track refresh state globally to prevent concurrent refresh attempts
let isRefreshing = false;
let failedQueue: { resolve: (token: string) => void; reject: (error: unknown) => void }[] = [];

/**
 * Decode JWT payload to get expiration time.
 * Returns null if token is invalid or cannot be decoded.
 */
function getTokenExpiry(token: string): number | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const decoded = JSON.parse(atob(payload));
    return decoded.exp ? decoded.exp * 1000 : null; // Convert to milliseconds
  } catch {
    return null;
  }
}

/**
 * Check if access token is expiring soon (within threshold).
 */
function isTokenExpiringSoon(): boolean {
  const token = localStorage.getItem('access_token');
  if (!token) return false;

  const expiry = getTokenExpiry(token);
  if (!expiry) return false;

  return expiry - Date.now() < TOKEN_REFRESH_THRESHOLD_MS;
}

/**
 * Proactively refresh the access token if it's expiring soon.
 * Called before API requests to prevent 401 errors.
 */
async function proactiveTokenRefresh(): Promise<void> {
  if (!isTokenExpiringSoon()) return;

  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return;

  // Prevent concurrent refresh attempts
  if (isRefreshing) return;

  try {
    isRefreshing = true;
    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });

    const { access_token, refresh_token: newRefreshToken } = response.data;
    localStorage.setItem('access_token', access_token);
    if (newRefreshToken) {
      localStorage.setItem('refresh_token', newRefreshToken);
    }
  } catch {
    // Proactive refresh failed - let the 401 interceptor handle it
  } finally {
    isRefreshing = false;
  }
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generate UUID with fallback for non-secure contexts (HTTP)
function generateUUID(): string {
  // crypto.randomUUID() only works in secure contexts (HTTPS or localhost)
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Fallback for HTTP contexts
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Request interceptor to add auth token and proactively refresh expiring tokens
api.interceptors.request.use(
  async (config) => {
    // Proactively refresh token if expiring soon (before the request)
    // Skip for auth endpoints to avoid infinite loops
    const isAuthEndpoint = config.url?.includes('/auth/') || config.url?.includes('/users/login');
    if (!isAuthEndpoint) {
      await proactiveTokenRefresh();
    }

    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add correlation ID for tracing
    if (!config.headers['X-Correlation-ID']) {
      config.headers['X-Correlation-ID'] = generateUUID();
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
const processQueue = (error: unknown, token: string | null = null) => {
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
    // Skip logging expected 404s (feedback not yet generated, etc.)
    if (import.meta.env.DEV) {
      const requestId = error.response?.headers['x-correlation-id'] || error.response?.headers['X-Correlation-ID'];
      const isExpected404 = error.response?.status === 404 && originalRequest?.url?.includes('/feedback/');
      if (requestId && !isExpected404) {
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
// Note: Backend has redirect_slashes=False, so no trailing slashes
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
// Note: Backend has redirect_slashes=False, so no trailing slashes
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

  // Export interview as PDF
  exportPDF: async (id: string) => {
    const response = await api.get(`/interviews/${id}/export`, {
      responseType: 'blob',
    });
    return response;
  },

  // Share management
  createShare: (id: string) =>
    api.post<{
      id: string;
      interview_id: string;
      token: string;
      expires_at: string;
      view_count: number;
      created_at: string;
      share_url: string | null;
    }>(`/interviews/${id}/share`),

  getShares: (id: string) =>
    api.get<Array<{
      id: string;
      interview_id: string;
      token: string;
      expires_at: string;
      view_count: number;
      created_at: string;
      share_url: string | null;
    }>>(`/interviews/${id}/shares`),

  revokeShare: (shareId: string) =>
    api.delete(`/interviews/shares/${shareId}`),

  getSharedInterview: (token: string) =>
    api.get<{
      interview_type: string;
      overall_score: number | null;
      audio_score: number | null;
      content_score: number | null;
      question_count: number;
      created_at: string;
      shared_by: string;
      responses: Array<{
        question: string;
        transcript: string | null;
        audio_url: string | null;
        overall_content_score: number | null;
        strengths: string[];
        improvements: string[];
        detailed_feedback: string | null;
      }>;
    }>(`/interviews/shared/${token}`),
};

// Questions API
// Note: Backend has redirect_slashes=False, so no trailing slashes
export const questionsAPI = {
  getAll: (params?: { category?: string; difficulty?: string }) =>
    api.get('/questions', { params }),

  getById: (id: string) => api.get(`/questions/${id}`),

  getRandomQuestion: (category?: string, difficulty?: string) =>
    api.get('/questions/random', { params: { category, difficulty } }),
};

// Responses API
// Note: Backend has redirect_slashes=False, so no trailing slashes
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
// Note: Backend has redirect_slashes=False, so no trailing slashes
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
// Note: Backend has redirect_slashes=False, so no trailing slashes
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
// Note: Backend has redirect_slashes=False, so no trailing slashes
export const subscriptionsAPI = {
  getStatus: () => api.get('/subscriptions/status'),

  getPricing: () => api.get<{ pro_monthly_price_id: string | null; pro_annual_price_id: string | null }>('/subscriptions/pricing'),

  createCheckout: (priceId: string) => {
    const referralCode = getReferralCode();
    return api.post('/subscriptions/checkout', {
      price_id: priceId,
      ...(referralCode && { referral_code: referralCode }),
    });
  },

  createPortalSession: () =>
    api.post<{ url: string }>('/subscriptions/portal'),

  cancel: () => api.post('/subscriptions/cancel'),
};

// Preparation API
// Note: Backend has redirect_slashes=False, so no trailing slashes
export const preparationAPI = {
  getAll: () =>
    api.get<{
      preparations: Array<{
        id: string;
        question_id: string;
        question_content: string;
        stage: string;
        draft_answer: string | null;
        created_at: string;
        updated_at: string;
      }>;
    }>('/preparation'),
  start: (questionId: string) =>
    api.post<{ preparation_id: string; stage: string; message: string }>('/preparation/start', {
      question_id: questionId,
    }),
  getState: (preparationId: string) =>
    api.get<{
      preparation_id: string;
      stage: string;
      question: {
        id: string;
        content: string;
        category?: string;
        difficulty?: string;
        company_tags?: string[];
      };
      qna: Array<{ question: string; answer: string; order: number }>;
      current_question: string | null;
      draft_answer: string | null;
      attempts: Array<{
        id: string;
        preparation_id: string;
        audio_url: string | null;
        transcript: string | null;
        delivery_score: number | null;
        comparison_feedback: string | null;
        strengths: string[];
        improvements: string[];
        created_at: string;
      }>;
    }>(`/preparation/${preparationId}/state`),
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
  updateDraft: (preparationId: string, draftAnswer: string) =>
    api.patch<{ draft_answer: string; stage: string }>(
      `/preparation/${preparationId}/draft`,
      { draft_answer: draftAnswer }
    ),
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

// User API
// Note: Backend has redirect_slashes=False, so no trailing slashes
export const userAPI = {
  getStats: () => api.get('/users/me/stats'),

  getProgress: () => api.get('/users/me/progress'),

  getReadinessScore: () => api.get('/users/me/readiness-score'),

  getImprovements: () => api.get('/users/me/improvements'),

  getSkillsGap: () => api.get<{
    dimensions: Array<{
      name: string;
      current_score: number;
      target_score: number;
      sessions_with_data: number;
      trend: 'improving' | 'declining' | 'stable';
    }>;
    sessions_analyzed: number;
    data_available: boolean;
    last_updated: string | null;
  }>('/users/me/skills-gap'),

  updateProfile: (data: { full_name?: string; email?: string; experience_level?: string }) =>
    api.patch('/users/me', data),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  deleteAccount: () => api.delete('/users/me'),
};

// Analytics API
// Note: Backend has redirect_slashes=False, so no trailing slashes
export const analyticsAPI = {
  getProgress: () => api.get<{
    data_points: Array<{
      session_id: string;
      created_at: string;
      filler_words_per_minute: number;
      speaking_pace_wpm: number;
      star_compliance_score: number;
      overall_confidence_score: number;
    }>;
    total_sessions: number;
  }>('/analytics/progress'),

  getSummary: () => api.get<{
    avg_filler_words_per_minute: number;
    avg_speaking_pace_wpm: number;
    avg_star_compliance_score: number;
    avg_confidence_score: number;
    total_sessions_analyzed: number;
    improvement_filler_words: number | null;
    improvement_star_compliance: number | null;
    improvement_confidence: number | null;
  }>('/analytics/summary'),

  getSessionAnalytics: (sessionId: string) => api.get(`/analytics/sessions/${sessionId}`),
};

export default api;
