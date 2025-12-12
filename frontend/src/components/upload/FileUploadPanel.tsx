/* path: frontend/src/components/upload/FileUploadPanel.tsx
   version: 1 */

import { X } from "lucide-react";
import { FileDropzone } from "./FileDropzone";
import { FileList } from "./FileList";
import { Button } from "../ui/Button";
import { IconButton } from "../ui/IconButton";
import { useFileUpload } from "@/lib/hooks/useFileUpload";

interface FileUploadPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Side panel for file uploads
 */
export function FileUploadPanel({ isOpen, onClose }: FileUploadPanelProps) {
  const {
    pendingFiles,
    uploadedFiles,
    isUploading,
    addFiles,
    removePendingFile,
    clearPendingFiles,
    uploadFiles,
    deleteUploadedFile,
  } = useFileUpload();

  const handleFilesSelected = (files: File[]) => {
    addFiles(files);
  };

  const handleUpload = async () => {
    try {
      await uploadFiles();
    } catch (error) {
      console.error("Upload failed:", error);
    }
  };

  const handleDeleteUploaded = async (fileId: string) => {
    if (window.confirm("Are you sure you want to delete this file?")) {
      try {
        await deleteUploadedFile(fileId);
      } catch (error) {
        console.error("Delete failed:", error);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-xl border-l border-gray-200 z-40">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Upload Files</h2>
          <IconButton icon={X} onClick={onClose} title="Close" />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Dropzone */}
          <FileDropzone
            onFilesSelected={handleFilesSelected}
            disabled={isUploading}
          />

          {/* File list */}
          <FileList
            pendingFiles={pendingFiles}
            uploadedFiles={uploadedFiles}
            onRemovePending={removePendingFile}
            onRemoveUploaded={handleDeleteUploaded}
          />
        </div>

        {/* Footer actions */}
        {pendingFiles.length > 0 && (
          <div className="p-4 border-t border-gray-200 space-y-2">
            <Button
              variant="primary"
              fullWidth
              onClick={handleUpload}
              disabled={isUploading}
            >
              {isUploading
                ? "Uploading..."
                : `Upload ${pendingFiles.length} file(s)`}
            </Button>
            <Button
              variant="secondary"
              fullWidth
              onClick={clearPendingFiles}
              disabled={isUploading}
            >
              Clear All
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
