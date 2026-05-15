import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { loginByToken, loginWithPassword } from '../api/auth';
import { useAuthStore } from '../store/auth';
import { useT } from '../i18n';

type LoginMode = 'password' | 'token';

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const t = useT();

  const [mode, setMode] = useState<LoginMode>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const user = mode === 'password'
        ? await loginWithPassword({ email: email.trim().toLowerCase(), password })
        : await loginByToken(tokenInput.trim());
      setAuth({ uid: user.entity_id, token: user.token });
      toast.success(t('login.success', { uid: user.entity_id }));
      navigate('/library');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || t(mode === 'password' ? 'login.error' : 'login.token_error'));
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = mode === 'password'
    ? Boolean(email.trim() && password)
    : Boolean(tokenInput.trim());

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-6 flex-1 min-h-[70vh]">
      <div className="glass-panel w-full max-w-md p-8 md:p-10 rounded-[24px] relative z-10 transition-transform duration-300 hover:-translate-y-1">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-gray-900 dark:text-white mb-3 tracking-tight">{t('login.title')}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('login.desc')}
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="grid grid-cols-2 gap-1 rounded-xl bg-gray-100/80 dark:bg-gray-800/80 p-1">
            <button
              type="button"
              onClick={() => setMode('password')}
              className={`h-10 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                mode === 'password'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              {t('login.password_tab')}
            </button>
            <button
              type="button"
              onClick={() => setMode('token')}
              className={`h-10 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                mode === 'token'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              {t('login.token_tab')}
            </button>
          </div>

          {mode === 'password' ? (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('login.email')}
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="glynk-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('login.password')}
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('login.password_placeholder')}
                  required
                  className="glynk-input"
                />
              </div>
            </>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('login.token_label')}
              </label>
              <textarea
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder={t('login.token_placeholder')}
                rows={3}
                required
                className="glynk-input font-mono resize-none"
              />
              <p className="mt-2 text-xs text-gray-400 dark:text-gray-500 font-medium">
                {t('login.token_hint')}
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !canSubmit}
            className="glynk-button-primary"
          >
            {loading ? (
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              t('login.submit')
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          {t('login.no_account')}{' '}
          <Link to="/register" className="text-blue-600 dark:text-blue-400 font-medium hover:underline transition-colors">
            {t('login.register')}
          </Link>
        </p>
      </div>
    </div>
  );
}
