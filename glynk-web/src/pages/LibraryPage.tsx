import { useEffect, useState, useCallback, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { listContents } from '../api/content';
import { semanticSearch } from '../api/search';
import type { Content } from '../types/content';
import type { SemanticSearchResult } from '../api/search';
import { useT } from '../i18n';

const sourceIcons: Record<string, string> = {
  book: '\u{1F4D6}',
  article: '\u{1F4C4}',
  pdf: '\u{1F4CB}',
  web: '\u{1F310}',
};

// Cache search results in module scope so they survive navigation
let cachedQuery = '';
let cachedResults: SemanticSearchResult[] | null = null;

export default function LibraryPage() {
  const t = useT();
  const [searchParams, setSearchParams] = useSearchParams();
  const [contents, setContents] = useState<Content[]>([]);
  const [total, setTotal] = useState(0);
  const urlQuery = searchParams.get('q') || '';
  const [query, setQuery] = useState(urlQuery);
  const [searchResults, setSearchResults] = useState<SemanticSearchResult[] | null>(null);
  const [loading, setLoading] = useState(true);
  const restoredRef = useRef(false);

  useEffect(() => {
    listContents(50, 0)
      .then((res) => { setContents(res.contents); setTotal(res.total); })
      .catch(() => toast.error(t('library.load_error')))
      .finally(() => setLoading(false));
  }, []);

  // Restore cached results or re-search from URL
  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;

    if (urlQuery && cachedQuery === urlQuery && cachedResults) {
      // Restore from cache (instant, no re-fetch)
      setSearchResults(cachedResults);
      setLoading(false);
    } else if (urlQuery) {
      // Re-search (first time or different query)
      setLoading(true);
      semanticSearch({ text: urlQuery, top_k: 20 })
        .then((res) => {
          setSearchResults(res.results);
          cachedQuery = urlQuery;
          cachedResults = res.results;
        })
        .catch(() => toast.error(t('library.search_error')))
        .finally(() => setLoading(false));
    }
  }, [urlQuery]);

  const handleSearch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) {
      setSearchResults(null);
      cachedQuery = '';
      cachedResults = null;
      setSearchParams({});
      return;
    }
    setLoading(true);
    setSearchParams({ q });
    try {
      const res = await semanticSearch({ text: q, top_k: 20 });
      setSearchResults(res.results);
      cachedQuery = q;
      cachedResults = res.results;
    } catch {
      toast.error(t('library.search_error'));
    } finally {
      setLoading(false);
    }
  }, [query, setSearchParams]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{t('library.title')}</h1>
        {total > 0 && !searchResults && (
          <span className="text-sm text-gray-400 dark:text-gray-500">
            {contents.length < total ? t('library.count_partial', { shown: contents.length, total }) : t('library.count', { count: total })}
          </span>
        )}
      </div>

      <form onSubmit={handleSearch} className="mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!e.target.value.trim()) {
              setSearchResults(null);
              cachedQuery = '';
              cachedResults = null;
              setSearchParams({});
            }
          }}
          placeholder={t('library.search_placeholder')}
          className="glynk-input"
        />
      </form>

      {loading && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">{t('library.loading')}</p>
      )}

      {/* Search results */}
      {!loading && searchResults && (
        <div className="space-y-3">
          {searchResults.length === 0 ? (
            <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">{t('library.no_results')}</p>
          ) : (
            searchResults.map((r) => {
              const spans = r.anchor?.spans || [];
              const loc = spans[0] || '';
              const to = loc ? `/read/${r.content_id}?loc=${loc}` : `/read/${r.content_id}`;
              return (
              <Link
                key={r.annotation_id}
                to={to}
                className="block p-4 md:p-5 rounded-xl glass-panel hover:-translate-y-0.5 transition-transform duration-200"
              >
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {r.content_title}
                  </h3>
                  <span className="text-xs text-gray-400 dark:text-gray-500 tabular-nums shrink-0">
                    {r.score.toFixed(2)}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                  {r.text}
                </p>
              </Link>
              );
            })
          )}
        </div>
      )}

      {/* Content grid */}
      {!loading && !searchResults && (
        <>
          {contents.length === 0 ? (
            <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">
              {t('library.empty')}
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {contents.map((c) => (
                <Link
                  key={c.content_id}
                  to={`/read/${c.content_id}`}
                  className="block p-4 md:p-5 rounded-xl glass-panel hover:-translate-y-0.5 transition-transform duration-200"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-base" role="img">
                      {sourceIcons[c.source_url ? 'web' : 'book'] ?? '\u{1F4C4}'}
                    </span>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {c.title}
                    </h3>
                  </div>
                  {c.author && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 truncate">
                      {c.author}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
