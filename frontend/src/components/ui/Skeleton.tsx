/**
 * Skeleton loading components for better UX during data loading.
 * Provides placeholder UI that matches the structure of actual content.
 */

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'circular' | 'rectangular';
}

/**
 * Base skeleton component with shimmer animation.
 */
export function Skeleton({ 
  className = '', 
  width, 
  height, 
  variant = 'rectangular' 
}: SkeletonProps) {
  const baseClasses = 'animate-pulse bg-surface-secondary rounded';
  
  const variantClasses = {
    text: 'h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div 
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  );
}

/**
 * Skeleton for text content (headings, paragraphs).
 */
export function SkeletonText({ 
  lines = 1, 
  className = '',
  width = '100%' 
}: { lines?: number; className?: string; width?: string | number }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === lines - 1 ? '75%' : width}
          className="h-4"
        />
      ))}
    </div>
  );
}

/**
 * Skeleton for stat cards (used in Dashboard).
 */
export function SkeletonStatCard() {
  return (
    <div className="card p-6">
      <Skeleton variant="text" width="60%" height={16} className="mb-4" />
      <Skeleton variant="text" width="40px" height={32} className="mb-2" />
      <Skeleton variant="text" width="50%" height={14} />
    </div>
  );
}

/**
 * Skeleton for interview cards (used in Dashboard).
 */
export function SkeletonInterviewCard() {
  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <Skeleton variant="text" width="70%" height={20} className="mb-2" />
          <Skeleton variant="text" width="50%" height={14} />
        </div>
        <Skeleton variant="circular" width={24} height={24} />
      </div>
      <div className="flex gap-2 mb-4">
        <Skeleton variant="rectangular" width={80} height={24} className="rounded-full" />
        <Skeleton variant="rectangular" width={100} height={24} className="rounded-full" />
      </div>
      <Skeleton variant="text" width="100%" height={14} className="mb-2" />
      <Skeleton variant="text" width="60%" height={14} />
    </div>
  );
}

/**
 * Skeleton for score rings (used in FeedbackPage).
 */
export function SkeletonScoreRing() {
  return (
    <div className="flex flex-col items-center">
      <Skeleton variant="circular" width={120} height={120} className="mb-4" />
      <Skeleton variant="text" width={80} height={16} className="mb-2" />
      <Skeleton variant="text" width={60} height={14} />
    </div>
  );
}

/**
 * Skeleton for question display (used in InterviewPage, PreparationPage).
 */
export function SkeletonQuestion() {
  return (
    <div className="card p-8">
      <Skeleton variant="rectangular" width={100} height={28} className="mb-6 rounded-full" />
      <SkeletonText lines={3} className="mb-6" />
      <div className="flex gap-4">
        <Skeleton variant="rectangular" width={120} height={40} className="rounded-lg" />
        <Skeleton variant="rectangular" width={100} height={40} className="rounded-lg" />
      </div>
    </div>
  );
}

/**
 * Skeleton for dashboard stats overview.
 */
export function SkeletonStatsOverview() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonStatCard key={i} />
      ))}
    </div>
  );
}

/**
 * Skeleton for interview list.
 */
export function SkeletonInterviewList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonInterviewCard key={i} />
      ))}
    </div>
  );
}
