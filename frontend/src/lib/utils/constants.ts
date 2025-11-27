/* path: src/lib/utils/constants.ts
   version: 2 */

export const API_ENDPOINTS = {
  // Conversations
  CONVERSATIONS: "/api/conversations",
  CONVERSATION_BY_ID: (id: string) => `/api/conversations/${id}`,

  // Groups
  GROUPS: "/api/groups",
  GROUP_BY_ID: (id: string) => `/api/groups/${id}`,

  // Chat
  CHAT_STREAM: "/api/chat/stream",

  // Files
  FILES_UPLOAD: "/api/files/upload",
  FILES_LIST: "/api/files",

  // Settings
  SETTINGS: "/api/settings",
} as const;

// Local storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: "auth_token",
  CURRENT_CONVERSATION: "current_conversation",
  SIDEBAR_COLLAPSED: "sidebar_collapsed",
} as const;

// UI constants
export const UI_CONSTANTS = {
  SIDEBAR_WIDTH: 280,
  SIDEBAR_WIDTH_COLLAPSED: 0,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_FILE_TYPES: [
    // Documents
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/json",
    "text/markdown",
    // Images
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
  ],
  MAX_FILES_PER_UPLOAD: 5,
} as const;

// Mock user (for development)
export const MOCK_USER = {
  id: "user-john-doe",
  name: "John Doe",
  email: "john.doe@example.com",
  token: "dev-token-12345",
} as const;
