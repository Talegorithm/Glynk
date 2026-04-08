/**
 * 全局颜色配置 - 统一高亮/标注颜色系统
 *
 * 颜色命名：yellow, green, blue, pink, ghost
 * 用途：阅读器高亮、笔记卡片侧边、批注标记
 */

export interface ColorConfig {
  name: string;           // 显示名称
  key: string;            // 后端存储的键值（yellow/green/blue/pink/ghost）
  highlight: string;      // 阅读器高亮背景色（rgba 或 gradient）
  border: string;         // 卡片左侧边框 Tailwind 类
}

export const HIGHLIGHT_COLORS: ColorConfig[] = [
  {
    name: '黄色',
    key: 'yellow',
    highlight: 'rgba(255, 237, 160, 0.5)',
    border: 'border-l-yellow-400',
  },
  {
    name: '绿色',
    key: 'green',
    highlight: 'rgba(187, 247, 208, 0.5)',
    border: 'border-l-green-400',
  },
  {
    name: '蓝色',
    key: 'blue',
    highlight: 'rgba(191, 219, 254, 0.5)',
    border: 'border-l-blue-400',
  },
  {
    name: '粉色',
    key: 'pink',
    highlight: 'rgba(252, 231, 243, 0.5)',
    border: 'border-l-pink-400',
  },
  {
    name: '幽灵',
    key: 'ghost',
    highlight: 'rgba(226, 232, 240, 0.5)',
    border: 'border-l-slate-400',
  },
];

// 用户可选颜色（排除系统保留颜色）
export const USER_SELECTABLE_COLORS = HIGHLIGHT_COLORS.filter(c => c.key !== 'ghost');

// 默认颜色
export const DEFAULT_COLOR = HIGHLIGHT_COLORS[0]; // 黄色

// 通过 key 查找颜色配置
export const getColorByKey = (key: string): ColorConfig | undefined => {
  return HIGHLIGHT_COLORS.find((c) => c.key === key);
};

// 通过 highlight rgba 值查找颜色配置
export const getColorByHighlight = (highlight: string): ColorConfig | undefined => {
  return HIGHLIGHT_COLORS.find((c) => c.highlight === highlight);
};
