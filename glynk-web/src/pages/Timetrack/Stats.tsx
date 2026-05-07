import { useEffect, useState, useMemo } from 'react';
import type { StatItem } from '../../api/timetrack';
import { timetrackApi } from '../../api/timetrack';
import {
  startOfDay, endOfDay,
  startOfWeek, endOfWeek,
  startOfMonth, endOfMonth,
  addDays, addWeeks, addMonths,
} from './dayLogic';

type ViewMode = 'day' | 'week' | 'month';

export default function TimetrackStats() {
  const [stats, setStats] = useState<StatItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('day');
  const [refDate, setRefDate] = useState(new Date());

  const { start, end, label } = useMemo(() => {
    let s, e, l;
    const now = new Date();
    const isToday = startOfDay(now).getTime() === startOfDay(refDate).getTime();

    if (viewMode === 'day') {
      s = startOfDay(refDate);
      e = endOfDay(refDate);
      l = isToday ? 'Today' : refDate.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
    } else if (viewMode === 'week') {
      s = startOfWeek(refDate);
      e = endOfWeek(refDate);
      l = `${s.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} - ${e.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`;
    } else {
      s = startOfMonth(refDate);
      e = endOfMonth(refDate);
      l = refDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
    }
    return { start: s, end: e, label: l };
  }, [viewMode, refDate]);

  useEffect(() => {
    setLoading(true);
    timetrackApi.getStats(start.toISOString(), end.toISOString())
      .then(setStats)
      .finally(() => setLoading(false));
  }, [start, end]);

  const handlePrev = () => {
    if (viewMode === 'day') setRefDate(addDays(refDate, -1));
    else if (viewMode === 'week') setRefDate(addWeeks(refDate, -1));
    else setRefDate(addMonths(refDate, -1));
  };

  const handleNext = () => {
    if (viewMode === 'day') setRefDate(addDays(refDate, 1));
    else if (viewMode === 'week') setRefDate(addWeeks(refDate, 1));
    else setRefDate(addMonths(refDate, 1));
  };

  const aggregatedData = useMemo(() => {
    const map = new Map<string, { name: string, color: string, durationMs: number }>();
    let totalMs = 0;

    stats.forEach(s => {
      if (!s.end_time) return;
      const start = new Date(s.start_time).getTime();
      const end = new Date(s.end_time).getTime();
      const duration = end - start;

      totalMs += duration;

      if (!map.has(s.tag_id)) {
        map.set(s.tag_id, { name: s.tag_name, color: s.tag_color, durationMs: 0 });
      }
      map.get(s.tag_id)!.durationMs += duration;
    });

    const items = Array.from(map.values()).sort((a, b) => b.durationMs - a.durationMs);
    return { items, totalMs };
  }, [stats]);

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Loading stats...</div>;
  }

  // We don't early return on empty data anymore, so the user can still navigate the calendar.

  // Generate SVG Pie Chart paths
  let cumulativePercent = 0;
  const getCoordinatesForPercent = (percent: number) => {
    const x = Math.cos(2 * Math.PI * percent);
    const y = Math.sin(2 * Math.PI * percent);
    return [x, y];
  };

  const formatHours = (ms: number) => (ms / 1000 / 3600).toFixed(1) + 'h';

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Statistics
        </h1>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center bg-white/50 dark:bg-gray-800/50 p-1 rounded-lg border border-gray-200 dark:border-gray-700">
            {(['day', 'week', 'month'] as ViewMode[]).map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors capitalize ${
                  viewMode === mode 
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' 
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3 bg-white/50 dark:bg-gray-800/50 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700">
            <button onClick={handlePrev} className="p-1 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
            </button>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[120px] text-center">
              {label}
            </span>
            <button onClick={handleNext} className="p-1 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            </button>
          </div>
        </div>
      </div>

      {aggregatedData.items.length === 0 ? (
        <div className="text-center py-20 text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl">
          No time tracked in this period.
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-8 items-center">
        {/* Pie Chart */}
        <div className="flex justify-center">
          <svg viewBox="-1 -1 2 2" className="w-64 h-64 -rotate-90 filter drop-shadow-md">
            {aggregatedData.items.map(item => {
              const percent = item.durationMs / aggregatedData.totalMs;
              const [startX, startY] = getCoordinatesForPercent(cumulativePercent);
              cumulativePercent += percent;
              
              // If it's a full circle (100%)
              if (percent === 1) {
                return <circle key={item.name} cx="0" cy="0" r="1" fill={item.color} />;
              }
              
              const [endX, endY] = getCoordinatesForPercent(cumulativePercent);
              const largeArcFlag = percent > 0.5 ? 1 : 0;
              const pathData = [
                `M ${startX} ${startY}`,
                `A 1 1 0 ${largeArcFlag} 1 ${endX} ${endY}`,
                `L 0 0`,
              ].join(' ');

              return (
                <path key={item.name} d={pathData} fill={item.color} className="hover:opacity-90 transition-opacity cursor-pointer">
                  <title>{item.name}: {formatHours(item.durationMs)}</title>
                </path>
              );
            })}
          </svg>
        </div>

        {/* Breakdown List */}
        <div className="space-y-4">
          {aggregatedData.items.map(item => {
            const percent = ((item.durationMs / aggregatedData.totalMs) * 100).toFixed(1);
            return (
              <div key={item.name} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="font-medium text-gray-700 dark:text-gray-300">{item.name}</span>
                  </div>
                  <span className="text-gray-500 dark:text-gray-400 font-mono">
                    {formatHours(item.durationMs)} ({percent}%)
                  </span>
                </div>
                <div className="h-2 w-full bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-1000"
                    style={{ width: `${percent}%`, backgroundColor: item.color }}
                  />
                </div>
              </div>
            );
          })}
        </div>
        </div>
      )}
    </div>
  );
}
