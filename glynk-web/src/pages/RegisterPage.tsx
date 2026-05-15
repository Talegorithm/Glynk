import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { register, requestRegisterCode } from '../api/auth';
import { useAuthStore } from '../store/auth';
import { useT } from '../i18n';

export default function RegisterPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const t = useT();

  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [code, setCode] = useState('');
  const [requestingCode, setRequestingCode] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [codeSent, setCodeSent] = useState(false);

  const normalizedEmail = email.trim().toLowerCase();

  async function handleRequestCode() {
    if (!normalizedEmail) return;
    setRequestingCode(true);
    try {
      await requestRegisterCode(normalizedEmail);
      setCodeSent(true);
      toast.success(t('register.code_sent'));
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || t('register.code_error'));
    } finally {
      setRequestingCode(false);
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error(t('register.password_mismatch'));
      return;
    }

    setSubmitting(true);
    try {
      const res = await register({
        display_name: displayName.trim() || undefined,
        email: normalizedEmail,
        password,
        code: code.trim(),
      });
      setAuth({ uid: res.entity_id, token: res.token });
      toast.success(t('register.success.title'));
      navigate('/library');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || t('register.error'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-6 flex-1 min-h-[70vh]">
      <div className="glass-panel w-full max-w-md p-8 md:p-10 rounded-[24px] relative z-10 transition-transform duration-300 hover:-translate-y-1">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-gray-900 dark:text-white mb-3 tracking-tight">{t('register.title')}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('register.desc')}
          </p>
        </div>

        <form onSubmit={handleRegister} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('register.display_name')}
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder={t('register.display_name_placeholder')}
              className="glynk-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('register.email')}
            </label>
            <div className="flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="glynk-input"
              />
              <button
                type="button"
                onClick={handleRequestCode}
                disabled={requestingCode || !normalizedEmail}
                className="shrink-0 px-4 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {requestingCode ? t('register.sending_code') : t('register.request_code')}
              </button>
            </div>
            {codeSent && (
              <p className="mt-2 text-xs text-blue-600 dark:text-blue-400 font-medium">
                {t('register.code_hint')}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('register.code')}
            </label>
            <input
              type="text"
              inputMode="numeric"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="123456"
              required
              className="glynk-input font-mono tracking-[0.3em]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('register.password')}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('register.password_placeholder')}
              required
              className="glynk-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('register.confirm_password')}
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder={t('register.confirm_password_placeholder')}
              required
              className="glynk-input"
            />
          </div>

          <button
            type="submit"
            disabled={submitting || !normalizedEmail || !password || !confirmPassword || code.length !== 6}
            className="glynk-button-primary"
          >
            {submitting ? t('register.submitting') : t('register.submit')}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          {t('register.has_account')}{' '}
          <Link to="/login" className="text-blue-600 dark:text-blue-400 font-medium hover:underline transition-colors">{t('register.login')}</Link>
        </p>
      </div>
    </div>
  );
}
