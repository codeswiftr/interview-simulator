import { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  MessageSquare,
  Mic2,
  Target,
  Star,
  AlertCircle,
  BarChart3
} from 'lucide-react';
import { analyticsAPI } from '../lib/api';
import { Card } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';
import type { AxiosError } from 'axios';

interface AnalyticsDataPoint {
  session_id: string;
  created_at: string;
  filler_words_per_minute: number;
  speaking_pace_wpm: number;
  star_compliance_score: number;
  overall_confidence_score: number;
}

interface AnalyticsSummary {
  avg_filler_words_per_minute: number;
  avg_speaking_pace_wpm: number;
  avg_star_compliance_score: number;
  avg_confidence_score: number;
  total_sessions_analyzed: number;
  improvement_filler_words: number | null;
  improvement_star_compliance: number | null;
  improvement_confidence: number | null;
}

export default function AnalyticsDashboardPage() {
  const [dataPoints, setDataPoints] = useState<AnalyticsDataPoint[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [progressRes, summaryRes] = await Promise.all([
        analyticsAPI.getProgress(),
        analyticsAPI.getSummary(),
      ]);

      setDataPoints(progressRes.data.data_points);
      setSummary(summaryRes.data);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Format data for charts
  const chartData = dataPoints.map((point) => ({
    date: new Date(point.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    confidence: Math.round(point.overall_confidence_score),
    star: Math.round(point.star_compliance_score),
    fillerWords: Number(point.filler_words_per_minute.toFixed(1)),
    speakingPace: Math.round(point.speaking_pace_wpm),
  }));

  const renderImprovementIndicator = (value: number | null, label: string, isLowerBetter = false) => {
    if (value === null) {
      return (
        <div className="flex items-center gap-1.5 text-xs text-text-tertiary">
          <span>Need 4+ sessions</span>
        </div>
      );
    }

    const isPositive = isLowerBetter ? value < 0 : value > 0;
    const color = isPositive ? 'text-status-success' : 'text-status-error';
    const Icon = isPositive ? TrendingUp : TrendingDown;

    return (
      <div className={`flex items-center gap-1.5 text-xs ${color} font-medium`}>
        <Icon className="w-3.5 h-3.5" />
        <span>
          {isPositive ? '+' : ''}{value.toFixed(1)}% {label}
        </span>
      </div>
    );
  };

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <Card variant="glass" className="p-6 text-center">
          <AlertCircle className="w-12 h-12 text-status-error mx-auto mb-4" />
          <h2 className="heading-card text-text-primary mb-2">Failed to Load Analytics</h2>
          <p className="text-text-secondary mb-4">{error}</p>
          <button onClick={loadData} className="btn-primary">
            Try Again
          </button>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 pb-20 md:pb-8 max-w-6xl">
        <div className="mb-8">
          <Skeleton className="h-10 w-64 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  // Empty state
  if (!summary || summary.total_sessions_analyzed === 0) {
    return (
      <div className="container mx-auto px-4 py-8 pb-20 md:pb-8 max-w-6xl">
        <section className="mb-8">
          <h1 className="heading-page text-text-primary">Analytics</h1>
          <p className="text-text-secondary mt-1">
            Track your communication metrics and improvement trends
          </p>
        </section>

        <Card variant="glass" className="p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-electric-blue/10 flex items-center justify-center mx-auto mb-4">
            <BarChart3 className="w-8 h-8 text-electric-blue" />
          </div>
          <h2 className="heading-section text-text-primary mb-2">No Analytics Yet</h2>
          <p className="text-text-secondary mb-6 max-w-md mx-auto">
            Complete your first interview to see detailed analytics on your communication skills,
            filler words, speaking pace, and STAR compliance.
          </p>
          <a href="/practice" className="btn-primary inline-flex items-center gap-2">
            Start Practicing
          </a>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 pb-20 md:pb-8 max-w-6xl">
      {/* Page Header */}
      <section className="mb-8">
        <h1 className="heading-page text-text-primary">Analytics</h1>
        <p className="text-text-secondary mt-1">
          Track your communication metrics and improvement trends
        </p>
      </section>

      {/* Summary Stats Cards */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Average Confidence Score */}
        <Card variant="glass" className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-electric-blue/10">
              <Target className="w-4 h-4 text-electric-blue" />
            </div>
            <span className="text-sm font-medium text-text-secondary">Confidence</span>
          </div>
          <p className="text-3xl font-bold text-text-primary">
            {Math.round(summary.avg_confidence_score)}
          </p>
          <p className="text-xs text-text-tertiary mt-1 mb-2">average score</p>
          {renderImprovementIndicator(summary.improvement_confidence, 'vs last sessions')}
        </Card>

        {/* Average STAR Compliance */}
        <Card variant="glass" className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-status-success/10">
              <Star className="w-4 h-4 text-status-success" />
            </div>
            <span className="text-sm font-medium text-text-secondary">STAR Method</span>
          </div>
          <p className="text-3xl font-bold text-text-primary">
            {Math.round(summary.avg_star_compliance_score)}
          </p>
          <p className="text-xs text-text-tertiary mt-1 mb-2">average score</p>
          {renderImprovementIndicator(summary.improvement_star_compliance, 'vs last sessions')}
        </Card>

        {/* Average Filler Words */}
        <Card variant="glass" className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-status-warning/10">
              <MessageSquare className="w-4 h-4 text-status-warning" />
            </div>
            <span className="text-sm font-medium text-text-secondary">Filler Words</span>
          </div>
          <p className="text-3xl font-bold text-text-primary">
            {summary.avg_filler_words_per_minute.toFixed(1)}
          </p>
          <p className="text-xs text-text-tertiary mt-1 mb-2">per minute</p>
          {renderImprovementIndicator(summary.improvement_filler_words, 'vs last sessions', true)}
        </Card>

        {/* Total Sessions */}
        <Card variant="glass" className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-indigo-500/10">
              <BarChart3 className="w-4 h-4 text-indigo-500" />
            </div>
            <span className="text-sm font-medium text-text-secondary">Sessions</span>
          </div>
          <p className="text-3xl font-bold text-text-primary">
            {summary.total_sessions_analyzed}
          </p>
          <p className="text-xs text-text-tertiary mt-1">analyzed</p>
        </Card>
      </section>

      {/* Progress Chart - Confidence & STAR Compliance */}
      {chartData.length > 0 && (
        <section className="mb-8">
          <Card variant="glass" className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-electric-blue/10">
                <TrendingUp className="w-5 h-5 text-electric-blue" />
              </div>
              <div>
                <h2 className="heading-card">Performance Over Time</h2>
                <p className="text-xs text-text-tertiary mt-0.5">Confidence score and STAR method compliance</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--text-tertiary))"
                  tick={{ fill: 'hsl(var(--text-tertiary))' }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                />
                <YAxis
                  domain={[0, 100]}
                  stroke="hsl(var(--text-tertiary))"
                  tick={{ fill: 'hsl(var(--text-tertiary))' }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--text-primary))',
                  }}
                  labelStyle={{ color: 'hsl(var(--text-primary))' }}
                />
                <Legend
                  wrapperStyle={{ color: 'hsl(var(--text-primary))' }}
                />
                <Line
                  type="monotone"
                  dataKey="confidence"
                  stroke="hsl(var(--electric-blue))"
                  strokeWidth={2}
                  name="Confidence"
                  dot={{ fill: 'hsl(var(--electric-blue))' }}
                />
                <Line
                  type="monotone"
                  dataKey="star"
                  stroke="hsl(var(--status-success))"
                  strokeWidth={2}
                  name="STAR Compliance"
                  dot={{ fill: 'hsl(var(--status-success))' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </section>
      )}

      {/* Filler Words Trend */}
      {chartData.length > 0 && (
        <section className="mb-8">
          <Card variant="glass" className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-status-warning/10">
                <MessageSquare className="w-5 h-5 text-status-warning" />
              </div>
              <div>
                <h2 className="heading-card">Filler Words Trend</h2>
                <p className="text-xs text-text-tertiary mt-0.5">Frequency per minute over time</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--text-tertiary))"
                  tick={{ fill: 'hsl(var(--text-tertiary))' }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                />
                <YAxis
                  stroke="hsl(var(--text-tertiary))"
                  tick={{ fill: 'hsl(var(--text-tertiary))' }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--text-primary))',
                  }}
                  labelStyle={{ color: 'hsl(var(--text-primary))' }}
                />
                <Area
                  type="monotone"
                  dataKey="fillerWords"
                  stroke="hsl(var(--status-warning))"
                  fill="hsl(var(--status-warning))"
                  fillOpacity={0.2}
                  strokeWidth={2}
                  name="Filler Words/min"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </section>
      )}

      {/* Speaking Pace Chart */}
      {chartData.length > 0 && (
        <section>
          <Card variant="glass" className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-indigo-500/10">
                <Mic2 className="w-5 h-5 text-indigo-500" />
              </div>
              <div>
                <h2 className="heading-card">Speaking Pace</h2>
                <p className="text-xs text-text-tertiary mt-0.5">Words per minute with optimal zone (120-150)</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--text-tertiary))"
                  tick={{ fill: 'hsl(var(--text-tertiary))' }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                />
                <YAxis
                  domain={[80, 180]}
                  stroke="hsl(var(--text-tertiary))"
                  tick={{ fill: 'hsl(var(--text-tertiary))' }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--text-primary))',
                  }}
                  labelStyle={{ color: 'hsl(var(--text-primary))' }}
                />
                {/* Optimal zone - lower bound */}
                <ReferenceLine
                  y={120}
                  stroke="hsl(var(--status-success))"
                  strokeDasharray="3 3"
                  strokeOpacity={0.5}
                />
                {/* Optimal zone - upper bound */}
                <ReferenceLine
                  y={150}
                  stroke="hsl(var(--status-success))"
                  strokeDasharray="3 3"
                  strokeOpacity={0.5}
                />
                <Line
                  type="monotone"
                  dataKey="speakingPace"
                  stroke="hsl(var(--indigo-500))"
                  strokeWidth={2}
                  name="Speaking Pace (WPM)"
                  dot={{ fill: 'hsl(var(--indigo-500))' }}
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-4 text-xs text-text-tertiary text-center">
              Green zone (120-150 WPM) is the optimal speaking pace for interviews
            </div>
          </Card>
        </section>
      )}
    </div>
  );
}
