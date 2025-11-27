// path: tests/mocks/handlers/auth.ts
// version: 3 - Fixed URL matching for apiClient with base URL

import { rest } from 'msw'

// API base URL used by apiClient
const API_BASE_URL = 'http://localhost:8000'

// Mock users for authentication
const mockUsers = [
  {
    id: 'user-john-doe',
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'user' as const,
    status: 'active' as const,
    groupIds: ['ugroup-1'],
  },
  {
    id: 'user-manager',
    name: 'Jane Manager',
    email: 'jane.manager@example.com',
    role: 'manager' as const,
    status: 'active' as const,
    groupIds: ['ugroup-1', 'ugroup-2'],
  },
  {
    id: 'user-root',
    name: 'Admin Root',
    email: 'admin@example.com',
    role: 'root' as const,
    status: 'active' as const,
    groupIds: [],
  },
]

/**
 * Auth API handlers - MSW v1 syntax with full URLs
 */
export const authHandlers = [
  // GET /api/auth/config
  rest.get(`${API_BASE_URL}/api/auth/config`, (req, res, ctx) => {
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
  }),

  // GET /api/auth/generic
  rest.get(`${API_BASE_URL}/api/auth/generic`, (req, res, ctx) => {
    const genericUser = {
      id: 'user-generic',
      name: 'John Doe',
      email: 'generic@example.com',
      role: 'user' as const,
      status: 'active' as const,
      groupIds: [],
    }

    return res(
      ctx.status(200),
      ctx.json({ user: genericUser })
    )
  }),

  // GET /api/auth/verify
  rest.get(`${API_BASE_URL}/api/auth/verify`, (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization')
    
    if (!authHeader) {
      return res(
        ctx.status(401),
        ctx.json({ error: 'No authorization token provided' })
      )
    }

    // Default to returning the first user
    const user = mockUsers[0]

    return res(
      ctx.status(200),
      ctx.json({ user })
    )
  }),

  // GET /api/auth/sso/verify
  rest.get(`${API_BASE_URL}/api/auth/sso/verify`, (req, res, ctx) => {
    // Return a default user for SSO
    const user = mockUsers[0]

    return res(
      ctx.status(200),
      ctx.json({ user })
    )
  }),

  // POST /api/auth/login
  rest.post(`${API_BASE_URL}/api/auth/login`, async (req, res, ctx) => {
    const body = await req.json() as { username: string; password: string }

    // Find user by email (username is email)
    const user = mockUsers.find(u => u.email === body.username)

    if (!user || body.password !== 'password123') {
      return res(
        ctx.status(401),
        ctx.json({ error: 'Invalid credentials' })
      )
    }

    return res(
      ctx.status(200),
      ctx.json({
        user,
        token: `mock-token-${user.id}`,
      })
    )
  }),

  // POST /api/auth/logout
  rest.post(`${API_BASE_URL}/api/auth/logout`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ success: true })
    )
  }),

  // POST /api/auth/revoke-own-session
  rest.post(`${API_BASE_URL}/api/auth/revoke-own-session`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ success: true })
    )
  }),

  // POST /api/auth/revoke-all-sessions
  rest.post(`${API_BASE_URL}/api/auth/revoke-all-sessions`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ success: true })
    )
  }),

  // GET /api/auth/sessions
  rest.get(`${API_BASE_URL}/api/auth/sessions`, (req, res, ctx) => {
    const mockSessions = [
      {
        id: 'session-1',
        userId: 'user-john-doe',
        createdAt: new Date().toISOString(),
        lastActivityAt: new Date().toISOString(),
        ipAddress: '192.168.1.1',
        userAgent: 'Mozilla/5.0',
      },
    ]

    return res(
      ctx.status(200),
      ctx.json({ sessions: mockSessions })
    )
  }),
]