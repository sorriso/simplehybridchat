/* path: frontend/src/lib/api/auth.ts
   version: 3.1
   
   Changes in v3.1:
   - ADDED: userManagementApi (was missing in v3.0)
   - Complete API module with both authApi and userManagementApi
   
   Changes in v3:
   - SECURITY: Passwords hashed with SHA256 before transmission
   - login() computes password_hash client-side
   - Backend receives SHA256, stores bcrypt(SHA256)
*/

import { apiClient } from "./client";
import { hashPasswordForTransmission } from "@/lib/utils/crypto";
import type {
  User,
  ServerAuthConfig,
  LoginRequest,
  LoginResponse,
  UserSession,
  UserGroup,
} from "@/types/auth";

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
   * SECURITY: Password is hashed with SHA256 before transmission
   */
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const passwordHash = await hashPasswordForTransmission(password);
    
    const response = await apiClient.post<LoginResponse>("/api/auth/login", {
      email,
      password_hash: passwordHash,
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