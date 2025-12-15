/* path: frontend/src/components/settings/SettingsPanel.tsx
   version: 10
   
   Changes in v10:
   - ADDED: "My Groups" section for all users to see their user-groups
   - Shows group IDs (group names will be added in future version)
   - Visible to all authenticated users, not just managers/root */

   import { useMemo, useState, useEffect } from "react";
   import { X, LogOut, ShieldAlert } from "lucide-react";
   import { IconButton } from "../ui/IconButton";
   import { Button } from "../ui/Button";
   import { PromptCustomization } from "./PromptCustomization";
   import { UserManagementPanel } from "../admin/UserManagementPanel";
   import { useSettings } from "@/lib/hooks/useSettings";
   import { useAuth, userManagementApi } from "@/lib/hooks/useAuth";
   import { calculatePermissions } from "@/lib/utils/permissions";
   import type { UserGroup } from "@/types/auth";
   
   interface SettingsPanelProps {
     isOpen?: boolean;
     onClose?: () => void;
   }
   
   /**
    * Settings panel component
    */
   export function SettingsPanel({ isOpen = true, onClose }: SettingsPanelProps) {
     const { settings, isSaving, updatePromptCustomization } = useSettings();
     const { user, logout, forceLogout, authMode } = useAuth();
     const [userGroups, setUserGroups] = useState<UserGroup[]>([]);
   
     // Memoize permissions to prevent re-renders (MUST be before early return)
     const permissions = useMemo(
       () => calculatePermissions(user, authMode),
       [user, authMode],
     );
   
     // Check if user can access admin features
     const canAccessUserManagement = permissions.isRoot || permissions.isManager;
   
     // Load user groups
     useEffect(() => {
       if (isOpen && user) {
         loadUserGroups();
       }
     }, [isOpen, user]);
   
     const loadUserGroups = async () => {
       try {
         const groups = await userManagementApi.getAllGroups();
         setUserGroups(groups);
       } catch (error) {
         console.error("Failed to load user groups:", error);
       }
     };
   
     if (!isOpen) return null;
   
     const handleLogout = async () => {
       try {
         // Logout FIRST (clears token, updates state)
         await logout();
         
         // Then close panel
         if (onClose) {
           onClose();
         }
         
         // Force page reload to ensure clean state
         window.location.reload();
       } catch (error) {
         console.error("Logout failed:", error);
         // Close panel even if logout fails
         if (onClose) {
           onClose();
         }
       }
     };
   
     const handleForceLogout = async () => {
       await forceLogout();
     };
   
     return (
       <div className="fixed right-0 top-0 h-full w-[700px] bg-white shadow-xl border-l border-gray-200 z-40">
         <div className="flex flex-col h-full">
           {/* Header */}
           <div className="flex items-center justify-between p-4 border-b border-gray-200">
             <h2 className="text-lg font-semibold text-gray-900">Settings</h2>
             {onClose && <IconButton icon={X} onClick={onClose} title="Close" />}
           </div>
   
           {/* Content */}
           <div className="flex-1 overflow-y-auto p-6 space-y-8">
             {/* User Info Section */}
             <div>
               <h3 className="text-base font-semibold text-gray-900 mb-3">
                 User Information
               </h3>
               <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                 <div>
                   <span className="text-sm font-medium text-gray-600">Name:</span>
                   <span className="text-sm text-gray-900 ml-2">
                     {user?.name || "Unknown"}
                   </span>
                 </div>
                 <div>
                   <span className="text-sm font-medium text-gray-600">
                     Email:
                   </span>
                   <span className="text-sm text-gray-900 ml-2">
                     {user?.email || "Unknown"}
                   </span>
                 </div>
                 <div>
                   <span className="text-sm font-medium text-gray-600">Role:</span>
                   <span className="text-sm text-gray-900 ml-2 capitalize">
                     {user?.role || "Unknown"}
                   </span>
                 </div>
                 <div>
                   <span className="text-sm font-medium text-gray-600">
                     Status:
                   </span>
                   <span
                     className={`text-sm ml-2 ${user?.status === "active" ? "text-green-600" : "text-red-600"}`}
                   >
                     {user?.status === "active" ? "Authenticated" : "Inactive"}
                   </span>
                 </div>
               </div>
             </div>
   
             {/* Prompt Customization Section */}
             <div>
               <h3 className="text-base font-semibold text-gray-900 mb-3">
                 AI Behavior
               </h3>
               <PromptCustomization
                 initialValue={settings?.promptCustomization || ""}
                 onSave={async (value: string) => {
                   await updatePromptCustomization(value);
                 }}
                 isSaving={isSaving}
               />
             </div>
   
             {/* User Management Section (Root/Manager only) */}
             {canAccessUserManagement && user && (
               <div>
                 <h3 className="text-base font-semibold text-gray-900 mb-3">
                   User Management
                 </h3>
                 <UserManagementPanel
                   currentUser={user}
                   permissions={{
                     canManageAllUsers: permissions.isRoot,
                     canActivateDeactivateGroupMembers:
                       permissions.canToggleUserStatus,
                     canManageGroups: permissions.canViewGroups,
                     canCreateGroups: permissions.canCreateGroups,
                   }}
                 />
               </div>
             )}
   
             {/* My Groups Section (All users) */}
             {user && (
               <div>
                 <h3 className="text-base font-semibold text-gray-900 mb-3">
                   My Groups
                 </h3>
                 <div className="space-y-2">
                   {user.groupIds && user.groupIds.length > 0 ? (
                     user.groupIds.map((groupId) => {
                       const group = userGroups.find((g) => g.id === groupId);
                       return (
                         <div
                           key={groupId}
                           className="p-3 border border-gray-200 rounded-lg bg-gray-50"
                         >
                           <p className="text-sm font-medium text-gray-900">
                             {group?.name || `Group ${groupId}`}
                           </p>
                           {group && (
                             <p className="text-xs text-gray-500 mt-1">
                               {group.memberIds?.length || 0} member(s) • {group.status}
                             </p>
                           )}
                         </div>
                       );
                     })
                   ) : (
                     <p className="text-sm text-gray-500">
                       You are not a member of any user groups.
                     </p>
                   )}
                 </div>
               </div>
             )}
   
             {/* Theme Section (placeholder for future) */}
             <div>
               <h3 className="text-base font-semibold text-gray-900 mb-3">
                 Appearance
               </h3>
               <p className="text-sm text-gray-500">
                 Theme preferences coming soon...
               </p>
             </div>
   
             {/* Session Management Section */}
             {authMode !== "none" && (
               <div>
                 <h3 className="text-base font-semibold text-gray-900 mb-3">
                   Session
                 </h3>
                 <div className="space-y-3">
                   <Button
                     variant="secondary"
                     onClick={handleLogout}
                     className="w-full flex items-center justify-center gap-2"
                   >
                     <LogOut size={18} />
                     Logout
                   </Button>
                   <Button
                     variant="danger"
                     onClick={handleForceLogout}
                     className="w-full flex items-center justify-center gap-2"
                   >
                     <ShieldAlert size={18} />
                     Force Logout
                   </Button>
                   <p className="text-xs text-gray-500">
                     Force logout will revoke your session and require
                     re-authentication.
                   </p>
                 </div>
               </div>
             )}
   
             {/* About Section */}
             <div className="pt-8 border-t border-gray-200">
               <p className="text-xs text-gray-500">Version 0.1.0</p>
               <p className="text-xs text-gray-400 mt-1">
                 Built with Next.js, NLUX, and FastAPI
               </p>
             </div>
           </div>
         </div>
       </div>
     );
   }