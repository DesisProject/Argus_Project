import { Navigate, Outlet } from 'react-router';
import { getToken } from './services/auth';

export const ProtectedRoute = () => {
  const token = getToken();
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};
