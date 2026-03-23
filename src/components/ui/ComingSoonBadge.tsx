import { Sparkles } from 'lucide-react';

interface ComingSoonBadgeProps {
  /** Position of the badge relative to parent */
  position?: 'top-right' | 'top-left' | 'inline';
  /** Variant style */
  variant?: 'badge' | 'overlay';
  /** Custom text */
  text?: string;
}

/**
 * A reusable "Coming Soon" badge component to indicate features in development.
 * 
 * Usage:
 * - `position="top-right"` for cards (default)
 * - `position="inline"` for buttons or text
 * - `variant="overlay"` for a semi-transparent overlay effect
 */
export default function ComingSoonBadge({
  position = 'top-right',
  variant = 'badge',
  text = 'Coming Soon',
}: ComingSoonBadgeProps) {
  const positionClasses = {
    'top-right': 'absolute -top-2 -right-2 z-10',
    'top-left': 'absolute -top-2 -left-2 z-10',
    'inline': 'inline-flex ml-2',
  };

  if (variant === 'overlay') {
    return (
      <div className="absolute inset-0 bg-surface-primary/60 dark:bg-surface-dark/60 backdrop-blur-[2px] rounded-xl flex items-center justify-center z-10">
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-electric-blue/10 border border-electric-blue/20">
          <Sparkles className="w-4 h-4 text-electric-blue animate-pulse" />
          <span className="text-sm font-semibold text-electric-blue">{text}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`${positionClasses[position]} flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r from-electric-blue to-indigo-500 text-white text-xs font-bold shadow-lg shadow-electric-blue/25 animate-pulse`}>
      <Sparkles className="w-3 h-3" />
      <span>{text}</span>
    </div>
  );
}
