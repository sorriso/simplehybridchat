/* path: frontend/src/lib/api/client.ts
   version: 2 */

   import { storage } from "../utils/storage";

   /**
    * Base API client configuration
    */
   const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
   
   /**
    * Routes that don't require authentication
    */
   const PUBLIC_ROUTES = [
     "/api/auth/config",
     "/api/auth/login",
     "/api/auth/register",
     "/api/auth/generic",
     "/api/auth/sso/verify",
   ];
   
   /**
    * Check if route is public (no auth required)
    */
   function isPublicRoute(endpoint: string): boolean {
     return PUBLIC_ROUTES.some(route => endpoint.startsWith(route));
   }
   
   /**
    * Get authentication token from storage
    */
   function getAuthToken(): string | null {
     return storage.getAuthToken();
   }
   
   /**
    * Custom error class for API errors
    */
   export class ApiError extends Error {
     constructor(
       public status: number,
       message: string,
       public data?: any,
     ) {
       super(message);
       this.name = "ApiError";
     }
   }
   
   /**
    * Generic API request function with error handling
    */
   async function apiRequest<T>(
     endpoint: string,
     options: RequestInit = {},
   ): Promise<T> {
     const url = `${API_BASE_URL}${endpoint}`;
   
     // Build headers
     const headers: HeadersInit = {
       "Content-Type": "application/json",
       ...options.headers,
     };
   
     // Add Authorization header for protected routes only
     if (!isPublicRoute(endpoint)) {
       const token = getAuthToken();
       if (token) {
         headers.Authorization = `Bearer ${token}`;
       }
     }
   
     try {
       const response = await fetch(url, {
         ...options,
         headers,
       });
   
       if (!response.ok) {
         const errorData = await response.json().catch(() => ({}));
         throw new ApiError(
           response.status,
           errorData.message || errorData.error || `HTTP ${response.status}: ${response.statusText}`,
           errorData,
         );
       }
   
       return await response.json();
     } catch (error) {
       if (error instanceof ApiError) {
         throw error;
       }
       throw new ApiError(0, "Network error or server unreachable");
     }
   }
   
   /**
    * API client methods
    */
   export const apiClient = {
     /**
      * GET request
      */
     get: <T>(endpoint: string, options?: RequestInit): Promise<T> => {
       return apiRequest<T>(endpoint, {
         ...options,
         method: "GET",
       });
     },
   
     /**
      * POST request
      */
     post: <T>(
       endpoint: string,
       data?: any,
       options?: RequestInit,
     ): Promise<T> => {
       return apiRequest<T>(endpoint, {
         ...options,
         method: "POST",
         body: data ? JSON.stringify(data) : undefined,
       });
     },
   
     /**
      * PUT request
      */
     put: <T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> => {
       return apiRequest<T>(endpoint, {
         ...options,
         method: "PUT",
         body: data ? JSON.stringify(data) : undefined,
       });
     },
   
     /**
      * DELETE request
      */
     delete: <T>(endpoint: string, options?: RequestInit): Promise<T> => {
       return apiRequest<T>(endpoint, {
         ...options,
         method: "DELETE",
       });
     },
   
     /**
      * Upload file with progress tracking
      */
     uploadFile: async (
       endpoint: string,
       file: File,
       onProgress?: (progress: number) => void,
     ): Promise<any> => {
       return new Promise((resolve, reject) => {
         const xhr = new XMLHttpRequest();
         const formData = new FormData();
         formData.append("file", file);
   
         // Track upload progress
         if (onProgress) {
           xhr.upload.addEventListener("progress", (e) => {
             if (e.lengthComputable) {
               const progress = (e.loaded / e.total) * 100;
               onProgress(progress);
             }
           });
         }
   
         xhr.addEventListener("load", () => {
           if (xhr.status >= 200 && xhr.status < 300) {
             try {
               const response = JSON.parse(xhr.responseText);
               resolve(response);
             } catch (error) {
               reject(new Error("Invalid JSON response"));
             }
           } else {
             reject(new ApiError(xhr.status, `Upload failed: ${xhr.statusText}`));
           }
         });
   
         xhr.addEventListener("error", () => {
           reject(new ApiError(0, "Network error during upload"));
         });
   
         xhr.open("POST", `${API_BASE_URL}${endpoint}`);
         
         // Add auth token for uploads
         const token = getAuthToken();
         if (token) {
           xhr.setRequestHeader("Authorization", `Bearer ${token}`);
         }
         
         xhr.send(formData);
       });
     },
   };