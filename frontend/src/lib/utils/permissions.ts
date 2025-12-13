/* path: frontend/src/lib/utils/permissions.ts
   version: 2 - FIXED: Added canManageGroup/canManageUser functions and corrected permission logic */

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
 */
export function calculatePermissions(
  user: User | null,
  authMode: AuthMode,
): UserPermissions {
  // No user (unauthenticated)
  if (!user) {
    const isNoneMode = authMode === "none";

    return {
      // Basic
      canLogin: authMode === "local",
      canLogout: false,
      canChat: isNoneMode,

      // Conversations
      canCreateConversation: isNoneMode,
      canDeleteOwnConversation: isNoneMode,
      canShareConversation: false,
      canViewSharedConversations: false,

      // Files
      canUploadFiles: isNoneMode,
      canDeleteOwnFiles: isNoneMode,

      // User management (no permissions)
      canViewUsers: false,
      canToggleUserStatus: false,
      canViewGroups: false,
      canManageGroupMembers: false,

      // Admin (no permissions)
      canCreateUsers: false,
      canDeleteUsers: false,
      canAssignRoles: false,
      canCreateGroups: false,
      canDeleteGroups: false,
      canAssignManagers: false,
      canToggleMaintenanceMode: false,
      canRevokeAllSessions: false,
      canViewAllSessions: false,

      // Role checks
      isUser: false,
      isManager: false,
      isRoot: false,
    };
  }

  const role = user.role;
  const isActive = user.status === "active";
  const isNoneMode = authMode === "none";

  // Disabled user - minimal permissions
  if (!isActive) {
    return {
      canLogin: false,
      canLogout: authMode === "local" || authMode === "sso",
      canChat: false,
      canCreateConversation: false,
      canDeleteOwnConversation: false,
      canShareConversation: false,
      canViewSharedConversations: false,
      canUploadFiles: false,
      canDeleteOwnFiles: false,
      canViewUsers: false,
      canToggleUserStatus: false,
      canViewGroups: false,
      canManageGroupMembers: false,
      canCreateUsers: false,
      canDeleteUsers: false,
      canAssignRoles: false,
      canCreateGroups: false,
      canDeleteGroups: false,
      canAssignManagers: false,
      canToggleMaintenanceMode: false,
      canRevokeAllSessions: false,
      canViewAllSessions: false,
      isUser: role === "user",
      isManager: role === "manager",
      isRoot: role === "root",
    };
  }

  // Active user - full permissions based on role
  return {
    // Basic - authenticated user cannot login again, can logout in auth modes
    canLogin: false,
    canLogout: !isNoneMode,
    canChat: true,

    // Conversations
    canCreateConversation: true,
    canDeleteOwnConversation: true,
    canShareConversation: !isNoneMode,
    canViewSharedConversations: !isNoneMode,

    // Files
    canUploadFiles: true,
    canDeleteOwnFiles: true,

    // User management (manager/root)
    canViewUsers: role === "manager" || role === "root",
    canToggleUserStatus: role === "manager" || role === "root",
    canViewGroups: role === "manager" || role === "root",
    canManageGroupMembers: role === "manager" || role === "root",

    // Admin (root only)
    canCreateUsers: role === "root",
    canDeleteUsers: role === "root",
    canAssignRoles: role === "root",
    canCreateGroups: role === "root",
    canDeleteGroups: role === "root",
    canAssignManagers: role === "root",
    canToggleMaintenanceMode: role === "root",
    canRevokeAllSessions: role === "root",
    canViewAllSessions: role === "root",

    // Role checks
    isUser: role === "user",
    isManager: role === "manager",
    isRoot: role === "root",
  };
}

/**
 * Check if current user can manage a specific group
 */
export function canManageGroup(
  currentUser: User | null,
  groupId: string,
  managedGroupIds: string[],
): boolean {
  if (!currentUser) return false;

  // Root can manage any group
  if (currentUser.role === "root") return true;

  // Manager can only manage their own groups
  if (currentUser.role === "manager") {
    return managedGroupIds.includes(groupId);
  }

  // Regular users cannot manage groups
  return false;
}

/**
 * Check if current user can manage a target user
 */
export function canManageUser(
  currentUser: User | null,
  targetUser: User,
  currentUserManagedGroupIds: string[],
  targetUserGroupIds: string[],
): boolean {
  if (!currentUser) return false;

  // Cannot manage yourself
  if (currentUser.id === targetUser.id) return false;

  // Root can manage anyone except themselves
  if (currentUser.role === "root") return true;

  // Manager can manage users in their groups, but not other managers/root
  if (currentUser.role === "manager") {
    // Cannot manage managers or root
    if (targetUser.role === "manager" || targetUser.role === "root") {
      return false;
    }

    // Can manage users in their groups
    return targetUserGroupIds.some((gid) =>
      currentUserManagedGroupIds.includes(gid),
    );
  }

  // Regular users cannot manage anyone
  return false;
}
