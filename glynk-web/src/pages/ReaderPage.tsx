/**
 * 阅读器页面 - 从 Brainow 迁移，适配 Glynk
 */

import { useEffect, useRef, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useReaderStore } from '../store/reader';
import { ReaderLayout } from '../components/reader/ReaderLayout';
import { ReaderToolbar } from '../components/reader/ReaderToolbar';
import { ReaderTOC } from '../components/reader/ReaderTOC';
import { ReaderOutline } from '../components/reader/ReaderOutline';
import { ReaderContent } from '../components/reader/ReaderContent';
import { LoginModal } from '../components/LoginModal';
import { getReadingProgress, startReadingSession, endReadingSession } from '../api/content';
import { useAuthStore } from '../store/auth';
import { useT } from '../i18n';

export default function ReaderPage() {
  const t = useT();
  const { contentId } = useParams<{ contentId: string }>();
  const [searchParams] = useSearchParams();
  const locParam = searchParams.get('loc');

  const init = useReaderStore((state) => state.init);
  const jumpToLocation = useReaderStore((state) => state.jumpToLocation);
  const reset = useReaderStore((state) => state.reset);
  const isLoading = useReaderStore((state) => state.isLoading);

  const token = useAuthStore((state) => state.token);
  const sessionIdRef = useRef<string | null>(null);
  const sessionStartRef = useRef<number>(0);
  const initedRef = useRef(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const loginDismissedRef = useRef(false);

  // 初始化阅读器
  useEffect(() => {
    if (!contentId || initedRef.current) return;
    initedRef.current = true;

    const doInit = async () => {
      await init(contentId);

      // 如果 URL 有 loc 参数，跳转到指定位置
      if (locParam) {
        await jumpToLocation(locParam);
      } else if (token) {
        // 否则检查阅读进度
        const progress = await getReadingProgress(contentId);
        if (progress?.span_id) {
          await jumpToLocation(progress.span_id);
        }
      }
    };

    doInit();
  }, [contentId, locParam, init, jumpToLocation, token]);

  // 未登录时弹出登录提示
  useEffect(() => {
    if (!token && !loginDismissedRef.current) {
      setShowLoginModal(true);
    }
  }, [token]);

  // 阅读会话追踪
  useEffect(() => {
    if (!contentId || !token) return;

    sessionStartRef.current = Date.now();

    // 确定来源
    const source = locParam ? 'direct_link' : 'library';

    startReadingSession(contentId, source)
      .then(id => { sessionIdRef.current = id; })
      .catch(() => {});

    // 可见性变化 / 离开时结束会话
    const endSession = () => {
      if (!sessionIdRef.current) return;
      const duration = Math.round((Date.now() - sessionStartRef.current) / 1000);

      // 使用 sendBeacon 确保离开时也能发送
      const url = `/api/reading-sessions/${sessionIdRef.current}/end`;
      const body = JSON.stringify({ duration_seconds: duration });

      if (navigator.sendBeacon) {
        navigator.sendBeacon(url, new Blob([body], { type: 'application/json' }));
      } else {
        endReadingSession(sessionIdRef.current, duration).catch(() => {});
      }
    };

    const handleVisibilityChange = () => {
      if (document.hidden) endSession();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', endSession);

    return () => {
      endSession();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', endSession);
    };
  }, [contentId, token, locParam]);

  // 清理
  useEffect(() => {
    return () => {
      initedRef.current = false;
      reset();
    };
  }, [reset]);

  // 初次加载或无内容时，ReaderContent内部会有处理
  // 如果要展示一个整页 loading，只在初次还没有 contentMeta 时展示
  const contentMeta = useReaderStore((state) => state.contentMeta);
  if (isLoading && !contentMeta) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-57px)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-3" />
          <p className="text-sm text-gray-400 dark:text-gray-500">{t('reader.loading')}</p>
        </div>
      </div>
    );
  }

  const handleLoginClose = () => {
    setShowLoginModal(false);
    loginDismissedRef.current = true;
  };

  const requestLogin = () => {
    setShowLoginModal(true);
  };

  return (
    <>
      <ReaderLayout
        toolbar={<ReaderToolbar />}
        toc={<ReaderTOC />}
        outline={<ReaderOutline />}
        content={<ReaderContent requestLogin={requestLogin} />}
      />
      {showLoginModal && !token && (
        <LoginModal
          onClose={handleLoginClose}
          hint={t('reader.login_hint')}
        />
      )}
    </>
  );
}
