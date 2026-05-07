import { useEffect, useState, useMemo } from 'react';
import type { StatItem } from '../../api/timetrack';
import { timetrackApi } from '../../api/timetrack';
import { useTimetrackStore } from '../../store/timetrack';
import { startOfDay, endOfDay, addDays } from './dayLogic';

function formatDuration(ms: number) {
  const totalMinutes = Math.floor(ms / 1000 / 60);
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

function formatTime(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}

export default function TimetrackLogs() {
  const [stats, setStats] = useState<StatItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refDate, setRefDate] = useState(new Date());
  
  // Also need tags for the filter
  const { tags, fetchTags } = useTimetrackStore();
  const [selectedTagId, setSelectedTagId] = useState<string>('all');
  const [onlyWithNote, setOnlyWithNote] = useState(false);

  useEffect(() => {
    fetchTags();
  }, []);

  const { start, end, label } = useMemo(() => {
    const now = new Date();
    const isToday = startOfDay(now).getTime() === startOfDay(refDate).getTime();
    
    const s = startOfDay(refDate);
    const e = endOfDay(refDate);
    const l = isToday ? 'Today' : refDate.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
    
    return { start: s, end: e, label: l };
  }, [refDate]);

  useEffect(() => {
    setLoading(true);
    timetrackApi.getStats(start.toISOString(), end.toISOString())
      .then(setStats)
      .finally(() => setLoading(false));
  }, [start, end]);

  const handlePrev = () => setRefDate(addDays(refDate, -1));
  const handleNext = () => setRefDate(addDays(refDate, 1));

  const handleDelete = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this record?')) return;
    try {
      await timetrackApi.deleteSession(sessionId);
      setStats(prev => prev.filter(s => s.id !== sessionId));
    } catch (e) {
      console.error(e);
      alert('Failed to delete session');
    }
  };

  const filteredStats = useMemo(() => {
    let filtered = stats.filter(s => s.end_time); // Only completed sessions
    if (selectedTagId !== 'all') {
      filtered = filtered.filter(s => s.tag_id === selectedTagId);
    }
    if (onlyWithNote) {
      filtered = filtered.filter(s => !!s.note?.trim());
    }
    // Sort descending by start_time
    return filtered.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());
  }, [stats, selectedTagId, onlyWithNote]);

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Records
        </h1>
        
        <div className="flex items-center gap-4">
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

      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Tag:</label>
          <select 
            value={selectedTagId} 
            onChange={e => setSelectedTagId(e.target.value)}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-2 py-1 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Tags</option>
            {tags.map(tag => (
              <option key={tag.id} value={tag.id}>{tag.name}</option>
            ))}
          </select>
        </div>
        
        <label className="flex items-center gap-2 cursor-pointer bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 px-3 py-1 rounded-lg hover:bg-white dark:hover:bg-gray-800 transition-colors">
          <input 
            type="checkbox" 
            checked={onlyWithNote}
            onChange={e => setOnlyWithNote(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:bg-gray-700 dark:border-gray-600"
          />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">With Remark</span>
        </label>
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray-500 dark:text-gray-400">Loading records...</div>
      ) : filteredStats.length === 0 ? (
        <div className="text-center py-20 text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl">
          No records found for this period.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredStats.map(session => {
            const durationMs = new Date(session.end_time!).getTime() - new Date(session.start_time).getTime();
            return (
              <div key={session.id} className="bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-3 flex flex-col gap-2 transition-all hover:bg-white dark:hover:bg-gray-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: session.tag_color }} />
                    <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{session.tag_name}</span>
                  </div>
                  
                  <div className="flex items-center gap-3 text-right">
                    <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <span>{formatTime(session.start_time)} - {formatTime(session.end_time!)}</span>
                    </div>
                    <span className="text-sm font-mono font-medium text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-700/50 px-2 py-0.5 rounded-md">
                      {formatDuration(durationMs)}
                    </span>
                    <button 
                      onClick={() => handleDelete(session.id)}
                      className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                      title="Delete record"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  </div>
                </div>
                
                {session.note?.trim() && (
                  <div className="pl-4.5 mt-1">
                    <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words leading-relaxed">
                      {session.note}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
