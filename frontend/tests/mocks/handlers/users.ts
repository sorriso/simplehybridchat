// path: tests/mocks/handlers/users.ts
// version: 5 - Removed debug logs for clean test output

import { rest } from 'msw'
import { mockUsers, mockUserGroups, mockServerConfig } from '../data/users'

// API base URL used by apiClient
const API_BASE_URL = 'http://localhost:8000'

// In-memory storage
let users = [...mockUsers]
let userGroups = [...mockUserGroups]
let serverConfig = { ...mockServerConfig }

/**
 * Reset handler state (call in afterEach)
 */
export function resetUsersState() {
  users = [...mockUsers]
  userGroups = [...mockUserGroups]
  serverConfig = { ...mockServerConfig }
}

/**
 * Users & Admin API handlers - MSW v1 syntax with full URLs
 */
export const usersHandlers = [
  // GET /api/users
  rest.get(`${API_BASE_URL}/api/users`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ users })
    )
  }),

  // GET /api/users/:id
  rest.get(`${API_BASE_URL}/api/users/:id`, (req, res, ctx) => {
    const { id } = req.params
    const user = users.find(u => u.id === id)

    if (!user) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'User not found' })
      )
    }

    return res(
      ctx.status(200),
      ctx.json({ user })
    )
  }),

  // PUT /api/users/:id/status
  rest.put(`${API_BASE_URL}/api/users/:id/status`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { status: 'active' | 'disabled' }

    const index = users.findIndex(u => u.id === id)

    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'User not found' })
      )
    }

    users[index] = {
      ...users[index],
      status: body.status,
      updatedAt: new Date(),
    }

    return res(
      ctx.status(200),
      ctx.json({ user: users[index] })
    )
  }),

  // PUT /api/users/:id/role
  rest.put(`${API_BASE_URL}/api/users/:id/role`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { role: 'user' | 'manager' | 'root' }

    const index = users.findIndex(u => u.id === id)

    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'User not found' })
      )
    }

    users[index] = {
      ...users[index],
      role: body.role,
      updatedAt: new Date(),
    }

    return res(
      ctx.status(200),
      ctx.json({ user: users[index] })
    )
  }),

  // GET /api/user-groups
  rest.get(`${API_BASE_URL}/api/user-groups`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ groups: userGroups })
    )
  }),

  // POST /api/user-groups
  rest.post(`${API_BASE_URL}/api/user-groups`, async (req, res, ctx) => {
    const body = await req.json() as { name: string }

    const newGroup = {
      id: `ugroup-${Date.now()}`,
      name: body.name,
      status: 'active' as const,
      createdAt: new Date(),
      managerIds: [],
      memberIds: [],
    }

    userGroups.push(newGroup)

    return res(
      ctx.status(201),
      ctx.json({ group: newGroup })
    )
  }),

  // PUT /api/user-groups/:id
  rest.put(`${API_BASE_URL}/api/user-groups/:id`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { name: string }

    const index = userGroups.findIndex(g => g.id === id)

    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    userGroups[index] = {
      ...userGroups[index],
      name: body.name,
      updatedAt: new Date(),
    }

    return res(
      ctx.status(200),
      ctx.json({ group: userGroups[index] })
    )
  }),

  // PUT /api/user-groups/:id/status
  rest.put(`${API_BASE_URL}/api/user-groups/:id/status`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { status: 'active' | 'disabled' }

    const index = userGroups.findIndex(g => g.id === id)

    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    userGroups[index] = {
      ...userGroups[index],
      status: body.status,
      updatedAt: new Date(),
    }

    return res(
      ctx.status(200),
      ctx.json({ group: userGroups[index] })
    )
  }),

  // POST /api/user-groups/:id/members
  rest.post(`${API_BASE_URL}/api/user-groups/:id/members`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { userId: string }

    const groupIndex = userGroups.findIndex(g => g.id === id)

    if (groupIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    if (!userGroups[groupIndex].memberIds.includes(body.userId)) {
      userGroups[groupIndex].memberIds.push(body.userId)
    }

    // Add group to user
    const userIndex = users.findIndex(u => u.id === body.userId)
    if (userIndex !== -1 && !users[userIndex].groupIds.includes(id as string)) {
      users[userIndex].groupIds.push(id as string)
    }

    return res(
      ctx.status(200),
      ctx.json({ group: userGroups[groupIndex] })
    )
  }),

  // DELETE /api/user-groups/:groupId/members/:userId
  rest.delete(`${API_BASE_URL}/api/user-groups/:groupId/members/:userId`, (req, res, ctx) => {
    const { groupId, userId } = req.params

    const groupIndex = userGroups.findIndex(g => g.id === groupId)

    if (groupIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    userGroups[groupIndex].memberIds = userGroups[groupIndex].memberIds.filter(
      id => id !== userId
    )

    // Remove group from user
    const userIndex = users.findIndex(u => u.id === userId)
    if (userIndex !== -1) {
      users[userIndex].groupIds = users[userIndex].groupIds.filter(
        gId => gId !== groupId
      )
    }

    return res(
      ctx.status(200),
      ctx.json({ group: userGroups[groupIndex] })
    )
  }),

  // POST /api/user-groups/:id/managers
  rest.post(`${API_BASE_URL}/api/user-groups/:id/managers`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { userId: string }

    const groupIndex = userGroups.findIndex(g => g.id === id)

    if (groupIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    if (!userGroups[groupIndex].managerIds.includes(body.userId)) {
      userGroups[groupIndex].managerIds.push(body.userId)
    }

    // Update user role to manager if not already
    const userIndex = users.findIndex(u => u.id === body.userId)
    if (userIndex !== -1 && users[userIndex].role === 'user') {
      users[userIndex] = {
        ...users[userIndex],
        role: 'manager',
      }
    }

    return res(
      ctx.status(200),
      ctx.json({ group: userGroups[groupIndex] })
    )
  }),

  // DELETE /api/user-groups/:groupId/managers/:userId
  rest.delete(`${API_BASE_URL}/api/user-groups/:groupId/managers/:userId`, (req, res, ctx) => {
    const { groupId, userId } = req.params

    const groupIndex = userGroups.findIndex(g => g.id === groupId)

    if (groupIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    userGroups[groupIndex].managerIds = userGroups[groupIndex].managerIds.filter(
      id => id !== userId
    )

    return res(
      ctx.status(200),
      ctx.json({ group: userGroups[groupIndex] })
    )
  }),

  // POST /api/admin/maintenance
  rest.post(`${API_BASE_URL}/api/admin/maintenance`, async (req, res, ctx) => {
    const body = await req.json() as { enabled: boolean }

    serverConfig = {
      ...serverConfig,
      maintenanceMode: body.enabled,
    }

    return res(
      ctx.status(200),
      ctx.json({ success: true, maintenanceMode: body.enabled })
    )
  }),
]

/**
 * Helper to set maintenance mode
 */
export function setMaintenanceMode(enabled: boolean) {
  serverConfig.maintenanceMode = enabled
}