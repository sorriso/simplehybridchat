/* path: tests/unit/hooks/useAuth.test.unit.extended.ts
   version: 1 - Extended tests for uncovered API endpoints (lines 105-263) */

   import { renderHook, waitFor } from '@testing-library/react';
   import { useAuth, sessionApi, userManagementApi } from '@/lib/hooks/useAuth';
   import { server } from '@/tests/mocks/server';
   import { rest } from 'msw';
   
   describe('useAuth - Extended API Coverage', () => {
     beforeEach(() => {
       localStorage.clear();
       jest.clearAllMocks();
     });
   
     describe('sessionApi - getAllSessions', () => {
       it('should fetch all active sessions', async () => {
         const mockSessions = [
           {
             id: 'session-1',
             userId: 'user-1',
             createdAt: new Date().toISOString(),
             expiresAt: new Date(Date.now() + 3600000).toISOString(),
             ip: '192.168.1.1',
             userAgent: 'Mozilla/5.0',
           },
           {
             id: 'session-2',
             userId: 'user-2',
             createdAt: new Date().toISOString(),
             expiresAt: new Date(Date.now() + 3600000).toISOString(),
             ip: '192.168.1.2',
             userAgent: 'Chrome',
           },
         ];
   
         server.use(
           rest.get('http://localhost:8000/api/auth/sessions', (req, res, ctx) => {
             return res(ctx.json({ sessions: mockSessions }));
           })
         );
   
         const sessions = await sessionApi.getAllSessions();
   
         expect(sessions).toEqual(mockSessions);
         expect(sessions).toHaveLength(2);
       });
   
       it('should handle errors when fetching sessions', async () => {
         server.use(
           rest.get('http://localhost:8000/api/auth/sessions', (req, res, ctx) => {
             return res(ctx.status(500), ctx.json({ error: 'Server error' }));
           })
         );
   
         await expect(sessionApi.getAllSessions()).rejects.toThrow();
       });
     });
   
     describe('userManagementApi - getAllUsers', () => {
       it('should fetch all users', async () => {
         const mockUsers = [
           {
             id: 'user-1',
             email: 'user1@example.com',
             role: 'user' as const,
             createdAt: new Date().toISOString(),
           },
           {
             id: 'user-2',
             email: 'user2@example.com',
             role: 'manager' as const,
             createdAt: new Date().toISOString(),
           },
         ];
   
         server.use(
           rest.get('http://localhost:8000/api/users', (req, res, ctx) => {
             return res(ctx.json({ users: mockUsers }));
           })
         );
   
         const users = await userManagementApi.getAllUsers();
   
         expect(users).toEqual(mockUsers);
         expect(users).toHaveLength(2);
       });
     });
   
     describe('userManagementApi - assignRole', () => {
       it('should assign role to user', async () => {
         const updatedUser = {
           id: 'user-1',
           email: 'user@example.com',
           role: 'manager' as const,
           createdAt: new Date().toISOString(),
         };
   
         server.use(
           rest.put('http://localhost:8000/api/users/:userId/role', (req, res, ctx) => {
             return res(ctx.json({ user: updatedUser }));
           })
         );
   
         const user = await userManagementApi.assignRole('user-1', 'manager');
   
         expect(user).toEqual(updatedUser);
         expect(user.role).toBe('manager');
       });
   
       it('should handle errors when assigning role', async () => {
         server.use(
           rest.put('http://localhost:8000/api/users/:userId/role', (req, res, ctx) => {
             return res(ctx.status(403), ctx.json({ error: 'Forbidden' }));
           })
         );
   
         await expect(
           userManagementApi.assignRole('user-1', 'root')
         ).rejects.toThrow();
       });
     });
   
     describe('userManagementApi - getAllGroups', () => {
       it('should fetch all user groups', async () => {
         const mockGroups = [
           {
             id: 'group-1',
             name: 'Engineering',
             managerIds: ['manager-1'],
             memberIds: ['user-1', 'user-2'],
             createdAt: new Date().toISOString(),
           },
           {
             id: 'group-2',
             name: 'Sales',
             managerIds: ['manager-2'],
             memberIds: ['user-3'],
             createdAt: new Date().toISOString(),
           },
         ];
   
         server.use(
           rest.get('http://localhost:8000/api/user-groups', (req, res, ctx) => {
             return res(ctx.json({ groups: mockGroups }));
           })
         );
   
         const groups = await userManagementApi.getAllGroups();
   
         expect(groups).toEqual(mockGroups);
         expect(groups).toHaveLength(2);
       });
     });
   
     describe('userManagementApi - createGroup', () => {
       it('should create a new user group', async () => {
         const newGroup = {
           id: 'group-new',
           name: 'Marketing',
           managerIds: [],
           memberIds: [],
           createdAt: new Date().toISOString(),
         };
   
         server.use(
           rest.post('http://localhost:8000/api/user-groups', (req, res, ctx) => {
             return res(ctx.json({ group: newGroup }));
           })
         );
   
         const group = await userManagementApi.createGroup('Marketing');
   
         expect(group).toEqual(newGroup);
         expect(group.name).toBe('Marketing');
       });
   
       it('should handle errors when creating group', async () => {
         server.use(
           rest.post('http://localhost:8000/api/user-groups', (req, res, ctx) => {
             return res(ctx.status(400), ctx.json({ error: 'Group already exists' }));
           })
         );
   
         await expect(
           userManagementApi.createGroup('Duplicate')
         ).rejects.toThrow();
       });
     });
   
     describe('userManagementApi - updateGroup', () => {
       it('should update user group name', async () => {
         const updatedGroup = {
           id: 'group-1',
           name: 'Engineering Team',
           managerIds: ['manager-1'],
           memberIds: ['user-1'],
           createdAt: new Date().toISOString(),
         };
   
         server.use(
           rest.put('http://localhost:8000/api/user-groups/:groupId', (req, res, ctx) => {
             return res(ctx.json({ group: updatedGroup }));
           })
         );
   
         const group = await userManagementApi.updateGroup('group-1', 'Engineering Team');
   
         expect(group).toEqual(updatedGroup);
         expect(group.name).toBe('Engineering Team');
       });
     });
   
     describe('userManagementApi - deleteGroup', () => {
       it('should delete user group', async () => {
         server.use(
           rest.delete('http://localhost:8000/api/user-groups/:groupId', (req, res, ctx) => {
             return res(ctx.status(204));
           })
         );
   
         await expect(
           userManagementApi.deleteGroup('group-1')
         ).resolves.not.toThrow();
       });
     });
   
     describe('userManagementApi - addUserToGroup', () => {
       it('should add user to group', async () => {
         const updatedGroup = {
           id: 'group-1',
           name: 'Engineering',
           managerIds: ['manager-1'],
           memberIds: ['user-1', 'user-2', 'user-new'],
           createdAt: new Date().toISOString(),
         };
   
         server.use(
           rest.post('http://localhost:8000/api/user-groups/:groupId/members', (req, res, ctx) => {
             return res(ctx.json({ group: updatedGroup }));
           })
         );
   
         const group = await userManagementApi.addUserToGroup('group-1', 'user-new');
   
         expect(group).toEqual(updatedGroup);
         expect(group.memberIds).toContain('user-new');
       });
     });
   
     describe('userManagementApi - removeUserFromGroup', () => {
       it('should remove user from group', async () => {
         const updatedGroup = {
           id: 'group-1',
           name: 'Engineering',
           managerIds: ['manager-1'],
           memberIds: ['user-1'], // user-2 removed
           createdAt: new Date().toISOString(),
         };
   
         server.use(
           rest.delete('http://localhost:8000/api/user-groups/:groupId/members/:userId', (req, res, ctx) => {
             return res(ctx.json({ group: updatedGroup }));
           })
         );
   
         const group = await userManagementApi.removeUserFromGroup('group-1', 'user-2');
   
         expect(group).toEqual(updatedGroup);
         expect(group.memberIds).not.toContain('user-2');
       });
     });
   
     describe('userManagementApi - assignManagerToGroup', () => {
       it('should assign manager to group', async () => {
         const updatedGroup = {
           id: 'group-1',
           name: 'Engineering',
           managerIds: ['manager-1', 'manager-new'],
           memberIds: ['user-1'],
           createdAt: new Date().toISOString(),
         };
   
         server.use(
           rest.post('http://localhost:8000/api/user-groups/:groupId/managers', (req, res, ctx) => {
             return res(ctx.json({ group: updatedGroup }));
           })
         );
   
         const group = await userManagementApi.assignManagerToGroup('group-1', 'manager-new');
   
         expect(group).toEqual(updatedGroup);
         expect(group.managerIds).toContain('manager-new');
       });
     });
   
     describe('userManagementApi - removeManagerFromGroup', () => {
       it('should remove manager from group', async () => {
         const updatedGroup = {
           id: 'group-1',
           name: 'Engineering',
           managerIds: ['manager-1'], // manager-2 removed
           memberIds: ['user-1'],
           createdAt: new Date().toISOString(),
         };
   
         server.use(
           rest.delete('http://localhost:8000/api/user-groups/:groupId/managers/:userId', (req, res, ctx) => {
             return res(ctx.json({ group: updatedGroup }));
           })
         );
   
         const group = await userManagementApi.removeManagerFromGroup('group-1', 'manager-2');
   
         expect(group).toEqual(updatedGroup);
         expect(group.managerIds).not.toContain('manager-2');
       });
     });
   
     describe('userManagementApi - toggleMaintenanceMode', () => {
       it('should enable maintenance mode', async () => {
         server.use(
           rest.post('http://localhost:8000/api/admin/maintenance', async (req, res, ctx) => {
             const body = await req.json();
             expect(body.enabled).toBe(true);
             return res(ctx.status(200), ctx.json({ success: true }));
           })
         );
   
         await expect(
           userManagementApi.toggleMaintenanceMode(true)
         ).resolves.not.toThrow();
       });
   
       it('should disable maintenance mode', async () => {
         server.use(
           rest.post('http://localhost:8000/api/admin/maintenance', async (req, res, ctx) => {
             const body = await req.json();
             expect(body.enabled).toBe(false);
             return res(ctx.status(200), ctx.json({ success: true }));
           })
         );
   
         await expect(
           userManagementApi.toggleMaintenanceMode(false)
         ).resolves.not.toThrow();
       });
   
       it('should handle errors when toggling maintenance', async () => {
         server.use(
           rest.post('http://localhost:8000/api/admin/maintenance', (req, res, ctx) => {
             return res(ctx.status(403), ctx.json({ error: 'Forbidden' }));
           })
         );
   
         await expect(
           userManagementApi.toggleMaintenanceMode(true)
         ).rejects.toThrow();
       });
     });
   });