/* path: src/types/file.ts
   version: 1 */

/**
 * Uploaded file type
 */
export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  mimeType: string;
  url: string;
  uploadedAt: Date;
  status: "pending" | "processing" | "completed" | "error";
  userId: string;
}

export interface FileUploadRequest {
  file: File;
}

export interface FileUploadResponse {
  file: UploadedFile;
  message: string;
}

export interface FileUploadProgress {
  fileId: string;
  progress: number; // 0-100
  status: "uploading" | "processing" | "completed" | "error";
}

// Client-side file representation before upload
export interface PendingFile {
  id: string; // temporary client-side ID
  file: File;
  progress: number;
  status: "pending" | "uploading" | "completed" | "error";
  error?: string;
}
