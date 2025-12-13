/* path: frontend/src/types/browser.ts
   version: 4 */

/**
 * Browser storage keys
 */
export const STORAGE_KEYS = {
  AUTH_TOKEN: "auth_token",
  CURRENT_USER: "current_user",
  CURRENT_CONVERSATION: "current_conversation_id",
  SETTINGS: "user_settings",
} as const;

/**
 * Type-safe localStorage wrapper
 */
export interface Storage {
  get: (key: string) => string | null;
  set: (key: string, value: string) => void;
  remove: (key: string) => void;
  clear: () => void;
}

/**
 * Browser API extensions
 */
declare global {
  interface Window {
    msw?: {
      worker?: {
        start: () => Promise<void>;
        stop: () => void;
      };
    };
  }
}
