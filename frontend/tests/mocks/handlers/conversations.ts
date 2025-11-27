// path: tests/mocks/handlers/conversations.ts
// version: 7 - Dynamic messageCount calculation from actual messages

import { rest } from 'msw'
import { mockConversations, mockConversationGroups, mockMessages } from '../data/conversations'

// API base URL used by apiClient
const API_BASE_URL = 'http://localhost:8000'

// In-memory storage
let conversations = [...mockConversations]
let conversationGroups = [...mockConversationGroups]

/**
 * Reset handler state (call in afterEach)
 */
export function resetConversationsState() {
  conversations = [...mockConversations]
  conversationGroups = [...mockConversationGroups]
}

/**
 * Conversations API handlers - MSW v1 syntax with full URLs
 */
export const conversationsHandlers = [
  // GET /api/conversations
  rest.get(`${API_BASE_URL}/api/conversations`, (req, res, ctx) => {
    // Calculate messageCount dynamically from mockMessages
    const conversationsWithCount = conversations.map(conv => ({
      ...conv,
      messageCount: mockMessages[conv.id]?.length || 0
    }))
    
    return res(
      ctx.status(200),
      ctx.json({ conversations: conversationsWithCount })
    )
  }),

  // POST /api/conversations
  rest.post(`${API_BASE_URL}/api/conversations`, async (req, res, ctx) => {
    const body = await req.json() as { title?: string; groupId?: string }
    
    const newConversation = {
      id: `conv-${Date.now()}`,
      title: body.title || 'New Conversation',
      groupId: body.groupId || null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messageCount: 0,
      ownerId: 'user-john-doe',
      sharedWithGroupIds: [],
      isShared: false,
    }

    conversations.unshift(newConversation)

    // Add to group if specified
    if (body.groupId) {
      const group = conversationGroups.find(g => g.id === body.groupId)
      if (group) {
        group.conversationIds.push(newConversation.id)
      }
    }

    return res(
      ctx.status(201),
      ctx.json({ conversation: newConversation })
    )
  }),

  // GET /api/conversations/:id
  rest.get(`${API_BASE_URL}/api/conversations/:id`, (req, res, ctx) => {
    const { id } = req.params
    const conversation = conversations.find(c => c.id === id)
    
    if (!conversation) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Conversation not found' })
      )
    }

    // Calculate messageCount dynamically
    const conversationWithCount = {
      ...conversation,
      messageCount: mockMessages[id as string]?.length || 0
    }

    return res(
      ctx.status(200),
      ctx.json({ conversation: conversationWithCount })
    )
  }),

  // GET /api/conversations/:id/messages
  rest.get(`${API_BASE_URL}/api/conversations/:id/messages`, (req, res, ctx) => {
    const { id } = req.params
    const conversation = conversations.find(c => c.id === id)
    
    if (!conversation) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Conversation not found' })
      )
    }

    // Return messages for this conversation
    const messages = mockMessages[id as string] || []
    console.log(`[MSW] Returning ${messages.length} messages for conversation ${id}`)
    
    return res(
      ctx.status(200),
      ctx.json({ messages })
    )
  }),

  // PUT /api/conversations/:id
  rest.put(`${API_BASE_URL}/api/conversations/:id`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { title?: string; groupId?: string | null }
    
    const index = conversations.findIndex(c => c.id === id)
    
    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Conversation not found' })
      )
    }

    const oldGroupId = conversations[index].groupId
    const newGroupId = body.groupId

    // Update conversation
    conversations[index] = {
      ...conversations[index],
      ...body,
      updatedAt: new Date().toISOString(),
    }

    // Update group conversationIds if groupId changed
    if (oldGroupId !== newGroupId) {
      // Remove from old group
      if (oldGroupId) {
        const oldGroup = conversationGroups.find(g => g.id === oldGroupId)
        if (oldGroup) {
          oldGroup.conversationIds = oldGroup.conversationIds.filter(cId => cId !== id)
          console.log(`[MSW] Removed conversation ${id} from group ${oldGroupId}`)
        }
      }

      // Add to new group
      if (newGroupId) {
        const newGroup = conversationGroups.find(g => g.id === newGroupId)
        if (newGroup && !newGroup.conversationIds.includes(id as string)) {
          newGroup.conversationIds.push(id as string)
          console.log(`[MSW] Added conversation ${id} to group ${newGroupId}`)
        }
      }
    }

    // Return with dynamically calculated messageCount
    const conversationWithCount = {
      ...conversations[index],
      messageCount: mockMessages[id as string]?.length || 0
    }

    return res(
      ctx.status(200),
      ctx.json({ conversation: conversationWithCount })
    )
  }),

  // DELETE /api/conversations/:id
  rest.delete(`${API_BASE_URL}/api/conversations/:id`, (req, res, ctx) => {
    const { id } = req.params
    const index = conversations.findIndex(c => c.id === id)
    
    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Conversation not found' })
      )
    }

    // Remove from groups
    conversationGroups.forEach(group => {
      const convIndex = group.conversationIds.indexOf(id as string)
      if (convIndex !== -1) {
        group.conversationIds.splice(convIndex, 1)
      }
    })

    conversations.splice(index, 1)

    return res(
      ctx.status(200),
      ctx.json({ success: true })
    )
  }),

  // POST /api/conversations/:id/share
  rest.post(`${API_BASE_URL}/api/conversations/:id/share`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { groupIds: string[] }
    
    const conversation = conversations.find(c => c.id === id)
    
    if (!conversation) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Conversation not found' })
      )
    }

    conversation.sharedWithGroupIds = body.groupIds
    conversation.isShared = body.groupIds.length > 0

    return res(
      ctx.status(200),
      ctx.json({ conversation })
    )
  }),

  // GET /api/groups (main endpoint used by frontend)
  rest.get(`${API_BASE_URL}/api/groups`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ groups: conversationGroups })
    )
  }),

  // POST /api/groups
  rest.post(`${API_BASE_URL}/api/groups`, async (req, res, ctx) => {
    const body = await req.json() as { name: string }
    
    const newGroup = {
      id: `group-${Date.now()}`,
      name: body.name,
      conversationIds: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      ownerId: 'user-john-doe',
    }

    conversationGroups.push(newGroup)

    return res(
      ctx.status(201),
      ctx.json({ group: newGroup })
    )
  }),

  // GET /api/groups/:id
  rest.get(`${API_BASE_URL}/api/groups/:id`, (req, res, ctx) => {
    const { id } = req.params
    const group = conversationGroups.find(g => g.id === id)
    
    if (!group) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    return res(
      ctx.status(200),
      ctx.json({ group })
    )
  }),

  // PUT /api/groups/:id
  rest.put(`${API_BASE_URL}/api/groups/:id`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { name: string }
    
    const index = conversationGroups.findIndex(g => g.id === id)
    
    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    conversationGroups[index] = {
      ...conversationGroups[index],
      name: body.name,
      updatedAt: new Date().toISOString(),
    }

    return res(
      ctx.status(200),
      ctx.json({ group: conversationGroups[index] })
    )
  }),

  // DELETE /api/groups/:id
  rest.delete(`${API_BASE_URL}/api/groups/:id`, (req, res, ctx) => {
    const { id } = req.params
    const index = conversationGroups.findIndex(g => g.id === id)
    
    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    // Move conversations out of group
    const group = conversationGroups[index]
    group.conversationIds.forEach(convId => {
      const conversation = conversations.find(c => c.id === convId)
      if (conversation) {
        conversation.groupId = null
      }
    })

    conversationGroups.splice(index, 1)

    return res(
      ctx.status(200),
      ctx.json({ success: true })
    )
  }),

  // POST /api/groups/:id/conversations
  rest.post(`${API_BASE_URL}/api/groups/:id/conversations`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { conversationId: string }
    
    const groupIndex = conversationGroups.findIndex(g => g.id === id)
    
    if (groupIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    if (!conversationGroups[groupIndex].conversationIds.includes(body.conversationId)) {
      conversationGroups[groupIndex].conversationIds.push(body.conversationId)
    }

    // Update conversation groupId
    const conversation = conversations.find(c => c.id === body.conversationId)
    if (conversation) {
      conversation.groupId = id as string
    }

    return res(
      ctx.status(200),
      ctx.json({ group: conversationGroups[groupIndex] })
    )
  }),

  // DELETE /api/groups/:groupId/conversations/:conversationId
  rest.delete(`${API_BASE_URL}/api/groups/:groupId/conversations/:conversationId`, (req, res, ctx) => {
    const { groupId, conversationId } = req.params
    
    const groupIndex = conversationGroups.findIndex(g => g.id === groupId)
    
    if (groupIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    conversationGroups[groupIndex].conversationIds = conversationGroups[groupIndex].conversationIds.filter(
      id => id !== conversationId
    )

    // Remove groupId from conversation
    const conversation = conversations.find(c => c.id === conversationId)
    if (conversation) {
      conversation.groupId = null
    }

    return res(
      ctx.status(200),
      ctx.json({ group: conversationGroups[groupIndex] })
    )
  }),

  // Legacy: GET /api/conversation-groups
  rest.get(`${API_BASE_URL}/api/conversation-groups`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ groups: conversationGroups })
    )
  }),

  // Legacy: POST /api/conversation-groups
  rest.post(`${API_BASE_URL}/api/conversation-groups`, async (req, res, ctx) => {
    const body = await req.json() as { name: string }
    
    const newGroup = {
      id: `group-${Date.now()}`,
      name: body.name,
      conversationIds: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      ownerId: 'user-john-doe',
    }

    conversationGroups.push(newGroup)

    return res(
      ctx.status(201),
      ctx.json({ group: newGroup })
    )
  }),

  // Legacy: PUT /api/conversation-groups/:id
  rest.put(`${API_BASE_URL}/api/conversation-groups/:id`, async (req, res, ctx) => {
    const { id } = req.params
    const body = await req.json() as { name: string }
    
    const index = conversationGroups.findIndex(g => g.id === id)
    
    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    conversationGroups[index] = {
      ...conversationGroups[index],
      name: body.name,
      updatedAt: new Date().toISOString(),
    }

    return res(
      ctx.status(200),
      ctx.json({ group: conversationGroups[index] })
    )
  }),

  // Legacy: DELETE /api/conversation-groups/:id
  rest.delete(`${API_BASE_URL}/api/conversation-groups/:id`, (req, res, ctx) => {
    const { id } = req.params
    const index = conversationGroups.findIndex(g => g.id === id)
    
    if (index === -1) {
      return res(
        ctx.status(404),
        ctx.json({ error: 'Group not found' })
      )
    }

    // Move conversations out of group
    const group = conversationGroups[index]
    group.conversationIds.forEach(convId => {
      const conversation = conversations.find(c => c.id === convId)
      if (conversation) {
        conversation.groupId = null
      }
    })

    conversationGroups.splice(index, 1)

    return res(
      ctx.status(200),
      ctx.json({ success: true })
    )
  }),
]