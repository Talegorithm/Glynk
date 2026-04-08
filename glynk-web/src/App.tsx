import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';
import LandingPage from './pages/LandingPage';
import ExplorePage from './pages/ExplorePage';
import RegisterPage from './pages/RegisterPage';
import LoginPage from './pages/LoginPage';
import LibraryPage from './pages/LibraryPage';
import ReaderPage from './pages/ReaderPage';
import NotesPage from './pages/NotesPage';
import { TimeGradientBg } from './components/background/TimeGradientBg';
import { useThemeStore } from './store/theme';

export default function App() {
  // Initialize theme tracking to apply classes
  useThemeStore();

  return (
    <TimeGradientBg showStars={true}>
      <Toaster position="top-center" richColors />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/explore" element={<ExplorePage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route element={<PrivateRoute />}>
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/notes" element={<NotesPage />} />
          </Route>
        </Route>

        <Route element={<PrivateRoute />}>
          <Route path="/read/:contentId" element={<ReaderPage />} />
          <Route path="/read/:contentId/:fileIdx" element={<ReaderPage />} />
        </Route>
      </Routes>
    </TimeGradientBg>
  );
}
