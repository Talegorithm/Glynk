import { useEffect, useState, useRef } from 'react';
import { useTimetrackStore } from '../../store/timetrack';
import type { Tag } from '../../api/timetrack';

const COLORS = [
  '#EF4444', '#F97316', '#F59E0B', '#10B981', '#3B82F6', '#6366F1', '#8B5CF6', '#EC4899', '#6B7280'
];

function formatDuration(ms: number) {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function formatHoursOrMins(ms: number) {
  const totalMinutes = Math.floor(ms / 1000 / 60);
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;
  
  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  return `${mins}m`;
}

export default function TimetrackIndex() {
  const {
    tags, activeSessions, todayStats, singleMode, loading,
    fetchTags, fetchActiveSessions, fetchTodayStats, setSingleMode,
    createTag, deleteTag, reorderTags, startSession, stopSession, updateSessionNote
  } = useTimetrackStore();

  const [isAdding, setIsAdding] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState(COLORS[0]);
  
  const [now, setNow] = useState(Date.now());
  const [noteModal, setNoteModal] = useState<{ sessionId: string, note: string } | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Drag and drop state
  const [draggedIdx, setDraggedIdx] = useState<number | null>(null);

  useEffect(() => {
    fetchTags();
    fetchActiveSessions();
    fetchTodayStats();
  }, []);

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleAddTag = async () => {
    if (!newTagName.trim()) return;
    await createTag(newTagName.trim(), newTagColor);
    setNewTagName('');
    setIsAdding(false);
  };

  const onDragStart = (e: React.DragEvent, idx: number) => {
    setDraggedIdx(idx);
    e.dataTransfer.effectAllowed = 'move';
  };

  const onDragOver = (e: React.DragEvent, idx: number) => {
    e.preventDefault();
    if (draggedIdx === null || draggedIdx === idx) return;

    const newTags = [...tags];
    const draggedTag = newTags[draggedIdx];
    newTags.splice(draggedIdx, 1);
    newTags.splice(idx, 0, draggedTag);
    
    setDraggedIdx(idx);
    reorderTags(newTags); // Note: might cause frequent API calls, debounce in production
  };

  const onDragEnd = () => {
    setDraggedIdx(null);
  };

  // Long press handling
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isLongPressRef = useRef(false);

  const handlePointerDown = (tagId: string, sessionId?: string, currentNote: string = '') => {
    isLongPressRef.current = false;
    timerRef.current = setTimeout(() => {
      isLongPressRef.current = true;
      if (sessionId) {
        setNoteModal({ sessionId, note: currentNote });
      }
    }, 600); // 600ms long press
  };

  const handlePointerUp = (tagId: string, sessionId?: string) => {
    if (isEditing) return; // Disable timer clicks in edit mode
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    
    if (isLongPressRef.current) {
      // It was a long press, so we don't toggle the timer.
      // Reset it for the next interaction
      setTimeout(() => { isLongPressRef.current = false; }, 100);
      return;
    }
    
    // Normal click
    if (sessionId) {
      stopSession(sessionId);
    } else {
      startSession(tagId);
    }
  };

  const handleSaveNote = async () => {
    if (noteModal) {
      await updateSessionNote(noteModal.sessionId, noteModal.note);
      setNoteModal(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Time Tracker
        </h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
              isEditing
                ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-300 dark:border-amber-700/50'
                : 'bg-white/50 dark:bg-gray-800/50 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            {isEditing ? 'Done' : 'Edit'}
          </button>
          
          <div className="flex items-center bg-white/50 dark:bg-gray-800/50 p-1 rounded-full border border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setSingleMode(true)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                singleMode 
                  ? 'bg-blue-500 text-white shadow-sm' 
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
              }`}
            >
              Single
            </button>
            <button
              onClick={() => setSingleMode(false)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                !singleMode 
                  ? 'bg-blue-500 text-white shadow-sm' 
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
              }`}
            >
              Multi
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {tags.map((tag, idx) => {
          const session = activeSessions.find(s => s.tag_id === tag.id);
          const isActive = !!session;
          const currentDuration = session ? now - new Date(session.start_time).getTime() : 0;
          
          const pastDuration = todayStats.find(s => s.tag_id === tag.id)?.duration_ms || 0;
          const totalToday = pastDuration + currentDuration;

          return (
            <div
              key={tag.id}
              draggable={isEditing}
              onDragStart={(e) => onDragStart(e, idx)}
              onDragOver={(e) => onDragOver(e, idx)}
              onDragEnd={onDragEnd}
              onPointerDown={() => !isEditing && handlePointerDown(tag.id, session?.id, session?.note)}
              onPointerUp={() => handlePointerUp(tag.id, session?.id)}
              onPointerCancel={() => {
                if (timerRef.current) clearTimeout(timerRef.current);
              }}
              onPointerLeave={() => {
                if (timerRef.current) clearTimeout(timerRef.current);
              }}
              onContextMenu={(e) => {
                if (!isEditing) e.preventDefault(); // Prevent mobile context menu on long press
              }}
              className={`relative group p-4 rounded-2xl border-2 transition-all select-none overflow-hidden ${
                isEditing ? 'cursor-grab active:cursor-grabbing hover:border-blue-400' : 'cursor-pointer hover:border-gray-300 dark:hover:border-gray-600'
              } ${
                isActive && !isEditing
                  ? 'border-transparent shadow-lg scale-105 ring-4 ring-opacity-30' 
                  : isEditing && isActive
                  ? 'border-transparent shadow-sm ring-2 ring-opacity-50'
                  : 'border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 hover:bg-white dark:hover:bg-gray-800'
              }`}
              style={{
                backgroundColor: isActive ? `${tag.color}15` : undefined,
                borderColor: isActive ? tag.color : undefined,
                '--tw-ring-color': tag.color,
              } as React.CSSProperties}
            >
              <div className="flex flex-col items-center justify-center gap-2 h-full min-h-[100px]">
                <div 
                  className="w-4 h-4 rounded-full shadow-sm"
                  style={{ backgroundColor: tag.color }}
                />
                <span className={`font-semibold text-center ${isActive ? 'text-gray-900 dark:text-gray-100' : 'text-gray-600 dark:text-gray-400'}`}>
                  {tag.name}
                </span>
                
                <div className="flex flex-col items-center mt-1">
                  {isActive && (
                    <span className="font-mono text-sm tracking-widest text-gray-800 dark:text-gray-200">
                      {formatDuration(currentDuration)}
                    </span>
                  )}
                  {totalToday > 0 && !isActive && (
                    <span className="text-xs text-gray-400 dark:text-gray-500 font-mono mt-1">
                      Today: {formatHoursOrMins(totalToday)}
                    </span>
                  )}
                </div>

                {isActive && session.note && !isEditing && (
                  <div className="absolute top-2 right-2">
                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </div>
                )}
              </div>
              
              {isEditing && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteTag(tag.id);
                  }}
                  className="absolute top-2 right-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          );
        })}

        {/* Add Tag Button */}
        {isEditing && (
          !isAdding ? (
            <button
              onClick={() => setIsAdding(true)}
              className="flex flex-col items-center justify-center min-h-[136px] p-4 rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-600 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-400 dark:hover:border-gray-500 transition-colors bg-transparent"
            >
            <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span className="font-medium">New Tag</span>
          </button>
        ) : (
          <div className="flex flex-col min-h-[136px] p-4 rounded-2xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 space-y-3">
            <input
              type="text"
              value={newTagName}
              onChange={e => setNewTagName(e.target.value)}
              placeholder="Tag name"
              autoFocus
              className="w-full bg-transparent border-b border-gray-300 dark:border-gray-600 px-1 py-1 text-sm focus:outline-none focus:border-blue-500"
              onKeyDown={e => e.key === 'Enter' && handleAddTag()}
            />
            <div className="flex flex-wrap gap-1.5">
              {COLORS.map(c => (
                <button
                  key={c}
                  onClick={() => setNewTagColor(c)}
                  className={`w-5 h-5 rounded-full transition-transform ${newTagColor === c ? 'scale-125 ring-2 ring-offset-1 ring-gray-400 dark:ring-offset-gray-800' : ''}`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
            <div className="flex justify-end gap-2 mt-auto">
              <button onClick={() => setIsAdding(false)} className="text-xs text-gray-500 hover:text-gray-700">Cancel</button>
              <button onClick={handleAddTag} className="text-xs font-medium text-blue-500 hover:text-blue-600">Save</button>
            </div>
            </div>
          )
        )}
      </div>

      {noteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-sm shadow-xl animate-in zoom-in-95 duration-200">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Add Remark</h3>
            <textarea
              value={noteModal.note}
              onChange={e => setNoteModal({ ...noteModal, note: e.target.value })}
              className="w-full h-24 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none mb-4"
              placeholder="What are you working on?"
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setNoteModal(null)}
                className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNote}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
