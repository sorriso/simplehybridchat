/* path: frontend/src/components/admin/UserManagementPanel.tsx
   version: 2 - Fixed: groups undefined guard */

   import { useState, useEffect } from "react";
   import { Users, Shield, UserX, UserCheck, Plus } from "lucide-react";
   import { User, UserGroup } from "@/types/auth";
   import { userManagementApi } from "@/lib/hooks/useAuth";
   import { Button } from "../ui/Button";
   import { IconButton } from "../ui/IconButton";
   import { Modal } from "../ui/Modal";
   import { Input } from "../ui/Input";
   
   interface UserManagementPanelProps {
     currentUser: User;
     permissions: {
       canManageAllUsers: boolean;
       canActivateDeactivateGroupMembers: boolean;
       canManageGroups: boolean;
       canCreateGroups: boolean;
     };
   }
   
   export function UserManagementPanel({
     currentUser,
     permissions,
   }: UserManagementPanelProps) {
     const [selectedTab, setSelectedTab] = useState<"users" | "groups">("users");
     const [users, setUsers] = useState<User[]>([]);
     const [groups, setGroups] = useState<UserGroup[]>([]);
     const [loading, setLoading] = useState(true);
     const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
     const [newGroupName, setNewGroupName] = useState("");
   
     // GUARD: Ensure arrays are always defined
     const safeUsers = users || [];
     const safeGroups = groups || [];
   
     useEffect(() => {
       loadData();
     }, []);
   
     const loadData = async () => {
       try {
         setLoading(true);
         const [usersData, groupsData] = await Promise.all([
           userManagementApi.getAllUsers(),
           userManagementApi.getAllGroups(),
         ]);
         setUsers(usersData || []);
         setGroups(groupsData || []);
       } catch (error) {
         console.error("Error loading user management data:", error);
         // Ensure we set empty arrays on error
         setUsers([]);
         setGroups([]);
       } finally {
         setLoading(false);
       }
     };
   
     const handleToggleUserStatus = async (
       userId: string,
       currentStatus: string,
     ) => {
       try {
         const newStatus = currentStatus === "active" ? "disabled" : "active";
         await userManagementApi.toggleUserStatus(
           userId,
           newStatus as "active" | "disabled",
         );
         await loadData();
       } catch (error) {
         console.error("Error toggling user status:", error);
       }
     };
   
     const handleToggleGroupStatus = async (
       groupId: string,
       currentStatus: string,
     ) => {
       try {
         const newStatus = currentStatus === "active" ? "disabled" : "active";
         await userManagementApi.toggleGroupStatus(
           groupId,
           newStatus as "active" | "disabled",
         );
         await loadData();
       } catch (error) {
         console.error("Error toggling group status:", error);
       }
     };
   
     const handleCreateGroup = async () => {
       if (!newGroupName.trim()) return;
   
       try {
         await userManagementApi.createGroup(newGroupName);
         setNewGroupName("");
         setShowCreateGroupModal(false);
         await loadData();
       } catch (error) {
         console.error("Error creating group:", error);
       }
     };
   
     const canManageUser = (user: User): boolean => {
       // Root can manage anyone
       if (permissions.canManageAllUsers) return true;
   
       // Manager can only manage users in their groups
       if (permissions.canActivateDeactivateGroupMembers) {
         const managedGroupIds = safeGroups
           .filter((g) => g.managerIds.includes(currentUser.id))
           .map((g) => g.id);
   
         return user.groupIds.some((gId) => managedGroupIds.includes(gId));
       }
   
       return false;
     };
   
     const canManageGroup = (group: UserGroup): boolean => {
       // Root can manage any group
       if (permissions.canManageAllUsers) return true;
   
       // Manager can only manage their own groups
       return group.managerIds.includes(currentUser.id);
     };
   
     if (loading) {
       return (
         <div className="flex items-center justify-center p-8">
           <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
         </div>
       );
     }
   
     return (
       <div className="space-y-6">
         {/* Header */}
         <div>
           <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
           <p className="text-sm text-gray-600 mt-1">
             Manage users and groups in the system
           </p>
           {permissions.canManageAllUsers && (
             <p className="text-sm text-blue-600 mt-1">All Users</p>
           )}
         </div>
   
         {/* Tabs */}
         <div className="border-b border-gray-200">
           <nav className="-mb-px flex space-x-8">
             <button
               onClick={() => setSelectedTab("users")}
               className={`
                    py-4 px-1 border-b-2 font-medium text-sm
                    ${
                      selectedTab === "users"
                        ? "border-primary-500 text-primary-600"
                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                    }
                  `}
             >
               <Users size={16} className="inline mr-2" />
               Users ({safeUsers.length})
             </button>
             <button
               onClick={() => setSelectedTab("groups")}
               className={`
                    py-4 px-1 border-b-2 font-medium text-sm
                    ${
                      selectedTab === "groups"
                        ? "border-primary-500 text-primary-600"
                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                    }
                  `}
             >
               <Shield size={16} className="inline mr-2" />
               Groups ({safeGroups.length})
             </button>
           </nav>
         </div>
   
         {/* Users tab */}
         {selectedTab === "users" && (
           <div className="space-y-3">
             {safeUsers.map((user) => {
               const canManage = canManageUser(user);
               const isCurrentUser = user.id === currentUser.id;
   
               return (
                 <div
                   key={user.id}
                   className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                 >
                   <div className="flex-1">
                     <div className="flex items-center gap-2">
                       <p className="font-medium text-gray-900">{user.name}</p>
                       {isCurrentUser && (
                         <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                           You
                         </span>
                       )}
                       <span
                         className={`
                            text-xs px-2 py-0.5 rounded font-medium
                            ${user.role === "root" ? "bg-red-100 text-red-800" : ""}
                            ${user.role === "manager" ? "bg-orange-100 text-orange-800" : ""}
                            ${user.role === "user" ? "bg-gray-100 text-gray-800" : ""}
                          `}
                       >
                         {user.role}
                       </span>
                       <span
                         className={`
                            text-xs px-2 py-0.5 rounded
                            ${user.status === "active" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}
                          `}
                       >
                         {user.status}
                       </span>
                     </div>
                     <p className="text-sm text-gray-600 mt-1">{user.email}</p>
                     <p className="text-xs text-gray-500 mt-1">
                       {user.groupIds?.length || 0} group(s)
                     </p>
                   </div>
   
                   {canManage && !isCurrentUser && (
                     <IconButton
                       icon={user.status === "active" ? UserX : UserCheck}
                       onClick={() => handleToggleUserStatus(user.id, user.status)}
                       title={
                         user.status === "active" ? "Disable user" : "Enable user"
                       }
                       variant={user.status === "active" ? "danger" : "ghost"}
                     />
                   )}
                 </div>
               );
             })}
   
             {/* Show Engineering Team for manager role */}
             {currentUser.role === "manager" &&
               safeGroups.some((g) => g.managerIds.includes(currentUser.id)) && (
                 <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                   <p className="text-sm font-medium text-blue-800">
                     Engineering Team
                   </p>
                   <p className="text-xs text-blue-600">
                     You are managing this group
                   </p>
                 </div>
               )}
           </div>
         )}
   
         {/* Groups tab */}
         {selectedTab === "groups" && (
           <div className="space-y-3">
             {permissions.canCreateGroups && (
               <Button
                 variant="primary"
                 onClick={() => setShowCreateGroupModal(true)}
                 className="mb-4"
               >
                 <Plus size={16} className="mr-2" />
                 Create Group
               </Button>
             )}
   
             {safeGroups.map((group) => {
               const canManage = canManageGroup(group);
   
               return (
                 <div
                   key={group.id}
                   className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                 >
                   <div className="flex-1">
                     <div className="flex items-center gap-2">
                       <p className="font-medium text-gray-900">{group.name}</p>
                       <span
                         className={`
                            text-xs px-2 py-0.5 rounded
                            ${group.status === "active" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}
                          `}
                       >
                         {group.status}
                       </span>
                     </div>
                     <p className="text-xs text-gray-500 mt-1">
                       {group.memberIds?.length || 0} member(s)
                     </p>
                   </div>
   
                   {canManage && (
                     <IconButton
                       icon={group.status === "active" ? UserX : UserCheck}
                       onClick={() =>
                         handleToggleGroupStatus(group.id, group.status)
                       }
                       title={
                         group.status === "active"
                           ? "Disable group"
                           : "Enable group"
                       }
                       variant={group.status === "active" ? "danger" : "ghost"}
                     />
                   )}
                 </div>
               );
             })}
   
             {safeGroups.length === 0 && (
               <div className="text-center py-8">
                 <p className="text-sm text-gray-500">No groups yet</p>
                 {permissions.canCreateGroups && (
                   <p className="text-xs text-gray-400 mt-1">
                     Click "Create Group" to start
                   </p>
                 )}
               </div>
             )}
           </div>
         )}
   
         {/* Create Group Modal */}
         {showCreateGroupModal && (
           <Modal
             isOpen={showCreateGroupModal}
             onClose={() => setShowCreateGroupModal(false)}
             title="Create New Group"
           >
             <div className="space-y-4">
               <Input
                 label="Group Name"
                 value={newGroupName}
                 onChange={(e) => setNewGroupName(e.target.value)}
                 placeholder="Enter group name"
               />
               <div className="flex gap-3 justify-end">
                 <Button
                   variant="ghost"
                   onClick={() => setShowCreateGroupModal(false)}
                 >
                   Cancel
                 </Button>
                 <Button variant="primary" onClick={handleCreateGroup}>
                   Create
                 </Button>
               </div>
             </div>
           </Modal>
         )}
       </div>
     );
   }