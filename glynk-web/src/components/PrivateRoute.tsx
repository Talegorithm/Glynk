import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/auth';

export default function PrivateRoute() {
  const authenticated = useAuthStore((s) => s.isAuthenticated());

  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
