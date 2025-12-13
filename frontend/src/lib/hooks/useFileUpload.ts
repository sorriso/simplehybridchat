/* path: frontend/src/lib/hooks/useFileUpload.ts
   version: 4 - FIXED: Added deleteUploadedFile method
   
   Changes in v4:
   - ADDED: deleteUploadedFile() to delete file from server and state
   - Reason: FileUploadPanel requires this method
   
   Changes in v3:
   - FIXED: Type-safe file type validation with ALLOWED_FILE_TYPES */

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

      // Check file type - cast to readonly array for type-safe includes
      const allowedTypes = UI_CONSTANTS.ALLOWED_FILE_TYPES as readonly string[];
      if (!allowedTypes.includes(file.type)) {
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
      for (const pendingFile of pendingFiles) {
        setPendingFiles((prev) =>
          prev.map((f) =>
            f.id === pendingFile.id
              ? { ...f, status: "uploading", progress: 0 }
              : f,
          ),
        );

        try {
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

          setPendingFiles((prev) =>
            prev.filter((f) => f.id !== pendingFile.id),
          );
          setUploadedFiles((prev) => [...prev, uploadedFile]);
        } catch (error) {
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
    } finally {
      setIsUploading(false);
    }
  }, [pendingFiles, isUploading]);

  /**
   * Clear uploaded files
   */
  const clearUploadedFiles = useCallback(() => {
    setUploadedFiles([]);
  }, []);

  /**
   * Delete an uploaded file from server
   */
  const deleteUploadedFile = useCallback(async (fileId: string) => {
    try {
      await filesApi.delete(fileId);
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch (error) {
      console.error("Failed to delete file:", error);
      throw error;
    }
  }, []);

  return {
    pendingFiles,
    uploadedFiles,
    isUploading,
    addFiles,
    removePendingFile,
    clearPendingFiles,
    uploadFiles,
    clearUploadedFiles,
    deleteUploadedFile,
  };
}
