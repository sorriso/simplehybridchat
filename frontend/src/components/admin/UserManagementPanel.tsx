/* path: frontend/src/components/admin/UserManagementPanel.tsx
   version: 9
   
   Changes in v9:
   - AUTO-SAVE: Group name saves automatically on blur (when leaving field)
   - REMOVED: "Save" button (everything is now auto-saved)
   - Only "Close" button remains in Edit Group modal
   - Consistent UX: members auto-save on click, name auto-saves on blur */

   "use client";

   import { useState, useEffect } from "react";
   import { Users, Shield, UserX, UserCheck, Plus, Edit2 } from "lucide-react";
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
     
     // Create Group modal
     const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
     const [newGroupName, setNewGroupName] = useState("");
     
     // Edit Group modal
     const [showEditGroupModal, setShowEditGroupModal] = useState(false);
     const [editingGroup, setEditingGroup] = useState<UserGroup | null>(null);
     const [editGroupName, setEditGroupName] = useState("");
     
     // Create User modal
     const [showCreateUserModal, setShowCreateUserModal] = useState(false);
     const [newUserName, setNewUserName] = useState("");
     const [newUserEmail, setNewUserEmail] = useState("");
     const [newUserPassword, setNewUserPassword] = useState("");
     const [newUserRole, setNewUserRole] = useState<"user" | "manager" | "root">("user");
   
     // Edit User modal
     const [showEditUserModal, setShowEditUserModal] = useState(false);
     const [editingUser, setEditingUser] = useState<User | null>(null);
   
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
         const finalUsers = usersData || [];
         const finalGroups = groupsData || [];
         
         setUsers(finalUsers);
         setGroups(finalGroups);
         
         // Return data for immediate use
         return { users: finalUsers, groups: finalGroups };
       } catch (error) {
         console.error("Error loading user management data:", error);
         setUsers([]);
         setGroups([]);
         return { users: [], groups: [] };
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
   
     const handleUpdateGroupName = async () => {
       if (!editGroupName.trim() || !editingGroup) return;
   
       try {
         await userManagementApi.updateGroup(editingGroup.id, editGroupName);
         
         const { groups: updatedGroups } = await loadData();
         
         // Update editingGroup with fresh data
         const freshGroup = updatedGroups.find(g => g.id === editingGroup.id);
         if (freshGroup) {
           setEditingGroup(freshGroup);
           setEditGroupName(freshGroup.name);
         }
       } catch (error) {
         console.error("Error updating group:", error);
       }
     };
   
     const handleCreateUser = async () => {
       if (!newUserName.trim() || !newUserEmail.trim() || !newUserPassword.trim()) {
         return;
       }
   
       try {
         await userManagementApi.createUser({
           name: newUserName,
           email: newUserEmail,
           password: newUserPassword,
           role: newUserRole,
         });
         
         // Reset form
         setNewUserName("");
         setNewUserEmail("");
         setNewUserPassword("");
         setNewUserRole("user");
         setShowCreateUserModal(false);
         
         await loadData();
       } catch (error) {
         console.error("Error creating user:", error);
       }
     };
   
     const handleToggleUserGroup = async (userId: string, groupId: string, isCurrentlyMember: boolean) => {
       try {
         if (isCurrentlyMember) {
           await userManagementApi.removeUserFromGroup(groupId, userId);
         } else {
           await userManagementApi.addUserToGroup(groupId, userId);
         }
         
         // Load fresh data and update editingUser immediately
         const { users: updatedUsers } = await loadData();
         
         if (editingUser && editingUser.id === userId) {
           const freshUser = updatedUsers.find(u => u.id === userId);
           if (freshUser) {
             setEditingUser(freshUser);
           }
         }
       } catch (error) {
         console.error("Error toggling user group:", error);
       }
     };
   
     const handleToggleGroupMember = async (groupId: string, userId: string, isCurrentlyMember: boolean) => {
       try {
         if (isCurrentlyMember) {
           await userManagementApi.removeUserFromGroup(groupId, userId);
         } else {
           await userManagementApi.addUserToGroup(groupId, userId);
         }
         
         // Load fresh data and update editingGroup immediately
         const { groups: updatedGroups } = await loadData();
         
         if (editingGroup && editingGroup.id === groupId) {
           const freshGroup = updatedGroups.find(g => g.id === groupId);
           if (freshGroup) {
             setEditingGroup(freshGroup);
           }
         }
       } catch (error) {
         console.error("Error toggling group member:", error);
       }
     };
   
     const openEditGroupModal = (group: UserGroup) => {
       setEditingGroup(group);
       setEditGroupName(group.name);
       setShowEditGroupModal(true);
     };
   
     const openEditUserModal = (user: User) => {
       setEditingUser(user);
       setShowEditUserModal(true);
     };
   
     const canManageUser = (user: User): boolean => {
       if (permissions.canManageAllUsers) return true;
   
       if (permissions.canActivateDeactivateGroupMembers) {
         const managedGroupIds = safeGroups
           .filter((g) => g.managerIds.includes(currentUser.id))
           .map((g) => g.id);
   
         return user.groupIds.some((gId) => managedGroupIds.includes(gId));
       }
   
       return false;
     };
   
     const canManageGroup = (group: UserGroup): boolean => {
       if (permissions.canManageAllUsers) return true;
       return group.managerIds.includes(currentUser.id);
     };
   
     const getGroupName = (groupId: string): string => {
       const group = safeGroups.find((g) => g.id === groupId);
       return group?.name || groupId;
     };
   
     const getUserName = (userId: string): string => {
       const user = safeUsers.find((u) => u.id === userId);
       return user?.name || userId;
     };
   
     // Password validation helpers
     const passwordRules = [
       { id: 'length', text: 'At least 8 characters', test: (pwd: string) => pwd.length >= 8 },
       { id: 'uppercase', text: 'One uppercase letter', test: (pwd: string) => /[A-Z]/.test(pwd) },
       { id: 'lowercase', text: 'One lowercase letter', test: (pwd: string) => /[a-z]/.test(pwd) },
       { id: 'digit', text: 'One digit', test: (pwd: string) => /\d/.test(pwd) },
     ];
   
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
                     ? "border-primary-600 text-primary-600"
                     : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                 }
               `}
             >
               <Users className="inline-block w-4 h-4 mr-2" />
               Users ({safeUsers.length})
             </button>
             <button
               onClick={() => setSelectedTab("groups")}
               className={`
                 py-4 px-1 border-b-2 font-medium text-sm
                 ${
                   selectedTab === "groups"
                     ? "border-primary-600 text-primary-600"
                     : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                 }
               `}
             >
               <Shield className="inline-block w-4 h-4 mr-2" />
               Groups ({safeGroups.length})
             </button>
           </nav>
         </div>
   
         {/* Users tab */}
         {selectedTab === "users" && (
           <div className="space-y-3">
             {permissions.canManageAllUsers && (
               <Button
                 variant="primary"
                 onClick={() => setShowCreateUserModal(true)}
                 className="mb-4"
               >
                 <Plus size={16} className="mr-2" />
                 Create User
               </Button>
             )}
   
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
                       {user.id === currentUser.id && (
                         <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                           You
                         </span>
                       )}
                       <span
                         className={`
                           text-xs px-2 py-0.5 rounded
                           ${
                             user.role === "root"
                               ? "bg-purple-100 text-purple-800"
                               : user.role === "manager"
                                 ? "bg-blue-100 text-blue-800"
                                 : "bg-gray-100 text-gray-800"
                           }
                         `}
                       >
                         {user.role}
                       </span>
                       <span
                         className={`
                           text-xs px-2 py-0.5 rounded
                           ${
                             user.status === "active"
                               ? "bg-green-100 text-green-800"
                               : "bg-red-100 text-red-800"
                           }
                         `}
                       >
                         {user.status}
                       </span>
                     </div>
                     <p className="text-xs text-gray-500 mt-1">{user.email}</p>
                     <div className="flex gap-1 mt-1 flex-wrap">
                       {user.groupIds?.map((groupId) => (
                         <span
                           key={groupId}
                           className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600"
                         >
                           {getGroupName(groupId)}
                         </span>
                       ))}
                       {(!user.groupIds || user.groupIds.length === 0) && (
                         <span className="text-xs text-gray-400">No groups</span>
                       )}
                     </div>
                   </div>
   
                   <div className="flex gap-2">
                     {canManage && (
                       <IconButton
                         icon={Edit2}
                         onClick={() => openEditUserModal(user)}
                         title="Edit user"
                         variant="ghost"
                       />
                     )}
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
                 </div>
               );
             })}
   
             {safeUsers.length === 0 && (
               <div className="text-center py-8">
                 <p className="text-sm text-gray-500">No users yet</p>
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
                           ${
                             group.status === "active"
                               ? "bg-green-100 text-green-800"
                               : "bg-red-100 text-red-800"
                           }
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
                     <div className="flex gap-2">
                       <IconButton
                         icon={Edit2}
                         onClick={() => openEditGroupModal(group)}
                         title="Edit group"
                         variant="ghost"
                       />
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
                     </div>
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
   
         {/* Edit Group Modal */}
         {showEditGroupModal && editingGroup && (
           <Modal
             isOpen={showEditGroupModal}
             onClose={() => {
               setShowEditGroupModal(false);
               setEditingGroup(null);
               setEditGroupName("");
             }}
             title="Edit Group"
           >
             <div className="space-y-4">
               <Input
                 label="Group Name"
                 value={editGroupName}
                 onChange={(e) => setEditGroupName(e.target.value)}
                 onBlur={handleUpdateGroupName}
                 placeholder="Enter group name"
               />
               
               <div>
                 <label className="block text-sm font-medium text-gray-700 mb-2">
                   Members
                 </label>
                 <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3 space-y-2">
                   {safeUsers.map((user) => {
                     const isMember = editingGroup.memberIds?.includes(user.id) || false;
                     return (
                       <label
                         key={user.id}
                         className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                       >
                         <input
                           type="checkbox"
                           checked={isMember}
                           onChange={() => handleToggleGroupMember(editingGroup.id, user.id, isMember)}
                           className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 cursor-pointer"
                         />
                         <span className="text-sm text-gray-900">{user.name}</span>
                         <span className="text-xs text-gray-500">({user.email})</span>
                       </label>
                     );
                   })}
                 </div>
               </div>
               
               <div className="flex justify-end">
                 <Button
                   variant="primary"
                   onClick={() => {
                     setShowEditGroupModal(false);
                     setEditingGroup(null);
                     setEditGroupName("");
                   }}
                 >
                   Close
                 </Button>
               </div>
             </div>
           </Modal>
         )}
   
         {/* Create User Modal */}
         {showCreateUserModal && (
           <Modal
             isOpen={showCreateUserModal}
             onClose={() => setShowCreateUserModal(false)}
             title="Create New User"
           >
             <div className="space-y-4">
               <Input
                 label="Name"
                 value={newUserName}
                 onChange={(e) => setNewUserName(e.target.value)}
                 placeholder="Full name"
               />
               <Input
                 label="Email"
                 type="email"
                 value={newUserEmail}
                 onChange={(e) => setNewUserEmail(e.target.value)}
                 placeholder="user@example.com"
               />
               <div>
                 <Input
                   label="Password"
                   type="password"
                   value={newUserPassword}
                   onChange={(e) => setNewUserPassword(e.target.value)}
                   placeholder="Strong password"
                 />
                 <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                   <p className="text-xs font-medium text-gray-700 mb-2">
                     Password must contain:
                   </p>
                   <ul className="space-y-1">
                     {passwordRules.map((rule) => {
                       const isValid = newUserPassword ? rule.test(newUserPassword) : false;
                       return (
                         <li
                           key={rule.id}
                           className={`text-xs flex items-center gap-2 ${
                             isValid ? "text-green-600" : "text-gray-500"
                           }`}
                         >
                           <span className="w-4 h-4 flex items-center justify-center">
                             {isValid ? "✓" : "○"}
                           </span>
                           {rule.text}
                         </li>
                       );
                     })}
                   </ul>
                 </div>
               </div>
               <div>
                 <label className="block text-sm font-medium text-gray-700 mb-2">
                   Role
                 </label>
                 <select
                   value={newUserRole}
                   onChange={(e) =>
                     setNewUserRole(e.target.value as "user" | "manager" | "root")
                   }
                   className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                 >
                   <option value="user">User</option>
                   <option value="manager">Manager</option>
                   <option value="root">Root</option>
                 </select>
               </div>
               <div className="flex gap-3 justify-end">
                 <Button
                   variant="ghost"
                   onClick={() => setShowCreateUserModal(false)}
                 >
                   Cancel
                 </Button>
                 <Button 
                   variant="primary" 
                   onClick={handleCreateUser}
                   disabled={!passwordRules.every(r => newUserPassword && r.test(newUserPassword))}
                 >
                   Create
                 </Button>
               </div>
             </div>
           </Modal>
         )}
   
         {/* Edit User Modal */}
         {showEditUserModal && editingUser && (
           <Modal
             isOpen={showEditUserModal}
             onClose={() => {
               setShowEditUserModal(false);
               setEditingUser(null);
             }}
             title="Edit User"
           >
             <div className="space-y-4">
               <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                 <div>
                   <span className="text-sm font-medium text-gray-600">Name:</span>
                   <span className="text-sm text-gray-900 ml-2">
                     {editingUser.name}
                   </span>
                 </div>
                 <div>
                   <span className="text-sm font-medium text-gray-600">Email:</span>
                   <span className="text-sm text-gray-900 ml-2">
                     {editingUser.email}
                   </span>
                 </div>
                 <div>
                   <span className="text-sm font-medium text-gray-600">Role:</span>
                   <span className="text-sm text-gray-900 ml-2 capitalize">
                     {editingUser.role}
                   </span>
                 </div>
                 <div>
                   <span className="text-sm font-medium text-gray-600">Status:</span>
                   <span
                     className={`text-sm ml-2 ${
                       editingUser.status === "active"
                         ? "text-green-600"
                         : "text-red-600"
                     }`}
                   >
                     {editingUser.status}
                   </span>
                 </div>
               </div>
               
               <div>
                 <label className="block text-sm font-medium text-gray-700 mb-2">
                   Groups
                 </label>
                 <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3 space-y-2">
                   {safeGroups.map((group) => {
                     const userGroupIds = editingUser.groupIds || [];
                     const isMember = userGroupIds.includes(group.id);
                     return (
                       <label
                         key={group.id}
                         className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                       >
                         <input
                           type="checkbox"
                           checked={isMember}
                           onChange={() => handleToggleUserGroup(editingUser.id, group.id, isMember)}
                           className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 cursor-pointer"
                         />
                         <span className="text-sm text-gray-900">{group.name}</span>
                         <span
                           className={`text-xs px-2 py-0.5 rounded ${
                             group.status === "active"
                               ? "bg-green-100 text-green-700"
                               : "bg-red-100 text-red-700"
                           }`}
                         >
                           {group.status}
                         </span>
                       </label>
                     );
                   })}
                   {safeGroups.length === 0 && (
                     <p className="text-sm text-gray-500 text-center py-2">
                       No groups available
                     </p>
                   )}
                 </div>
               </div>
               
               <div className="flex gap-3 justify-end">
                 <Button
                   variant="ghost"
                   onClick={() => {
                     setShowEditUserModal(false);
                     setEditingUser(null);
                   }}
                 >
                   Close
                 </Button>
               </div>
             </div>
           </Modal>
         )}
       </div>
     );
   }