import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';

export default function TimetrackLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-transparent">
      <nav className="border-b border-gray-200/20 dark:border-gray-800/20 px-6 py-3 flex items-center justify-between glass-panel sticky top-0 z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </Link>
            <span className="text-xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
              Timetrack
            </span>
          </div>
          
          <div className="flex items-center gap-4 ml-4">
            <Link
              to="/timetrack"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/timetrack' 
                  ? 'text-blue-600 dark:text-blue-400' 
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
              }`}
            >
              Timers
            </Link>
            <Link
              to="/timetrack/logs"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/timetrack/logs' 
                  ? 'text-blue-600 dark:text-blue-400' 
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
              }`}
            >
              Logs
            </Link>
            <Link
              to="/timetrack/stats"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/timetrack/stats' 
                  ? 'text-blue-600 dark:text-blue-400' 
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
              }`}
            >
              Stats
            </Link>
          </div>
        </div>
      </nav>
      <main className="flex-1 relative z-0 overflow-y-auto h-full pb-20">
        <Outlet />
      </main>
    </div>
  );
}
