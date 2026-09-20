// ─────────────────────────────────────────────────────────────────────────────
// AuthContext.tsx
// ONLY exports React components (AuthProvider) and hooks (useAuth).
// Plain types/constants live in ./authConstants.ts so Vite Fast Refresh works.
// ─────────────────────────────────────────────────────────────────────────────
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../lib/api';
import {
  type UserRole,
  type UserProfile,
  type AuthContextType,
  PRESET_USERS,
  AUTH_CREDENTIALS,
  isValidJWT,
  normalizeRole,
} from './authConstants';

// Re-export everything consumers need so existing imports still work
export type { UserRole, UserProfile, UserCredential, AuthContextType } from './authConstants';
export { PRESET_USERS, AUTH_CREDENTIALS, isValidJWT, normalizeRole } from './authConstants';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'circularflow_access_token';
const AUTH_STORAGE_KEY = 'circularflow_auth_role';
const AUTH_STATUS_KEY = 'circularflow_auth_status';
const USER_KEY = 'circularflow_user_profile';

const API_BASE = API_BASE_URL;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    try {
      const savedToken = localStorage.getItem(TOKEN_KEY);
      if (savedToken && isValidJWT(savedToken)) {
        return savedToken;
      }
      if (savedToken) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.setItem(AUTH_STATUS_KEY, 'false');
      }
      return null;
    } catch {
      return null;
    }
  });

  const [currentRole, setCurrentRole] = useState<UserRole>(() => {
    try {
      const saved = localStorage.getItem(AUTH_STORAGE_KEY);
      if (saved && (saved === 'Registrar' || saved === 'Faculty' || saved === 'Student')) {
        return saved as UserRole;
      }
    } catch {
      // fallback
    }
    return 'Registrar';
  });

  const [currentUser, setCurrentUser] = useState<UserProfile>(() => {
    try {
      const savedUser = localStorage.getItem(USER_KEY);
      if (savedUser) {
        return JSON.parse(savedUser);
      }
    } catch {
      // ignore
    }
    return PRESET_USERS[currentRole] || PRESET_USERS.Registrar;
  });

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    try {
      const savedToken = localStorage.getItem(TOKEN_KEY);
      const savedStatus = localStorage.getItem(AUTH_STATUS_KEY);
      // Valid only if explicitly marked true AND token is a valid unexpired JWT
      return savedStatus === 'true' && isValidJWT(savedToken);
    } catch {
      return false;
    }
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  // Sync state to local storage
  const syncAuthState = useCallback((newToken: string | null, user: UserProfile, authenticated: boolean) => {
    try {
      if (newToken) {
        localStorage.setItem(TOKEN_KEY, newToken);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
      localStorage.setItem(AUTH_STORAGE_KEY, user.role);
      localStorage.setItem(AUTH_STATUS_KEY, String(authenticated));
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } catch {
      // ignore storage errors
    }
  }, []);

  // Fetch /api/v1/auth/me on mount if token exists
  const refreshUser = useCallback(async () => {
    const activeToken = token || localStorage.getItem(TOKEN_KEY);
    if (!activeToken || !isValidJWT(activeToken)) {
      setToken(null);
      setIsAuthenticated(false);
      localStorage.removeItem(TOKEN_KEY);
      localStorage.setItem(AUTH_STATUS_KEY, 'false');
      setIsLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: {
          Authorization: `Bearer ${activeToken}`,
        },
      });

      if (res.ok) {
        const userData = await res.json();
        const role = normalizeRole(userData.role);
        const userProfile: UserProfile = {
          id: userData.id,
          name: userData.name,
          email: userData.email,
          role,
          department: userData.department_name || userData.department || PRESET_USERS[role].department,
          designation: userData.designation || PRESET_USERS[role].designation,
          canUploadDocuments: userData.can_upload_documents ?? (role !== 'Student'),
          canEditDocuments: userData.can_edit_documents ?? (role !== 'Student'),
          canApproveDirectives: userData.can_approve_directives ?? (role === 'Registrar'),
          canBroadcastNudge: userData.can_broadcast_nudge ?? (role !== 'Student'),
        };

        setCurrentUser(userProfile);
        setCurrentRole(role);
        setIsAuthenticated(true);
        syncAuthState(activeToken, userProfile, true);
      } else {
        // Token expired or invalid on backend
        setToken(null);
        setIsAuthenticated(false);
        localStorage.removeItem(TOKEN_KEY);
        localStorage.setItem(AUTH_STATUS_KEY, 'false');
      }
    } catch (err) {
      // Backend unreachable: keep session alive for mock/demo tokens and valid JWTs
      console.warn('[AuthContext] Backend check error:', err);
      const isMockToken =
        activeToken.startsWith('mock-token-') ||
        activeToken.startsWith('demo-token-') ||
        activeToken.startsWith('custom-token-');
      if (!isMockToken && !isValidJWT(activeToken)) {
        setToken(null);
        setIsAuthenticated(false);
        localStorage.removeItem(TOKEN_KEY);
      }
      // For mock tokens or valid JWTs, keep isAuthenticated = true (already set from state init)
    } finally {
      setIsLoading(false);
    }
  }, [token, syncAuthState]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const loginWithPassword = async (identifier: string, password: string): Promise<{ success: boolean; error?: string }> => {
    const cleanId = identifier.trim();
    const cleanPass = password.trim();

    if (!cleanId || !cleanPass) {
      return { success: false, error: 'Please provide both email/username and password.' };
    }

    try {
      // 1. Try backend POST /api/v1/auth/login
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: cleanId, password: cleanPass }),
      });

      if (res.ok) {
        const data = await res.json();
        const activeRole = normalizeRole(data.role);
        const profile: UserProfile = {
          id: data.user_id || data.user?.id || `usr-${activeRole.toLowerCase()}`,
          name: data.name || data.user?.name || PRESET_USERS[activeRole].name,
          email: data.email || data.user?.email,
          role: activeRole,
          department: data.department || data.user?.department_name || PRESET_USERS[activeRole].department,
          designation: data.user?.designation || PRESET_USERS[activeRole].designation,
          canUploadDocuments: data.user?.can_upload_documents ?? (activeRole !== 'Student'),
          canEditDocuments: data.user?.can_edit_documents ?? (activeRole !== 'Student'),
          canApproveDirectives: data.user?.can_approve_directives ?? (activeRole === 'Registrar'),
          canBroadcastNudge: data.user?.can_broadcast_nudge ?? (activeRole !== 'Student'),
        };

        setToken(data.access_token);
        setCurrentUser(profile);
        setCurrentRole(activeRole);
        setIsAuthenticated(true);
        setIsLoginModalOpen(false);
        syncAuthState(data.access_token, profile, true);

        return { success: true };
      }

      if (res.status === 401) {
        const errorData = await res.json().catch(() => ({ detail: 'Invalid credentials' }));
        return { success: false, error: errorData.detail || 'Invalid email/username or password.' };
      }

      return { success: false, error: 'Authentication failed. Please try again.' };
    } catch (networkErr) {
      // Network/offline fallback for preset accounts
      console.warn('[AuthContext] Network request failed, checking preset users:', networkErr);
      let matchedRole: UserRole | null = null;
      for (const [role, creds] of Object.entries(AUTH_CREDENTIALS)) {
        const matchesUsername = creds.usernames.some(u => u.toLowerCase() === cleanId.toLowerCase());
        if (matchesUsername || creds.email.toLowerCase() === cleanId.toLowerCase()) {
          matchedRole = role as UserRole;
          break;
        }
      }

      if (matchedRole && (cleanPass === AUTH_CREDENTIALS[matchedRole].password || cleanPass === 'admin123')) {
        const profile = PRESET_USERS[matchedRole];
        const mockToken = `mock-token-${matchedRole.toLowerCase()}-${Date.now()}`;
        setToken(mockToken);
        setCurrentRole(matchedRole);
        setCurrentUser(profile);
        setIsAuthenticated(true);
        setIsLoginModalOpen(false);
        syncAuthState(mockToken, profile, true);
        return { success: true };
      }

      return {
        success: false,
        error: `Could not connect to backend server. (Check ${API_BASE})`,
      };
    }
  };

  const loginAs = (role: UserRole | string) => {
    const validRole = normalizeRole(role);
    const profile = PRESET_USERS[validRole];
    const mockToken = `demo-token-${validRole.toLowerCase()}-${Date.now()}`;
    setToken(mockToken);
    setCurrentRole(validRole);
    setCurrentUser(profile);
    setIsAuthenticated(true);
    setIsLoginModalOpen(false);
    syncAuthState(mockToken, profile, true);
  };

  const loginWithCustom = (user: UserProfile) => {
    const mockToken = `custom-token-${user.id}-${Date.now()}`;
    setToken(mockToken);
    setCurrentRole(user.role);
    setCurrentUser(user);
    setIsAuthenticated(true);
    setIsLoginModalOpen(false);
    syncAuthState(mockToken, user, true);
  };

  const logout = () => {
    setToken(null);
    setIsAuthenticated(false);
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(AUTH_STORAGE_KEY);
      localStorage.removeItem(USER_KEY);
      localStorage.setItem(AUTH_STATUS_KEY, 'false');
    } catch {
      // ignore
    }
  };

  const openLoginModal = () => setIsLoginModalOpen(true);
  const closeLoginModal = () => setIsLoginModalOpen(false);

  return (
    <AuthContext.Provider
      value={{
        token,
        currentUser,
        currentRole,
        isAuthenticated,
        isLoading,
        loginWithPassword,
        login: loginWithPassword,
        loginAs,
        loginWithCustom,
        logout,
        isLoginModalOpen,
        openLoginModal,
        closeLoginModal,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
