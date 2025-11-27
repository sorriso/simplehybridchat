// path: tests/mocks/scenarios/auth-modes.ts
// version: 3 - Converted to MSW v1 syntax

import { rest } from 'msw'
import { mockUsers } from '../data/users'
import { getServer } from '../server-instance'

/**
 * Scenarios for different authentication modes - MSW v1 syntax
 */
export const authModeScenarios = {
  /**
   * Mode "none" - No authentication required
   */
  noAuthMode: () => {
    getServer().use(
      rest.get('/api/auth/config', (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            config: {
              mode: 'none',
              allowMultiLogin: true,
              maintenanceMode: false,
            },
          })
        )
      })
    )
  },

  /**
   * Mode "local" - Username/password authentication
   */
  localAuthMode: () => {
    getServer().use(
      rest.get('/api/auth/config', (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            config: {
              mode: 'local',
              allowMultiLogin: false,
              maintenanceMode: false,
            },
          })
        )
      })
    )
  },

  /**
   * Mode "sso" - Single Sign-On authentication
   */
  ssoAuthMode: () => {
    getServer().use(
      rest.get('/api/auth/config', (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            config: {
              mode: 'sso',
              allowMultiLogin: false,
              maintenanceMode: false,
              ssoConfig: {
                tokenHeader: 'X-Auth-Token',
                nameHeader: 'X-User-Name',
                emailHeader: 'X-User-Email',
              },
            },
          })
        )
      })
    )
  },

  /**
   * Maintenance mode enabled
   */
  maintenanceMode: () => {
    getServer().use(
      rest.get('/api/auth/config', (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            config: {
              mode: 'local',
              allowMultiLogin: false,
              maintenanceMode: true,
            },
          })
        )
      })
    )
  },

  /**
   * User with disabled status
   */
  disabledUser: () => {
    getServer().use(
      rest.get('/api/auth/verify', (req, res, ctx) => {
        const disabledUser = mockUsers.find(u => u.status === 'disabled')
        return res(
          ctx.status(200),
          ctx.json({ user: disabledUser })
        )
      })
    )
  },

  /**
   * Root user logged in
   */
  rootUserLoggedIn: () => {
    getServer().use(
      rest.get('/api/auth/verify', (req, res, ctx) => {
        const rootUser = mockUsers.find(u => u.role === 'root')
        return res(
          ctx.status(200),
          ctx.json({ user: rootUser })
        )
      })
    )
  },

  /**
   * Manager user logged in
   */
  managerUserLoggedIn: () => {
    getServer().use(
      rest.get('/api/auth/verify', (req, res, ctx) => {
        const managerUser = mockUsers.find(u => u.role === 'manager')
        return res(
          ctx.status(200),
          ctx.json({ user: managerUser })
        )
      })
    )
  },

  /**
   * Regular user logged in
   */
  regularUserLoggedIn: () => {
    getServer().use(
      rest.get('/api/auth/verify', (req, res, ctx) => {
        const regularUser = mockUsers.find(u => u.role === 'user' && u.id === 'user-john-doe')
        return res(
          ctx.status(200),
          ctx.json({ user: regularUser })
        )
      })
    )
  },
}

/**
 * Apply auth mode scenario helper (for handler use)
 */
export function applyAuthModeScenario(
  endpoint: string,
  config: any,
  body?: any
): any {
  // This is used by handlers to apply scenario-specific behavior
  // Returns null if no special handling needed
  return null
}