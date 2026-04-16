import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { getMyAnnotations, searchMyAnnotations } from '../api/annotation';
import type { Annotation } from '../types/annotation';
import { useT } from '../i18n';
import { getAuthoredUnits } from '../api/content';
import { DropEditor } from '../components/notes/DropEditor';

type FilterTab = 'all' | 'highlight' | 'note' | 'hook' | 'idea';

const PAGE_SIZE = 50;

const tabKeys: FilterTab[] = ['all', 'idea', 'highlight', 'hook', 'note'];

export default function NotesPage() {
  const t = useT();

  const tabs = tabKeys.map((key) => ({
    key,
    label: t(`notes.tab.${key}`),
  }));
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [filter, setFilter] = useState<FilterTab>('all');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [isSearch, setIsSearch] = useState(false);

  const load = useCallback(async (p = 0) => {
    setLoading(true);
    try {
      if (filter === 'idea') {
        const res = await getAuthoredUnits(PAGE_SIZE, p * PAGE_SIZE);
        // Map Content back to Annotation-like shape for display
        const mappedAnnotations: Annotation[] = res.contents.map((c: any) => ({
          id: c.content_id,
          content_id: c.content_id,
          anchor: {},
          type: 'idea',
          text: c.text,
          tags: [],
          created_at: c.created_at,
          visibility: 'public',
          source: 'human',
          contextuality: 'standalone'
        }));
        setAnnotations(mappedAnnotations);
        setTotal(res.total);
      } else {
        const typeParam = filter === 'all' ? undefined : filter;
        const res = await getMyAnnotations({ type: typeParam, limit: PAGE_SIZE, offset: p * PAGE_SIZE });
        setAnnotations(res.annotations);
        setTotal(res.total);
      }
      setIsSearch(false);
    } catch {
      toast.error(t('notes.load_error'));
    } finally {
      setLoading(false);
    }
  }, [filter, t]);

  useEffect(() => {
    setPage(0);
    if (!query.trim()) load(0);
  }, [load, query]);

  function handlePageChange(newPage: number) {
    setPage(newPage);
    load(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) { setPage(0); load(0); return; }
    setLoading(true);
    try {
      const res = await searchMyAnnotations(q);
      setAnnotations(res.results);
      setTotal(res.results.length);
      setIsSearch(true);
      setPage(0);
    } catch {
      toast.error(t('notes.search_error'));
    } finally {
      setLoading(false);
    }
  }

  function formatDate(dateStr?: string) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  }

  const typeBadge: Record<string, { label: string; cls: string }> = {
    highlight: { label: t('type.highlight'), cls: 'bg-yellow-100 text-yellow-700' },
    hook: { label: t('type.hook'), cls: 'bg-purple-100 text-purple-700' },
    note: { label: t('type.note'), cls: 'bg-blue-100 text-blue-700' },
    reaction: { label: t('type.reaction'), cls: 'bg-green-100 text-green-700' },
    idea: { label: t('type.idea', { defaultValue: 'Idea' }), cls: 'bg-emerald-100 text-emerald-700' },
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const offset = page * PAGE_SIZE;

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{t('notes.title')}</h1>
        <span className="text-sm text-gray-400 dark:text-gray-500">
          {total > 0 && (isSearch
            ? t('notes.results', { count: total })
            : totalPages > 1
              ? t('notes.range', { from: offset + 1, to: Math.min(offset + annotations.length, total), total })
              : t('notes.count', { count: total })
          )}
        </span>
      </div>

      <form onSubmit={handleSearch} className="mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('notes.search_placeholder')}
          className="glynk-input"
        />
      </form>

      <DropEditor onSuccess={() => { if (filter === 'idea' || filter === 'all') load(0); }} />

      <div className="flex gap-1 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setFilter(tab.key); setPage(0); }}
            className={`px-3 py-1.5 text-sm rounded-lg cursor-pointer transition-colors ${
              filter === tab.key
                ? 'bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">{t('notes.loading')}</p>}

      {!loading && annotations.length === 0 && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">{t('notes.empty')}</p>
      )}

      {!loading && (
        <div className="space-y-3">
          {annotations.map((a) => {
            const anchor = a.anchor as Record<string, unknown>;
            const spans = (anchor?.spans as string[]) || [];
            const firstSpan = spans[0] || '';
            let linkTo = firstSpan
              ? `/read/${a.content_id}?loc=${firstSpan}`
              : `/read/${a.content_id}`;
              
            if (a.type === 'idea') {
              linkTo = '#'; // Ideas are standalone, maybe view in modal later, for now just no-op
            }

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

      {/* Pagination */}
      {!loading && !isSearch && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page === 0}
            className="px-3 py-1.5 text-sm rounded-lg cursor-pointer transition-colors disabled:opacity-30 disabled:cursor-default text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {t('notes.prev')}
          </button>
          <span className="text-sm text-gray-400 dark:text-gray-500 tabular-nums">
            {page + 1} / {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 text-sm rounded-lg cursor-pointer transition-colors disabled:opacity-30 disabled:cursor-default text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {t('notes.next')}
          </button>
        </div>
      )}
    </div>
  );
}
