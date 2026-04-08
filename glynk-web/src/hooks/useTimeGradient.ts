// 时间渐变背景 Hook
import { useState, useEffect } from 'react';

export type TimeOfDay = 'earlyMorning' | 'morning' | 'lateMorning' | 'noon' | 'afternoon' | 'evening' | 'night' | 'lateNight';

export interface GradientConfig {
  colors: string[];
  positions: number[];
}
// 时间渐变配置（8个时间段）
const TIME_GRADIENTS: Record<TimeOfDay, GradientConfig> = {
  earlyMorning: {
    colors: ['#E4E4EA', '#D7DAE7', '#C4D1DE'],
    positions: [0, 50, 100],
  },
  morning: {
    colors: ['#C9E1F3', '#CBDEF4', '#EEDCD8'],
    positions: [0, 48, 100],
  },
  lateMorning: {
    colors: ['#D2E5F4', '#C0DCF2', '#9DC6E0'],
    positions: [0, 50, 100],
  },
  noon: {
    colors: ['#66A8F3', '#8BC0FD', '#C0DBF0'],
    positions: [0, 50, 100],
  },
  afternoon: {
    colors: ['#B5D3DE', '#CBD5D6', '#E8DDE0'],
    positions: [0, 39, 100],
  },
  evening: {
    colors: ['#B4C8FF', '#AEC3FF', '#F3D6E2'],
    positions: [0, 41, 100],
  },
  night: {
    colors: ['#24374C', '#62768D', '#CBBEA5'],
    positions: [0, 50, 100],
  },
  lateNight: {
    colors: ['#010630', '#283D51', '#283D51'],
    positions: [0, 41, 100],
  },
};

/**
 * 根据小时获取时间段类型
 */
function getTimeOfDay(): TimeOfDay {
  const hour = new Date().getHours();

  if (hour >= 5 && hour < 7) return 'earlyMorning';
  if (hour >= 7 && hour < 9) return 'morning';
  if (hour >= 9 && hour < 12) return 'lateMorning';
  if (hour >= 12 && hour < 16) return 'noon';
  if (hour >= 16 && hour < 18) return 'afternoon';
  if (hour >= 18 && hour < 21) return 'evening';
  if (hour >= 21 && hour < 22) return 'night';
  return 'lateNight'; // 22:00-5:00
}

/**
 * 生成CSS渐变字符串
 */
function generateGradientCSS(config: GradientConfig): string {
  const stops = config.colors
    .map((color, index) => `${color} ${config.positions[index]}%`)
    .join(', ');

  return `linear-gradient(180deg, ${stops})`;
}

/**
 * 检查是否为夜晚时间（显示星空）
 */
export function isNightTime(): boolean {
  const hour = new Date().getHours();
  return hour >= 21 || hour < 5;
}

/**
 * 时间渐变Hook
 * @returns CSS渐变字符串 + 是否夜晚
 */
export function useTimeGradient() {
  const [gradient, setGradient] = useState('');
  const [isNight, setIsNight] = useState(false);

  useEffect(() => {
    const updateGradient = () => {
      const timeType = getTimeOfDay();
      const config = TIME_GRADIENTS[timeType];
      const gradientCSS = generateGradientCSS(config);

      setGradient(gradientCSS);
      setIsNight(isNightTime());
    };

    // 初始化
    updateGradient();

    // 每分钟检查一次
    const interval = setInterval(updateGradient, 60000);

    return () => clearInterval(interval);
  }, []);

  return { gradient, isNight };
}
