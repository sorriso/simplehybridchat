/* path: src/components/upload/FileList.tsx
   version: 1 */

import { FileText, X, CheckCircle, AlertCircle, Loader } from "lucide-react";
import { PendingFile, UploadedFile } from "@/types/file";
import { IconButton } from "../ui/IconButton";

interface FileListProps {
  pendingFiles: PendingFile[];
  uploadedFiles: UploadedFile[];
  onRemovePending: (id: string) => void;
  onRemoveUploaded: (id: string) => void;
}

/**
 * Component to display list of files (pending and uploaded)
 */
export function FileList({
  pendingFiles,
  uploadedFiles,
  onRemovePending,
  onRemoveUploaded,
}: FileListProps) {
  /**
   * Format file size to human readable format
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  /**
   * Get status icon for pending file
   */
  const getStatusIcon = (file: PendingFile) => {
    switch (file.status) {
      case "uploading":
        return <Loader size={16} className="animate-spin text-blue-500" />;
      case "completed":
        return <CheckCircle size={16} className="text-green-500" />;
      case "error":
        return <AlertCircle size={16} className="text-red-500" />;
      default:
        return <FileText size={16} className="text-gray-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Pending files */}
      {pendingFiles.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Pending Upload
          </h3>
          <div className="space-y-2">
            {pendingFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
              >
                {getStatusIcon(file)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.file.size)}
                    {file.status === "uploading" &&
                      ` • ${Math.round(file.progress)}%`}
                  </p>
                  {file.status === "uploading" && (
                    <div className="mt-1 w-full bg-gray-200 rounded-full h-1">
                      <div
                        className="bg-blue-500 h-1 rounded-full transition-all"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                  {file.error && (
                    <p className="text-xs text-red-600 mt-1">{file.error}</p>
                  )}
                </div>
                {file.status === "pending" && (
                  <IconButton
                    icon={X}
                    size="sm"
                    onClick={() => onRemovePending(file.id)}
                    title="Remove"
                  />
                )}
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
