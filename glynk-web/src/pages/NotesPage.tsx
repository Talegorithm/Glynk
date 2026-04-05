import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { getMyAnnotations, searchMyAnnotations } from '../api/annotation';
import type { QueryResult } from '../types/annotation';

type FilterTab = 'all' | 'highlight' | 'note';

const tabs: { key: FilterTab; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'highlight', label: '高亮' },
  { key: 'note', label: '笔记' },
];

export default function NotesPage() {
  const [results, setResults] = useState<QueryResult[]>([]);
  const [filter, setFilter] = useState<FilterTab>('all');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const loadAnnotations = useCallback(async () => {
    setLoading(true);
    try {
      const typeParam = filter === 'all' ? undefined : filter;
      const res = await getMyAnnotations({ type: typeParam });
      setResults(res.results);
    } catch {
      toast.error('加载失败');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    if (!query.trim()) {
      loadAnnotations();
    }
  }, [loadAnnotations, query]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) {
      loadAnnotations();
      return;
    }
    setLoading(true);
    try {
      const res = await searchMyAnnotations(q);
      setResults(res.results);
    } catch {
      toast.error('搜索失败');
    } finally {
      setLoading(false);
    }
  }

  function formatDate(dateStr?: string) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-8">Notes</h1>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索笔记..."
          className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600"
        />
      </form>

      {/* Filter tabs */}
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

      {loading && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">加载中...</p>
      )}

      {!loading && results.length === 0 && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">暂无笔记</p>
      )}

      {!loading && (
        <div className="space-y-3">
          {results.map((r) => {
            const ann = r.annotation;
            const linkTo = ann.location
              ? `/read/${ann.content_id}?loc=${ann.location}`
              : `/read/${ann.content_id}`;

            return (
              <Link
                key={ann.annotation_id ?? `${ann.content_id}-${ann.text.slice(0, 20)}`}
                to={linkTo}
                className="block p-4 border border-gray-200 dark:border-gray-800 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      ann.type === 'highlight'
                        ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                    }`}
                  >
                    {ann.type === 'highlight' ? '高亮' : '笔记'}
                  </span>
                  {r.content_title && (
                    <span className="text-xs text-gray-400 dark:text-gray-500 truncate">
                      {r.content_title}
                    </span>
                  )}
                  {ann.created_at && (
                    <span className="text-xs text-gray-400 dark:text-gray-500 ml-auto shrink-0">
                      {formatDate(ann.created_at)}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed line-clamp-3">
                  {ann.text}
                </p>
                {ann.note && (
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 italic">
                    {ann.note}
                  </p>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
