import { useMemo } from 'react';
import { Tooltip } from 'react-tooltip';

interface ActivityDay {
  date: string;
  count: number;
  score?: number; // Average score for that day
  trend?: 'improvement' | 'regression' | 'neutral'; // New field for trend
}

interface CalendarDay {
  date: string;
  count: number;
  score?: number;
  trend?: 'improvement' | 'regression' | 'neutral';
  dayOfWeek: number;
}

interface ActivityHeatmapProps {
  data?: ActivityDay[];
}

export default function ActivityHeatmap({ data = [] }: ActivityHeatmapProps) {
  // Generate last 365 days
  const calendarData = useMemo(() => {
    const today = new Date();
    const days: CalendarDay[] = [];
    // Start from 52 weeks ago (approx 1 year)
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - 364);

    // Map existing data for quick lookup
    const dataMap = new Map(data.map(d => [d.date, d]));

    for (let i = 0; i < 365; i++) {
      const currentDate = new Date(startDate);
      currentDate.setDate(startDate.getDate() + i);
      const dateStr = currentDate.toISOString().split('T')[0];
      const activity = dataMap.get(dateStr);

      days.push({
        date: dateStr,
        count: activity?.count || 0,
        score: activity?.score,
        trend: activity?.trend,
        dayOfWeek: currentDate.getDay(),
      });
    }
    return days;
  }, [data]);

  // Group by weeks
  const weeks = useMemo(() => {
    const result: (CalendarDay | null)[][] = [];
    let currentWeek: (CalendarDay | null)[] = [];
    
    // Pad the first week if necessary
    const firstDay = new Date(calendarData[0].date).getDay();
    for (let i = 0; i < firstDay; i++) {
      currentWeek.push(null);
    }

    calendarData.forEach((day) => {
      currentWeek.push(day);
      if (currentWeek.length === 7) {
        result.push(currentWeek);
        currentWeek = [];
      }
    });

    if (currentWeek.length > 0) {
      result.push(currentWeek);
    }

    return result;
  }, [calendarData]);

  const getColor = (count: number, trend?: 'improvement' | 'regression' | 'neutral') => {
    if (count === 0) return 'bg-surface-tertiary dark:bg-surface-tertiary/30';
    
    // Color based on trend (Green = Improvement, Orange = Regression)
    if (trend === 'improvement') {
      if (count >= 4) return 'bg-emerald-600';
      if (count >= 3) return 'bg-emerald-500';
      return 'bg-emerald-400';
    }
    
    if (trend === 'regression') {
      if (count >= 4) return 'bg-orange-600';
      if (count >= 3) return 'bg-orange-500';
      return 'bg-orange-400';
    }

    // Neutral / Default (Blue-ish or lighter green)
    if (count >= 4) return 'bg-electric-blue';
    if (count >= 3) return 'bg-blue-400';
    return 'bg-blue-300';
  };

  return (
    <div className="w-full overflow-x-auto pb-2">
      <div className="min-w-[700px]">
        <div className="flex gap-1">
          {weeks.map((week, weekIndex) => (
            <div key={weekIndex} className="flex flex-col gap-1">
              {week.map((day, dayIndex) => {
                if (!day) return <div key={`empty-${dayIndex}`} className="w-3 h-3" />;
                
                return (
                  <div
                    key={day.date}
                    className={`w-3 h-3 rounded-sm ${getColor(day.count, day.trend)} transition-colors hover:ring-2 hover:ring-offset-1 hover:ring-electric-blue cursor-pointer`}
                    data-tooltip-id="activity-tooltip"
                    data-tooltip-content={`${day.date}: ${day.count} sessions${day.trend ? ` (${day.trend})` : ''}`}
                  />
                );
              })}
            </div>
          ))}
        </div>
        <div className="flex items-center justify-end gap-4 mt-3 text-xs text-text-tertiary">
          <div className="flex items-center gap-2">
             <span>Improvement</span>
             <div className="flex gap-1">
               <div className="w-3 h-3 rounded-sm bg-emerald-400" />
               <div className="w-3 h-3 rounded-sm bg-emerald-600" />
             </div>
          </div>
          <div className="flex items-center gap-2">
             <span>Regression</span>
             <div className="flex gap-1">
               <div className="w-3 h-3 rounded-sm bg-orange-400" />
               <div className="w-3 h-3 rounded-sm bg-orange-600" />
             </div>
          </div>
        </div>
      </div>
      <Tooltip id="activity-tooltip" className="z-50 !bg-surface-dark !text-white !px-3 !py-2 !rounded-lg !text-xs !opacity-100" />
    </div>
  );
}
