import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { register } from '../api/auth';
import { useAuthStore } from '../store/auth';

export default function RegisterPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [step, setStep] = useState<1 | 2>(1);
  const [uid, setUid] = useState('');
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resultToken, setResultToken] = useState('');
  const [resultUid, setResultUid] = useState('');
  const [saved, setSaved] = useState(false);

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await register({
        uid: uid.trim() || undefined,
        email: email.trim() || undefined,
      });
      setAuth({ uid: res.uid, token: res.token });
      setResultToken(res.token);
      setResultUid(res.uid);
      setStep(2);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || '注册失败');
    } finally {
      setSubmitting(false);
    }
  }

  function copyToken() {
    navigator.clipboard.writeText(resultToken);
    toast.success('已复制');
  }

  if (step === 2) {
    return (
      <div className="max-w-md mx-auto px-6 py-20">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">注册成功</h1>
        <p className="text-sm text-gray-500 mb-1">
          uid：<span className="font-mono font-medium text-gray-700">{resultUid}</span>
        </p>
        <p className="text-sm text-gray-500 mb-8">
          请保存下方 Token。它是你的登录凭证和 API 密钥，不要泄露给他人。
        </p>

        <div className="relative mb-4">
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl font-mono text-sm text-gray-700 break-all select-all">
            {resultToken}
          </div>
          <button onClick={copyToken}
            className="absolute top-2 right-2 px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 cursor-pointer">
            复制
          </button>
        </div>

        <p className="text-xs text-gray-400 mb-6">
          用途：浏览器登录时粘贴 · Agent 调用时作为 Authorization: Bearer Token
        </p>

        <label className="flex items-center gap-2 mb-8 cursor-pointer">
          <input type="checkbox" checked={saved} onChange={(e) => setSaved(e.target.checked)} className="rounded" />
          <span className="text-sm text-gray-700">我已保存好 Token</span>
        </label>

        <button onClick={() => navigate('/library')} disabled={!saved}
          className="w-full py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 cursor-pointer">
          进入 Glynk
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-6 py-20">
      <h1 className="text-2xl font-semibold text-gray-900 mb-2">创建账号</h1>
      <p className="text-sm text-gray-500 mb-8">
        直接注册即可。uid 和邮箱都可以之后再设置。
      </p>

      <form onSubmit={handleRegister} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            uid <span className="text-gray-400 font-normal">(选填，不填自动生成)</span>
          </label>
          <input
            type="text"
            value={uid}
            onChange={(e) => setUid(e.target.value.toLowerCase())}
            placeholder="如 sunlit"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
          />
          <p className="mt-1 text-xs text-gray-400">小写字母、数字、连字符，3-20 字符</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            邮箱 <span className="text-gray-400 font-normal">(选填，用于找回 Token)</span>
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
          />
        </div>

        <button type="submit" disabled={submitting}
          className="w-full py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 cursor-pointer">
          {submitting ? '创建中...' : '注册'}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        已有 Token？<Link to="/login" className="text-gray-900 font-medium hover:underline">登录</Link>
      </p>
    </div>
  );
}
