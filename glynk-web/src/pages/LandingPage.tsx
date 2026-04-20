import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useT } from '../i18n';

// 指向同域下的静态资源（glynk-web/public/install.sh，由 build 钩子从
// ../skills/install-remote.sh 同步生成），避免 GitHub 从国内访问不稳。
const INSTALL_SH_URL = '/install.sh';

const INSTALL_COMMANDS = {
  claude: `curl -sL ${INSTALL_SH_URL} | bash`,
  other: `curl -sL ${INSTALL_SH_URL} | bash -s -- --target <your-skills-dir>`,
};

export default function LandingPage() {
  const t = useT();
  const [copied, setCopied] = useState<string | null>(null);
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on outside click
  useEffect(() => {
    if (!showMenu) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showMenu]);

  const copyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label);
      setShowMenu(false);
      setTimeout(() => setCopied(null), 2000);
    });
  };

  const steps = [
    { emoji: '1', title: t('landing.step1.title'), desc: t('landing.step1.desc') },
    { emoji: '2', title: t('landing.step2.title'), desc: t('landing.step2.desc') },
    { emoji: '3', title: t('landing.step3.title'), desc: t('landing.step3.desc') },
    { emoji: '4', title: t('landing.step4.title'), desc: t('landing.step4.desc') },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* 内容需放置于背景上层的相对容器 */}
      <div className="relative z-10 w-full h-full flex flex-col items-center">
        {/* Hero */}
        <section className="px-6 py-32 md:py-48 max-w-3xl mx-auto text-center w-full">
          <div className="glass-panel rounded-3xl p-10 md:p-14 transition-all duration-500 hover:shadow-2xl hover:-translate-y-2 inline-block shadow-lg mx-auto w-full">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-gray-900 dark:text-white leading-tight">
              {t('landing.hero.title')}
            </h1>
            <p className="mt-8 text-lg md:text-xl text-gray-700 dark:text-gray-300 max-w-xl mx-auto leading-relaxed">
              {t('landing.hero.desc')}<br/><span className="inline-block mt-2 font-medium text-blue-600 dark:text-blue-400">{t('landing.hero.highlight')}</span>
            </p>
            <div className="mt-12 flex items-center justify-center gap-4 flex-wrap">
              <Link
                to="/register"
                className="px-8 py-3.5 bg-blue-600 shadow-blue-500/30 shadow-lg text-white rounded-xl text-base font-semibold hover:bg-blue-700 hover:-translate-y-0.5 transition-all w-full sm:w-auto text-center"
              >
                {t('landing.cta.start')}
              </Link>

              {/* Install Skill dropdown */}
              <div className="relative w-full sm:w-auto" ref={menuRef}>
                <button
                  onClick={() => setShowMenu(!showMenu)}
                  className="px-8 py-3.5 bg-white/50 dark:bg-gray-800/50 backdrop-blur border border-white/40 dark:border-gray-700/50 rounded-xl text-base font-semibold text-gray-800 dark:text-gray-200 hover:bg-white/80 dark:hover:bg-gray-700/80 hover:-translate-y-0.5 transition-all w-full sm:w-auto text-center cursor-pointer flex items-center justify-center gap-2"
                >
                  {copied ? t('landing.cta.copied') : t('landing.cta.skill')}
                  {!copied && (
                    <svg className={`w-4 h-4 transition-transform ${showMenu ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </button>

                {showMenu && (
                  <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 sm:left-0 sm:translate-x-0 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl overflow-hidden z-50">
                    <button
                      onClick={() => copyText(INSTALL_COMMANDS.claude, 'claude')}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer flex items-start gap-3"
                    >
                      <span className="text-lg mt-0.5">{'>'}_</span>
                      <div>
                        <div className="text-sm font-semibold text-gray-900 dark:text-white">{t('landing.skill.claude_code')}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{t('landing.skill.claude_code_desc')}</div>
                      </div>
                    </button>
                    <div className="border-t border-gray-100 dark:border-gray-700" />
                    <button
                      onClick={() => copyText(INSTALL_COMMANDS.other, 'other')}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer flex items-start gap-3"
                    >
                      <span className="text-lg mt-0.5">🤖</span>
                      <div>
                        <div className="text-sm font-semibold text-gray-900 dark:text-white">{t('landing.skill.other_agent')}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{t('landing.skill.other_agent_desc')}</div>
                      </div>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="px-6 py-24 w-full">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-center text-sm font-bold tracking-widest uppercase text-gray-500 dark:text-gray-400 mb-16 drop-shadow-sm">
              {t('landing.how')}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              {steps.map((step) => (
                <div key={step.title} className="glass-panel rounded-2xl p-8 text-center md:text-left transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-100/80 dark:bg-blue-900/50 text-xl shadow-inner mb-6">
                    {step.emoji}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    {step.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed font-medium">
                    {step.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* For Agents */}
        <section className="px-6 py-24 w-full">
          <div className="max-w-3xl mx-auto glass-panel rounded-3xl p-10 md:p-12 hover:-translate-y-1 transition-transform duration-300">
            <h2 className="text-center text-sm font-bold tracking-widest uppercase text-gray-500 dark:text-gray-400 mb-10 drop-shadow-sm">
              {t('landing.dev')}
            </h2>
            <div className="bg-gray-900/90 dark:bg-black/90 backdrop-blur border border-gray-700/50 rounded-2xl p-6 overflow-x-auto shadow-2xl">
              <pre className="text-sm text-gray-300 font-mono leading-relaxed whitespace-pre">
  {`# Claude Code
${INSTALL_COMMANDS.claude}

# 其他 Agent（自行指定目标目录）
${INSTALL_COMMANDS.other}`}
              </pre>
            </div>
            <p className="mt-8 text-center text-sm font-medium text-gray-600 dark:text-gray-400">
              {t('landing.dev.desc')}
            </p>
          </div>
        </section>

        {/* Footer */}
        <footer className="w-full border-t border-white/20 dark:border-gray-800/50 px-6 py-12 mt-10">
          <p className="text-center text-sm font-medium text-gray-500 dark:text-gray-400 drop-shadow-sm">
            {t('landing.footer')}
          </p>
          <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-3">
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" className="hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
              京ICP备2024066391号-3
            </a>
          </p>
        </footer>
      </div>
    </div>
  );
}
