import { useState } from 'react';
import { Code2, Network, MessageSquare, ChevronRight, ArrowRight } from 'lucide-react';
import { cn } from '../../lib/utils';
import { formatRelativeTime } from '../../lib/utils';

export interface Session {
  id: string;
  type: 'coding' | 'system-design' | 'behavioral' | string;
  title: string;
  score: number | null;
  duration: number; // minutes
  completedAt: string; // ISO date
}

interface RecentSessionsProps {
  sessions: Session[];
  onReview?: (sessionId: string) => void;
  onStartNew?: () => void;
  isLoading?: boolean;
}

const typeConfig: Record<string, { icon: React.ElementType; label: string; color: string; bg: string }> = {
  coding: {
    icon: Code2,
    label: 'Coding',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
  },
  'system-design': {
    icon: Network,
    label: 'System Design',
    color: 'text-violet-400',
    bg: 'bg-violet-500/10',
  },
  behavioral: {
    icon: MessageSquare,
    label: 'Behavioral',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
  },
  mixed: {
    icon: Code2,
    label: 'Mixed',
    color: 'text-sky-400',
    bg: 'bg-sky-500/10',
  },
};

const fallbackType = {
  icon: Code2,
  label: 'Interview',
  color: 'text-[#71717a]',
  bg: 'bg-white/[0.05]',
};

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null || score === undefined) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-white/[0.05] text-[#71717a] border border-white/[0.06]">
        Pending
      </span>
    );
  }

  const isHigh = score >= 80;
  const isMid = score >= 60 && score < 80;

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold tabular-nums',
        isHigh
          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
          : isMid
          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
          : 'bg-red-500/10 text-red-400 border border-red-500/20'
      )}
      style={{ fontFamily: "'JetBrains Mono', monospace" }}
      aria-label={`Score: ${score}`}
    >
      {score}
    </span>
  );
}

function SessionRow({
  session,
  onReview,
  index,
}: {
  session: Session;
  onReview?: (id: string) => void;
  index: number;
}) {
  const [hovered, setHovered] = useState(false);
  const config = typeConfig[session.type] ?? fallbackType;
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'group relative flex items-center gap-4 px-4 py-3.5 rounded-xl border border-white/[0.06]',
        'bg-white/[0.02] hover:bg-white/[0.05] transition-all duration-200',
        'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0a0b]',
        'animate-stagger-in'
      )}
      style={{
        animationDelay: `${index * 60}ms`,
        animationFillMode: 'forwards',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => onReview?.(session.id)}
      onKeyDown={(e) => e.key === 'Enter' && onReview?.(session.id)}
      tabIndex={0}
      role="button"
      aria-label={`Review session: ${session.title}, score ${session.score ?? 'pending'}`}
    >
      {/* Type icon */}
      <div
        className={cn(
          'shrink-0 w-9 h-9 rounded-lg flex items-center justify-center',
          config.bg
        )}
        aria-hidden="true"
      >
        <Icon size={16} className={config.color} />
      </div>

      {/* Title + meta */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[#fafafa] truncate">{session.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[11px] text-[#71717a]">{config.label}</span>
          <span className="text-[#71717a]/40 text-[10px]">·</span>
          <span className="text-[11px] text-[#71717a]">
            {formatRelativeTime(session.completedAt)}
          </span>
          {session.duration > 0 && (
            <>
              <span className="text-[#71717a]/40 text-[10px]">·</span>
              <span className="text-[11px] text-[#71717a]">{session.duration}m</span>
            </>
          )}
        </div>
      </div>

      {/* Score */}
      <div className="shrink-0">
        <ScoreBadge score={session.score} />
      </div>

      {/* Slide-in Review button */}
      <div
        className={cn(
          'shrink-0 flex items-center gap-1 overflow-hidden transition-all duration-200',
          hovered ? 'max-w-[80px] opacity-100' : 'max-w-0 opacity-0'
        )}
        aria-hidden={!hovered}
      >
        <button
          className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/20 transition-colors whitespace-nowrap"
          onClick={(e) => {
            e.stopPropagation();
            onReview?.(session.id);
          }}
          tabIndex={hovered ? 0 : -1}
        >
          Review
          <ArrowRight size={11} />
        </button>
      </div>

      {/* Always-visible chevron on mobile */}
      <ChevronRight
        size={14}
        className={cn(
          'shrink-0 text-[#71717a] transition-all duration-200',
          hovered ? 'opacity-0' : 'opacity-100',
          'sm:block'
        )}
        aria-hidden="true"
      />
    </div>
  );
}

// Empty state
function EmptyState({ onStartNew }: { onStartNew?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div
        className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
        style={{
          background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))',
          border: '1px solid rgba(255,255,255,0.06)',
        }}
        aria-hidden="true"
      >
        <Code2 size={24} className="text-blue-400" />
      </div>
      <h3 className="text-[#fafafa] font-semibold text-base mb-2">No sessions yet</h3>
      <p className="text-[#71717a] text-sm max-w-xs mb-6">
        Start your first practice session and build the muscle memory for FAANG interviews.
      </p>
      {onStartNew && (
        <button
          onClick={onStartNew}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          style={{
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            boxShadow: '0 4px 16px rgba(59,130,246,0.3)',
          }}
        >
          Start First Session
          <ArrowRight size={16} />
        </button>
      )}
    </div>
  );
}

// Skeleton row
function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 px-4 py-3.5 rounded-xl border border-white/[0.06] bg-white/[0.02] animate-pulse">
      <div className="w-9 h-9 rounded-lg bg-white/[0.05] shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3 bg-white/[0.05] rounded w-2/3" />
        <div className="h-2.5 bg-white/[0.04] rounded w-1/3" />
      </div>
      <div className="w-8 h-5 bg-white/[0.05] rounded-full shrink-0" />
    </div>
  );
}

export default function RecentSessions({
  sessions,
  onReview,
  onStartNew,
  isLoading,
}: RecentSessionsProps) {
  if (isLoading) {
    return (
      <div
        className="rounded-2xl border border-white/[0.06] bg-[rgba(20,20,22,0.8)] backdrop-blur-xl p-5 space-y-2"
        aria-busy="true"
        aria-label="Loading recent sessions"
      >
        <div className="h-4 bg-white/[0.05] rounded w-1/4 mb-4 animate-pulse" />
        {[1, 2, 3].map((i) => (
          <SkeletonRow key={i} />
        ))}
      </div>
    );
  }

  return (
    <section
      className="rounded-2xl border border-white/[0.06] bg-[rgba(20,20,22,0.8)] backdrop-blur-xl p-5"
      aria-label="Recent practice sessions"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-[#71717a]">
          Recent Sessions
        </h2>
        {sessions.length > 0 && (
          <span className="text-[11px] text-[#71717a] bg-white/[0.04] border border-white/[0.06] px-2 py-0.5 rounded-full">
            {sessions.length} total
          </span>
        )}
      </div>

      {sessions.length === 0 ? (
        <EmptyState onStartNew={onStartNew} />
      ) : (
        <div className="space-y-2">
          {sessions.map((session, i) => (
            <SessionRow
              key={session.id}
              session={session}
              onReview={onReview}
              index={i}
            />
          ))}
        </div>
      )}
    </section>
  );
}
