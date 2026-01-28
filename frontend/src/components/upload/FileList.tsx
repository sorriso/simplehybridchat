/* path: frontend/src/components/upload/FileList.tsx
   version: 2.2
   
   Changes in v2.2:
   - FIX: Date sorting now uses correct field 'uploadedAt' (was 'uploaded_at')
*/

import { useState, useMemo } from "react";
import { X, CheckCircle, AlertCircle, FileText, Loader2, Search, ArrowUpDown } from "lucide-react";
import { IconButton } from "../ui/IconButton";
import type { PendingFile, UploadedFile } from "@/types/file";

interface FileListProps {
  pendingFiles: PendingFile[];
  uploadedFiles: UploadedFile[];
  onRemovePending: (id: string) => void;
  onRemoveUploaded: (id: string) => void;
}

type SortOption = 'name-asc' | 'name-desc' | 'date-desc' | 'date-asc' | 'size-desc' | 'size-asc';

function wildcardToRegex(pattern: string): RegExp {
  const escaped = pattern
    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
    .replace(/\*/g, '.*')
    .replace(/\?/g, '.');
  return new RegExp(`^${escaped}$`, 'i');
}

function matchesSearch(filename: string, searchTerm: string): boolean {
  if (!searchTerm.trim()) return true;
  const term = searchTerm.trim();
  
  if (term.includes('*') || term.includes('?')) {
    const regex = wildcardToRegex(term);
    return regex.test(filename);
  }
  
  return filename.toLowerCase().includes(term.toLowerCase());
}

function sortFiles(files: UploadedFile[], sortBy: SortOption): UploadedFile[] {
  const sorted = [...files];
  
  switch (sortBy) {
    case 'name-asc':
      return sorted.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
    case 'name-desc':
      return sorted.sort((a, b) => b.name.toLowerCase().localeCompare(a.name.toLowerCase()));
    case 'date-desc':
      return sorted.sort((a, b) => new Date(b.uploadedAt || 0).getTime() - new Date(a.uploadedAt || 0).getTime());
    case 'date-asc':
      return sorted.sort((a, b) => new Date(a.uploadedAt || 0).getTime() - new Date(b.uploadedAt || 0).getTime());
    case 'size-desc':
      return sorted.sort((a, b) => b.size - a.size);
    case 'size-asc':
      return sorted.sort((a, b) => a.size - b.size);
    default:
      return sorted;
  }
}

export function FileList({
  pendingFiles,
  uploadedFiles,
  onRemovePending,
  onRemoveUploaded,
}: FileListProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>('name-asc');

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const filteredAndSortedFiles = useMemo(() => {
    const filtered = uploadedFiles.filter(file => matchesSearch(file.name, searchTerm));
    return sortFiles(filtered, sortBy);
  }, [uploadedFiles, searchTerm, sortBy]);

  return (
    <div className="space-y-3">
      {/* Pending files */}
      {pendingFiles.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Pending ({pendingFiles.length})
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {pendingFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-2 p-2.5 bg-gray-50 rounded-lg"
              >
                {file.status === "uploading" && (
                  <Loader2 size={14} className="text-blue-500 flex-shrink-0 animate-spin" />
                )}
                {file.status === "pending" && (
                  <FileText size={14} className="text-gray-400 flex-shrink-0" />
                )}
                {file.status === "error" && (
                  <AlertCircle size={14} className="text-red-500 flex-shrink-0" />
                )}

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.file.name}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>{formatFileSize(file.file.size)}</span>
                    {file.status === "uploading" && file.progress !== undefined && (
                      <><span>•</span><span className="text-blue-600">{file.progress}%</span></>
                    )}
                    {file.status === "error" && file.error && (
                      <><span>•</span><span className="text-red-600">{file.error}</span></>
                    )}
                  </div>

                  {file.status === "uploading" && file.progress !== undefined && (
                    <div className="mt-1.5 w-full bg-gray-200 rounded-full h-0.5">
                      <div
                        className="bg-blue-500 h-0.5 rounded-full transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                </div>

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

      {/* Uploaded files with search and sort */}
      {uploadedFiles.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-gray-700">
              Uploaded ({filteredAndSortedFiles.length}/{uploadedFiles.length})
            </h3>
          </div>

          {/* Search and sort controls */}
          <div className="space-y-2 mb-3">
            {/* Search bar */}
            <div className="relative">
              <Search 
                size={14} 
                className="absolute left-2.5 top-1/2 transform -translate-y-1/2 text-gray-400"
              />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search... (*.pdf, inv*, etc.)"
                className="w-full pl-8 pr-8 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm("")}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X size={14} />
                </button>
              )}
            </div>

            {/* Sort selector */}
            <div className="relative">
              <ArrowUpDown 
                size={14} 
                className="absolute left-2.5 top-1/2 transform -translate-y-1/2 text-gray-400"
              />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              >
                <option value="name-asc">Name (A → Z)</option>
                <option value="name-desc">Name (Z → A)</option>
                <option value="date-desc">Date (Newest first)</option>
                <option value="date-asc">Date (Oldest first)</option>
                <option value="size-desc">Size (Largest first)</option>
                <option value="size-asc">Size (Smallest first)</option>
              </select>
            </div>
          </div>

          {/* Files list with scroll */}
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {filteredAndSortedFiles.length > 0 ? (
              filteredAndSortedFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-2 p-2.5 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                >
                  <CheckCircle size={14} className="text-green-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.size)}
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
              ))
            ) : (
              <div className="text-center py-6 text-gray-500 bg-gray-50 rounded-lg">
                <Search size={24} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">No files match &quot;{searchTerm}&quot;</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {pendingFiles.length === 0 && uploadedFiles.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <FileText size={40} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm">No files yet</p>
        </div>
      )}
    </div>
  );
}