import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, BarChart2, Target, TrendingUp, AlertCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { interviewsAPI } from '../lib/api';
import StatsCard from '../components/dashboard/StatsCard';
import InterviewCard from '../components/interview/InterviewCard';
import NewInterviewModal from '../components/interview/NewInterviewModal';
import type { InterviewSession, CreateInterviewFormData } from '../types';

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    loadInterviews();
  }, []);

  const loadInterviews = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await interviewsAPI.getAll();
      setSessions(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load interviews');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateInterview = async (data: CreateInterviewFormData) => {
    const response = await interviewsAPI.create(data);
    const newSession = response.data;

    // Navigate to the interview session
    navigate(`/interview/${newSession.id}`);
  };

  const handleSessionClick = (session: InterviewSession) => {
    navigate(`/interview/${session.id}`);
  };

  // Calculate stats
  const stats = {
    totalInterviews: sessions.length,
    completedInterviews: sessions.filter((s) => s.status === 'completed').length,
    averageScore: sessions
      .filter((s) => s.overall_score !== null && s.overall_score !== undefined)
      .reduce((acc, s) => acc + (s.overall_score || 0), 0) /
      Math.max(1, sessions.filter((s) => s.overall_score !== null).length),
    inProgress: sessions.filter((s) => s.status === 'in_progress').length,
  };

  return (
    <div className="min-h-screen bg-surface-primary">
      <div className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Header Section */}
        <div className="mb-8">
          <h1 className="heading-page mb-2">Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!</h1>
          <p className="text-text-secondary">Track your progress and continue practicing your interview skills.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Interviews"
            value={stats.totalInterviews}
            icon={BarChart2}
            subtitle={`${stats.completedInterviews} completed`}
          />
          <StatsCard
            title="Average Score"
            value={stats.averageScore > 0 ? `${Math.round(stats.averageScore)}/100` : 'N/A'}
            icon={Target}
            subtitle={stats.averageScore > 0 ? 'All time average' : 'Complete interviews to see'}
          />
          <StatsCard
            title="In Progress"
            value={stats.inProgress}
            icon={TrendingUp}
            subtitle={stats.inProgress > 0 ? 'Resume practice' : 'Start a new interview'}
          />
          <StatsCard
            title="Practice Streak"
            value="Coming Soon"
            icon={TrendingUp}
            subtitle="Feature in development"
          />
        </div>

        {/* Start New Interview CTA */}
        <div className="mb-8">
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn-primary w-full md:w-auto flex items-center justify-center gap-2"
          >
            <Plus size={20} />
            Start New Interview
          </button>
        </div>

        {/* Interview History */}
        <div className="mb-4">
          <h2 className="heading-section mb-4">Recent Interviews</h2>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="card p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-electric-blue border-t-transparent mb-4"></div>
            <p className="text-text-secondary">Loading your interviews...</p>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="card p-8 border-status-error/20 bg-status-error/5">
            <div className="flex items-center gap-3 text-status-error">
              <AlertCircle size={24} />
              <div>
                <p className="font-semibold mb-1">Failed to load interviews</p>
                <p className="body-small">{error}</p>
              </div>
            </div>
            <button
              onClick={loadInterviews}
              className="btn-secondary mt-4"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && sessions.length === 0 && (
          <div className="card p-12 text-center">
            <div className="max-w-md mx-auto">
              <BarChart2 size={48} className="text-text-tertiary mx-auto mb-4" />
              <h3 className="heading-card mb-2">No interviews yet</h3>
              <p className="text-text-secondary mb-6">
                Get started by creating your first interview session. Practice makes perfect!
              </p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="btn-primary"
              >
                <Plus size={20} className="inline mr-2" />
                Start Your First Interview
              </button>
            </div>
          </div>
        )}

        {/* Interview List */}
        {!isLoading && !error && sessions.length > 0 && (
          <div className="grid gap-4">
            {sessions.map((session) => (
              <InterviewCard
                key={session.id}
                session={session}
                onClick={() => handleSessionClick(session)}
              />
            ))}
          </div>
        )}
      </div>

      {/* New Interview Modal */}
      <NewInterviewModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateInterview}
      />
    </div>
  );
}
