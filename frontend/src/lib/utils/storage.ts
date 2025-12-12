/* path: frontend/src/lib/utils/storage.ts
   version: 3 */

   import { STORAGE_KEYS } from "./constants";

   /**
    * Safe localStorage wrapper with type support and error handling
    */
   export const storage = {
     /**
      * Get item from localStorage
      * @param {string} key - The key to get
      * @returns {T | null} The item or null if not found
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
      * @param {string} key - The key to set
      * @param {T} value - The value to set
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
      * @param {string} key - The key to remove
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
      * @returns {void}
      */
     clear: (): void => {
       if (typeof window === "undefined") return;
   
       try {
         window.localStorage.clear();
       } catch (error) {
         console.error("Error clearing localStorage:", error);
       }
     },
   
     // ========================================================================
     // Authentication-specific methods
     // ========================================================================
   
     /**
      * Get authentication token from localStorage
      * @returns {string | null} The auth token or null if not found
      */
     getAuthToken: (): string | null => {
       if (typeof window === "undefined") return null;
   
       try {
         return window.localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
       } catch (error) {
         console.error("Error reading auth token:", error);
         return null;
       }
     },
   
     /**
      * Set authentication token in localStorage
      * @param {string} token - The auth token to store
      */
     setAuthToken: (token: string): void => {
       if (typeof window === "undefined") return;
   
       try {
         window.localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
       } catch (error) {
         console.error("Error setting auth token:", error);
       }
     },
   
     /**
      * Clear authentication token from localStorage
      */
     clearAuthToken: (): void => {
       if (typeof window === "undefined") return;
   
       try {
         window.localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
       } catch (error) {
         console.error("Error clearing auth token:", error);
       }
     },
   
     // ========================================================================
     // v3.0: Compatibility aliases for useAuth hook
     // ========================================================================
   
     /**
      * Get token (alias for getAuthToken)
      * @returns {string | null} The auth token or null if not found
      */
     getToken: (): string | null => {
       return storage.getAuthToken();
     },
   
     /**
      * Set token (alias for setAuthToken)
      * @param {string} token - The auth token to store
      */
     setToken: (token: string): void => {
       storage.setAuthToken(token);
     },
   
     /**
      * Remove token (alias for clearAuthToken)
      */
     removeToken: (): void => {
       storage.clearAuthToken();
     },
   };