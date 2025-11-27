/* path: src/types/auth.ts
   version: 1 */

/**
 * User role levels
 */
export type UserRole = "user" | "manager" | "root";

/**
 * Authentication modes supported by the server
 */
export type AuthMode = "none" | "local" | "sso";

/**
 * User status
 */
export type UserStatus = "active" | "disabled";

/**
 * User group
 */
export interface UserGroup {
  id: string;
  name: string;
  status: "active" | "disabled";
  createdAt: Date;
  managerIds: string[]; // Users with manager role for this group
  memberIds: string[]; // All users in the group
}

/**
 * Extended user with authorization info
 */
export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  groupIds: string[]; // Groups this user belongs to
  createdAt: Date;
  lastLogin?: Date;
}

/**
 * Server configuration for authentication
 */
export interface ServerAuthConfig {
  mode: AuthMode;
  allowMultiLogin: boolean; // Whether multiple simultaneous logins are allowed
  maintenanceMode: boolean; // Whether app is in maintenance mode

  // SSO configuration (only present if mode === 'sso')
  ssoConfig?: {
    tokenHeader: string; // e.g., "X-Auth-Token"
    nameHeader?: string; // e.g., "X-User-Name"
    emailHeader?: string; // e.g., "X-User-Email"
    firstNameHeader?: string;
    lastNameHeader?: string;
  };
}

/**
 * Session information
 */
export interface UserSession {
  sessionId: string;
  userId: string;
  createdAt: Date;
  expiresAt: Date;
  ipAddress?: string;
  userAgent?: string;
}

/**
 * Login request (for local auth mode)
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * Login response
 */
export interface LoginResponse {
  user: User;
  token: string;
  expiresAt: Date;
}

/**
 * Auth context state
 */
export interface AuthContextState {
  user: User | null;
  serverConfig: ServerAuthConfig | null;
  loading: boolean;
  error: string | null;
}

/**
 * Permissions helper type
 */
export interface UserPermissions {
  // User permissions
  canUseApp: boolean;
  canManageOwnPreferences: boolean;
  canShareOwnConversations: boolean;
  canForceLogout: boolean;

  // Manager permissions
  canManageGroupMembers: boolean;
  canActivateDeactivateGroupMembers: boolean;
  canManageGroups: boolean;

  // Root permissions
  canManageAllUsers: boolean;
  canCreateGroups: boolean;
  canAssignManagers: boolean;
  canRevokeAllSessions: boolean;
  canToggleMaintenanceMode: boolean;
}

/**
 * Conversation sharing info
 */
export interface ConversationShare {
  conversationId: string;
  sharedWithGroupIds: string[];
  sharedBy: string; // userId
  sharedAt: Date;
}
