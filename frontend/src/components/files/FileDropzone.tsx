/* path: frontend/src/components/files/FileDropzone.tsx
   version: 1.0
   
   Drag & drop zone for file uploads
*/

'use client';

import { useCallback, useState } from 'react';
import { Upload } from 'lucide-react';

interface FileDropzoneProps {
  onFilesAdded: (files: File[]) => void;
  disabled?: boolean;
  maxFiles?: number;
}

export function FileDropzone({
  onFilesAdded,
  disabled = false,
  maxFiles = 5,
}: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  
  /**
   * Handle drag enter
   */
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);
  
  /**
   * Handle drag leave
   */
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only set dragging to false if leaving the dropzone itself
    if (e.currentTarget === e.target) {
      setIsDragging(false);
    }
  }, []);
  
  /**
   * Handle drag over
   */
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);
  
  /**
   * Handle drop
   */
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    setIsDragging(false);
    
    if (disabled) return;
    
    const files = Array.from(e.dataTransfer.files);
    
    if (files.length > 0) {
      // Limit to maxFiles
      const filesToAdd = files.slice(0, maxFiles);
      onFilesAdded(filesToAdd);
    }
  }, [disabled, maxFiles, onFilesAdded]);
  
  /**
   * Handle file input change
   */
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    if (files.length > 0) {
      // Limit to maxFiles
      const filesToAdd = files.slice(0, maxFiles);
      onFilesAdded(filesToAdd);
    }
    
    // Reset input value to allow selecting the same file again
    e.target.value = '';
  }, [maxFiles, onFilesAdded]);
  
  /**
   * Trigger file input click
   */
  const handleClick = useCallback(() => {
    if (disabled) return;
    
    const input = document.getElementById('file-input') as HTMLInputElement;
    input?.click();
  }, [disabled]);
  
  return (
    <div
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        relative border-2 border-dashed rounded-lg p-8
        transition-all duration-200 cursor-pointer
        ${isDragging
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400 bg-gray-50'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      {/* Hidden file input */}
      <input
        id="file-input"
        type="file"
        multiple
        disabled={disabled}
        onChange={handleFileInputChange}
        className="hidden"
        accept=".pdf,.txt,.csv,.json,.md,.png,.jpg,.jpeg,.gif,.webp"
      />
      
      {/* Content */}
      <div className="flex flex-col items-center justify-center text-center">
        <div
          className={`
            mb-4 p-4 rounded-full
            ${isDragging ? 'bg-blue-100' : 'bg-gray-100'}
          `}
        >
          <Upload
            size={32}
            className={isDragging ? 'text-blue-600' : 'text-gray-400'}
          />
        </div>
        
        <p className="text-lg font-medium text-gray-900 mb-2">
          {isDragging ? 'Drop files here' : 'Drop files or click to upload'}
        </p>
        
        <p className="text-sm text-gray-600">
          Maximum {maxFiles} files • PDF, TXT, CSV, JSON, MD, PNG, JPEG, GIF, WebP
        </p>
      </div>
    </div>
  );
}