import { Navigate, Outlet } from 'react-router';
import { getToken } from '../services/auth';

export const ProtectedRoute = () => {
  const token = getToken();
  
  // If they don't have a ticket, bounce them to the login page
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // If they do have a ticket, let them through to the child routes (Dashboard)
  return <Outlet />;
};
