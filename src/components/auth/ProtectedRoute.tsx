import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, type UserRole } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { isAuthenticated, isLoading, currentRole } = useAuth();
  const { isDark } = useTheme();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className={`min-h-screen flex flex-col items-center justify-center ${
        isDark ? 'bg-slate-950 text-slate-100' : 'bg-[#f0f5ff] text-slate-900'
      }`}>
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 p-0.5 shadow-lg animate-pulse">
            <div className={`w-full h-full rounded-[14px] flex items-center justify-center ${
              isDark ? 'bg-slate-950' : 'bg-white'
            }`}>
              <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm font-semibold tracking-tight">Verifying Institutional Session...</p>
            <p className="text-xs text-slate-500 mt-0.5">CircularFlow AI Governance OS</p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(currentRole)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};
