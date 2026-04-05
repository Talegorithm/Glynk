import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { sendVerifyCode, register } from '../api/auth';
import { useAuthStore } from '../store/auth';

export default function RegisterPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  // Step 1 state
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [uid, setUid] = useState('');
  const [name, setName] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [sending, setSending] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Step 2 state
  const [step, setStep] = useState<1 | 2>(1);
  const [token, setToken] = useState('');
  const [saved, setSaved] = useState(false);

  const uidPattern = /^[a-z0-9-]{3,20}$/;

  async function handleSendCode() {
    if (!email.trim()) return;
    setSending(true);
    try {
      await sendVerifyCode(email.trim());
      setCodeSent(true);
      toast.success('验证码已发送');
    } catch {
      toast.error('发送验证码失败');
    } finally {
      setSending(false);
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (!uidPattern.test(uid)) {
      toast.error('uid 格式：小写字母、数字、连字符，3-20 字符');
      return;
    }
    setSubmitting(true);
    try {
      const res = await register({
        uid: uid.trim(),
        email: email.trim(),
        code: code.trim(),
        name: name.trim() || undefined,
      });
      setAuth({ uid: res.uid, token: res.token, name: res.name, email: res.email });
      setToken(res.token);
      setStep(2);
    } catch {
      toast.error('注册失败，请检查验证码');
    } finally {
      setSubmitting(false);
    }
  }

  function copyToken() {
    navigator.clipboard.writeText(token);
    toast.success('已复制');
  }

  if (step === 2) {
    return (
      <div className="max-w-md mx-auto px-6 py-20">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">注册成功</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
          请保存你的 Token，它是你唯一的登录凭证。
        </p>

        <div className="relative mb-6">
          <div className="p-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl font-mono text-sm text-gray-700 dark:text-gray-300 break-all select-all">
            {token}
          </div>
          <button
            onClick={copyToken}
            className="absolute top-2 right-2 px-3 py-1 text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 cursor-pointer"
          >
            复制
          </button>
        </div>

        <label className="flex items-center gap-2 mb-8 cursor-pointer">
          <input
            type="checkbox"
            checked={saved}
            onChange={(e) => setSaved(e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">我已保存好 token</span>
        </label>

        <button
          onClick={() => navigate('/library')}
          disabled={!saved}
          className="w-full py-2.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 cursor-pointer"
        >
          进入 Glynk
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-6 py-20">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-8">注册</h1>

      <form onSubmit={handleRegister} className="space-y-5">
        {/* Email */}
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

        {/* Code */}
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

        {/* UID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            用户 ID
          </label>
          <input
            type="text"
            value={uid}
            onChange={(e) => setUid(e.target.value.toLowerCase())}
            placeholder="小写字母、数字、连字符，3-20 字符"
            required
            pattern="[a-z0-9-]{3,20}"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600"
          />
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            昵称 <span className="text-gray-400 dark:text-gray-500 font-normal">(可选)</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="显示名称"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600"
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !codeSent}
          className="w-full py-2.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 cursor-pointer"
        >
          {submitting ? '注册中...' : '注册'}
        </button>
      </form>
    </div>
  );
}
