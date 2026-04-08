import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { getMyAnnotations, searchMyAnnotations } from '../api/annotation';
import type { Annotation } from '../types/annotation';

type FilterTab = 'all' | 'highlight' | 'note' | 'hook';

const tabs: { key: FilterTab; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'highlight', label: '高亮' },
  { key: 'hook', label: 'Hook' },
  { key: 'note', label: '笔记' },
];

export default function NotesPage() {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<FilterTab>('all');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const typeParam = filter === 'all' ? undefined : filter;
      const res = await getMyAnnotations({ type: typeParam, limit: 50 });
      setAnnotations(res.annotations);
      setTotal(res.total);
    } catch {
      toast.error('加载失败');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    if (!query.trim()) load();
  }, [load, query]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) { load(); return; }
    setLoading(true);
    try {
      const res = await searchMyAnnotations(q);
      setAnnotations(res.results);
      setTotal(res.results.length);
    } catch {
      toast.error('搜索失败');
    } finally {
      setLoading(false);
    }
  }

  function formatDate(dateStr?: string) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  }

  const typeBadge: Record<string, { label: string; cls: string }> = {
    highlight: { label: '高亮', cls: 'bg-yellow-100 text-yellow-700' },
    hook: { label: 'Hook', cls: 'bg-purple-100 text-purple-700' },
    note: { label: '笔记', cls: 'bg-blue-100 text-blue-700' },
    reaction: { label: '反应', cls: 'bg-green-100 text-green-700' },
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Notes</h1>
        <span className="text-sm text-gray-400 dark:text-gray-500">{total} 条</span>
      </div>

      <form onSubmit={handleSearch} className="mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索笔记..."
          className="glynk-input"
        />
      </form>

      <div className="flex gap-1 mb-6">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setFilter(t.key)}
            className={`px-3 py-1.5 text-sm rounded-lg cursor-pointer transition-colors ${
              filter === t.key
                ? 'bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">加载中...</p>}

      {!loading && annotations.length === 0 && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">暂无标注</p>
      )}

      {!loading && (
        <div className="space-y-3">
          {annotations.map((a) => {
            const anchor = a.anchor as Record<string, unknown>;
            const spans = (anchor?.spans as string[]) || [];
            const firstSpan = spans[0] || '';
            const linkTo = firstSpan
              ? `/read/${a.content_id}?loc=${firstSpan}`
              : `/read/${a.content_id}`;

            const badge = typeBadge[a.type] || { label: a.type, cls: 'bg-gray-100 text-gray-600' };

            return (
              <Link
                key={a.id}
                to={linkTo}
                className="block p-4 md:p-5 rounded-xl glass-panel hover:-translate-y-0.5 transition-transform duration-200"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${badge.cls}`}>
                    {badge.label}
                  </span>
                  {a.tags?.length > 0 && (
                    <span className="text-xs text-gray-400 dark:text-gray-500 truncate">
                      {a.tags.join(' · ')}
                    </span>
                  )}
                  <span className="text-xs text-gray-400 dark:text-gray-500 ml-auto shrink-0">
                    {formatDate(a.created_at)}
                  </span>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed line-clamp-3">
                  {a.text}
                </p>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
