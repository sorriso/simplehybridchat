// path: tests/mocks/handlers/files.ts
// version: 3 - Fixed URL matching for apiClient with base URL

import { rest } from 'msw'
import { mockFiles } from '../data/files'

// API base URL used by apiClient
const API_BASE_URL = 'http://localhost:8000'

// In-memory storage
let files = [...mockFiles]

/**
 * Reset handler state (call in afterEach)
 */
export function resetFilesState() {
  files = [...mockFiles]
}

/**
 * Files API handlers - MSW v1 syntax with full URLs
 */
export const filesHandlers = [
  // GET /api/files
  rest.get(`${API_BASE_URL}/api/files`, (req, res, ctx) => {
    const conversationId = req.url.searchParams.get('conversationId')
    
    let filteredFiles = files
    if (conversationId) {
      filteredFiles = files.filter(f => f.conversationId === conversationId)
    }

    return res(
      ctx.status(200),
      ctx.json({ files: filteredFiles })
    )
  }),

  // POST /api/files/upload
  rest.post(`${API_BASE_URL}/api/files/upload`, async (req, res, ctx) => {
    // In real implementation, would handle multipart form data
    // For mocks, we simulate the response
    
    const newFile = {
      id: `file-${Date.now()}`,
      name: 'uploaded-file.pdf',
      size: 1024,
      mimeType: 'application/pdf',
      url: `/uploads/file-${Date.now()}.pdf`,
      uploadedAt: new Date().toISOString(),
      status: 'completed' as const,
      userId: 'user-john-doe',
      conversationId: null,
    }

    files.push(newFile)

    return res(
      ctx.status(201),
      ctx.json({ file: newFile })
    )
  }),

  // GET /api/files/:id
  rest.get(`${API_BASE_URL}/api/files/:id`, (req, res, ctx) => {
    const { id } = req.params
    const file = files.find(f => f.id === id)
    
    if (!file) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'File not found' })
      )
    }

    return res(
      ctx.status(200),
      ctx.json({ file })
    )
  }),

  // DELETE /api/files/:id
  rest.delete(`${API_BASE_URL}/api/files/:id`, (req, res, ctx) => {
    const { id } = req.params
    const index = files.findIndex(f => f.id === id)
    
    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'File not found' })
      )
    }

    files.splice(index, 1)

    return res(
      ctx.status(200),
      ctx.json({ success: true })
    )
  }),

  // POST /api/files/:id/attach
  rest.post(`${API_BASE_URL}/api/files/:id/attach`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { conversationId: string }
    
    const file = files.find(f => f.id === id)
    
    if (!file) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'File not found' })
      )
    }

    file.conversationId = body.conversationId

    return res(
      ctx.status(200),
      ctx.json({ file })
    )
  }),

  // POST /api/files/:id/detach
  rest.post(`${API_BASE_URL}/api/files/:id/detach`, (req, res, ctx) => {
    const { id } = req.params
    const file = files.find(f => f.id === id)
    
    if (!file) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'File not found' })
      )
    }

    file.conversationId = null

    return res(
      ctx.status(200),
      ctx.json({ file })
    )
  }),
]