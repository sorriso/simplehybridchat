/* path: frontend/src/lib/utils/permissions.ts
   version: 1 */

import type { User, AuthMode } from "@/types/auth";

/**
 * Permission flags for the current user
 */
export interface UserPermissions {
  // Basic permissions
  canLogin: boolean;
  canLogout: boolean;
  canChat: boolean;

  // Conversation permissions
  canCreateConversation: boolean;
  canDeleteOwnConversation: boolean;
  canShareConversation: boolean;
  canViewSharedConversations: boolean;

  // File permissions
  canUploadFiles: boolean;
  canDeleteOwnFiles: boolean;

  // User management (manager level)
  canViewUsers: boolean;
  canToggleUserStatus: boolean;
  canViewGroups: boolean;
  canManageGroupMembers: boolean;

  // Admin permissions (root level)
  canCreateUsers: boolean;
  canDeleteUsers: boolean;
  canAssignRoles: boolean;
  canCreateGroups: boolean;
  canDeleteGroups: boolean;
  canAssignManagers: boolean;
  canToggleMaintenanceMode: boolean;
  canRevokeAllSessions: boolean;
  canViewAllSessions: boolean;

  // Role checks
  isUser: boolean;
  isManager: boolean;
  isRoot: boolean;
}

/**
 * Calculate permissions based on user role and auth mode
 * @param user - Current user or null if not authenticated
 * @param authMode - Current authentication mode
 * @returns Permission flags object
 */
export function calculatePermissions(
  user: User | null,
  authMode: AuthMode,
): UserPermissions {
  // Default permissions (no user / not authenticated)
  const defaultPermissions: UserPermissions = {
    // Basic
    canLogin: authMode === "local",
    canLogout: false,
    canChat: authMode === "none",

    // Conversations
    canCreateConversation: authMode === "none",
    canDeleteOwnConversation: authMode === "none",
    canShareConversation: false,
    canViewSharedConversations: false,

    // Files
    canUploadFiles: authMode === "none",
    canDeleteOwnFiles: authMode === "none",

    // User management
    canViewUsers: false,
    canToggleUserStatus: false,
    canViewGroups: false,
    canManageGroupMembers: false,

    // Admin
    canCreateUsers: false,
    canDeleteUsers: false,
    canAssignRoles: false,
    canCreateGroups: false,
    canDeleteGroups: false,
    canAssignManagers: false,
    canToggleMaintenanceMode: false,
    canRevokeAllSessions: false,
    canViewAllSessions: false,

    // Roles
    isUser: false,
    isManager: false,
    isRoot: false,
  };

  // No user - return defaults
  if (!user) {
    return defaultPermissions;
  }

  // User is disabled - minimal permissions
  if (user.status === "disabled") {
    return {
      ...defaultPermissions,
      canLogin: false,
      canLogout: authMode !== "none",
      canChat: false,
    };
  }

  // Base authenticated user permissions
  const basePermissions: UserPermissions = {
    // Basic
    canLogin: false, // Already logged in
    canLogout: authMode !== "none",
    canChat: true,

    // Conversations
    canCreateConversation: true,
    canDeleteOwnConversation: true,
    canShareConversation: true,
    canViewSharedConversations: true,

    // Files
    canUploadFiles: true,
    canDeleteOwnFiles: true,

    // User management (defaults for regular users)
    canViewUsers: false,
    canToggleUserStatus: false,
    canViewGroups: false,
    canManageGroupMembers: false,

    // Admin (defaults for regular users)
    canCreateUsers: false,
    canDeleteUsers: false,
    canAssignRoles: false,
    canCreateGroups: false,
    canDeleteGroups: false,
    canAssignManagers: false,
    canToggleMaintenanceMode: false,
    canRevokeAllSessions: false,
    canViewAllSessions: false,

    // Roles
    isUser: user.role === "user",
    isManager: user.role === "manager",
    isRoot: user.role === "root",
  };

  // Add manager permissions
  if (user.role === "manager" || user.role === "root") {
    basePermissions.canViewUsers = true;
    basePermissions.canToggleUserStatus = true;
    basePermissions.canViewGroups = true;
    basePermissions.canManageGroupMembers = true;
  }

  // Add root-only permissions
  if (user.role === "root") {
    basePermissions.canCreateUsers = true;
    basePermissions.canDeleteUsers = true;
    basePermissions.canAssignRoles = true;
    basePermissions.canCreateGroups = true;
    basePermissions.canDeleteGroups = true;
    basePermissions.canAssignManagers = true;
    basePermissions.canToggleMaintenanceMode = true;
    basePermissions.canRevokeAllSessions = true;
    basePermissions.canViewAllSessions = true;
  }

  return basePermissions;
}

/**
 * Check if user can manage a specific group
 * @param user - Current user
 * @param groupId - Group ID to check
 * @param managedGroupIds - List of group IDs the user manages
 */
export function canManageGroup(
  user: User | null,
  groupId: string,
  managedGroupIds: string[],
): boolean {
  if (!user) return false;
  if (user.role === "root") return true;
  if (user.role === "manager") {
    return managedGroupIds.includes(groupId);
  }
  return false;
}

/**
 * Check if user can manage a specific user
 * @param currentUser - Current user performing the action
 * @param targetUser - User being managed
 * @param managedGroupIds - Groups the current user manages
 * @param targetUserGroupIds - Groups the target user belongs to
 */
export function canManageUser(
  currentUser: User | null,
  targetUser: User,
  managedGroupIds: string[],
  targetUserGroupIds: string[],
): boolean {
  if (!currentUser) return false;

  // Root can manage everyone except themselves for role changes
  if (currentUser.role === "root") {
    return currentUser.id !== targetUser.id;
  }

  // Managers can manage users in their groups (except other managers and root)
  if (currentUser.role === "manager") {
    if (targetUser.role === "manager" || targetUser.role === "root") {
      return false;
    }
    // Check if target user is in any of the manager's groups
    return targetUserGroupIds.some((gid) => managedGroupIds.includes(gid));
  }

  return false;
}
