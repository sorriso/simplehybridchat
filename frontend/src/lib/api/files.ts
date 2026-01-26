/* path: frontend/src/lib/api/files.ts
   version: 4 - FIXED: Use FILES_UPLOAD endpoint for upload operation */

   import { apiClient } from "./client";
   import { API_ENDPOINTS } from "../utils/constants";
   import type { UploadedFile, FileUploadResponse } from "@/types/file";
   
   /**
    * API functions for file management
    */
   export const filesApi = {
     /**
      * Upload a single file
      */
     upload: async (
       file: File,
       onProgress?: (progress: number) => void,
     ): Promise<UploadedFile> => {
       const response = (await apiClient.uploadFile(
         API_ENDPOINTS.FILES_UPLOAD,
         file,
         onProgress,
       )) as FileUploadResponse;
   
       return response.file;
     },
   
     /**
      * Upload multiple files
      */
     uploadMultiple: async (
       files: File[],
       onProgress?: (fileId: string, progress: number) => void,
     ): Promise<UploadedFile[]> => {
       const uploadPromises = files.map((file) => {
         return filesApi.upload(file, (progress) => {
           if (onProgress) {
             onProgress(file.name, progress);
           }
         });
       });
   
       return Promise.all(uploadPromises);
     },
   
     /**
      * Get all uploaded files for the current user
      */
     getAll: async (): Promise<UploadedFile[]> => {
       const response = await apiClient.get<{ files: UploadedFile[] }>(
         API_ENDPOINTS.FILES,
       );
       return response.files;
     },
   
     /**
      * Delete a file
      */
     delete: async (fileId: string): Promise<void> => {
       await apiClient.delete(API_ENDPOINTS.FILE_BY_ID(fileId));
     },
   };