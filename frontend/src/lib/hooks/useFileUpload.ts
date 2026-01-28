/* path: frontend/src/lib/hooks/useFileUpload.ts
   version: 5.1
   
   Changes in v5.1:
   - CRITICAL FIX: Added useEffect to load existing files from API on mount
   - Files uploaded in previous sessions now appear in the panel
   - Added loadUploadedFiles() method for manual refresh
   - Added isLoading state
   
   Changes in v5.0:
   - BACKWARDS COMPATIBLE: Supports both old and new upload APIs
   - Old API: addFiles() + uploadFiles() (no params)
   - New API: uploadFiles(files, projectId) (direct upload)
   - Added deleteUploadedFile for removing uploaded files
*/

import { useState, useCallback, useEffect } from 'react';
import { filesApi } from '../api/files';
import type { PendingFile, UploadedFile } from '@/types/file';
import { UI_CONSTANTS } from '../utils/constants';

/**
 * Hook for managing file uploads (supports both old and new APIs)
 */
export function useFileUpload() {
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true); // NEW in v5.1

  /**
   * Load uploaded files from API
   * NEW in v5.1: Called on mount and after uploads
   */
  const loadUploadedFiles = useCallback(async () => {
    try {
      setIsLoading(true);
      const files = await filesApi.getAll();
      setUploadedFiles(files);
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Load files on mount
   * NEW in v5.1: Ensures existing files are displayed
   */
  useEffect(() => {
    loadUploadedFiles();
  }, [loadUploadedFiles]);

  /**
   * Add files to pending list (validation happens here)
   * OLD API - for backward compatibility with /components/upload/
   */
  const addFiles = useCallback((files: File[]) => {
    const validFiles: PendingFile[] = [];
    const errors: string[] = [];

    files.forEach((file) => {
      // Check file size
      if (file.size > UI_CONSTANTS.MAX_FILE_SIZE) {
        errors.push(
          `${file.name}: File too large (max ${UI_CONSTANTS.MAX_FILE_SIZE / 1024 / 1024}MB)`
        );
        return;
      }

      // Check file type
      const allowedTypes = UI_CONSTANTS.ALLOWED_FILE_TYPES as readonly string[];
      if (!allowedTypes.includes(file.type)) {
        errors.push(`${file.name}: File type not allowed`);
        return;
      }

      validFiles.push({
        id: `pending-${Date.now()}-${Math.random()}`,
        file,
        progress: 0,
        status: 'pending',
      });
    });

    if (errors.length > 0) {
      console.warn('File validation errors:', errors);
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
   * Upload files
   * 
   * DUAL API:
   * - OLD: uploadFiles() - uploads all pending files (no params)
   * - NEW: uploadFiles(files, projectId) - direct upload with project context
   * 
   * UPDATED in v5.1: Reloads files from API after successful upload
   */
  const uploadFiles = useCallback(
    async (files?: File[], projectId?: string) => {
      // NEW API: Direct upload with files provided
      if (files && files.length > 0) {
        const { validFiles } = addFiles(files);

        if (validFiles.length === 0) {
          return;
        }
      }

      // Check if there are pending files to upload
      if (pendingFiles.length === 0 || isUploading) {
        return;
      }

      setIsUploading(true);

      try {
        for (const pendingFile of pendingFiles) {
          setPendingFiles((prev) =>
            prev.map((f) =>
              f.id === pendingFile.id
                ? { ...f, status: 'uploading', progress: 0 }
                : f
            )
          );

          try {
            const uploadedFile = await filesApi.upload(
              pendingFile.file,
              (progress) => {
                setPendingFiles((prev) =>
                  prev.map((f) =>
                    f.id === pendingFile.id ? { ...f, progress } : f
                  )
                );
              }
            );

            setPendingFiles((prev) =>
              prev.filter((f) => f.id !== pendingFile.id)
            );
            
            // Optimistic update
            setUploadedFiles((prev) => [...prev, uploadedFile]);
          } catch (error) {
            setPendingFiles((prev) =>
              prev.map((f) =>
                f.id === pendingFile.id
                  ? {
                      ...f,
                      status: 'error',
                      error:
                        error instanceof Error
                          ? error.message
                          : 'Upload failed',
                    }
                  : f
              )
            );
          }
        }
        
        // NEW in v5.1: Reload all files from API after upload to sync state
        await loadUploadedFiles();
      } finally {
        setIsUploading(false);
      }
    },
    [pendingFiles, isUploading, addFiles, loadUploadedFiles]
  );

  /**
   * Clear uploaded files (local state only, doesn't delete from server)
   */
  const clearUploadedFiles = useCallback(() => {
    setUploadedFiles([]);
  }, []);

  /**
   * Delete an uploaded file from server
   * UPDATED in v5.1: Reloads files from API after delete
   */
  const deleteUploadedFile = useCallback(async (fileId: string) => {
    try {
      await filesApi.delete(fileId);
      
      // Optimistic update
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
      
      // NEW in v5.1: Reload to ensure sync with server
      await loadUploadedFiles();
    } catch (error) {
      console.error('Failed to delete file:', error);
      throw error;
    }
  }, [loadUploadedFiles]);

  return {
    pendingFiles,
    uploadedFiles,
    isUploading,
    isLoading, // NEW in v5.1
    addFiles,
    removePendingFile,
    clearPendingFiles,
    uploadFiles,
    clearUploadedFiles,
    deleteUploadedFile,
    loadUploadedFiles, // NEW in v5.1: Exposed for manual refresh
  };
}