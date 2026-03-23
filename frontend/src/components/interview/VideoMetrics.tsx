import { useEffect, useState } from 'react';
import { BarChart3, Loader2 } from 'lucide-react';
import { videoAPI } from '../../lib/api';
import { useInterview } from '../../contexts/InterviewContext';
import { Card } from '../ui/Card';

type VideoMetric = {
  response_id: string;
  video_url: string | null;
  video_confidence_score: number | null;
  video_eye_contact_pct: number | null;
  video_posture_score: number | null;
  video_gesture_count: number | null;
  video_duration_seconds: number | null;
  analysis_complete: boolean;
};

interface VideoMetricsProps {
  enabled?: boolean;
}

/**
 * VideoMetrics
 *
 * Displays the 5 video_* metrics from GET /api/v1/interviews/{id}/video-metrics:
 * confidence, eye contact, posture, gestures, duration.
 *
 * Feature-flagged by VITE_VIDEO_FEATURES_ENABLED and an optional `enabled` prop.
 */
export function VideoMetrics({ enabled }: VideoMetricsProps) {
  const featureFlag =
    enabled ?? import.meta.env.VITE_VIDEO_FEATURES_ENABLED === 'true';

  const { session } = useInterview();

  const [metrics, setMetrics] = useState<VideoMetric[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!featureFlag || !session) return;
    let cancelled = false;

    const fetchMetrics = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await videoAPI.getVideoMetrics(session.id);
        if (cancelled) return;
        setMetrics(res.data as VideoMetric[]);
      } catch (err: unknown) {
        if (cancelled) return;
        const axErr = err as { response?: { status?: number } };
        if (axErr?.response?.status === 404) {
          setMetrics([]);
          return;
        }
        console.error('[VideoMetrics] failed to fetch video metrics', err);
        setError('Unable to load video metrics right now.');
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void fetchMetrics();

    return () => {
      cancelled = true;
    };
  }, [featureFlag, session]);

  if (!featureFlag || !session) {
    return null;
  }

  const hasData = metrics && metrics.length > 0;

  const aggregate = (fn: (m: VideoMetric) => number | null) => {
    if (!metrics) return null;
    const values = metrics
      .map(fn)
      .filter((v): v is number => typeof v === 'number');
    if (!values.length) return null;
    return values.reduce((a, b) => a + b, 0) / values.length;
  };

  const avgConfidence = aggregate((m) => m.video_confidence_score);
  const avgEyeContact = aggregate((m) => m.video_eye_contact_pct);
  const avgPosture = aggregate((m) => m.video_posture_score);
  const avgGestures = aggregate((m) =>
    m.video_gesture_count !== null ? m.video_gesture_count : null
  );
  const avgDuration = aggregate((m) => m.video_duration_seconds);

  const allComplete =
    !!metrics &&
    metrics.length > 0 &&
    metrics.every((m) => m.analysis_complete === true);

  return (
    <Card
      variant="glass"
      className="mt-4 p-4 sm:p-5 border-dashed border-border-subtle/70 bg-surface-secondary/60"
    >
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-text-tertiary" />
          <h3 className="text-sm font-semibold text-text-secondary">
            Video Analysis (beta)
          </h3>
        </div>
        {loading && (
          <span className="inline-flex items-center gap-1 text-xs text-text-tertiary">
            <Loader2 className="w-3 h-3 animate-spin" />
            Analyzing…
          </span>
        )}
        {!loading && hasData && !allComplete && (
          <span className="text-xs text-text-tertiary">
            Processing some answers…
          </span>
        )}
      </div>

      {error && (
        <p className="text-xs text-status-error mb-2">{error}</p>
      )}

      {!loading && !hasData && !error && (
        <p className="text-xs text-text-tertiary">
          Video metrics will appear here after your responses have been analyzed.
        </p>
      )}

      {hasData && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
          <MetricPill
            label="Confidence"
            value={avgConfidence}
            suffix="%"
            format={(v) => Math.round(v * 100)}
          />
          <MetricPill
            label="Eye contact"
            value={avgEyeContact}
            suffix="%"
            format={(v) => Math.round(v * 100)}
          />
          <MetricPill
            label="Posture"
            value={avgPosture}
            suffix="/ 1.0"
            format={(v) => v.toFixed(2)}
          />
          <MetricPill
            label="Gestures"
            value={avgGestures}
            format={(v) => Math.round(v)}
          />
          <MetricPill
            label="Avg duration"
            value={avgDuration}
            suffix="s"
            format={(v) => Math.round(v)}
          />
        </div>
      )}
    </Card>
  );
}

interface MetricPillProps {
  label: string;
  value: number | null;
  suffix?: string;
  format?: (v: number) => number | string;
}

function MetricPill({ label, value, suffix, format }: MetricPillProps) {
  const display =
    value === null
      ? '—'
      : format
      ? format(value)
      : Math.round(value);

  return (
    <div className="flex flex-col gap-0.5 rounded-lg border border-border-subtle/60 bg-surface-primary/60 px-2.5 py-1.5">
      <span className="text-[10px] uppercase tracking-wide text-text-tertiary">
        {label}
      </span>
      <span className="text-xs font-semibold text-text-secondary">
        {display}
        {suffix ? <span className="ml-1 text-[10px] text-text-tertiary">{suffix}</span> : null}
      </span>
    </div>
  );
}
