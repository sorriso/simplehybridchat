/* path: frontend/src/lib/utils/storage.ts
   version: 3 */

import { STORAGE_KEYS } from "./constants";

/**
 * Safe localStorage wrapper with type support and error handling
 */
export const storage = {
  /**
   * Get item from localStorage
   */
  get: <T>(key: string): T | null => {
    if (typeof window === "undefined") return null;

    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return null;
    }
  },

  /**
   * Set item in localStorage
   */
  set: <T>(key: string, value: T): void => {
    if (typeof window === "undefined") return;

    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  },

  /**
   * Remove item from localStorage
   */
  remove: (key: string): void => {
    if (typeof window === "undefined") return;

    try {
      window.localStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  },

  /**
   * Clear all items from localStorage
   */
  clear: (): void => {
    if (typeof window === "undefined") return;

    try {
      window.localStorage.clear();
    } catch (error) {
      console.error("Error clearing localStorage:", error);
    }
  },

  // Authentication-specific methods
  getAuthToken: (): string | null => {
    if (typeof window === "undefined") return null;

    try {
      return window.localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    } catch (error) {
      console.error("Error reading auth token:", error);
      return null;
    }
  },

  setAuthToken: (token: string): void => {
    if (typeof window === "undefined") return;

    try {
      window.localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
    } catch (error) {
      console.error("Error setting auth token:", error);
    }
  },

  clearAuthToken: (): void => {
    if (typeof window === "undefined") return;

    try {
      window.localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    } catch (error) {
      console.error("Error clearing auth token:", error);
    }
  },

  // Compatibility aliases
  getToken: (): string | null => {
    return storage.getAuthToken();
  },

  setToken: (token: string): void => {
    storage.setAuthToken(token);
  },

  removeToken: (): void => {
    storage.clearAuthToken();
  },
};
