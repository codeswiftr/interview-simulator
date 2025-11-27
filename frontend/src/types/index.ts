// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Question types
export interface Question {
  id: string;
  category: 'behavioral' | 'technical' | 'system_design';
  difficulty: 'easy' | 'medium' | 'hard';
  content: string; // The question text
  company_tags?: string[];
  topic_tags?: string[];
  sample_answer?: string;
  evaluation_criteria?: Record<string, unknown>;
  expected_duration_seconds: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Interview Session types
export interface InterviewSession {
  id: string;
  interview_type: 'behavioral' | 'technical' | 'system_design' | 'mixed';
  company_style?: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'analyzed' | 'cancelled';
  question_count: number;
  overall_score?: number;
  duration_seconds?: number;
  created_at: string;
}

// Response types
export interface InterviewResponse {
  id: string;
  session_id: string;
  question_id: string;
  audio_url: string;
  transcription?: string;
  duration_seconds?: number;
  submitted_at: string;
  created_at: string;
  updated_at: string;
  question?: Question;
  feedback?: Feedback;
}

// Content Feedback (per response)
export interface ContentFeedback {
  technical_accuracy: number;
  answer_structure: number;
  completeness: number;
  overall_content_score: number;
  strengths: string[];
  improvements: string[];
  detailed_feedback: string;
}

// Session Feedback (aggregated)
export interface SessionFeedback {
  overall_score: number;
  audio_score: number;
  content_score: number;
  top_strengths: string[];
  top_improvements: string[];
  recommended_practice_areas: string[];
}

// Legacy Feedback type for compatibility
export interface Feedback {
  id: string;
  response_id: string;
  overall_score: number;
  content_score: number;
  delivery_score: number;
  structure_score: number;
  technical_accuracy_score?: number;
  communication_clarity_score: number;
  strengths: string[];
  weaknesses: string[];
  improvement_suggestions: string[];
  detailed_analysis: string;
  created_at: string;
  updated_at: string;
}

// Session Summary types
export interface SessionSummary {
  session: InterviewSession;
  responses: InterviewResponse[];
  average_scores: {
    overall: number;
    content: number;
    delivery: number;
    structure: number;
    communication: number;
  };
  total_duration_seconds: number;
}

// Dashboard Stats types
export interface DashboardStats {
  total_sessions: number;
  completed_sessions: number;
  average_score: number;
  total_practice_time_seconds: number;
  recent_sessions: InterviewSession[];
  score_trend: Array<{ date: string; score: number }>;
}

// Form types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData {
  email: string;
  password: string;
  full_name: string;
  confirm_password: string;
}

export interface CreateInterviewFormData {
  interview_type: 'behavioral' | 'technical' | 'system_design' | 'mixed';
  company_style?: string;
  question_count: number;
}

// API Error types
export interface APIError {
  message: string;
  errors?: Record<string, string[]>;
  status_code?: number;
}
