import { Link, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/auth';
import { useThemeStore } from '../store/theme';

export default function Layout() {
  const { isAuthenticated, logout } = useAuthStore();
  const authenticated = isAuthenticated();
  const { theme, toggleTheme } = useThemeStore();

  return (
    <div className="min-h-screen flex flex-col bg-transparent">
      <nav className="border-b border-gray-200/20 dark:border-gray-800/20 px-6 py-3 flex items-center justify-between glass-panel sticky top-0 z-50">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
            Glynk
          </Link>
          {authenticated && (
            <>
              <Link
                to="/library"
                className="text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
              >
                Library
              </Link>
              <Link
                to="/notes"
                className="text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
              >
                Notes
              </Link>
            </>
          )}
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-md hover:bg-gray-200/50 dark:hover:bg-gray-700/50 text-gray-700 dark:text-gray-300 transition-colors cursor-pointer"
            title="Toggle theme"
          >
            {theme === 'sky' && (
              <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            )}
            {theme === 'dark' && (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
            {theme === 'light' && (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            )}
          </button>
          
          {authenticated ? (
            <button
              onClick={logout}
              className="text-sm text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100 cursor-pointer"
            >
              Logout
            </button>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="text-sm bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 px-4 py-1.5 rounded-md hover:opacity-90"
              >
                Register
              </Link>
            </>
          )}
        </div>
      </nav>
      <main className="flex-1 layout-main relative z-0">
        <Outlet />
      </main>
    </div>
  );
}
