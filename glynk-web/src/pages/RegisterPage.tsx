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
      <div className="w-full h-full flex flex-col items-center justify-center p-6 flex-1 min-h-[70vh]">
        <div className="glass-panel w-full max-w-md p-8 md:p-10 rounded-[24px] relative z-10 transition-transform duration-300 hover:-translate-y-1">
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">注册成功</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
            uid：<span className="font-mono font-medium text-gray-700 dark:text-gray-300">{resultUid}</span>
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
            请保存下方 Token。它是你的登录凭证和 API 密钥，不要泄露给他人。
          </p>

          <div className="relative mb-4">
            <div className="p-4 bg-gray-50/50 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-xl font-mono text-sm text-gray-700 dark:text-gray-300 break-all select-all shadow-inner backdrop-blur-sm">
              {resultToken}
            </div>
            <button onClick={copyToken}
              className="absolute top-3 right-3 px-3 py-1.5 text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors shadow-sm cursor-pointer">
              复制
            </button>
          </div>

          <p className="text-xs text-gray-400 dark:text-gray-500 mb-6 font-medium">
            用途：浏览器登录时粘贴 · Agent 调用时可用作 Authorization
          </p>

          <label className="flex items-center gap-3 mb-8 cursor-pointer select-none">
            <input type="checkbox" checked={saved} onChange={(e) => setSaved(e.target.checked)} className="rounded border-gray-300 w-4 h-4 text-blue-600 focus:ring-blue-500" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">我已妥善保存好 Token</span>
          </label>

          <button onClick={() => navigate('/library')} disabled={!saved}
            className="glynk-button">
            进入 Glynk
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-6 flex-1 min-h-[70vh]">
      <div className="glass-panel w-full max-w-md p-8 md:p-10 rounded-[24px] relative z-10 transition-transform duration-300 hover:-translate-y-1">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-gray-900 dark:text-white mb-3 tracking-tight">创建账号</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            直接注册即可。uid 和邮箱都可以之后再设置。
          </p>
        </div>

        <form onSubmit={handleRegister} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              uid <span className="text-gray-400 dark:text-gray-500 font-normal ml-1">(选填，不填自动生成)</span>
            </label>
            <input
              type="text"
              value={uid}
              onChange={(e) => setUid(e.target.value.toLowerCase())}
              placeholder="如 sunlit"
              className="glynk-input"
            />
            <p className="mt-2 text-xs text-gray-400 dark:text-gray-500 font-medium tracking-wide">小写字母、数字、连字符，3-20 字符</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              邮箱 <span className="text-gray-400 dark:text-gray-500 font-normal ml-1">(选填，用于找回 Token)</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="glynk-input"
            />
          </div>

          <button type="submit" disabled={submitting} className="glynk-button-primary">
            {submitting ? '创建中...' : '注册'}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          已有 Token？<Link to="/login" className="text-blue-600 dark:text-blue-400 font-medium hover:underline transition-colors">登录</Link>
        </p>
      </div>
    </div>
  );
}
