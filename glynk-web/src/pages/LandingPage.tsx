import { Link } from 'react-router-dom';

const steps = [
  { emoji: '1', title: '导入', desc: '从 URL、文件或 API 导入内容，自动解析结构' },
  { emoji: '2', title: '标注', desc: '高亮、笔记、标签 —— 你的理解成为元数据' },
  { emoji: '3', title: '发现', desc: '语义搜索跨越所有内容，找到隐藏的关联' },
  { emoji: '4', title: '飞轮', desc: '越多人标注，内容越丰富，发现越精准' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="px-6 py-32 md:py-48 max-w-3xl mx-auto text-center">
        <h1 className="text-4xl md:text-6xl font-semibold tracking-tight text-gray-900 dark:text-gray-100 leading-tight">
          好内容不该被埋没
        </h1>
        <p className="mt-6 text-lg md:text-xl text-gray-500 dark:text-gray-400 max-w-xl mx-auto leading-relaxed">
          Glynk 是 Agent 时代的开放内容基础设施。导入、标注、语义搜索 —— 让知识自由流动。
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            to="/register"
            className="px-6 py-2.5 bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            开始使用
          </Link>
          <Link
            to="/docs"
            className="px-6 py-2.5 border border-gray-300 dark:border-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
          >
            查看 API 文档
          </Link>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-gray-200 dark:border-gray-800 px-6 py-24">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-center text-sm font-medium tracking-widest uppercase text-gray-400 dark:text-gray-500 mb-16">
            How it works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 md:gap-8">
            {steps.map((step) => (
              <div key={step.title} className="text-center md:text-left">
                <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 text-sm font-medium text-gray-600 dark:text-gray-400 mb-4">
                  {step.emoji}
                </div>
                <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Developer */}
      <section className="border-t border-gray-200 dark:border-gray-800 px-6 py-24">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-center text-sm font-medium tracking-widest uppercase text-gray-400 dark:text-gray-500 mb-10">
            For Developers
          </h2>
          <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 overflow-x-auto">
            <pre className="text-sm text-gray-700 dark:text-gray-300 font-mono leading-relaxed whitespace-pre">
{`curl -X POST https://glynk.wiki/api/search/semantic \\
  -H "Authorization: Bearer <your-token>" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "如何理解注意力机制", "top_k": 5}'`}
            </pre>
          </div>
          <p className="mt-6 text-center text-sm text-gray-400 dark:text-gray-500">
            RESTful API, 语义搜索, 批量操作 —— 一切为自动化而生
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 px-6 py-12 text-center">
        <p className="text-sm text-gray-400 dark:text-gray-500">
          glynk.wiki &middot; 开放内容基础设施
        </p>
      </footer>
    </div>
  );
}
