// path: tests/mocks/scenarios/permissions.ts
// version: 3 - Converted to MSW v1 syntax

import { rest } from 'msw'
import { mockUsers } from '../data/users'
import { getServer } from '../server-instance'

// Current permission level
let currentPermissionLevel: 'user' | 'manager' | 'root' = 'user'

/**
 * Set current permission level
 */
export function setPermissionLevel(level: 'user' | 'manager' | 'root') {
  currentPermissionLevel = level
}

/**
 * Get current permission level
 */
export function getPermissionLevel(): 'user' | 'manager' | 'root' {
  return currentPermissionLevel
}

/**
 * Reset permission level to default
 */
export function resetPermissionLevel() {
  currentPermissionLevel = 'user'
}

/**
 * Apply permission scenario helper (for handler use)
 */
export function applyPermissionScenario(resource: string, action: string): any {
  // Returns null if permission granted, error response if denied
  const deniedResources: Record<string, string[]> = {
    user: ['users', 'user-groups', 'admin'],
    manager: ['admin', 'user-groups-create'],
  }

  const denied = deniedResources[currentPermissionLevel] || []
  
  if (denied.includes(resource) || denied.includes(`${resource}-${action}`)) {
    return {
      status: 403,
      body: { error: 'Forbidden - insufficient permissions' },
    }
  }

  return null
}

/**
 * Permission scenarios for testing - MSW v1 syntax
 */
export const permissionScenarios = {
  /**
   * Regular user permissions (limited access)
   */
  userPermissions: () => {
    setPermissionLevel('user')
    getServer().use(
      rest.get('/api/auth/verify', (req, res, ctx) => {
        const user = mockUsers.find(u => u.role === 'user' && u.status === 'active')
        return res(
          ctx.status(200),
          ctx.json({ user })
        )
      }),
      // Block access to user management
      rest.get('/api/users', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - insufficient permissions' })
        )
      }),
      // Block access to group management
      rest.post('/api/user-groups', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - insufficient permissions' })
        )
      })
    )
  },

  /**
   * Manager permissions (group management)
   */
  managerPermissions: () => {
    setPermissionLevel('manager')
    getServer().use(
      rest.get('/api/auth/verify', (req, res, ctx) => {
        const manager = mockUsers.find(u => u.role === 'manager')
        return res(
          ctx.status(200),
          ctx.json({ user: manager })
        )
      }),
      // Allow access to users in managed groups
      rest.get('/api/users', (req, res, ctx) => {
        const managedUsers = mockUsers.filter(u => 
          u.groupIds?.some(gid => gid === 'group-engineering')
        )
        return res(
          ctx.status(200),
          ctx.json({ users: managedUsers })
        )
      }),
      // Block creating new groups
      rest.post('/api/user-groups', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - only root can create groups' })
        )
      })
    )
  },

  /**
   * Root permissions (full access)
   */
  rootPermissions: () => {
    setPermissionLevel('root')
    getServer().use(
      rest.get('/api/auth/verify', (req, res, ctx) => {
        const root = mockUsers.find(u => u.role === 'root')
        return res(
          ctx.status(200),
          ctx.json({ user: root })
        )
      })
      // No restrictions for root - handlers will allow everything
    )
  },

  /**
   * User trying to access admin features
   */
  unauthorizedAdminAccess: () => {
    setPermissionLevel('user')
    getServer().use(
      rest.post('/api/admin/maintenance', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - admin access required' })
        )
      }),
      rest.post('/api/auth/revoke-all-sessions', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - admin access required' })
        )
      })
    )
  },

  /**
   * Manager trying to access root-only features
   */
  managerAccessingRootFeatures: () => {
    setPermissionLevel('manager')
    getServer().use(
      rest.post('/api/user-groups', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - only root can create groups' })
        )
      }),
      rest.put('/api/users/:id/role', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - only root can change roles' })
        )
      }),
      rest.post('/api/admin/maintenance', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - only root can toggle maintenance' })
        )
      })
    )
  },
}

/**
 * Check if current user has permission
 */
export function checkPermission(requiredLevel: 'user' | 'manager' | 'root'): boolean {
  const levels = { user: 1, manager: 2, root: 3 }
  return levels[currentPermissionLevel] >= levels[requiredLevel]
}