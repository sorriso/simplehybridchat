/* path: frontend/src/lib/hooks/useAuth.ts
   version: 8.0
   
   Changes in v8.0:
   - SECURITY: Removed duplicate authApi definition from this file
   - Now imports authApi from lib/api/auth.ts (with SHA256 hashing)
   - Fixes 422 error where password was sent in plaintext
   - useAuth hook now uses centralized authApi with proper security
   
   Changes in v7:
   - FIX: updateGroup uses response.data
   - ADDED: createUser function
*/

import { useState, useEffect, useCallback } from "react";
import { storage } from "../utils/storage";
import { authApi, userManagementApi } from "../api/auth";
import type {
  User,
  ServerAuthConfig,
  AuthMode,
} from "@/types/auth";
import { calculatePermissions } from "../utils/permissions";

// ============================================================================
// USEAUTH HOOK
// ============================================================================

interface AuthState {
  user: User | null;
  authMode: AuthMode;
  serverConfig: ServerAuthConfig | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  permissions: ReturnType<typeof calculatePermissions>;
  maintenanceMode: boolean;
}

/**
 * Authentication hook - manages user authentication state
 */
export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    authMode: "local",
    serverConfig: null,
    isAuthenticated: false,
    loading: true,
    error: null,
    permissions: calculatePermissions(null, "local"),
    maintenanceMode: false,
  });

  // Load auth state on mount
  useEffect(() => {
    loadAuthState();
  }, []);

  /**
   * Load authentication state from server
   */
  const loadAuthState = async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      // Get server auth configuration
      const config = await authApi.getServerConfig();
      const authMode = config.mode;
      const maintenanceMode = config.maintenanceMode || false;

      // Handle maintenance mode (only root can proceed)
      if (maintenanceMode) {
        const token = storage.getAuthToken();
        if (token) {
          try {
            const user = await authApi.verifyToken(token);
            if (user.role === "root") {
              setState({
                user,
                authMode,
                serverConfig: config,
                isAuthenticated: user.status === "active",
                loading: false,
                error: null,
                permissions: calculatePermissions(user, authMode),
                maintenanceMode: true,
              });
              return;
            }
          } catch (err) {
            // Token invalid, continue to maintenance mode
          }
        }

        // Non-root users see maintenance mode
        setState({
          user: null,
          authMode,
          serverConfig: config,
          isAuthenticated: false,
          loading: false,
          error: null,
          permissions: calculatePermissions(null, authMode),
          maintenanceMode: true,
        });
        return;
      }

      // Handle different auth modes
      let user: User | null = null;

      if (authMode === "none") {
        // No authentication required - get generic user
        user = await authApi.getGenericUser();
      } else if (authMode === "local") {
        // Check for stored token
        const token = storage.getAuthToken();
        if (token) {
          try {
            user = await authApi.verifyToken(token);
          } catch (err) {
            // Token invalid, clear it
            storage.clearAuthToken();
          }
        }
      } else if (authMode === "sso") {
        // Verify SSO session
        try {
          user = await authApi.verifySsoSession();
        } catch (err) {
          // SSO session invalid
        }
      }

      setState({
        user,
        authMode,
        serverConfig: config,
        isAuthenticated: user ? user.status === "active" : false,
        loading: false,
        error: null,
        permissions: calculatePermissions(user, authMode),
        maintenanceMode: false,
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Authentication failed",
      }));
    }
  };

  /**
   * Login with email/password (local mode only)
   */
  const login = useCallback(
    async (email: string, password: string) => {
      if (state.authMode !== "local") {
        throw new Error("Login is only available in local auth mode");
      }

      try {
        setState((prev) => ({ ...prev, loading: true, error: null }));

        const response = await authApi.login(email, password);

        // Store token
        storage.setAuthToken(response.token);

        // Get user info
        const user = await authApi.verifyToken(response.token);

        setState((prev) => ({
          ...prev,
          user,
          isAuthenticated: user.status === "active",
          loading: false,
          permissions: calculatePermissions(user, prev.authMode),
        }));

        return user;
      } catch (err) {
        setState((prev) => ({
          ...prev,
          loading: false,
          error: err instanceof Error ? err.message : "Login failed",
        }));
        throw err;
      }
    },
    [state.authMode],
  );

  /**
   * Logout current user
   */
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      storage.clearAuthToken();
      setState((prev) => ({
        ...prev,
        user: null,
        isAuthenticated: false,
        permissions: calculatePermissions(null, prev.authMode),
      }));
    }
  }, []);

  /**
   * Force logout - revoke own session and reload page
   */
  const forceLogout = useCallback(async () => {
    try {
      await authApi.revokeOwnSession();
    } catch (err) {
      console.error("Force logout error:", err);
    } finally {
      storage.clearAuthToken();
      window.location.reload();
    }
  }, []);

  /**
   * Reload authentication state
   */
  const reload = useCallback(() => {
    loadAuthState();
  }, []);

  return {
    // State
    user: state.user,
    authMode: state.authMode,
    serverConfig: state.serverConfig,
    isAuthenticated: state.isAuthenticated,
    loading: state.loading,
    error: state.error,
    permissions: state.permissions,
    maintenanceMode: state.maintenanceMode,

    // Actions
    login,
    logout,
    forceLogout,
    reload,
  };
}

// Re-export API modules for backward compatibility
export { authApi, userManagementApi };