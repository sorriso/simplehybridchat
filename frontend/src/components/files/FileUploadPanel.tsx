/* path: frontend/src/components/files/FileUploadPanel.tsx
   version: 4.1
   
   Changes in v4.1:
   - FIX: Use correct hook method names (clearUploadedFiles instead of clearAllFiles)
   - FIX: handleRemoveUploaded is now a no-op (files already on server)
   
   Changes in v4.0:
   - Added projectId prop for contextual upload
   - Passes projectId to useFileUpload hook
   - Shows project context in UI
*/

'use client';

import { X, Upload, AlertCircle } from 'lucide-react';
import { FileDropzone } from './FileDropzone';
import { FileList } from './FileList';
import { useFileUpload } from '@/lib/hooks/useFileUpload';

interface FileUploadPanelProps {
  isOpen: boolean;
  onClose: () => void;
  projectId?: string;
  projectName?: string;
  onUploadComplete?: () => void;
}

export function FileUploadPanel({
  isOpen,
  onClose,
  projectId,
  projectName,
  onUploadComplete,
}: FileUploadPanelProps) {
  const {
    pendingFiles,
    uploadedFiles,
    isUploading,
    uploadFiles,
    removePendingFile,
    clearPendingFiles,
    clearUploadedFiles,
  } = useFileUpload();
  
  /**
   * Handle files dropped or selected
   */
  const handleFilesAdded = async (files: File[]) => {
    await uploadFiles(files, projectId);
  };
  
  /**
   * Remove uploaded file from list (local only, not from server)
   * In this modal, we just hide it from the list
   */
  const handleRemoveUploaded = (fileId: string) => {
    // Just close the modal - uploaded files are already on server
    // The parent component will refresh the file list
  };
  
  /**
   * Handle close with cleanup
   */
  const handleClose = () => {
    if (isUploading) {
      if (!confirm('Files are still uploading. Are you sure you want to close?')) {
        return;
      }
    }
    
    clearPendingFiles();
    clearUploadedFiles();
    onClose();
    onUploadComplete?.();
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Upload Files</h2>
              {projectId && projectName && (
                <p className="text-sm text-gray-600 mt-1">
                  Uploading to project: <span className="font-medium">{projectName}</span>
                </p>
              )}
              {projectId && !projectName && (
                <p className="text-sm text-gray-600 mt-1">
                  Uploading to project: <span className="font-medium">{projectId}</span>
                </p>
              )}
              {!projectId && (
                <p className="text-sm text-gray-600 mt-1">
                  Uploading to: <span className="font-medium">My Files</span>
                </p>
              )}
            </div>
            <button
              onClick={handleClose}
              disabled={isUploading}
              className="text-gray-400 hover:text-gray-500 transition-colors disabled:opacity-50"
            >
              <X size={24} />
            </button>
          </div>
          
          {/* Content */}
          <div className="px-6 py-4 space-y-6">
            {/* Info banner */}
            <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <AlertCircle size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">File upload constraints:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Maximum file size: 10 MB</li>
                  <li>Maximum files per upload: 5</li>
                  <li>Allowed types: PDF, TXT, CSV, JSON, MD, PNG, JPEG, GIF, WebP</li>
                </ul>
              </div>
            </div>
            
            {/* Dropzone */}
            <FileDropzone
              onFilesAdded={handleFilesAdded}
              disabled={isUploading}
              maxFiles={5}
            />
            
            {/* File lists */}
            {(pendingFiles.length > 0 || uploadedFiles.length > 0) && (
              <div className="space-y-4">
                {pendingFiles.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">
                      {isUploading ? 'Uploading...' : 'Pending Files'}
                    </h3>
                    <FileList
                      files={pendingFiles}
                      onRemove={removePendingFile}
                      type="pending"
                    />
                  </div>
                )}
                
                {uploadedFiles.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">
                      Uploaded Files ({uploadedFiles.length})
                    </h3>
                    <FileList
                      files={uploadedFiles}
                      onRemove={handleRemoveUploaded}
                      type="uploaded"
                    />
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* Footer */}
          <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {pendingFiles.length > 0 && (
                <span>{pendingFiles.length} file(s) pending</span>
              )}
              {uploadedFiles.length > 0 && (
                <span className="ml-4">{uploadedFiles.length} file(s) uploaded</span>
              )}
            </div>
            
            <button
              onClick={handleClose}
              disabled={isUploading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? 'Uploading...' : 'Done'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}