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
          <ResultCard key={r.id} result={r} t={t} />
        ))}
      </div>
    </div>
  );
}

function ResultCard({ result: r, t }: { result: SemanticSearchResult; t: ReturnType<typeof useT> }) {
  const cardInner = (
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0 flex-1">
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap line-clamp-5">
          {r.text}
        </p>
        {r.target && r.content_title && (
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 truncate">
            {r.default_view === 'target' ? t('explore.at_source', { defaultValue: '在' }) : t('explore.on_source', { defaultValue: '关于' })}{' '}
            <span className="text-gray-700 dark:text-gray-300">{r.content_title}</span>
          </p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {r.type && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
            {t(`type.${r.type}`, { defaultValue: r.type })}
          </span>
        )}
        <span className="text-xs text-gray-400 dark:text-gray-500 tabular-nums">
          {r.score.toFixed(2)}
        </span>
      </div>
    </div>
  );

  const cardClasses =
    'block p-5 border border-gray-200 dark:border-gray-800 rounded-xl transition-colors';

  // 有 target → 点击跳原文语境（browse_url 指向 /read/...）。
  // 没 target（standalone authored Unit）→ 卡片不可点（/u/{id} 路由待建）。
  if (r.target) {
    return (
      <Link to={r.browse_url} className={`${cardClasses} hover:bg-gray-50 dark:hover:bg-gray-900`}>
        {cardInner}
      </Link>
    );
  }
  return <div className={cardClasses}>{cardInner}</div>;
}
