import { Link } from 'react-router-dom';

const steps = [
  { emoji: '1', title: '导入', desc: '从 URL、文件或 API 导入内容，自动解析结构' },
  { emoji: '2', title: '标注', desc: '高亮、笔记、标签 —— 你的理解成为元数据' },
  { emoji: '3', title: '发现', desc: '语义搜索跨越所有内容，找到隐藏的关联' },
  { emoji: '4', title: '飞轮', desc: '越多人标注，内容越丰富，发现越精准' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* 内容需放置于背景上层的相对容器 */}
      <div className="relative z-10 w-full h-full flex flex-col items-center">
        {/* Hero */}
        <section className="px-6 py-32 md:py-48 max-w-3xl mx-auto text-center w-full">
          <div className="glass-panel rounded-3xl p-10 md:p-14 transition-all duration-500 hover:shadow-2xl hover:-translate-y-2 inline-block shadow-lg mx-auto w-full">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-gray-900 dark:text-white leading-tight">
              好内容不该被埋没
            </h1>
            <p className="mt-8 text-lg md:text-xl text-gray-700 dark:text-gray-300 max-w-xl mx-auto leading-relaxed">
              Glynk 是 Agent 时代的开放内容基础设施。<br/><span className="inline-block mt-2 font-medium text-blue-600 dark:text-blue-400">导入、标注、语义搜索 —— 让知识自由流动。</span>
            </p>
            <div className="mt-12 flex items-center justify-center gap-4 flex-wrap">
              <Link
                to="/register"
                className="px-8 py-3.5 bg-blue-600 shadow-blue-500/30 shadow-lg text-white rounded-xl text-base font-semibold hover:bg-blue-700 hover:-translate-y-0.5 transition-all w-full sm:w-auto text-center"
              >
                开始使用
              </Link>
              <Link
                to="/docs"
                className="px-8 py-3.5 bg-white/50 dark:bg-gray-800/50 backdrop-blur border border-white/40 dark:border-gray-700/50 rounded-xl text-base font-semibold text-gray-800 dark:text-gray-200 hover:bg-white/80 dark:hover:bg-gray-700/80 hover:-translate-y-0.5 transition-all w-full sm:w-auto text-center"
              >
                查看 API 文档
              </Link>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="px-6 py-24 w-full">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-center text-sm font-bold tracking-widest uppercase text-gray-500 dark:text-gray-400 mb-16 drop-shadow-sm">
              How It Works
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
              For Developers
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
              RESTful API, 语义搜索, 批量操作 —— 一切为自动化而生
            </p>
          </div>
        </section>

        {/* Footer */}
        <footer className="w-full border-t border-white/20 dark:border-gray-800/50 px-6 py-12 mt-10">
          <p className="text-center text-sm font-medium text-gray-500 dark:text-gray-400 drop-shadow-sm">
            glynk.wiki &middot; 开放内容基础设施
          </p>
        </footer>
      </div>
    </div>
  );
}
