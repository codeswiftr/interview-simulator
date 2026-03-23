import { useEffect, useRef, useState } from 'react';
import { cn } from '../../lib/utils';

interface DayData {
  label: string; // 'Mon', 'Tue', etc.
  sessions: number;
  isToday: boolean;
}

interface WeeklyProgressProps {
  /** Array of 7 values, index 0 = Monday */
  data?: DayData[];
  /** Raw counts array (7 items) — alternative to `data` */
  counts?: number[];
}

function buildDefaultData(counts?: number[]): DayData[] {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  // Determine today's index (0=Mon … 6=Sun)
  const jsDay = new Date().getDay(); // 0=Sun
  const todayIndex = jsDay === 0 ? 6 : jsDay - 1;

  if (counts && counts.length === 7) {
    return days.map((label, i) => ({
      label,
      sessions: counts[i],
      isToday: i === todayIndex,
    }));
  }

  // Fallback: zeros with today marked
  return days.map((label, i) => ({
    label,
    sessions: 0,
    isToday: i === todayIndex,
  }));
}

export default function WeeklyProgress({ data, counts }: WeeklyProgressProps) {
  const [animated, setAnimated] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Trigger bar grow animation when component mounts (or comes into view)
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setAnimated(true), 100);
          observer.disconnect();
        }
      },
      { threshold: 0.2 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const days = data ?? buildDefaultData(counts);
  const maxSessions = Math.max(...days.map((d) => d.sessions), 1);
  const totalThisWeek = days.reduce((acc, d) => acc + d.sessions, 0);

  return (
    <section
      ref={ref}
      className="rounded-2xl border border-white/[0.06] bg-[rgba(20,20,22,0.8)] backdrop-blur-xl p-5"
      aria-label="Weekly practice activity"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-[#71717a]">
          This Week
        </h2>
        <div className="flex items-baseline gap-1">
          <span
            className="tabular-nums font-bold text-[#fafafa]"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
            aria-label={`${totalThisWeek} sessions this week`}
          >
            {totalThisWeek}
          </span>
          <span className="text-xs text-[#71717a]">sessions</span>
        </div>
      </div>

      {/* Bar chart */}
      <div
        className="flex items-end justify-between gap-2"
        role="img"
        aria-label="Bar chart showing daily session counts for the week"
      >
        {days.map((day, i) => {
          const heightPct = (day.sessions / maxSessions) * 100;
          const barHeight = Math.max(heightPct, 4); // minimum visible height

          return (
            <div
              key={day.label}
              className="flex flex-col items-center gap-2 flex-1"
            >
              {/* Session count above bar */}
              <span
                className={cn(
                  'text-[10px] tabular-nums font-medium transition-opacity duration-300',
                  day.sessions > 0 ? 'text-[#fafafa]' : 'text-transparent'
                )}
                style={{ fontFamily: "'JetBrains Mono', monospace" }}
                aria-hidden="true"
              >
                {day.sessions > 0 ? day.sessions : '·'}
              </span>

              {/* Bar container */}
              <div
                className="relative w-full rounded-full overflow-hidden"
                style={{ height: 80 }}
                aria-label={`${day.label}: ${day.sessions} session${day.sessions !== 1 ? 's' : ''}`}
              >
                {/* Track */}
                <div
                  className="absolute inset-0 rounded-full"
                  style={{ background: 'rgba(255,255,255,0.04)' }}
                />

                {/* Fill bar — grows upward */}
                <div
                  className="absolute bottom-0 left-0 right-0 rounded-full"
                  style={{
                    height: animated ? `${barHeight}%` : '0%',
                    transition: `height 600ms cubic-bezier(0.4, 0, 0.2, 1) ${i * 60}ms`,
                    background: day.isToday
                      ? 'linear-gradient(180deg, #8b5cf6 0%, #3b82f6 100%)'
                      : 'linear-gradient(180deg, rgba(139,92,246,0.5) 0%, rgba(59,130,246,0.5) 100%)',
                    boxShadow: day.isToday && day.sessions > 0
                      ? '0 0 12px rgba(139,92,246,0.5), 0 0 24px rgba(59,130,246,0.2)'
                      : 'none',
                  }}
                />
              </div>

              {/* Day label */}
              <span
                className={cn(
                  'text-[10px] font-medium',
                  day.isToday ? 'text-[#fafafa]' : 'text-[#71717a]'
                )}
                aria-hidden="true"
              >
                {day.label}
              </span>

              {/* Today indicator dot */}
              {day.isToday && (
                <div
                  className="w-1 h-1 rounded-full"
                  style={{
                    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    boxShadow: '0 0 4px rgba(139,92,246,0.8)',
                  }}
                  aria-hidden="true"
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Y-axis hint */}
      {maxSessions > 0 && (
        <div className="flex justify-between mt-3 pt-3 border-t border-white/[0.04]">
          <span className="text-[9px] text-[#71717a]/60 uppercase tracking-wider">
            Sessions / day
          </span>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <div
                className="w-2.5 h-2.5 rounded-sm"
                style={{ background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)' }}
                aria-hidden="true"
              />
              <span className="text-[9px] text-[#71717a]/60">Today</span>
            </div>
            <div className="flex items-center gap-1">
              <div
                className="w-2.5 h-2.5 rounded-sm"
                style={{ background: 'rgba(139,92,246,0.4)' }}
                aria-hidden="true"
              />
              <span className="text-[9px] text-[#71717a]/60">Other days</span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
