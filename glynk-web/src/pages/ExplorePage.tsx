import { useState } from 'react';
import { Link } from 'react-router-dom';
import { semanticSearch } from '../api/search';
import type { SemanticSearchResult } from '../api/search';
import { useT } from '../i18n';

export default function ExplorePage() {
  const t = useT();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SemanticSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;

    setLoading(true);
    try {
      const res = await semanticSearch({ text: q, top_k: 20 });
      setResults(res.results);
      setSearched(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <form onSubmit={handleSearch} className="mb-10">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('explore.placeholder')}
            className="w-full px-4 py-3 pr-24 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600 text-base"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
          >
            {loading ? '...' : t('explore.submit')}
          </button>
        </div>
      </form>

      {loading && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500">{t('explore.loading')}</p>
      )}

      {!loading && searched && results.length === 0 && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500">{t('explore.no_results')}</p>
      )}

      <div className="space-y-4">
        {results.map((r) => (
          <Link
            key={r.id}
            to={`/read/${r.content_id}`}
            className="block p-5 border border-gray-200 dark:border-gray-800 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                {r.content_title && (
                  <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1 truncate">
                    {r.content_title}
                  </h3>
                )}
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 leading-relaxed">
                  {r.text}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                  {t(`type.${r.type}`)}
                </span>
                <span className="text-xs text-gray-400 dark:text-gray-500 tabular-nums">
                  {r.score.toFixed(2)}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
