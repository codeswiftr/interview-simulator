import { useEffect, useRef, useState } from 'react';
import { Flame } from 'lucide-react';
import { cn } from '../../lib/utils';

interface HeroStatsProps {
  totalInterviews: number;
  weeklyChange: number;
  averageScore: number;
  scoreChange: number;
  streakDays: number;
  streakHistory: boolean[]; // last 7 days, index 0 = oldest
}

// Animated counter hook
function useCountUp(target: number, duration = 1200, delay = 0) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => {
      const start = performance.now();
      const step = (now: number) => {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        setValue(Math.round(eased * target));
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    }, delay);
    return () => clearTimeout(timer);
  }, [target, duration, delay]);
  return value;
}

// Mini sparkline SVG (last 7 data points)
function Sparkline({ data }: { data: number[] }) {
  if (!data.length) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 64;
  const h = 24;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  });
  const polyline = pts.join(' ');
  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      aria-hidden="true"
      className="overflow-visible"
    >
      <defs>
        <linearGradient id="spark-grad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>
      <polyline
        points={polyline}
        fill="none"
        stroke="url(#spark-grad)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* End dot */}
      <circle
        cx={pts[pts.length - 1]?.split(',')[0]}
        cy={pts[pts.length - 1]?.split(',')[1]}
        r="2.5"
        fill="#8b5cf6"
      />
    </svg>
  );
}

