import { useAuthStore } from '../store/auth';

const zh: Record<string, string> = {
  // Layout
  'nav.library': '书架',
  'nav.notes': '笔记',
  'nav.logout': '退出',
  'nav.login': '登录',
  'nav.register': '注册',

  // Landing
  'landing.hero.title': '好内容不该被埋没',
  'landing.hero.desc': 'Glynk 是 Agent 时代的开放内容基础设施。',
  'landing.hero.highlight': '导入、标注、语义搜索 —— 让知识自由流动。',
  'landing.cta.start': '开始使用',
  'landing.cta.skill': '安装 SKILL',
  'landing.cta.copied': '已复制！',
  'landing.skill.claude_code': 'Claude Code',
  'landing.skill.claude_code_desc': '一键装到 ~/.claude/skills/',
  'landing.skill.other_agent': '其他 Agent',
  'landing.skill.other_agent_desc': '自行指定目标目录 --target',
  'landing.how': 'How It Works',
  'landing.step1.title': '导入',
  'landing.step1.desc': '从 URL、文件或 API 导入内容，自动解析结构',
  'landing.step2.title': '标注',
  'landing.step2.desc': '高亮、笔记、标签 —— 你的理解成为元数据',
  'landing.step3.title': '发现',
  'landing.step3.desc': '语义搜索跨越所有内容，找到隐藏的关联',
  'landing.step4.title': '飞轮',
  'landing.step4.desc': '越多人标注，内容越丰富，发现越精准',
  'landing.dev': 'For Agents',
  'landing.dev.desc': '兼容 Agent Skills 标准 —— Claude Code / Cursor / Copilot / Codex 一键安装',
  'landing.footer': 'glynk.wiki · 开放内容基础设施',

  // Login
  'login.title': '欢迎回来',
  'login.desc': '使用邮箱密码登录，也可使用 API Token。',
  'login.password_tab': '邮箱登录',
  'login.token_tab': 'Token 登录',
  'login.email': '邮箱',
  'login.password': '密码',
  'login.password_placeholder': '输入密码',
  'login.token_label': 'API Token',
  'login.token_placeholder': 'glk_...',
  'login.token_hint': 'Agent 和 API 使用的 Bearer token 也可以用于浏览器登录。',
  'login.submit': '登录',
  'login.success': '欢迎回来，{uid}',
  'login.error': '邮箱或密码错误',
  'login.token_error': 'Token 无效',
  'login.no_account': '没有账号？',
  'login.register': '立即注册',

  // Register
  'register.title': '创建账号',
  'register.desc': '填写邮箱，验证后设置密码。',
  'register.display_name': '昵称',
  'register.display_name_placeholder': '如 sunlit',
  'register.email': '邮箱',
  'register.request_code': '发送验证码',
  'register.sending_code': '发送中',
  'register.code': '验证码',
  'register.code_sent': '验证码已发送',
  'register.code_hint': '验证码已发送，请查看邮箱和垃圾箱。',
  'register.code_error': '验证码发送失败',
  'register.password': '密码',
  'register.password_placeholder': '至少 8 个字符',
  'register.confirm_password': '确认密码',
  'register.confirm_password_placeholder': '再次输入密码',
  'register.password_mismatch': '两次输入的密码不一致',
  'register.submitting': '创建中...',
  'register.submit': '注册',
  'register.has_account': '已有账号？',
  'register.login': '登录',
  'register.success.title': '注册成功',
  'register.error': '注册失败',

  // Library
  'library.title': '书架',
  'library.search_placeholder': '语义搜索...',
  'library.loading': '加载中...',
  'library.no_results': '无结果',
  'library.empty': '还没有内容',
  'library.load_error': '加载失败',
  'library.search_error': '搜索失败',
  'library.count': '{count} 条',
  'library.count_partial': '最新 {shown} / {total} 条',

  // Notes
  'notes.title': '笔记',
  'notes.tab.all': '全部',
  'notes.tab.highlight': '高亮',
  'notes.tab.hook': 'Hook',
  'notes.tab.note': '笔记',
  'notes.search_placeholder': '搜索笔记...',
  'notes.loading': '加载中...',
  'notes.empty': '暂无标注',
  'notes.load_error': '加载失败',
  'notes.search_error': '搜索失败',
  'notes.results': '{count} 条结果',
  'notes.range': '{from}-{to} / {total} 条',
  'notes.count': '{count} 条',
  'notes.prev': '上一页',
  'notes.next': '下一页',
  'notes.tab.idea': '想法',
  'notes.drop_placeholder': '随手记下一个想法或灵感... (Cmd+Enter 提交)',
  'notes.drop_submit': '放下',
  'notes.drop_success': '已成功放下',
  'notes.drop_error': '提交失败，请重试',

  // Thread
  'thread.title': '讨论',
  'thread.empty': '暂无讨论。来说点什么吧！',
  'thread.replying_to': '回复层内...',
  'thread.placeholder': '加入讨论...',
  'thread.submit': '回复',
  'thread.cancel': '取消',

  // Reader
  'reader.loading': '加载中...',
  'reader.empty': '暂无内容',
  'reader.back': '返回',
  'reader.toc': '目录',
  'reader.outline': '大纲',
  'reader.translate': '翻译',
  'reader.translating': '翻译中...',
  'reader.show_original': '显示原文',
  'reader.same_language': '内容已是您的偏好语言',
  'reader.settings': '设置',
  'reader.toc.loading': '加载目录中...',
  'reader.toc.empty': '暂无目录',
  'reader.outline.loading': '加载大纲中...',
  'reader.outline.empty': '暂无大纲',
  'reader.translation_pending': '正在准备翻译...',
  'reader.translation_failed': '翻译失败，显示原文',
  'reader.login_hint': '登录后可保存阅读进度、划线和笔记',

  // Reader Settings
  'settings.appearance': '外观',
  'settings.theme.light': '白昼',
  'settings.theme.dark': '星夜',
  'settings.theme.auto': '自动',
  'settings.font': '字体',
  'settings.font.sans': '无衬线',
  'settings.font.serif': '衬线',

  // Annotation
  'annotation.edit': '编辑笔记',
  'annotation.add': '添加笔记',
  'annotation.selected_text': '选中的文本',
  'annotation.note_placeholder': '输入你的想法...',
  'annotation.note_hint': '提示: Ctrl+Enter 保存，Esc 取消',
  'annotation.color': '高亮颜色',
  'annotation.cancel': '取消',
  'annotation.save': '保存',
  'annotation.delete': '删除',

  // Selection
  'selection.highlight': '高亮',
  'selection.note': '笔记',
  'selection.copy': '复制',
  'selection.close': '关闭',
  'selection.color': '选择颜色',
  'selection.reply': '回复',

  // Citation
  'citation.preview': '引注预览',
  'citation.not_loaded': '引注内容在后续章节，请继续阅读查看完整上下文',

  // Explore
  'explore.placeholder': '在集体意识中搜索...',
  'explore.submit': '搜索',
  'explore.loading': '搜索中...',
  'explore.no_results': '没有找到相关结果',

  // Type badges
  'type.highlight': '高亮',
  'type.hook': 'Hook',
  'type.note': '笔记',
  'type.reaction': '反应',
  'type.idea': '想法',
};

