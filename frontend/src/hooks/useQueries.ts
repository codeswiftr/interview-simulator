import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  authAPI,
  interviewsAPI,
  questionsAPI,
  feedbackAPI,
  userAPI,
  subscriptionsAPI,
} from '../lib/api';
import { queryKeys } from '../lib/queryClient';

/**
 * React Query hooks for data fetching with automatic caching and deduplication.
 * These hooks replace direct API calls in components and provide:
 * - Automatic caching (5 min stale time by default)
 * - Request deduplication
 * - Loading and error states
 * - Background refetching
 */

// ========== User Hooks ==========

export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.userProfile(),
    queryFn: async () => {
      const response = await authAPI.getCurrentUser();
      return response.data;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes - user data changes infrequently
  });
}

export function useUserStats() {
  return useQuery({
    queryKey: queryKeys.dashboardStats(),
    queryFn: async () => {
      const response = await userAPI.getStats();
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes - stats may change during session
  });
}

export function useUserProgress() {
  return useQuery({
    queryKey: [...queryKeys.stats, 'progress'] as const,
    queryFn: async () => {
      const response = await userAPI.getProgress();
      return response.data;
    },
  });
}

export function useReadinessScore() {
  return useQuery({
    queryKey: [...queryKeys.stats, 'readiness'] as const,
    queryFn: async () => {
      const response = await userAPI.getReadinessScore();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

// ========== Interview Hooks ==========

export function useInterviews() {
  return useQuery({
    queryKey: queryKeys.interviewsList(),
    queryFn: async () => {
      const response = await interviewsAPI.getAll();
      return response.data;
    },
  });
}

export function useInterview(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.interviewDetail(id || ''),
    queryFn: async () => {
      if (!id) throw new Error('Interview ID is required');
      const response = await interviewsAPI.getById(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useInterviewQuestions(interviewId: string | undefined) {
  return useQuery({
    queryKey: [...queryKeys.interviewDetail(interviewId || ''), 'questions'] as const,
    queryFn: async () => {
      if (!interviewId) throw new Error('Interview ID is required');
      const response = await interviewsAPI.getQuestions(interviewId);
      return response.data;
    },
    enabled: !!interviewId,
  });
}

export function useInterviewResponses(interviewId: string | undefined) {
  return useQuery({
    queryKey: [...queryKeys.interviewDetail(interviewId || ''), 'responses'] as const,
    queryFn: async () => {
      if (!interviewId) throw new Error('Interview ID is required');
      const response = await interviewsAPI.getResponses(interviewId);
      return response.data;
    },
    enabled: !!interviewId,
  });
}

// ========== Questions Hooks ==========

export function useQuestions(params?: { category?: string; difficulty?: string }) {
  return useQuery({
    queryKey: queryKeys.questionsList(params),
    queryFn: async () => {
      const response = await questionsAPI.getAll(params);
      return response.data;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes - questions rarely change
  });
}

export function useQuestion(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.questionDetail(id || ''),
    queryFn: async () => {
      if (!id) throw new Error('Question ID is required');
      const response = await questionsAPI.getById(id);
      return response.data;
    },
    enabled: !!id,
    staleTime: 30 * 60 * 1000,
  });
}

// ========== Feedback Hooks ==========

export function useFeedbackForSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.feedbackForInterview(sessionId || ''),
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID is required');
      const response = await feedbackAPI.getAllBySessionId(sessionId);
      return response.data;
    },
    enabled: !!sessionId,
    staleTime: 10 * 60 * 1000, // 10 minutes - feedback doesn't change after generation
  });
}

export function useFeedbackStatus(sessionId: string | undefined) {
  return useQuery({
    queryKey: [...queryKeys.feedbackForInterview(sessionId || ''), 'status'] as const,
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID is required');
      const response = await feedbackAPI.getSessionStatus(sessionId);
      return response.data;
    },
    enabled: !!sessionId,
    refetchInterval: (query) => {
      // Poll every 2 seconds if feedback is still generating
      const data = query.state.data as { status?: string } | undefined;
      return data?.status === 'processing' ? 2000 : false;
    },
  });
}

export function useFeedbackComparison(sessionId: string | undefined) {
  return useQuery({
    queryKey: [...queryKeys.feedbackForInterview(sessionId || ''), 'comparison'] as const,
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID is required');
      const response = await feedbackAPI.getComparison(sessionId);
      return response.data;
    },
    enabled: !!sessionId,
  });
}

// ========== Subscription Hooks ==========

export function useSubscriptionStatus() {
  return useQuery({
    queryKey: queryKeys.currentSubscription(),
    queryFn: async () => {
      const response = await subscriptionsAPI.getStatus();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function usePricing() {
  return useQuery({
    queryKey: queryKeys.pricing(),
    queryFn: async () => {
      const response = await subscriptionsAPI.getPricing();
      return response.data;
    },
    staleTime: 60 * 60 * 1000, // 1 hour - pricing rarely changes
  });
}

// ========== Mutations ==========

export function useCreateInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      interview_type: string;
      company_style?: string;
      question_count?: number;
      difficulty?: string;
    }) => {
      const response = await interviewsAPI.create(data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate interviews list to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.interviewsList() });
    },
  });
}

export function useDeleteInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await interviewsAPI.delete(id);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.interviewsList() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboardStats() });
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { full_name?: string; email?: string; experience_level?: string }) => {
      const response = await userAPI.updateProfile(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.userProfile() });
    },
  });
}

export function useGenerateFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await feedbackAPI.generateForSession(sessionId);
      return response.data;
    },
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.feedbackForInterview(sessionId) });
    },
  });
}
