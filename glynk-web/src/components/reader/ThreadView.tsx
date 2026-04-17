import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { getSpanThread, createAnnotation, deleteAnnotation } from '../../api/annotation';
import type { Annotation } from '../../types/annotation';
import { useAuthStore } from '../../store/auth';
import { useT } from '../../i18n';
import { USER_SELECTABLE_COLORS, getColorByKey } from '../../config/colors';
import { highlightSpanRange } from '../../utils/reader/selection';
import type { SelectionRange } from '../../utils/reader/selection';

interface ThreadViewProps {
  contentId: string;
  targetSpan: string;
  pendingSelection?: SelectionRange | null;
  onClose: () => void;
  requestLogin?: () => void;
  onThreadUpdated?: () => void;
}

export function ThreadView({ contentId, targetSpan, pendingSelection, onClose, requestLogin, onThreadUpdated }: ThreadViewProps) {
  const t = useT();
  const token = useAuthStore((state) => state.token);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null); // target reply's unit ID if nested
  const [submitting, setSubmitting] = useState(false);
  const [highlightColor, setHighlightColor] = useState('yellow');
  const uid = useAuthStore((state) => state.uid);

  // Live preview highlight color changes
  useEffect(() => {
    if (pendingSelection && highlightColor) {
      const colorConfig = getColorByKey(highlightColor);
      if (colorConfig) {
        highlightSpanRange(
          pendingSelection.startSpanId,
          pendingSelection.endSpanId,
          pendingSelection.startOffset,
          pendingSelection.endOffset,
          colorConfig.highlight,
          'TEMP_THREAD_HIGHLIGHT'
        );
      }
    }
  }, [highlightColor, pendingSelection]);

  useEffect(() => {
    async function fetchThread() {
      if (!contentId || !targetSpan) return;
      setLoading(true);
      try {
        const data = await getSpanThread(contentId, targetSpan);
        // Backend returns all anchors for this unit (flat list).
        // Roots: role='reply' with target_span === targetSpan (or role='note').
        // Children: role='reply' with metadata.in_reply_to === parent reply's unit_id.
        setAnnotations(data);
      } catch (err) {
        console.error('Failed to load thread:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchThread();
  }, [contentId, targetSpan]);

  const treeData = buildTree(annotations, uid, targetSpan);

  // Identify root annotation so we can allow deleting a pure highlight
  const rootAnnotation = annotations.find(
    a => (a.type === 'highlight' || a.type === 'note') && 
         (a.author_id === uid || (!a.author_id && true)) && // assume ours if no author_id locally
         (a.target_span === targetSpan || (a.anchor as any)?.startSpanId === targetSpan)
  );

  async function handleDelete(id: string, unitId: string | null) {
    if (!confirm('确定删除这条记录吗？')) return;
    try {
      if (unitId) {
        // Technically we might want a delete target_unit api, but deleting the annotation removes the anchor
      }
      await deleteAnnotation(id);
      
      onThreadUpdated?.();

      if (rootAnnotation && id === rootAnnotation.id) {
        onClose();
        return;
      }
      
      const data = await getSpanThread(contentId, targetSpan);
      setAnnotations(data);
    } catch (err) {
      console.error('Delete failed:', err);
    }
  }

  async function handleEdit(id: string, newText: string) {
    try {
      const { updateAnnotation } = await import('../../api/annotation');
      await updateAnnotation(id, { text: newText });
      onThreadUpdated?.();
      const data = await getSpanThread(contentId, targetSpan);
      setAnnotations(data);
    } catch (err) {
      console.error('Update failed:', err);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!replyText.trim() || !token) {
      if (!token) requestLogin?.();
      return;
    }

    setSubmitting(true);
    try {
      let finalAnchor: any = { targetSpanId: targetSpan };
      
      if (!replyingTo && pendingSelection) {
        finalAnchor = {
          startSpanId: pendingSelection.startSpanId,
          endSpanId: pendingSelection.endSpanId,
          startOffset: pendingSelection.startOffset,
          endOffset: pendingSelection.endOffset,
          color: highlightColor,
          spans: pendingSelection.spanIds,
        };
      } else {
        // Just linking to the existing span
        finalAnchor = {
          startSpanId: targetSpan,
          endSpanId: targetSpan,
          startOffset: 0,
          endOffset: 0,
          color: 'none'
        };
      }

      await createAnnotation({
        content_id: contentId,
        anchor: finalAnchor,
        type: replyingTo ? 'reply' : 'note',
        text: replyText.trim(),
        visibility: 'public',
        ...(replyingTo ? { in_reply_to: replyingTo } : {})
      });

      setReplyText('');
      setReplyingTo(null);
      
      onThreadUpdated?.();

      // refetch
      const data = await getSpanThread(contentId, targetSpan);
      setAnnotations(data);
    } catch (err) {
      console.error('Reply failed:', err);
    } finally {
      setSubmitting(false);
    }
  }

  return createPortal(
    <div 
      className="fixed top-0 right-0 h-full w-full max-w-[400px] bg-white dark:bg-gray-900 sky:bg-white/40 sky:dark:bg-black/30 backdrop-blur-2xl shadow-2xl z-[2147483647] flex flex-col border-l border-gray-200 dark:border-gray-800 sky:border-white/40 sky:dark:border-white/10 transition-transform"
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200/50 dark:border-gray-800/50 shrink-0 mt-2">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
          {t('thread.title', { defaultValue: '讨论' })}
        </h2>
        <div className="flex items-center gap-2">
          {rootAnnotation && (
            <button 
              onClick={() => handleDelete(rootAnnotation.id, rootAnnotation.text ? rootAnnotation.id : null)}
              className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors title='删除高亮'"
              title="删除标注"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
          <button onClick={onClose} aria-label="Close" className="p-2 -mr-2 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer flex items-center justify-center focus:outline-none">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading && <p className="text-sm text-gray-400">{t('common.loading', { defaultValue: 'Loading...' })}</p>}
        {!loading && treeData.length === 0 && (
          <div className="text-center py-10">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('thread.empty', { defaultValue: 'No notes or discussions yet. Be the first!' })}
            </p>
          </div>
        )}
        {!loading && treeData.map(node => (
          <ThreadNode 
            key={node.id} 
            node={node} 
            onReplyClick={(uId) => setReplyingTo(uId)} 
            onDeleteClick={handleDelete}
            onEditSubmit={handleEdit}
          />
        ))}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 dark:border-gray-800 sky:border-white/20 sky:dark:border-white/10 shrink-0 bg-transparent">
        {!replyingTo && pendingSelection && (
          <div className="flex items-center gap-2 mb-2 px-1">
            <span className="text-xs text-gray-500 font-medium">高亮颜色：</span>
            {USER_SELECTABLE_COLORS.map(c => (
              <button
                key={c.key}
                type="button"
                onClick={() => setHighlightColor(c.key)}
                className={`w-5 h-5 rounded-full border-2 transition-transform ${highlightColor === c.key ? 'scale-110 border-blue-500 shadow-sm' : 'border-transparent hover:scale-105'}`}
                style={{ backgroundColor: c.highlight.replace(/,\s*[\d.]+\)/, ', 1)') }} // Make it more solid for the picker button
                title={c.name}
              />
            ))}
          </div>
        )}
        {replyingTo && (
          <div className="flex items-center justify-between mb-2 text-xs text-blue-600 dark:text-blue-400">
            <span>{t('thread.replying_to', { defaultValue: '回复中...' })}</span>
            <button type="button" onClick={() => setReplyingTo(null)} className="hover:underline text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">取消</button>
          </div>
        )}
        <textarea
          value={replyText}
          onChange={(e) => setReplyText(e.target.value)}
          placeholder={t('thread.placeholder', { defaultValue: '加入讨论...' })}
          className="glynk-input resize-none min-h-[80px] mt-1"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              handleSubmit(e as any);
            }
          }}
        />
        <div className="mt-2 flex justify-end">
          <button 
            type="submit" 
            disabled={submitting || !replyText.trim()}
            className="px-5 py-2 bg-blue-600 shadow-lg shadow-blue-500/30 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all duration-300 hover:-translate-y-0.5 cursor-pointer"
          >
            {submitting ? '发送中' : (replyingTo ? '回复' : '发送')}
          </button>
        </div>
      </form>
    </div>,
    document.body
  );
}

