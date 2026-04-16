/**
 * 登录弹窗 — 可关闭，用于阅读器等非强制登录场景
 */

import { useState } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { loginByToken } from '../api/auth';
import { useAuthStore } from '../store/auth';
import { useT } from '../i18n';

interface LoginModalProps {
  onClose: () => void;
  hint?: string;
}

export function LoginModal({ onClose, hint }: LoginModalProps) {
  const t = useT();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    const raw = tokenInput.trim();
    if (!raw) return;
    setLoading(true);
    try {
      const user = await loginByToken(raw);
      setAuth({ uid: user.entity_id, token: raw });
      toast.success(t('login.success', { uid: user.entity_id }));
      onClose();
    } catch {
      toast.error(t('login.error'));
    } finally {
      setLoading(false);
    }
  }

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
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                API Token
              </label>
              <textarea
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder={t('login.placeholder')}
                rows={2}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-mono text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !tokenInput.trim()}
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
