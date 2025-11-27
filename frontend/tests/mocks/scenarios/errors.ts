// path: tests/mocks/scenarios/errors.ts
// version: 3 - Converted to MSW v1 syntax

import { rest } from 'msw'
import { getServer } from '../server-instance'

// Current scenario state
let currentScenario: {
  delay?: number
  errorResponse?: { status: number; body: any }
} = {}

/**
 * Reset scenario state
 */
export function resetScenario() {
  currentScenario = {}
}

/**
 * Apply scenario helper for handlers
 */
export function applyScenario(type: 'delay' | 'response'): any {
  if (type === 'delay') {
    return currentScenario.delay || 0
  }
  if (type === 'response' && currentScenario.errorResponse) {
    return currentScenario.errorResponse
  }
  return null
}

/**
 * Error scenarios for testing - MSW v1 syntax
 */
export const errorScenarios = {
  /**
   * Simulate network error
   */
  networkError: () => {
    getServer().use(
      rest.get('/api/auth/config', (req, res) => {
        return res.networkError('Network error')
      }),
      rest.get('/api/auth/verify', (req, res) => {
        return res.networkError('Network error')
      }),
      rest.post('/api/auth/login', (req, res) => {
        return res.networkError('Network error')
      })
    )
  },

  /**
   * Simulate auth server error (500)
   */
  authServerError: () => {
    getServer().use(
      rest.get('/api/auth/config', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Internal server error' })
        )
      }),
      rest.post('/api/auth/login', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Internal server error' })
        )
      })
    )
  },

  /**
   * Simulate conversation creation error
   */
  conversationCreationError: () => {
    getServer().use(
      rest.post('/api/conversations', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Failed to create conversation' })
        )
      })
    )
  },

  /**
   * Simulate file upload error
   */
  fileUploadError: () => {
    getServer().use(
      rest.post('/api/files/upload', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Upload failed' })
        )
      })
    )
  },

  /**
   * Simulate settings save error
   */
  settingsSaveError: () => {
    getServer().use(
      rest.put('/api/settings', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Failed to save settings' })
        )
      })
    )
  },

  /**
   * Simulate unauthorized access (401)
   */
  unauthorizedAccess: () => {
    getServer().use(
      rest.get('/api/*', (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ error: 'Unauthorized' })
        )
      }),
      rest.post('/api/*', (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ error: 'Unauthorized' })
        )
      }),
      rest.put('/api/*', (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ error: 'Unauthorized' })
        )
      }),
      rest.delete('/api/*', (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ error: 'Unauthorized' })
        )
      })
    )
  },

  /**
   * Simulate forbidden access (403)
   */
  forbiddenAccess: () => {
    getServer().use(
      rest.get('/api/users', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - insufficient permissions' })
        )
      }),
      rest.post('/api/user-groups', (req, res, ctx) => {
        return res(
          ctx.status(403),
          ctx.json({ error: 'Forbidden - insufficient permissions' })
        )
      })
    )
  },

  /**
   * Simulate resource not found (404)
   */
  resourceNotFound: () => {
    getServer().use(
      rest.get('/api/conversations/:id', (req, res, ctx) => {
        return res(
          ctx.status(404),
          ctx.json({ error: 'Resource not found' })
        )
      }),
      rest.get('/api/users/:id', (req, res, ctx) => {
        return res(
          ctx.status(404),
          ctx.json({ error: 'Resource not found' })
        )
      })
    )
  },

  /**
   * Simulate slow API response
   */
  slowApi: (delayMs: number = 2000) => {
    getServer().use(
      rest.get('/api/*', (req, res, ctx) => {
        return res(
          ctx.delay(delayMs),
          ctx.status(200),
          ctx.json({})
        )
      }),
      rest.post('/api/*', (req, res, ctx) => {
        return res(
          ctx.delay(delayMs),
          ctx.status(200),
          ctx.json({})
        )
      })
    )
  },
}