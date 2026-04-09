import { Link } from 'react-router-dom';
import { useT } from '../i18n';

export default function LandingPage() {
  const t = useT();

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
              <Link
                to="/docs"
                className="px-8 py-3.5 bg-white/50 dark:bg-gray-800/50 backdrop-blur border border-white/40 dark:border-gray-700/50 rounded-xl text-base font-semibold text-gray-800 dark:text-gray-200 hover:bg-white/80 dark:hover:bg-gray-700/80 hover:-translate-y-0.5 transition-all w-full sm:w-auto text-center"
              >
                {t('landing.cta.docs')}
              </Link>
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

        {/* Developer */}
        <section className="px-6 py-24 w-full">
          <div className="max-w-3xl mx-auto glass-panel rounded-3xl p-10 md:p-12 hover:-translate-y-1 transition-transform duration-300">
            <h2 className="text-center text-sm font-bold tracking-widest uppercase text-gray-500 dark:text-gray-400 mb-10 drop-shadow-sm">
              {t('landing.dev')}
            </h2>
            <div className="bg-gray-900/90 dark:bg-black/90 backdrop-blur border border-gray-700/50 rounded-2xl p-6 overflow-x-auto shadow-2xl">
              <pre className="text-sm text-gray-300 font-mono leading-relaxed whitespace-pre">
  {`curl -X POST https://glynk.wiki/api/search/semantic \\
    -H "Authorization: Bearer <your-token>" \\
    -H "Content-Type: application/json" \\
    -d '{"text": "如何理解注意力机制", "top_k": 5}'`}
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
