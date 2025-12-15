/* path: frontend/src/lib/hooks/useAuth.ts
   version: 7
   
   Changes in v7:
   - FIX: updateGroup uses response.data (backend returns SingleUserGroupResponse with data field)
   - ADDED: createUser function for creating new users (was missing)
   - Reason: updateGroup was using response.group causing rename to fail
   
   Changes in v6:
   - FIX: Reverted getAllUsers and toggleUserStatus to use correct response fields
   - getAllUsers: response.data → response.users (backend returns {users: [...]})
   - toggleUserStatus: response.data → response.user (backend returns {user: {...}})
   - KEPT v5 fixes for user-groups endpoints (they DO use response.data)
   - Reason: /api/users routes use legacy format, /api/user-groups use SuccessResponse
   
   Changes in v5:
   - CRITICAL FIX: Changed response field access for user-groups endpoints
   - getAllGroups: response.groups → response.data
   - createGroup: response.group → response.data  
   - toggleGroupStatus: response.group → response.data
   - Reason: Backend returns SuccessResponse with 'data' field for user-groups
*/

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import { storage } from "../utils/storage";
import type {
  User,
  ServerAuthConfig,
  LoginRequest,
  LoginResponse,
  UserSession,
  UserGroup,
  AuthMode,
} from "@/types/auth";
import { calculatePermissions } from "../utils/permissions";

// ============================================================================
// AUTH API
// ============================================================================

/**
 * Authentication API endpoints
 */
export const authApi = {
  /**
   * Get server authentication configuration
   */
  getServerConfig: async (): Promise<ServerAuthConfig> => {
    const response = await apiClient.get<{ config: ServerAuthConfig }>(
      "/api/auth/config",
    );
    return response.config;
  },

  /**
   * Get generic user (for "none" auth mode)
   */
  getGenericUser: async (): Promise<User> => {
    const response = await apiClient.get<{ user: User }>("/api/auth/generic");
    return response.user;
  },

  /**
   * Verify token and get user info (for "local" auth mode)
   */
  verifyToken: async (token: string): Promise<User> => {
    const response = await apiClient.get<{ user: User }>("/api/auth/verify", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.user;
  },

  /**
   * Verify SSO session (for "sso" auth mode)
   */
  verifySsoSession: async (): Promise<User> => {
    const response = await apiClient.get<{ user: User }>(
      "/api/auth/sso/verify",
    );
    return response.user;
  },

  /**
   * Login with email/password (for "local" auth mode)
   *
   * v4.0: Changed from username to email to match backend expectations
   */
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>("/api/auth/login", {
      email,
      password,
    } as LoginRequest);
    return response;
  },

  /**
   * Logout current session
   */
  logout: async (): Promise<void> => {
    await apiClient.post("/api/auth/logout");
  },

  /**
   * Force logout - revoke own session (user permission)
   */
  revokeOwnSession: async (): Promise<void> => {
    await apiClient.post("/api/auth/revoke-own-session");
  },

  /**
   * Revoke all sessions (root permission only)
   */
  revokeAllSessions: async (): Promise<void> => {
    await apiClient.post("/api/auth/revoke-all-sessions");
  },

  /**
   * Get all active sessions (root permission)
   */
  getAllSessions: async (): Promise<UserSession[]> => {
    const response = await apiClient.get<{ sessions: UserSession[] }>(
      "/api/auth/sessions",
    );
    return response.sessions;
  },
};

/**
 * User management API endpoints (for managers and root)
 */
export const userManagementApi = {
  /**
   * Get all users (manager/root permission)
   */
  getAllUsers: async (): Promise<User[]> => {
    const response = await apiClient.get<{ users: User[] }>("/api/users");
    return response.users;
  },

  /**
   * Get user by ID
   */
  getUserById: async (userId: string): Promise<User> => {
    const response = await apiClient.get<{ user: User }>(
      `/api/users/${userId}`,
    );
    return response.user;
  },

  /**
   * Create new user (root only)
   */
  createUser: async (userData: {
    name: string;
    email: string;
    password: string;
    role?: "user" | "manager" | "root";
  }): Promise<User> => {
    const response = await apiClient.post<{ user: User }>(
      "/api/users",
      userData,
    );
    return response.user;
  },

  /**
   * Activate/deactivate user (manager for their groups, root for all)
   */
  toggleUserStatus: async (
    userId: string,
    status: "active" | "disabled",
  ): Promise<User> => {
    const response = await apiClient.put<{ user: User }>(
      `/api/users/${userId}/status`,
      { status },
    );
    return response.user;
  },

  /**
   * Assign role to user (root only)
   */
  assignRole: async (
    userId: string,
    role: "user" | "manager" | "root",
  ): Promise<User> => {
    const response = await apiClient.put<{ user: User }>(
      `/api/users/${userId}/role`,
      { role },
    );
    return response.user;
  },

  /**
   * Get all user groups
   */
  getAllGroups: async (): Promise<UserGroup[]> => {
    const response = await apiClient.get<{ data: UserGroup[] }>(
      "/api/user-groups",
    );
    return response.data;
  },

  /**
   * Create user group (root only)
   */
  createGroup: async (name: string): Promise<UserGroup> => {
    const response = await apiClient.post<{ data: UserGroup }>(
      "/api/user-groups",
      { name },
    );
    return response.data;
  },

  /**
   * Update user group
   */
  updateGroup: async (groupId: string, name: string): Promise<UserGroup> => {
    const response = await apiClient.put<{ data: UserGroup }>(
      `/api/user-groups/${groupId}`,
      { name },
    );
    return response.data;
  },

  /**
   * Toggle group status (manager for their groups, root for all)
   */
  toggleGroupStatus: async (
    groupId: string,
    status: "active" | "disabled",
  ): Promise<UserGroup> => {
    const response = await apiClient.put<{ data: UserGroup }>(
      `/api/user-groups/${groupId}/status`,
      { status },
    );
    return response.data;
  },

  /**
   * Add user to group (manager of the group or root)
   */
  addUserToGroup: async (
    groupId: string,
    userId: string,
  ): Promise<UserGroup> => {
    const response = await apiClient.post<{ group: UserGroup }>(
      `/api/user-groups/${groupId}/members`,
      { userId },
    );
    return response.group;
  },

  /**
   * Remove user from group (manager of the group or root)
   */
  removeUserFromGroup: async (
    groupId: string,
    userId: string,
  ): Promise<UserGroup> => {
    const response = await apiClient.delete<{ group: UserGroup }>(
      `/api/user-groups/${groupId}/members/${userId}`,
    );
    return response.group;
  },

  /**
   * Assign manager to group (root only)
   */
  assignManagerToGroup: async (
    groupId: string,
    userId: string,
  ): Promise<UserGroup> => {
    const response = await apiClient.post<{ group: UserGroup }>(
      `/api/user-groups/${groupId}/managers`,
      { userId },
    );
    return response.group;
  },

  /**
   * Remove manager from group (root only)
   */
  removeManagerFromGroup: async (
    groupId: string,
    userId: string,
  ): Promise<UserGroup> => {
    const response = await apiClient.delete<{ group: UserGroup }>(
      `/api/user-groups/${groupId}/managers/${userId}`,
    );
    return response.group;
  },

  /**
   * Toggle maintenance mode (root only)
   */
  toggleMaintenanceMode: async (enabled: boolean): Promise<void> => {
    await apiClient.post("/api/admin/maintenance", { enabled });
  },
};

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
   *
   * v4.0: Changed parameter name from username to email
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