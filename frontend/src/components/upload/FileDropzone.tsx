/* path: frontend/src/components/upload/FileDropzone.tsx
   version: 1 */

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText } from "lucide-react";
import { UI_CONSTANTS } from "@/lib/utils/constants";

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

/**
 * Drag and drop file upload component
 */
export function FileDropzone({ onFilesSelected, disabled }: FileDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFilesSelected(acceptedFiles);
    },
    [onFilesSelected],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled,
    maxFiles: UI_CONSTANTS.MAX_FILES_PER_UPLOAD,
    maxSize: UI_CONSTANTS.MAX_FILE_SIZE,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "text/csv": [".csv"],
      "application/json": [".json"],
      "text/markdown": [".md"],
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`
           border-2 border-dashed rounded-lg p-8
           transition-colors cursor-pointer
           ${
             isDragActive
               ? "border-primary-500 bg-primary-50"
               : "border-gray-300 bg-gray-50 hover:bg-gray-100"
           }
           ${disabled ? "opacity-50 cursor-not-allowed" : ""}
         `}
    >
      <input {...getInputProps()} />

      <div className="flex flex-col items-center justify-center text-center">
        {isDragActive ? (
          <>
            <Upload size={48} className="text-primary-500 mb-4" />
            <p className="text-lg font-medium text-primary-700">
              Drop files here
            </p>
          </>
        ) : (
          <>
            <FileText size={48} className="text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              Drag & drop files here
            </p>
            <p className="text-sm text-gray-500 mb-4">or click to browse</p>
            <div className="text-xs text-gray-400 space-y-1">
              <p>Supported: PDF, TXT, CSV, JSON, MD</p>
              <p>Max {UI_CONSTANTS.MAX_FILES_PER_UPLOAD} files</p>
              <p>Max {UI_CONSTANTS.MAX_FILE_SIZE / 1024 / 1024}MB per file</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
