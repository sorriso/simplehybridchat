// path: tests/mocks/handlers/settings.ts
// version: 3 - Fixed updatedAt type: Date instead of string (toISOString)

import { rest } from 'msw'
import { mockSettings } from '../data/settings'

// API base URL used by apiClient
const API_BASE_URL = 'http://localhost:8000'

// In-memory storage
let settings = { ...mockSettings }

/**
 * Reset handler state (call in afterEach)
 */
export function resetSettingsState() {
  settings = { ...mockSettings }
}

/**
 * Settings API handlers - MSW v1 syntax with full URLs
 */
export const settingsHandlers = [
  // GET /api/settings
  rest.get(`${API_BASE_URL}/api/settings`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json(settings)
    )
  }),

  // PUT /api/settings
  rest.put(`${API_BASE_URL}/api/settings`, async (req, res, ctx) => {
    const body = await req.json() as Partial<typeof settings>

    settings = {
      ...settings,
      ...body,
      updatedAt: new Date(),
    }

    return res(
      ctx.status(200),
      ctx.json(settings)
    )
  }),

  // POST /api/settings/reset
  rest.post(`${API_BASE_URL}/api/settings/reset`, (req, res, ctx) => {
    settings = { ...mockSettings }

    return res(
      ctx.status(200),
      ctx.json(settings)
    )
  }),
]