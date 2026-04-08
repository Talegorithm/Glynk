import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { listContents } from '../api/content';
import { semanticSearch } from '../api/search';
import type { Content } from '../types/content';
import type { SemanticSearchResult } from '../api/search';

const sourceIcons: Record<string, string> = {
  book: '\u{1F4D6}',
  article: '\u{1F4C4}',
  pdf: '\u{1F4CB}',
  web: '\u{1F310}',
};

export default function LibraryPage() {
  const [contents, setContents] = useState<Content[]>([]);
  const [searchResults, setSearchResults] = useState<SemanticSearchResult[] | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listContents(50, 0)
      .then((res) => setContents(res.contents))
      .catch(() => toast.error('加载失败'))
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) {
      setSearchResults(null);
      return;
    }
    setLoading(true);
    try {
      const res = await semanticSearch({ text: q, top_k: 20 });
      setSearchResults(res.results);
    } catch {
      toast.error('搜索失败');
    } finally {
      setLoading(false);
    }
  }, [query]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Library</h1>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!e.target.value.trim()) setSearchResults(null);
          }}
          placeholder="语义搜索..."
          className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600"
        />
      </form>

      {loading && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">加载中...</p>
      )}

      {/* Search results */}
      {!loading && searchResults && (
        <div className="space-y-3">
          {searchResults.length === 0 ? (
            <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">无结果</p>
          ) : (
            searchResults.map((r) => (
              <Link
                key={r.annotation_id}
                to={`/read/${r.content_id}`}
                className="block p-4 border border-gray-200 dark:border-gray-800 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
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
            ))
          )}
        </div>
      )}

      {/* Content grid */}
      {!loading && !searchResults && (
        <>
          {contents.length === 0 ? (
            <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-16">
              还没有内容
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {contents.map((c) => (
                <Link
                  key={c.content_id}
                  to={`/read/${c.content_id}`}
                  className="p-5 border border-gray-200 dark:border-gray-800 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
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
