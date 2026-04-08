import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { loginByToken } from '../api/auth';
import { useAuthStore } from '../store/auth';
import { SkyBackground } from '../components/common/SkyBackground';

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    const t = tokenInput.trim();
    if (!t) return;
    setLoading(true);
    try {
      const user = await loginByToken(t);
      setAuth({ uid: user.uid, token: t });
      toast.success(`欢迎回来，${user.uid}`);
      navigate('/library');
    } catch {
      toast.error('Token 无效');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* 渐变星空背景 */}
      <SkyBackground />

      {/* 登录面板 */}
      <div className="glass-panel w-full max-w-md mx-4 p-8 md:p-10 rounded-[24px] relative z-10 transition-transform duration-300 hover:-translate-y-1">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-gray-900 dark:text-white mb-3 tracking-tight">欢迎回来</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            请粘贴您的 API Token 登录 Glynk。
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
              placeholder="glk_..."
              rows={3}
              required
              className="w-full px-4 py-3 bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-mono text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 resize-none transition-all duration-300 backdrop-blur-sm shadow-inner"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !tokenInput.trim()}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-lg shadow-blue-500/30 flex justify-center items-center h-[48px]"
          >
            {loading ? (
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              '登录体验'
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          没有账号？{' '}
          <Link to="/register" className="text-blue-600 dark:text-blue-400 font-medium hover:underline transition-colors">
            立即注册
          </Link>
        </p>
      </div>
    </div>
  );
}
