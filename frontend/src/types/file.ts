/* path: frontend/src/types/file.ts
   version: 1 */

/**
 * File status during upload process
 */
export type FileStatus = "pending" | "uploading" | "completed" | "error";

/**
 * Pending file (during upload)
 */
export interface PendingFile {
  id: string;
  file: File;
  progress: number; // 0-100
  status: FileStatus;
  error?: string;
}

/**
 * Uploaded file (stored on server)
 */
export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
  status: "completed";
  uploadedAt: string;
}

/**
 * File upload API response
 */
export interface FileUploadResponse {
  file: UploadedFile;
}

/**
 * File list API response
 */
export interface FileListResponse {
  files: UploadedFile[];
}
