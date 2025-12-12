/* path: frontend/src/lib/utils/constants.ts
   version: 6
   
   Changes in v6:
   - ADDED: FILES_LIST endpoint for listing files
   - Reason: Build error - FILES_LIST was referenced but not defined
   
   Changes in v5:
   - ADDED: FILES_UPLOAD endpoint for file upload API
   - Reason: Build error - FILES_UPLOAD was referenced but not defined
*/

export const API_ENDPOINTS = {
  AUTH_LOGIN: "/api/auth/login",
  AUTH_LOGOUT: "/api/auth/logout",
  AUTH_VERIFY: "/api/auth/verify",
  AUTH_CONFIG: "/api/auth/config",
  CONVERSATIONS: "/api/conversations",
  CONVERSATION_BY_ID: (id: string) => `/api/conversations/${id}`,
  GROUPS: "/api/groups",
  GROUP_BY_ID: (id: string) => `/api/groups/${id}`,
  SETTINGS: "/api/settings",
  FILES: "/api/files",
  FILES_UPLOAD: "/api/files/upload",
  FILES_LIST: "/api/files",
  FILE_BY_ID: (id: string) => `/api/files/${id}`,
  USERS: "/api/admin/users",
  USER_BY_ID: (id: string) => `/api/admin/users/${id}`,
  USER_GROUPS: "/api/admin/groups",
  USER_GROUP_BY_ID: (id: string) => `/api/admin/groups/${id}`,
  CHAT_STREAM: "/api/chat/stream",
} as const;

export const STORAGE_KEYS = {
  AUTH_TOKEN: "auth_token",
  CURRENT_USER: "current_user",
  CURRENT_CONVERSATION: "current_conversation_id",
  SETTINGS: "user_settings",
} as const;

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