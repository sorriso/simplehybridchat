/* path: frontend/src/components/upload/FileList.tsx
   version: 1 */

import { X, CheckCircle, AlertCircle, FileText, Loader2 } from "lucide-react";
import { IconButton } from "../ui/IconButton";
import type { PendingFile, UploadedFile } from "@/types/file";

interface FileListProps {
  pendingFiles: PendingFile[];
  uploadedFiles: UploadedFile[];
  onRemovePending: (id: string) => void;
  onRemoveUploaded: (id: string) => void;
}

/**
 * Display list of pending and uploaded files
 */
export function FileList({
  pendingFiles,
  uploadedFiles,
  onRemovePending,
  onRemoveUploaded,
}: FileListProps) {
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className="space-y-4">
      {/* Pending files */}
      {pendingFiles.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Pending Files
          </h3>
          <div className="space-y-2">
            {pendingFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
              >
                {/* Status icon */}
                {file.status === "uploading" && (
                  <Loader2
                    size={16}
                    className="text-blue-500 flex-shrink-0 animate-spin"
                  />
                )}
                {file.status === "pending" && (
                  <FileText size={16} className="text-gray-400 flex-shrink-0" />
                )}
                {file.status === "error" && (
                  <AlertCircle
                    size={16}
                    className="text-red-500 flex-shrink-0"
                  />
                )}

                {/* File info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.file.name}
                  </p>
                  <div className="flex items-center gap-2">
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.file.size)}
                    </p>
                    {file.status === "uploading" &&
                      file.progress !== undefined && (
                        <>
                          <span className="text-xs text-gray-400">•</span>
                          <p className="text-xs text-blue-600">
                            {file.progress}%
                          </p>
                        </>
                      )}
                    {file.status === "error" && file.error && (
                      <>
                        <span className="text-xs text-gray-400">•</span>
                        <p className="text-xs text-red-600">{file.error}</p>
                      </>
                    )}
                  </div>

                  {/* Progress bar */}
                  {file.status === "uploading" &&
                    file.progress !== undefined && (
                      <div className="mt-2 w-full bg-gray-200 rounded-full h-1">
                        <div
                          className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    )}
                </div>

                {/* Remove button */}
                <IconButton
                  icon={X}
                  size="sm"
                  variant="secondary"
                  onClick={() => onRemovePending(file.id)}
                  title="Remove"
                  disabled={file.status === "uploading"}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Uploaded files */}
      {uploadedFiles.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Uploaded Files
          </h3>
          <div className="space-y-2">
            {uploadedFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-3 p-3 bg-green-50 rounded-lg"
              >
                <CheckCircle
                  size={16}
                  className="text-green-500 flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.size)} • {file.status}
                  </p>
                </div>
                <IconButton
                  icon={X}
                  size="sm"
                  variant="danger"
                  onClick={() => onRemoveUploaded(file.id)}
                  title="Delete"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {pendingFiles.length === 0 && uploadedFiles.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <FileText size={48} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm">No files yet</p>
        </div>
      )}
    </div>
  );
}
