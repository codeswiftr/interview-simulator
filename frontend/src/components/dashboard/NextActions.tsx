import { useEffect, useState } from 'react';
import { Network, AlertTriangle, Zap, ArrowRight } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ActionItem {
  id: string;
  icon: React.ElementType;
  iconColor: string;
  iconBg: string;
  title: string;
  description: string;
  ctaLabel: string;
  difficulty: 'easy' | 'medium' | 'hard';
  onAction?: () => void;
}

interface NextActionsProps {
  /** Override default recommendations */
  actions?: ActionItem[];
  onStartNew?: () => void;
  hasWeakAreas?: boolean;
  totalSessions?: number;
}

const difficultyConfig: Record<ActionItem['difficulty'], { label: string; color: string; bg: string }> = {
  easy: {
    label: 'Easy',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/20',
  },
  medium: {
    label: 'Medium',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/20',
  },
  hard: {
    label: 'Hard',
    color: 'text-red-400',
    bg: 'bg-red-500/10 border-red-500/20',
  },
};

function ActionCard({
  action,
  index,
  visible,
}: {
  action: ActionItem;
  index: number;
  visible: boolean;
}) {
  const Icon = action.icon;
  const diff = difficultyConfig[action.difficulty];

  return (
    <div
      className={cn(
        'relative flex flex-col gap-3 p-4 rounded-xl border border-white/[0.06]',
        'bg-white/[0.02] hover:bg-white/[0.05]',
        'hover:border-white/[0.12] hover:-translate-y-0.5',
        'transition-all duration-300 group',
        'focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2 focus-within:ring-offset-[#0a0a0b]'
      )}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(12px)',
        transition: `opacity 400ms cubic-bezier(0.4,0,0.2,1) ${index * 80}ms, transform 400ms cubic-bezier(0.4,0,0.2,1) ${index * 80}ms, background-color 200ms, border-color 200ms, box-shadow 200ms`,
      }}
    >
      {/* Icon + difficulty */}
      <div className="flex items-start justify-between">
        <div
          className={cn('w-9 h-9 rounded-lg flex items-center justify-center shrink-0', action.iconBg)}
          aria-hidden="true"
        >
          <Icon size={16} className={action.iconColor} />
        </div>
        <span
          className={cn(
            'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border',
            diff.bg,
            diff.color
          )}
        >
          {diff.label}
        </span>
      </div>

      {/* Text */}
      <div>
        <h3 className="text-sm font-semibold text-[#fafafa] mb-1">{action.title}</h3>
        <p className="text-xs text-[#71717a] leading-relaxed">{action.description}</p>
      </div>

      {/* CTA */}
      <button
        onClick={action.onAction}
        className={cn(
          'mt-auto self-start inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg',
          'text-[11px] font-semibold text-blue-400',
          'bg-blue-500/10 border border-blue-500/20',
          'hover:bg-blue-500/20 hover:border-blue-500/30',
          'transition-colors duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500'
        )}
      >
        {action.ctaLabel}
        <ArrowRight size={11} className="group-hover:translate-x-0.5 transition-transform duration-150" aria-hidden="true" />
      </button>
    </div>
  );
}

export default function NextActions({
  actions,
  onStartNew,
  hasWeakAreas = false,
  totalSessions = 0,
}: NextActionsProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 200);
    return () => clearTimeout(t);
  }, []);

  // Build smart defaults if no actions provided
  const defaultActions: ActionItem[] = [
    {
      id: 'system-design',
      icon: Network,
      iconColor: 'text-violet-400',
      iconBg: 'bg-violet-500/10',
      title: 'Practice System Design',
      description:
        totalSessions < 3
          ? 'Start with a classic: Design a URL shortener. FAANG engineers expect systems thinking.'
          : 'Level up: Design a distributed message queue or real-time leaderboard.',
      ctaLabel: 'Start Session',
      difficulty: totalSessions < 5 ? 'medium' : 'hard',
      onAction: onStartNew,
    },
    hasWeakAreas
      ? {
          id: 'weak-areas',
          icon: AlertTriangle,
          iconColor: 'text-amber-400',
          iconBg: 'bg-amber-500/10',
          title: 'Review Weak Areas',
          description:
            'Your recent scores show room for improvement. Focused practice on low-scoring categories compounds fast.',
          ctaLabel: 'See Analysis',
          difficulty: 'medium',
          onAction: onStartNew,
        }
      : {
          id: 'behavioral',
          icon: Zap,
          iconColor: 'text-sky-400',
          iconBg: 'bg-sky-500/10',
          title: 'Quick Behavioral Round',
          description:
            "5-minute STAR method drill. Behavioral questions account for 30% of FAANG loops — don't neglect them.",
          ctaLabel: 'Start Drill',
          difficulty: 'easy',
          onAction: onStartNew,
        },
    {
      id: 'mock',
      icon: Zap,
      iconColor: 'text-emerald-400',
      iconBg: 'bg-emerald-500/10',
      title: 'Full Mock Interview',
      description:
        'Simulate a complete 45-minute loop: coding + behavioral. Build stamina and time management.',
      ctaLabel: 'Start Mock',
      difficulty: 'hard',
      onAction: onStartNew,
    },
  ];

  const items = (actions ?? defaultActions).slice(0, 3);

  return (
    <section
      className="rounded-2xl border border-white/[0.06] bg-[rgba(20,20,22,0.8)] backdrop-blur-xl p-5"
      aria-label="Recommended next actions"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-[#71717a]">
          Next Actions
        </h2>
        <span
          className="text-[10px] font-semibold px-2 py-0.5 rounded-full border"
          style={{
            background: 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.1))',
            borderColor: 'rgba(139,92,246,0.2)',
            color: '#a78bfa',
          }}
        >
          Personalized
        </span>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {items.map((action, i) => (
          <ActionCard key={action.id} action={action} index={i} visible={visible} />
        ))}
      </div>
    </section>
  );
}