// Tree builder and components

interface ThreadNodeData {
  id: string; // anchor id
  unitId: string | null; // source unit id
  text: string;
  author: string;
  date: string;
  children: ThreadNodeData[];
  isMine: boolean;
  parentId: string | null;
}

function buildTree(annotations: Annotation[], uid: string | null, targetSpan: string): ThreadNodeData[] {
  // Roles shown in ThreadView. 'reply_to' is dead legacy (the old 2nd-anchor trick);
  // backend no longer emits it.
  const validTypes = ['reply', 'note'];
  const nodes = annotations
    .filter(a => validTypes.includes(a.type))
    .map(a => ({
      id: a.id,
      unitId: a.source_unit || null, // from updated api
      text: a.text,
      author: a.author_name || 'Anonymous',
      date: new Date(a.created_at || '').toLocaleDateString(),
      children: [],
      isMine: !a.author_id || a.author_id === uid,
      parentId: (a.anchor as any)?.in_reply_to || null,
      raw: a // keep reference to check target
    }));

  const nodeMap = new Map<string, ThreadNodeData & { raw: Annotation }>();
  nodes.forEach(n => {
    if (n.unitId) {
       nodeMap.set(n.unitId, n as any);
    }
  });

  const roots: ThreadNodeData[] = [];

  nodes.forEach(n => {
    if (n.parentId && nodeMap.has(n.parentId)) {
      nodeMap.get(n.parentId)!.children.push(n);
    } else {
      // Must match targetSpan to be a root for this thread view!
      const isMatch = n.raw.target_span === targetSpan || 
                      (n.raw.anchor as any)?.startSpanId === targetSpan || 
                      (n.raw.anchor as any)?.spans?.includes(targetSpan);
      if (isMatch) {
        roots.push(n);
      }
    }
  });

  return roots.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
}

