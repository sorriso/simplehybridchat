/* path: src/lib/hooks/useFileUpload.ts
   version: 2 - Fixed type checking for ALLOWED_FILE_TYPES.includes() */

import { useState, useCallback } from "react";
import { filesApi } from "../api/files";
import type { PendingFile, UploadedFile } from "@/types/file";
import { UI_CONSTANTS } from "../utils/constants";

/**
 * Hook for managing file uploads
 */
export function useFileUpload() {
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  /**
   * Add files to pending list (validation happens here)
   */
  const addFiles = useCallback((files: File[]) => {
    const validFiles: PendingFile[] = [];
    const errors: string[] = [];

    files.forEach((file) => {
      // Check file size
      if (file.size > UI_CONSTANTS.MAX_FILE_SIZE) {
        errors.push(
          `${file.name}: File too large (max ${UI_CONSTANTS.MAX_FILE_SIZE / 1024 / 1024}MB)`,
        );
        return;
      }

      // Check file type
      if (!UI_CONSTANTS.ALLOWED_FILE_TYPES.includes(file.type as any)) {
        errors.push(`${file.name}: File type not allowed`);
        return;
      }

      validFiles.push({
        id: `pending-${Date.now()}-${Math.random()}`,
        file,
        progress: 0,
        status: "pending",
      });
    });

    if (errors.length > 0) {
      console.warn("File validation errors:", errors);
      // In production, show these errors to user via toast/notification
    }

    if (validFiles.length > 0) {
      setPendingFiles((prev) => [...prev, ...validFiles]);
    }

    return { validFiles, errors };
  }, []);

  /**
   * Remove a pending file
   */
  const removePendingFile = useCallback((id: string) => {
    setPendingFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  /**
   * Clear all pending files
   */
  const clearPendingFiles = useCallback(() => {
    setPendingFiles([]);
  }, []);

  /**
   * Upload all pending files
   */
  const uploadFiles = useCallback(async () => {
    if (pendingFiles.length === 0 || isUploading) {
      return;
    }

    setIsUploading(true);

    try {
      // Upload files one by one (could be parallelized)
      for (const pendingFile of pendingFiles) {
        // Update status to uploading
        setPendingFiles((prev) =>
          prev.map((f) =>
            f.id === pendingFile.id
              ? { ...f, status: "uploading", progress: 0 }
              : f,
          ),
        );

        try {
          // Upload with progress tracking
          const uploadedFile = await filesApi.upload(
            pendingFile.file,
            (progress) => {
              setPendingFiles((prev) =>
                prev.map((f) =>
                  f.id === pendingFile.id ? { ...f, progress } : f,
                ),
              );
            },
          );

          // Mark as completed
          setPendingFiles((prev) =>
            prev.map((f) =>
              f.id === pendingFile.id
                ? { ...f, status: "completed", progress: 100 }
                : f,
            ),
          );

          // Add to uploaded files
          setUploadedFiles((prev) => [...prev, uploadedFile]);
        } catch (error) {
          // Mark as error
          setPendingFiles((prev) =>
            prev.map((f) =>
              f.id === pendingFile.id
                ? {
                    ...f,
                    status: "error",
                    error:
                      error instanceof Error ? error.message : "Upload failed",
                  }
                : f,
            ),
          );
        }
      }

      // Remove completed files from pending after a delay
      setTimeout(() => {
        setPendingFiles((prev) => prev.filter((f) => f.status !== "completed"));
      }, 2000);
    } finally {
      setIsUploading(false);
    }
  }, [pendingFiles, isUploading]);

  /**
   * Delete an uploaded file
   */
  const deleteUploadedFile = useCallback(async (fileId: string) => {
    try {
      await filesApi.delete(fileId);
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch (error) {
      console.error("Error deleting file:", error);
      throw error;
    }
  }, []);

  return {
    // State
    pendingFiles,
    uploadedFiles,
    isUploading,

    // Actions
    addFiles,
    removePendingFile,
    clearPendingFiles,
    uploadFiles,
    deleteUploadedFile,
  };
}
