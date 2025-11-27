// path: tests/mocks/data/conversations.ts
// version: 4 - Fixed messageCount to match actual messages

export interface MockConversation {
  id: string
  title: string
  groupId: string | null
  createdAt: string
  updatedAt: string
  messageCount: number
  ownerId: string
  sharedWithGroupIds: string[]
  isShared: boolean
}

export interface MockConversationGroup {
  id: string
  name: string
  conversationIds: string[]
  createdAt: string
  updatedAt: string
  ownerId: string
}

export interface MockMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  conversationId: string
}

// Mock messages for conversations
export const mockMessages: Record<string, MockMessage[]> = {
  'conv-1': [
    {
      id: 'msg-1-1',
      role: 'user',
      content: 'Hello, how are you?',
      timestamp: '2024-01-15T10:00:00Z',
      conversationId: 'conv-1',
    },
    {
      id: 'msg-1-2',
      role: 'assistant',
      content: 'Hello! I am doing well, thank you for asking. How can I assist you today?',
      timestamp: '2024-01-15T10:00:05Z',
      conversationId: 'conv-1',
    },
    {
      id: 'msg-1-3',
      role: 'user',
      content: 'I need help with my project.',
      timestamp: '2024-01-15T10:01:00Z',
      conversationId: 'conv-1',
    },
    {
      id: 'msg-1-4',
      role: 'assistant',
      content: 'Of course! I would be happy to help with your project. What specific area would you like assistance with?',
      timestamp: '2024-01-15T10:01:10Z',
      conversationId: 'conv-1',
    },
  ],
  'conv-2': [
    {
      id: 'msg-2-1',
      role: 'user',
      content: 'Can you explain async/await in JavaScript?',
      timestamp: '2024-01-14T09:00:00Z',
      conversationId: 'conv-2',
    },
    {
      id: 'msg-2-2',
      role: 'assistant',
      content: 'Certainly! Async/await is a modern way to handle asynchronous operations in JavaScript. It makes asynchronous code look and behave more like synchronous code.',
      timestamp: '2024-01-14T09:00:10Z',
      conversationId: 'conv-2',
    },
  ],
  'conv-3': [
    {
      id: 'msg-3-1',
      role: 'user',
      content: 'What are the project milestones?',
      timestamp: '2024-01-13T15:00:00Z',
      conversationId: 'conv-3',
    },
    {
      id: 'msg-3-2',
      role: 'assistant',
      content: 'Here are the key project milestones:\n1. Requirements gathering - Week 1\n2. Design phase - Week 2-3\n3. Development - Week 4-8\n4. Testing - Week 9\n5. Deployment - Week 10',
      timestamp: '2024-01-13T15:00:15Z',
      conversationId: 'conv-3',
    },
  ],
  'conv-4': [
    {
      id: 'msg-4-1',
      role: 'user',
      content: 'Remind me to call John tomorrow.',
      timestamp: '2024-01-12T08:00:00Z',
      conversationId: 'conv-4',
    },
    {
      id: 'msg-4-2',
      role: 'assistant',
      content: 'I have noted your reminder to call John tomorrow.',
      timestamp: '2024-01-12T08:00:05Z',
      conversationId: 'conv-4',
    },
  ],
  'conv-5': [
    {
      id: 'msg-5-1',
      role: 'user',
      content: 'Status update on Q1 goals?',
      timestamp: '2024-01-10T10:00:00Z',
      conversationId: 'conv-5',
    },
    {
      id: 'msg-5-2',
      role: 'assistant',
      content: 'Here is the Q1 status:\n- Revenue: 95% of target\n- Customer acquisition: 102% of target\n- Product launches: On track',
      timestamp: '2024-01-10T10:00:20Z',
      conversationId: 'conv-5',
    },
  ],
}

export const mockConversations: MockConversation[] = [
  {
    id: 'conv-1',
    title: 'First Conversation',
    groupId: null,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T14:30:00Z',
    messageCount: 4,
    ownerId: 'user-john-doe',
    sharedWithGroupIds: [],
    isShared: false,
  },
  {
    id: 'conv-2',
    title: 'Work Discussion',
    groupId: 'group-1',
    createdAt: '2024-01-14T09:00:00Z',
    updatedAt: '2024-01-15T11:00:00Z',
    messageCount: 2,
    ownerId: 'user-john-doe',
    sharedWithGroupIds: ['ugroup-1'],
    isShared: true,
  },
  {
    id: 'conv-3',
    title: 'Project Planning',
    groupId: 'group-1',
    createdAt: '2024-01-13T15:00:00Z',
    updatedAt: '2024-01-14T16:00:00Z',
    messageCount: 2,
    ownerId: 'user-john-doe',
    sharedWithGroupIds: [],
    isShared: false,
  },
  {
    id: 'conv-4',
    title: 'Personal Notes',
    groupId: null,
    createdAt: '2024-01-12T08:00:00Z',
    updatedAt: '2024-01-12T08:30:00Z',
    messageCount: 2,
    ownerId: 'user-john-doe',
    sharedWithGroupIds: [],
    isShared: false,
  },
  {
    id: 'conv-5',
    title: 'Manager Chat',
    groupId: 'group-2',
    createdAt: '2024-01-10T10:00:00Z',
    updatedAt: '2024-01-15T09:00:00Z',
    messageCount: 2,
    ownerId: 'user-manager',
    sharedWithGroupIds: ['ugroup-1', 'ugroup-2'],
    isShared: true,
  },
]

export const mockConversationGroups: MockConversationGroup[] = [
  {
    id: 'group-1',
    name: 'Work Projects',
    conversationIds: ['conv-2', 'conv-3'],
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-14T16:00:00Z',
    ownerId: 'user-john-doe',
  },
  {
    id: 'group-2',
    name: 'Team Discussions',
    conversationIds: ['conv-5'],
    createdAt: '2024-01-05T00:00:00Z',
    updatedAt: '2024-01-15T09:00:00Z',
    ownerId: 'user-manager',
  },
]