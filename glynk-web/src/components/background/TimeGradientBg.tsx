import { useEffect, useRef } from 'react';
import { useTimeGradient } from '../../hooks/useTimeGradient';
import { useThemeStore } from '../../store/theme';

interface TimeGradientBgProps {
  children?: React.ReactNode;
  className?: string;
  showStars?: boolean;
}

const STAR_CONFIG = {
  count: 100,
  minSize: 0.5,
  maxSize: 1.5,
  minOpacity: 0.1,
  maxOpacity: 0.8,
  animationSpeed: 1.2,
};

interface Star {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

export function TimeGradientBg({ children, className = '', showStars = true }: TimeGradientBgProps) {
  const { gradient, isNight } = useTimeGradient();
  const theme = useThemeStore((state) => state.theme);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!showStars || !isNight || theme !== 'sky') return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const stars: Star[] = [];
    let animationId: number;

    const setCanvasSize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      createStars();
    };

    const createStars = () => {
      stars.length = 0;
      for (let i = 0; i < STAR_CONFIG.count; i++) {
        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          size: Math.random() * (STAR_CONFIG.maxSize - STAR_CONFIG.minSize) + STAR_CONFIG.minSize,
          opacity: Math.random() * (STAR_CONFIG.maxOpacity - STAR_CONFIG.minOpacity) + STAR_CONFIG.minOpacity,
          speed: Math.random() * STAR_CONFIG.animationSpeed + 0.1,
        });
      }
    };

    const drawStars = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      stars.forEach((star) => {
        ctx.save();
        ctx.globalAlpha = star.opacity;
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        star.opacity += Math.sin(Date.now() * 0.002 * star.speed) * 0.02;
        star.opacity = Math.max(STAR_CONFIG.minOpacity, Math.min(STAR_CONFIG.maxOpacity, star.opacity));
      });
    };

    const animate = () => {
      drawStars();
      animationId = requestAnimationFrame(animate);
    };

    setCanvasSize();
    animate();

    const handleResize = () => {
      setCanvasSize();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [showStars, isNight, theme]);

  return (
    <div className={`relative min-h-screen ${className}`}>
      {theme === 'sky' && (
        <>
          <div
            className="fixed inset-0 transition-all duration-[2s] ease-in-out -z-20"
            style={{ background: gradient }}
          />
          {showStars && isNight && (
            <canvas
              ref={canvasRef}
              className="fixed inset-0 pointer-events-none -z-10"
            />
          )}
        </>
      )}
      {children && (
        <div className="relative z-0 flex flex-col min-h-screen">
          {children}
        </div>
      )}
    </div>
  );
}
