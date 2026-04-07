import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { loginByToken } from '../api/auth';
import { useAuthStore } from '../store/auth';

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
    <div className="max-w-md mx-auto px-6 py-20">
      <h1 className="text-2xl font-semibold text-gray-900 mb-2">登录</h1>
      <p className="text-sm text-gray-500 mb-8">
        粘贴你的 API Token 登录。
      </p>

      <form onSubmit={handleLogin} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Token
          </label>
          <textarea
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder="glk_..."
            rows={3}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-gray-300 resize-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !tokenInput.trim()}
          className="w-full py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 cursor-pointer"
        >
          {loading ? '验证中...' : '登录'}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-gray-500">
        没有账号？{' '}
        <Link to="/register" className="text-gray-900 font-medium hover:underline">
          注册
        </Link>
      </p>
    </div>
  );
}
