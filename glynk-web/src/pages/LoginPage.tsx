import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { loginByToken } from '../api/auth';
import { useAuthStore } from '../store/auth';
import { useT } from '../i18n';

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const t = useT();

  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    const raw = tokenInput.trim();
    if (!raw) return;
    setLoading(true);
    try {
      const user = await loginByToken(raw);
      setAuth({ uid: user.uid, token: raw });
      toast.success(t('login.success', { uid: user.uid }));
      navigate('/library');
    } catch {
      toast.error(t('login.error'));
    } finally {
      setLoading(false);
    }
  }

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
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API Token
            </label>
            <textarea
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder={t('login.placeholder')}
              rows={3}
              required
              className="glynk-input font-mono resize-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !tokenInput.trim()}
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