const en: Record<string, string> = {
  // Layout
  'nav.library': 'Library',
  'nav.notes': 'Notes',
  'nav.logout': 'Logout',
  'nav.login': 'Login',
  'nav.register': 'Register',

  // Landing
  'landing.hero.title': 'Great Content Deserves to Be Found',
  'landing.hero.desc': 'Glynk is open content infrastructure for the Agent era.',
  'landing.hero.highlight': 'Ingest, annotate, semantic search — let knowledge flow freely.',
  'landing.cta.start': 'Get Started',
  'landing.cta.skill': 'Install SKILL',
  'landing.cta.copied': 'Copied!',
  'landing.skill.claude_code': 'Claude Code',
  'landing.skill.claude_code_desc': 'One-liner into ~/.claude/skills/',
  'landing.skill.other_agent': 'Other agent',
  'landing.skill.other_agent_desc': 'Specify target dir with --target',
  'landing.how': 'How It Works',
  'landing.step1.title': 'Ingest',
  'landing.step1.desc': 'Import from URL, file, or API — auto-parse structure',
  'landing.step2.title': 'Annotate',
  'landing.step2.desc': 'Highlights, notes, tags — your understanding becomes metadata',
  'landing.step3.title': 'Discover',
  'landing.step3.desc': 'Semantic search across all content, find hidden connections',
  'landing.step4.title': 'Flywheel',
  'landing.step4.desc': 'More annotations, richer content, sharper discovery',
  'landing.dev': 'For Agents',
  'landing.dev.desc': 'Compatible with the Agent Skills standard — one-click install for Claude Code / Cursor / Copilot / Codex',
  'landing.footer': 'glynk.wiki · Open Content Infrastructure',

  // Login
  'login.title': 'Welcome Back',
  'login.desc': 'Log in with email and password, or use an API token.',
  'login.password_tab': 'Email',
  'login.token_tab': 'Token',
  'login.email': 'Email',
  'login.password': 'Password',
  'login.password_placeholder': 'Enter your password',
  'login.token_label': 'API Token',
  'login.token_placeholder': 'glk_...',
  'login.token_hint': 'The Bearer token used by agents and API clients can also log in here.',
  'login.submit': 'Log In',
  'login.success': 'Welcome back, {uid}',
  'login.error': 'Invalid email or password',
  'login.token_error': 'Invalid token',
  'login.no_account': "Don't have an account?",
  'login.register': 'Register now',

  // Register
  'register.title': 'Create Account',
  'register.desc': 'Verify your email, then set a password.',
  'register.display_name': 'Display name',
  'register.display_name_placeholder': 'e.g. sunlit',
  'register.email': 'Email',
  'register.request_code': 'Send code',
  'register.sending_code': 'Sending',
  'register.code': 'Code',
  'register.code_sent': 'Verification code sent',
  'register.code_hint': 'Code sent. Check your inbox and spam folder.',
  'register.code_error': 'Failed to send code',
  'register.password': 'Password',
  'register.password_placeholder': 'At least 8 characters',
  'register.confirm_password': 'Confirm password',
  'register.confirm_password_placeholder': 'Enter it again',
  'register.password_mismatch': 'Passwords do not match',
  'register.submitting': 'Creating...',
  'register.submit': 'Register',
  'register.has_account': 'Already have an account?',
  'register.login': 'Log in',
  'register.success.title': 'Registration Successful',
  'register.error': 'Registration failed',

  // Library
  'library.title': 'Library',
  'library.search_placeholder': 'Semantic search...',
  'library.loading': 'Loading...',
  'library.no_results': 'No results',
  'library.empty': 'No content yet',
  'library.load_error': 'Failed to load',
  'library.search_error': 'Search failed',
  'library.count': '{count} items',
  'library.count_partial': 'Latest {shown} / {total}',

  // Notes
  'notes.title': 'Notes',
  'notes.tab.all': 'All',
  'notes.tab.highlight': 'Highlights',
  'notes.tab.hook': 'Hooks',
  'notes.tab.note': 'Notes',
  'notes.search_placeholder': 'Search notes...',
  'notes.loading': 'Loading...',
  'notes.empty': 'No annotations yet',
  'notes.load_error': 'Failed to load',
  'notes.search_error': 'Search failed',
  'notes.results': '{count} results',
  'notes.range': '{from}-{to} / {total}',
  'notes.count': '{count}',
  'notes.prev': 'Previous',
  'notes.next': 'Next',
  'notes.tab.idea': 'Ideas',
  'notes.drop_placeholder': 'Write down an idea or note... (Cmd+Enter to save)',
  'notes.drop_submit': 'Drop',
  'notes.drop_success': 'Idea dropped successfully',
  'notes.drop_error': 'Failed to drop idea',

  // Thread
  'thread.title': 'Discussions',
  'thread.empty': 'No discussions yet. Be the first!',
  'thread.replying_to': 'Replying to comment...',
  'thread.placeholder': 'Join the discussion...',
  'thread.submit': 'Reply',
  'thread.cancel': 'Cancel',

  // Reader
  'reader.loading': 'Loading...',
  'reader.empty': 'No content',
  'reader.back': 'Back',
  'reader.toc': 'Contents',
  'reader.outline': 'Outline',
  'reader.translate': 'Translate',
  'reader.translating': 'Translating...',
  'reader.show_original': 'Show original',
  'reader.same_language': 'Content is already in your preferred language',
  'reader.settings': 'Settings',
  'reader.toc.loading': 'Loading...',
  'reader.toc.empty': 'No table of contents',
  'reader.outline.loading': 'Loading...',
  'reader.outline.empty': 'No outline',
  'reader.translation_pending': 'Preparing translation...',
  'reader.translation_failed': 'Translation failed, showing original',
  'reader.login_hint': 'Log in to save reading progress, highlights and notes',

  // Reader Settings
  'settings.appearance': 'Appearance',
  'settings.theme.light': 'Light',
  'settings.theme.dark': 'Dark',
  'settings.theme.auto': 'Auto',
  'settings.font': 'Font',
  'settings.font.sans': 'Sans-serif',
  'settings.font.serif': 'Serif',

  // Annotation
  'annotation.edit': 'Edit note',
  'annotation.add': 'Add note',
  'annotation.selected_text': 'Selected text',
  'annotation.note_placeholder': 'Write your thoughts...',
  'annotation.note_hint': 'Tip: Ctrl+Enter to save, Esc to cancel',
  'annotation.color': 'Highlight color',
  'annotation.cancel': 'Cancel',
  'annotation.save': 'Save',
  'annotation.delete': 'Delete',

  // Selection
  'selection.highlight': 'Highlight',
  'selection.note': 'Note',
  'selection.copy': 'Copy',
  'selection.close': 'Close',
  'selection.color': 'Pick color',
  'selection.reply': 'Discuss',

  // Citation
  'citation.preview': 'Citation Preview',
  'citation.not_loaded': 'Citation content is in a later chapter — continue reading for full context',

  // Explore
  'explore.placeholder': 'Search the collective mind...',
  'explore.submit': 'Search',
  'explore.loading': 'Searching...',
  'explore.no_results': 'No results found',

  // Type badges
  'type.highlight': 'Highlight',
  'type.hook': 'Hook',
  'type.note': 'Note',
  'type.reaction': 'Reaction',
  'type.idea': 'Idea',
};

const translations: Record<string, Record<string, string>> = { zh, en };

/**
 * Get translation function for current language.
 * Usage: const t = useT(); t('key') or t('key', { count: 5 })
 */
export function useT() {
  const lang = useAuthStore((s) => s.preferredLang) || 'zh';
  const dict = translations[lang] || translations.zh;

  return (key: string, params?: Record<string, string | number>): string => {
    let text = dict[key] ?? translations.zh[key] ?? (params?.defaultValue ? String(params.defaultValue) : key);
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        if (k !== 'defaultValue') {
          text = text.replace(`{${k}}`, String(v));
        }
      }
    }
    return text;
  };
}
