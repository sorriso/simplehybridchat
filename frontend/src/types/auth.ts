/* path: frontend/src/types/auth.ts
   version: 3
   
   Changes in v3:
   - SECURITY: LoginRequest now uses password_hash instead of password
   - Frontend sends SHA256(password) as password_hash
   - Backend receives hash, not plaintext
   
   Changes in v2:
   - FIXED: LoginRequest uses 'email' instead of 'username'
*/

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
  managerIds: string[];
  memberIds: string[];
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
  groupIds: string[];
  createdAt: Date;
  lastLogin?: Date;
}

/**
 * Server configuration for authentication
 */
export interface ServerAuthConfig {
  mode: AuthMode;
  allowMultiLogin: boolean;
  maintenanceMode: boolean;

  ssoConfig?: {
    tokenHeader: string;
    nameHeader?: string;
    emailHeader?: string;
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
 * 
 * SECURITY: password_hash is SHA256 computed client-side
 * Backend expects SHA256 hash, not plaintext password
 */
export interface LoginRequest {
  email: string;
  password_hash: string;
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
  canUseApp: boolean;
  canManageOwnPreferences: boolean;
  canShareOwnConversations: boolean;
  canForceLogout: boolean;

  canManageGroupMembers: boolean;
  canActivateDeactivateGroupMembers: boolean;
  canManageGroups: boolean;

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
  sharedBy: string;
  sharedAt: Date;
}