function ThreadNode({ node, onReplyClick, onDeleteClick, onEditSubmit }: { node: ThreadNodeData, onReplyClick: (unitId: string) => void, onDeleteClick: (id: string, unitId: string | null) => void, onEditSubmit: (id: string, newText: string) => Promise<void> }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(node.text);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleEditSubmit = async () => {
    if (!editText.trim() || editText === node.text) {
      setIsEditing(false);
      return;
    }
    setIsSubmitting(true);
    try {
      await onEditSubmit(node.id, editText);
      setIsEditing(false);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-100 dark:border-gray-700/50 shadow-sm relative group">
      <div className="flex items-center justify-between mb-2 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-800 dark:text-gray-200">{node.author}</span>
          <span>·</span>
          <span>{node.date}</span>
        </div>
        {node.isMine && !isEditing && (
          <div className="hidden group-hover:flex items-center gap-2">
            <button 
              onClick={() => setIsEditing(true)} 
              className="text-gray-400 hover:text-blue-500"
              title="Edit"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
            <button 
              onClick={() => onDeleteClick(node.id, node.unitId)} 
              className="text-gray-400 hover:text-red-500"
              title="Delete"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {isEditing ? (
        <div className="mt-2 space-y-2">
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="w-full text-sm p-2 border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 rounded outline-none resize-none focus:ring-1 focus:ring-blue-500 min-h-[60px]"
            autoFocus
          />
          <div className="flex justify-end gap-2">
            <button onClick={() => { setIsEditing(false); setEditText(node.text); }} className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700">取消</button>
            <button onClick={handleEditSubmit} disabled={isSubmitting} className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50">保存</button>
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed break-words whitespace-pre-wrap">
          {node.text}
        </p>
      )}
      
      {node.unitId && !isEditing && (
        <button onClick={() => onReplyClick(node.unitId!)} className="mt-2 text-xs text-blue-500 hover:text-blue-600 font-medium">
          回复
        </button>
      )} 
      
      {node.children.length > 0 && (
        <div className="mt-3 pl-4 border-l-2 border-gray-100 dark:border-gray-700 space-y-3">
          {node.children.map(c => <ThreadNode key={c.id} node={c} onReplyClick={onReplyClick} onDeleteClick={onDeleteClick} onEditSubmit={onEditSubmit} />)}
        </div>
      )}
    </div>
  );
}
