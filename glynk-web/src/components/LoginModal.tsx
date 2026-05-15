/**
 * 登录弹窗 — 可关闭，用于阅读器等非强制登录场景
 */

import { useState } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { loginByToken, loginWithPassword } from '../api/auth';
import { useAuthStore } from '../store/auth';
import { useT } from '../i18n';

interface LoginModalProps {
  onClose: () => void;
  hint?: string;
}

type LoginMode = 'password' | 'token';

export function LoginModal({ onClose, hint }: LoginModalProps) {
  const t = useT();
  const setAuth = useAuthStore((s) => s.setAuth);
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
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || t(mode === 'password' ? 'login.error' : 'login.token_error'));
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = mode === 'password'
    ? Boolean(email.trim() && password)
    : Boolean(tokenInput.trim());

  const modal = (
    <div className="fixed inset-0 z-[2147483646] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />

      <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
        {/* 关闭按钮 */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors cursor-pointer"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="px-8 pt-8 pb-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {t('login.title')}
          </h3>
          {hint && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{hint}</p>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="grid grid-cols-2 gap-1 rounded-xl bg-gray-100/80 dark:bg-gray-900/80 p-1">
              <button
                type="button"
                onClick={() => setMode('password')}
                className={`h-9 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
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
                className={`h-9 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    {t('login.email')}
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    {t('login.password')}
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t('login.password_placeholder')}
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm"
                  />
                </div>
              </>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  {t('login.token_label')}
                </label>
                <textarea
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder={t('login.token_placeholder')}
                  rows={2}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-mono text-sm"
                />
                <p className="mt-1.5 text-xs text-gray-400 dark:text-gray-500">
                  {t('login.token_hint')}
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !canSubmit}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {loading ? (
                <svg className="animate-spin h-5 w-5 text-white mx-auto" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                t('login.submit')
              )}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
            {t('login.no_account')}{' '}
            <Link to="/register" className="text-blue-600 dark:text-blue-400 font-medium hover:underline">
              {t('login.register')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