// Score ring — SVG donut with animated gradient stroke
function ScoreRing({ score, animated }: { score: number; animated: boolean }) {
  const radius = 40;
  const stroke = 6;
  const normalizedR = radius - stroke / 2;
  const circumference = 2 * Math.PI * normalizedR;
  const pct = Math.min(Math.max(score, 0), 100) / 100;
  const [dashOffset, setDashOffset] = useState(circumference);

  useEffect(() => {
    if (!animated) return;
    const timer = setTimeout(() => {
      setDashOffset(circumference * (1 - pct));
    }, 300);
    return () => clearTimeout(timer);
  }, [animated, pct, circumference]);

  const displayScore = useCountUp(score, 1200, 300);

  return (
    <div className="relative flex items-center justify-center" style={{ width: 96, height: 96 }}>
      <svg
        width={96}
        height={96}
        viewBox="0 0 96 96"
        style={{ transform: 'rotate(-90deg)' }}
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
        </defs>
        {/* Track */}
        <circle
          cx={48}
          cy={48}
          r={normalizedR}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={stroke}
        />
        {/* Fill */}
        <circle
          cx={48}
          cy={48}
          r={normalizedR}
          fill="none"
          stroke="url(#ring-grad)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)' }}
        />
      </svg>
      {/* Center label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="text-xl font-bold leading-none tabular-nums"
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          {displayScore}
        </span>
        <span className="text-[10px] text-[#71717a] mt-0.5">/100</span>
      </div>
    </div>
  );
}

// Streak calendar dots
function StreakDots({ history }: { history: boolean[] }) {
  const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
  // history[0] = oldest, history[6] = today
  return (
    <div className="flex items-center gap-1.5" aria-label="Last 7 days activity">
      {history.map((active, i) => (
        <div key={i} className="flex flex-col items-center gap-1">
          <div
            className={cn(
              'w-5 h-5 rounded-full transition-colors',
              active
                ? 'bg-[#3b82f6] shadow-[0_0_6px_rgba(59,130,246,0.6)]'
                : 'bg-white/[0.06] border border-white/[0.08]'
            )}
            aria-label={`${days[i]}: ${active ? 'active' : 'inactive'}`}
          />
          <span className="text-[9px] text-[#71717a] font-medium" aria-hidden="true">
            {days[i]}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function HeroStats({
  totalInterviews,
  weeklyChange,
  averageScore,
  scoreChange,
  streakDays,
  streakHistory,
}: HeroStatsProps) {
  const [mounted, setMounted] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Trigger animations shortly after mount
    const t = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(t);
  }, []);

  const countedInterviews = useCountUp(totalInterviews, 900, 100);
  const countedStreak = useCountUp(streakDays, 800, 200);

  // Build a plausible sparkline from total — last 7 weeks simulated
  const sparkData = (() => {
    const base = Math.max(totalInterviews - 6, 0);
    return Array.from({ length: 7 }, (_, i) =>
      i < 6 ? base + i : totalInterviews
    );
  })();

  const cardBase =
    'relative overflow-hidden rounded-2xl border border-white/[0.06] backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-white/[0.12] hover:shadow-2xl group';
  const cardBg = 'bg-[rgba(20,20,22,0.8)]';

  return (
    <div
      ref={containerRef}
      className="grid grid-cols-1 sm:grid-cols-3 gap-4"
      role="region"
      aria-label="Key performance stats"
    >
      {/* ---- Card 1: Interviews Completed ---- */}
      <div
        className={cn(
          cardBase,
          cardBg,
          'p-6',
          mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4',
          'transition-all duration-500 delay-[0ms]'
        )}
        style={{ transitionDelay: mounted ? '0ms' : '0ms' }}
      >
        {/* Gradient mesh accent */}
        <div
          className="absolute -top-10 -right-10 w-32 h-32 rounded-full pointer-events-none"
          style={{
            background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
          }}
          aria-hidden="true"
        />

        <div className="relative flex flex-col gap-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-widest text-[#71717a]">
                Interviews Completed
              </p>
              <p
                className="mt-2 tabular-nums font-bold leading-none"
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '2.75rem',
                  background: 'linear-gradient(135deg, #fafafa 60%, #a1a1aa)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
                aria-label={`${totalInterviews} interviews completed`}
              >
                {countedInterviews}
              </p>
            </div>
            <Sparkline data={sparkData} />
          </div>

          {/* Weekly badge */}
          {weeklyChange > 0 && (
            <span className="inline-flex self-start items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-[#3b82f6]/10 text-[#3b82f6] border border-[#3b82f6]/20">
              +{weeklyChange} this week
            </span>
          )}
          {weeklyChange === 0 && (
            <span className="inline-flex self-start items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-white/[0.05] text-[#71717a] border border-white/[0.06]">
              No sessions this week
            </span>
          )}
        </div>
      </div>

      {/* ---- Card 2: Average Score ---- */}
      <div
        className={cn(
          cardBase,
          cardBg,
          'p-6',
          mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        )}
        style={{ transitionDelay: mounted ? '80ms' : '0ms', transition: 'all 500ms cubic-bezier(0.4,0,0.2,1)' }}
      >
        <div
          className="absolute -top-10 -left-10 w-32 h-32 rounded-full pointer-events-none"
          style={{
            background: 'radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%)',
          }}
          aria-hidden="true"
        />

        <div className="relative flex flex-col gap-4">
          <p className="text-xs font-medium uppercase tracking-widest text-[#71717a]">
            Average Score
          </p>

          <div className="flex items-center gap-4">
            <ScoreRing score={averageScore} animated={mounted} />
            <div className="flex flex-col gap-2">
              <div>
                {scoreChange > 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/20">
                    +{scoreChange} pts
                  </span>
                )}
                {scoreChange < 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                    {scoreChange} pts
                  </span>
                )}
                {scoreChange === 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-white/[0.05] text-[#71717a] border border-white/[0.06]">
                    No change
                  </span>
                )}
              </div>
              <p className="text-xs text-[#71717a]">vs last 5 sessions</p>
            </div>
          </div>
        </div>
      </div>

      {/* ---- Card 3: Practice Streak ---- */}
      <div
        className={cn(
          cardBase,
          cardBg,
          'p-6',
          mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        )}
        style={{ transitionDelay: mounted ? '160ms' : '0ms', transition: 'all 500ms cubic-bezier(0.4,0,0.2,1)' }}
      >
        <div
          className="absolute -bottom-10 -right-10 w-32 h-32 rounded-full pointer-events-none"
          style={{
            background: 'radial-gradient(circle, rgba(251,146,60,0.12) 0%, transparent 70%)',
          }}
          aria-hidden="true"
        />

        <div className="relative flex flex-col gap-4">
          <p className="text-xs font-medium uppercase tracking-widest text-[#71717a]">
            Practice Streak
          </p>

          <div className="flex items-end gap-3">
            <div className="flex items-baseline gap-1">
              <span
                className="tabular-nums font-bold leading-none"
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '2.75rem',
                  background: 'linear-gradient(135deg, #fb923c, #f59e0b)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
                aria-label={`${streakDays} day streak`}
              >
                {countedStreak}
              </span>
              <span className="text-[#71717a] text-sm mb-1">days</span>
            </div>
            <Flame
              className="mb-1 text-orange-400"
              size={22}
              aria-hidden="true"
              style={{
                filter: streakDays > 0 ? 'drop-shadow(0 0 6px rgba(251,146,60,0.6))' : 'none',
              }}
            />
          </div>

          <StreakDots history={streakHistory.length === 7 ? streakHistory : Array(7).fill(false)} />
        </div>
      </div>
    </div>
  );
}
