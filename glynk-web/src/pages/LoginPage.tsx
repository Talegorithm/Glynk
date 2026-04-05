import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { loginByToken, loginByEmail, sendVerifyCode } from '../api/auth';
import { useAuthStore } from '../store/auth';

type Tab = 'token' | 'email';

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [tab, setTab] = useState<Tab>('token');

  // Token login
  const [tokenInput, setTokenInput] = useState('');
  const [tokenLoading, setTokenLoading] = useState(false);

  // Email login
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [sending, setSending] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);

  async function handleTokenLogin(e: React.FormEvent) {
    e.preventDefault();
    const t = tokenInput.trim();
    if (!t) return;
    setTokenLoading(true);
    try {
      const user = await loginByToken(t);
      setAuth({ uid: user.uid, token: t, name: user.name, email: user.email });
      navigate('/library');
    } catch {
      toast.error('Token 无效');
    } finally {
      setTokenLoading(false);
    }
  }

  async function handleSendCode() {
    if (!email.trim()) return;
    setSending(true);
    try {
      await sendVerifyCode(email.trim());
      setCodeSent(true);
      toast.success('验证码已发送');
    } catch {
      toast.error('发送失败');
    } finally {
      setSending(false);
    }
  }

  async function handleEmailLogin(e: React.FormEvent) {
    e.preventDefault();
    setEmailLoading(true);
    try {
      const res = await loginByEmail(email.trim(), code.trim());
      setAuth({ uid: res.uid, token: res.token, name: res.name, email: res.email });
      navigate('/library');
    } catch {
      toast.error('登录失败');
    } finally {
      setEmailLoading(false);
    }
  }

  const tabClass = (t: Tab) =>
    `flex-1 py-2 text-sm font-medium text-center cursor-pointer transition-colors ${
      tab === t
        ? 'text-gray-900 dark:text-gray-100 border-b-2 border-gray-900 dark:border-gray-100'
        : 'text-gray-400 dark:text-gray-500 border-b-2 border-transparent hover:text-gray-600 dark:hover:text-gray-300'
    }`;

  return (
    <div className="max-w-md mx-auto px-6 py-20">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-8">登录</h1>

      {/* Tabs */}
      <div className="flex mb-8 border-b border-gray-200 dark:border-gray-800">
        <button className={tabClass('token')} onClick={() => setTab('token')}>
          Token 登录
        </button>
        <button className={tabClass('email')} onClick={() => setTab('email')}>
          邮箱登录
        </button>
      </div>

      {tab === 'token' ? (
        <form onSubmit={handleTokenLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Token
            </label>
            <textarea
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="粘贴你的 token..."
              rows={3}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600 resize-none"
            />
          </div>
          <button
            type="submit"
            disabled={tokenLoading}
            className="w-full py-2.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
          >
            {tokenLoading ? '验证中...' : '登录'}
          </button>
        </form>
      ) : (
        <form onSubmit={handleEmailLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              邮箱
            </label>
            <div className="flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600"
              />
              <button
                type="button"
                onClick={handleSendCode}
                disabled={sending || !email.trim()}
                className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 cursor-pointer whitespace-nowrap"
              >
                {codeSent ? '重新发送' : '发送验证码'}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              验证码
            </label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="6 位验证码"
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600"
            />
          </div>
          <button
            type="submit"
            disabled={emailLoading}
            className="w-full py-2.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
          >
            {emailLoading ? '登录中...' : '登录'}
          </button>
        </form>
      )}

      <p className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        还没有账号？{' '}
        <Link to="/register" className="text-gray-900 dark:text-gray-100 font-medium hover:underline">
          注册
        </Link>
      </p>
    </div>
  );
}
