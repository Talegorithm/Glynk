import { Link, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/auth';

export default function Layout() {
  const { isAuthenticated, logout } = useAuthStore();
  const authenticated = isAuthenticated();

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-gray-950">
      <nav className="border-b border-gray-200 dark:border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
            glynk
          </Link>
          {authenticated && (
            <>
              <Link
                to="/library"
                className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              >
                Library
              </Link>
              <Link
                to="/notes"
                className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              >
                Notes
              </Link>
            </>
          )}
        </div>
        <div className="flex items-center gap-4">
          {authenticated ? (
            <button
              onClick={logout}
              className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 cursor-pointer"
            >
              Logout
            </button>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
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
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
