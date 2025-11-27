/* path: tests/unit/lib/auth.test.unit.ts
   version: 1 */

   import { authApi, userManagementApi } from '@/lib/api/auth';
   import { apiClient } from '@/lib/api/client';
   import type { User, UserSession, UserGroup, ServerAuthConfig, LoginResponse } from '@/types/auth';
   
   // Mock the API client
   jest.mock('@/lib/api/client');
   
   describe('authApi', () => {
     const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     describe('getServerConfig', () => {
       it('should fetch server authentication configuration', async () => {
         const mockConfig: ServerAuthConfig = { authMode: 'local', allowGuests: false };
         mockApiClient.get.mockResolvedValue({ config: mockConfig });
   
         const result = await authApi.getServerConfig();
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/auth/config');
         expect(result).toEqual(mockConfig);
       });
     });
   
     describe('getGenericUser', () => {
       it('should fetch generic user for none auth mode', async () => {
         const mockUser: User = {
           id: 'generic',
           username: 'guest',
           role: 'user',
           status: 'active',
           createdAt: new Date().toISOString(),
         };
         mockApiClient.get.mockResolvedValue({ user: mockUser });
   
         const result = await authApi.getGenericUser();
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/auth/generic');
         expect(result).toEqual(mockUser);
       });
     });
   
     describe('verifyToken', () => {
       it('should verify token and return user info', async () => {
         const mockUser: User = {
           id: '1',
           username: 'testuser',
           role: 'user',
           status: 'active',
           createdAt: new Date().toISOString(),
         };
         const token = 'test-token';
         mockApiClient.get.mockResolvedValue({ user: mockUser });
   
         const result = await authApi.verifyToken(token);
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/auth/verify', {
           headers: {
             Authorization: `Bearer ${token}`,
           },
         });
         expect(result).toEqual(mockUser);
       });
     });
   
     describe('verifySsoSession', () => {
       it('should verify SSO session', async () => {
         const mockUser: User = {
           id: '1',
           username: 'ssouser',
           role: 'user',
           status: 'active',
           createdAt: new Date().toISOString(),
         };
         mockApiClient.get.mockResolvedValue({ user: mockUser });
   
         const result = await authApi.verifySsoSession();
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/auth/sso/verify');
         expect(result).toEqual(mockUser);
       });
     });
   
     describe('login', () => {
       it('should login with username and password', async () => {
         const mockResponse: LoginResponse = {
           user: {
             id: '1',
             username: 'testuser',
             role: 'user',
             status: 'active',
             createdAt: new Date().toISOString(),
           },
           token: 'jwt-token',
         };
         mockApiClient.post.mockResolvedValue(mockResponse);
   
         const result = await authApi.login('testuser', 'password');
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/login', {
           username: 'testuser',
           password: 'password',
         });
         expect(result).toEqual(mockResponse);
       });
     });
   
     describe('logout', () => {
       it('should logout current session', async () => {
         mockApiClient.post.mockResolvedValue(undefined);
   
         await authApi.logout();
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/logout');
       });
     });
   
     describe('revokeOwnSession', () => {
       it('should revoke own session', async () => {
         mockApiClient.post.mockResolvedValue(undefined);
   
         await authApi.revokeOwnSession();
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/revoke-own-session');
       });
     });
   
     describe('revokeAllSessions', () => {
       it('should revoke all sessions (root only)', async () => {
         mockApiClient.post.mockResolvedValue(undefined);
   
         await authApi.revokeAllSessions();
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/revoke-all-sessions');
       });
     });
   
     describe('getAllSessions', () => {
       it('should get all active sessions', async () => {
         const mockSessions: UserSession[] = [
           {
             id: '1',
             userId: '1',
             token: 'token1',
             expiresAt: new Date().toISOString(),
             createdAt: new Date().toISOString(),
           },
         ];
         mockApiClient.get.mockResolvedValue({ sessions: mockSessions });
   
         const result = await authApi.getAllSessions();
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/auth/sessions');
         expect(result).toEqual(mockSessions);
       });
     });
   });
   
   describe('userManagementApi', () => {
     const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     describe('getAllUsers', () => {
       it('should fetch all users', async () => {
         const mockUsers: User[] = [
           {
             id: '1',
             username: 'user1',
             role: 'user',
             status: 'active',
             createdAt: new Date().toISOString(),
           },
         ];
         mockApiClient.get.mockResolvedValue({ users: mockUsers });
   
         const result = await userManagementApi.getAllUsers();
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/users');
         expect(result).toEqual(mockUsers);
       });
     });
   
     describe('getUserById', () => {
       it('should fetch user by ID', async () => {
         const mockUser: User = {
           id: '1',
           username: 'user1',
           role: 'user',
           status: 'active',
           createdAt: new Date().toISOString(),
         };
         mockApiClient.get.mockResolvedValue({ user: mockUser });
   
         const result = await userManagementApi.getUserById('1');
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/users/1');
         expect(result).toEqual(mockUser);
       });
     });
   
     describe('toggleUserStatus', () => {
       it('should toggle user status', async () => {
         const mockUser: User = {
           id: '1',
           username: 'user1',
           role: 'user',
           status: 'disabled',
           createdAt: new Date().toISOString(),
         };
         mockApiClient.put.mockResolvedValue({ user: mockUser });
   
         const result = await userManagementApi.toggleUserStatus('1', 'disabled');
   
         expect(mockApiClient.put).toHaveBeenCalledWith('/api/users/1/status', {
           status: 'disabled',
         });
         expect(result).toEqual(mockUser);
       });
     });
   
     describe('assignRole', () => {
       it('should assign role to user', async () => {
         const mockUser: User = {
           id: '1',
           username: 'user1',
           role: 'manager',
           status: 'active',
           createdAt: new Date().toISOString(),
         };
         mockApiClient.put.mockResolvedValue({ user: mockUser });
   
         const result = await userManagementApi.assignRole('1', 'manager');
   
         expect(mockApiClient.put).toHaveBeenCalledWith('/api/users/1/role', {
           role: 'manager',
         });
         expect(result).toEqual(mockUser);
       });
     });
   
     describe('getAllGroups', () => {
       it('should fetch all user groups', async () => {
         const mockGroups: UserGroup[] = [
           {
             id: '1',
             name: 'Group 1',
             status: 'active',
             memberIds: [],
             managerIds: [],
             createdAt: new Date().toISOString(),
           },
         ];
         mockApiClient.get.mockResolvedValue({ groups: mockGroups });
   
         const result = await userManagementApi.getAllGroups();
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/user-groups');
         expect(result).toEqual(mockGroups);
       });
     });
   
     describe('createGroup', () => {
       it('should create a new user group', async () => {
         const mockGroup: UserGroup = {
           id: '1',
           name: 'New Group',
           status: 'active',
           memberIds: [],
           managerIds: [],
           createdAt: new Date().toISOString(),
         };
         mockApiClient.post.mockResolvedValue({ group: mockGroup });
   
         const result = await userManagementApi.createGroup('New Group');
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/user-groups', {
           name: 'New Group',
         });
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('updateGroup', () => {
       it('should update user group', async () => {
         const mockGroup: UserGroup = {
           id: '1',
           name: 'Updated Group',
           status: 'active',
           memberIds: [],
           managerIds: [],
           createdAt: new Date().toISOString(),
         };
         mockApiClient.put.mockResolvedValue({ group: mockGroup });
   
         const result = await userManagementApi.updateGroup('1', 'Updated Group');
   
         expect(mockApiClient.put).toHaveBeenCalledWith('/api/user-groups/1', {
           name: 'Updated Group',
         });
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('toggleGroupStatus', () => {
       it('should toggle group status', async () => {
         const mockGroup: UserGroup = {
           id: '1',
           name: 'Group 1',
           status: 'disabled',
           memberIds: [],
           managerIds: [],
           createdAt: new Date().toISOString(),
         };
         mockApiClient.put.mockResolvedValue({ group: mockGroup });
   
         const result = await userManagementApi.toggleGroupStatus('1', 'disabled');
   
         expect(mockApiClient.put).toHaveBeenCalledWith('/api/user-groups/1/status', {
           status: 'disabled',
         });
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('addUserToGroup', () => {
       it('should add user to group', async () => {
         const mockGroup: UserGroup = {
           id: '1',
           name: 'Group 1',
           status: 'active',
           memberIds: ['user1'],
           managerIds: [],
           createdAt: new Date().toISOString(),
         };
         mockApiClient.post.mockResolvedValue({ group: mockGroup });
   
         const result = await userManagementApi.addUserToGroup('1', 'user1');
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/user-groups/1/members', {
           userId: 'user1',
         });
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('removeUserFromGroup', () => {
       it('should remove user from group', async () => {
         const mockGroup: UserGroup = {
           id: '1',
           name: 'Group 1',
           status: 'active',
           memberIds: [],
           managerIds: [],
           createdAt: new Date().toISOString(),
         };
         mockApiClient.delete.mockResolvedValue({ group: mockGroup });
   
         const result = await userManagementApi.removeUserFromGroup('1', 'user1');
   
         expect(mockApiClient.delete).toHaveBeenCalledWith('/api/user-groups/1/members/user1');
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('assignManagerToGroup', () => {
       it('should assign manager to group', async () => {
         const mockGroup: UserGroup = {
           id: '1',
           name: 'Group 1',
           status: 'active',
           memberIds: [],
           managerIds: ['manager1'],
           createdAt: new Date().toISOString(),
         };
         mockApiClient.post.mockResolvedValue({ group: mockGroup });
   
         const result = await userManagementApi.assignManagerToGroup('1', 'manager1');
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/user-groups/1/managers', {
           userId: 'manager1',
         });
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('removeManagerFromGroup', () => {
       it('should remove manager from group', async () => {
         const mockGroup: UserGroup = {
           id: '1',
           name: 'Group 1',
           status: 'active',
           memberIds: [],
           managerIds: [],
           createdAt: new Date().toISOString(),
         };
         mockApiClient.delete.mockResolvedValue({ group: mockGroup });
   
         const result = await userManagementApi.removeManagerFromGroup('1', 'manager1');
   
         expect(mockApiClient.delete).toHaveBeenCalledWith('/api/user-groups/1/managers/manager1');
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('toggleMaintenanceMode', () => {
       it('should toggle maintenance mode', async () => {
         mockApiClient.post.mockResolvedValue(undefined);
   
         await userManagementApi.toggleMaintenanceMode(true);
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/admin/maintenance', {
           enabled: true,
         });
       });
     });
   });