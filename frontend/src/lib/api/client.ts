/* path: frontend/src/lib/api/client.ts
   version: 3-FINAL-DEBUG - Real JWT token + 204 handling + DEBUG logs */

import { API_ENDPOINTS, STORAGE_KEYS } from "../utils/constants";

/**
 * Base API client configuration
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;

  try {
    return window.localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
  } catch (error) {
    console.error("Error reading auth token:", error);
    return null;
  }
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
  const token = getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        errorData,
      );
    }

    // Handle 204 No Content - no body to parse
    if (response.status === 204) {
      return undefined as T;
    }

    // Check if response has content before parsing
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await response.json();
    }

    return {} as T;
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
    // ============ DEBUG LOGS ============
    console.log("[DEBUG apiClient.post] Called with:");
    console.log("  endpoint:", endpoint);
    console.log("  data:", data);
    console.log("  typeof data:", typeof data);
    console.log("  data constructor:", data?.constructor?.name);
    console.log(
      "  JSON.stringify(data):",
      data ? JSON.stringify(data) : "undefined",
    );
    console.log("  Length:", data ? JSON.stringify(data).length : 0);
    // ====================================

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

      const token = getAuthToken();
      xhr.open("POST", `${API_BASE_URL}${endpoint}`);
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }
      xhr.send(formData);
    });
  },
};
