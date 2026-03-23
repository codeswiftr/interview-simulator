import { QueryClient } from '@tanstack/react-query';

/**
 * Global QueryClient configuration for React Query.
 *
 * Default settings:
 * - staleTime: 5 minutes - data is considered fresh for 5 minutes
 * - gcTime: 30 minutes - unused data is garbage collected after 30 minutes
 * - retry: 1 - retry failed requests once
 * - refetchOnWindowFocus: false - don't refetch on window focus (user-controlled)
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 30 * 60 * 1000, // 30 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 0,
    },
  },
});

/**
 * Query keys factory for type-safe and consistent query key management.
 * Use these to ensure cache invalidation works correctly across the app.
 */
export const queryKeys = {
  // User & Auth
  user: ['user'] as const,
  userProfile: () => [...queryKeys.user, 'profile'] as const,

  // Interviews
  interviews: ['interviews'] as const,
  interviewsList: () => [...queryKeys.interviews, 'list'] as const,
  interviewDetail: (id: string) => [...queryKeys.interviews, 'detail', id] as const,
  interviewProgress: (id: string) => [...queryKeys.interviews, 'progress', id] as const,

  // Questions
  questions: ['questions'] as const,
  questionsList: (params?: { category?: string; difficulty?: string }) =>
    [...queryKeys.questions, 'list', params] as const,
  questionDetail: (id: string) => [...queryKeys.questions, 'detail', id] as const,

  // Feedback
  feedback: ['feedback'] as const,
  feedbackForAnswer: (answerId: string) => [...queryKeys.feedback, 'answer', answerId] as const,
  feedbackForInterview: (interviewId: string) => [...queryKeys.feedback, 'interview', interviewId] as const,

  // Dashboard stats
  stats: ['stats'] as const,
  dashboardStats: () => [...queryKeys.stats, 'dashboard'] as const,

  // Subscriptions
  subscription: ['subscription'] as const,
  currentSubscription: () => [...queryKeys.subscription, 'current'] as const,
  pricing: () => [...queryKeys.subscription, 'pricing'] as const,
} as const;
