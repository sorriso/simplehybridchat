/* path: frontend/src/components/files/FileList.tsx
   version: 2.1
   
   Changes in v2.1:
   - FIX: Accept UploadedFile[] for backward compatibility
   - Can now handle: PendingFile[], FileMetadata[], or UploadedFile[]
   
   Changes in v2.0:
   - FIX: Access PendingFile properties via file.file (browser File object)
   - file.name → file.file.name
   - file.size → file.file.size
*/

'use client';

import { X, CheckCircle, AlertCircle, Loader2, File as FileIcon } from 'lucide-react';
import type { PendingFile, FileMetadata, UploadedFile } from '@/types/file';

interface FileListProps {
  files: PendingFile[] | FileMetadata[] | UploadedFile[];
  onRemove: (id: string) => void;
  type: 'pending' | 'uploaded';
}

export function FileList({ files, onRemove, type }: FileListProps) {
  /**
   * Format file size
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  /**
   * Render pending file item
   */
  const renderPendingFile = (file: PendingFile) => {
    const showProgress = file.status === 'uploading' && file.progress !== undefined;
    
    return (
      <div
        key={file.id}
        className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
      >
        <FileIcon className="text-gray-400 flex-shrink-0 mt-1" size={20} />
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <p className="text-sm font-medium text-gray-900 truncate">
              {file.file.name}
            </p>
            
            <button
              onClick={() => onRemove(file.id)}
              disabled={file.status === 'uploading'}
              className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
            >
              <X size={16} />
            </button>
          </div>
          
          <p className="text-xs text-gray-600 mb-2">
            {formatFileSize(file.file.size)}
          </p>
          
          {/* Status indicator */}
          {file.status === 'pending' && (
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Loader2 size={14} className="animate-spin" />
              <span>Waiting...</span>
            </div>
          )}
          
          {file.status === 'uploading' && showProgress && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs text-gray-600">
                <span>Uploading...</span>
                <span>{Math.round(file.progress || 0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-blue-600 h-full transition-all duration-300"
                  style={{ width: `${file.progress || 0}%` }}
                />
              </div>
            </div>
          )}
          
          {file.status === 'completed' && (
            <div className="flex items-center gap-1 text-xs text-green-600">
              <CheckCircle size={14} />
              <span>Upload complete</span>
            </div>
          )}
          
          {file.status === 'error' && (
            <div className="flex items-center gap-1 text-xs text-red-600">
              <AlertCircle size={14} />
              <span>{file.error || 'Upload failed'}</span>
            </div>
          )}
        </div>
      </div>
    );
  };
  
  /**
   * Render uploaded file item (works for both UploadedFile and FileMetadata)
   */
  const renderUploadedFile = (file: UploadedFile | FileMetadata) => {
    return (
      <div
        key={file.id}
        className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
      >
        <FileIcon className="text-green-500 flex-shrink-0 mt-1" size={20} />
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <p className="text-sm font-medium text-gray-900 truncate">
              {file.name}
            </p>
            
            <button
              onClick={() => onRemove(file.id)}
              className="text-gray-400 hover:text-red-600 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
          
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <span>{formatFileSize(file.size)}</span>
            <span>•</span>
            <span className="text-green-600 font-medium">Uploaded</span>
          </div>
        </div>
      </div>
    );
  };
  
  if (files.length === 0) {
    return null;
  }
  
  return (
    <div className="space-y-2">
      {type === 'pending'
        ? (files as PendingFile[]).map(renderPendingFile)
        : (files as (UploadedFile | FileMetadata)[]).map(renderUploadedFile)
      }
    </div>
  );
}