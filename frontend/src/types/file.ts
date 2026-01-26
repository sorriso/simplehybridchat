/* path: frontend/src/types/file.ts
   version: 5.0
   
   Changes in v5.0:
   - FUSION: Combined old (v1) and new (v4) type systems
   - Old system: Simple upload with UploadedFile
   - New system: Advanced v4 with FileMetadata, phases, versioning
   - Kept PendingFile simple (old style) - compatible with both systems
*/

/**
 * ============================================================================
 * OLD UPLOAD SYSTEM (v1) - Used by /components/upload/
 * ============================================================================
 */

/**
 * File status during upload process (v1)
 */
export type FileStatus = 'pending' | 'uploading' | 'completed' | 'error';

/**
 * Pending file (during upload) - v1 simple structure
 * Used by old /components/upload/ system
 */
export interface PendingFile {
  id: string;
  file: File;           // Browser File object (has .name, .size, .type)
  progress: number;     // 0-100
  status: FileStatus;
  error?: string;
}

/**
 * Uploaded file (stored on server) - v1 simple structure
 * Used by old /components/upload/ system
 */
export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
  status: 'completed';
  uploadedAt: string;
}

/**
 * File upload API response (v1)
 */
export interface FileUploadResponse {
  file: UploadedFile;
}

/**
 * File list API response (v1)
 */
export interface FileListResponse {
  files: UploadedFile[];
}

/**
 * ============================================================================
 * NEW UPLOAD SYSTEM (v4) - Used by /components/files/
 * ============================================================================
 */

/**
 * File scope determines where the file is stored and who can access it
 */
export type FileScope = 'system' | 'user_global' | 'user_project';

/**
 * Processing phases
 */
export type ProcessingPhase = 
  | '01-input_data'
  | '02-data_extraction'
  | '03-summary'
  | '04-chunking'
  | '05-graph_extraction'
  | '06-graph_aggregation';

/**
 * Phase processing status
 */
export type PhaseStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Global file processing status
 */
export type GlobalProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Version format: v{N}_algo-{version}
 * Example: v1_algo-1.0, v2_algo-2.0
 */
export interface PhaseVersion {
  version: string;                    // e.g., "v1_algo-1.0"
  algorithmVersion: string;           // e.g., "1.0"
  algorithmName: string;              // e.g., "basic_chunking"
  createdAt: string;                  // ISO 8601
  completedAt: string | null;         // ISO 8601
  status: PhaseStatus;
  parameters: Record<string, any>;
  stats: Record<string, any>;
  dependencies?: Record<string, string>; // phase -> version
  reprocessingReason?: string;
}

/**
 * Version metadata stored per phase
 */
export interface PhaseVersionMetadata {
  phase: ProcessingPhase;
  activeVersion: string;
  versions: PhaseVersion[];
}

/**
 * Phase processing status in file metadata
 */
export interface PhaseProcessingStatus {
  status: PhaseStatus;
  activeVersion: string;
  availableVersions: string[];
  lastUpdated: string;               // ISO 8601
}

/**
 * File processing status
 */
export interface FileProcessingStatus {
  global: GlobalProcessingStatus;
  phases: {
    '02-data_extraction': PhaseProcessingStatus;
    '03-summary': PhaseProcessingStatus;
    '04-chunking': PhaseProcessingStatus;
    '05-graph_extraction': PhaseProcessingStatus;
    '06-graph_aggregation': PhaseProcessingStatus;
  };
  lastUpdated: string;                // ISO 8601
}

/**
 * Active configuration - which version of each phase is used for RAG
 */
export interface ActiveConfiguration {
  '02-data_extraction': string;
  '03-summary': string;
  '04-chunking': string;
  '05-graph_extraction': string;
  '06-graph_aggregation': string;
  lastModified: string;               // ISO 8601
}

/**
 * File checksums for deduplication
 */
export interface FileChecksums {
  md5: string;
  sha256: string;
  simhash: string;
  minhash: string[];
}

/**
 * File statistics
 */
export interface FileStats {
  totalPages: number;
  totalImages: number;
  totalChunks: number;
  totalTripletsRaw: number;
  totalTripletsMerged: number;
  language: string;
}

/**
 * Promotion metadata (when file is promoted from project to system)
 */
export interface PromotionMetadata {
  promotedAt: string;                 // ISO 8601
  promotedBy: string;                 // user_id
  originalScope: FileScope;
  originalPath: string;
  originalOwner: string;
  originalProjectId: string | null;
  promotionReason: string;
  phasesPromoted: Record<string, string[]>; // phase -> versions
  activeConfigurationAtPromotion: ActiveConfiguration;
}

/**
 * File metadata (v4.0)
 * Renamed from "File" to avoid conflict with browser's native File type
 */
export interface FileMetadata {
  id: string;
  name: string;
  size: number;
  type: string;                       // MIME type
  minioPath: string;
  uploadedBy: string;
  uploadedAt: string;                 // ISO 8601
  
  scope: FileScope;
  projectId: string | null;
  projectName: string | null;
  
  promoted: boolean;
  promotedAt: string | null;
  promotedBy: string | null;
  promotedFrom: PromotionMetadata | null;
  
  checksums: FileChecksums;
  processingStatus: FileProcessingStatus;
  activeConfiguration: ActiveConfiguration;
  stats: FileStats;
}

/**
 * ============================================================================
 * NEW SYSTEM API TYPES
 * ============================================================================
 */

/**
 * File promotion request
 */
export interface FilePromotionRequest {
  reason: string;
}

/**
 * File promotion response
 */
export interface FilePromotionResponse {
  file: FileMetadata;
  message: string;
}

/**
 * Phase reprocessing request
 */
export interface PhaseReprocessingRequest {
  phase: Exclude<ProcessingPhase, '01-input_data'>; // Cannot reprocess input
  algorithmVersion: string;
  algorithmName: string;
  parameters: Record<string, any>;
  dependencies: Record<string, string>; // phase -> version
  reason: string;
  autoPropagate: boolean;
}

/**
 * Phase reprocessing response
 */
export interface PhaseReprocessingResponse {
  fileId: string;
  phase: ProcessingPhase;
  newVersion: string;
  queueId: string;
  triggeredPhases: ProcessingPhase[];
  estimatedDuration: string;
}

/**
 * Active configuration update request
 */
export interface ActiveConfigurationRequest {
  phases: {
    '02-data_extraction': string;
    '03-summary': string;
    '04-chunking': string;
    '05-graph_extraction': string;
    '06-graph_aggregation': string;
  };
}

/**
 * Active configuration update response
 */
export interface ActiveConfigurationResponse {
  fileId: string;
  activeConfiguration: ActiveConfiguration;
  previousConfiguration: Partial<ActiveConfiguration>;
}

/**
 * Phase versions list response
 */
export interface PhaseVersionsResponse {
  fileId: string;
  phase: ProcessingPhase;
  activeVersion: string;
  versions: PhaseVersion[];
}

/**
 * Processing queue entry
 */
export interface ProcessingQueueEntry {
  id: string;
  fileId: string;
  phase: ProcessingPhase;
  newVersion: string;
  algorithmVersion: string;
  algorithmName: string;
  status: PhaseStatus;
  startedAt: string | null;
  completedAt: string | null;
  error: string | null;
  parameters: Record<string, any>;
  dependencies: Record<string, string>;
  triggersReprocessing: ProcessingPhase[];
  createdAt: string;
  updatedAt: string;
  priority: number;
  metadata: {
    userId: string;
    projectId: string | null;
    fileName: string;
    minioBasePath: string;
    reprocessingReason: string;
  };
}

/**
 * File filters for listing
 */
export interface FileFilters {
  scope?: FileScope;
  projectId?: string;
  status?: GlobalProcessingStatus;
  search?: string;                    // Search in name
}

/**
 * ============================================================================
 * CONSTANTS
 * ============================================================================
 */

/**
 * Constants for file validation
 */
export const FILE_CONSTANTS = {
  MAX_FILE_SIZE: 10 * 1024 * 1024,    // 10MB
  MAX_FILES_PER_UPLOAD: 5,
  ALLOWED_MIME_TYPES: [
    'application/pdf',
    'text/plain',
    'text/csv',
    'application/json',
    'text/markdown',
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp',
  ],
} as const;

/**
 * Phase labels for UI display
 */
export const PHASE_LABELS: Record<ProcessingPhase, string> = {
  '01-input_data': 'Input Data',
  '02-data_extraction': 'Data Extraction',
  '03-summary': 'Summary',
  '04-chunking': 'Chunking',
  '05-graph_extraction': 'Graph Extraction',
  '06-graph_aggregation': 'Graph Aggregation',
} as const;

/**
 * Phase dependencies graph
 */
export const PHASE_DEPENDENCIES: Record<ProcessingPhase, ProcessingPhase[]> = {
  '01-input_data': [],
  '02-data_extraction': ['01-input_data'],
  '03-summary': ['02-data_extraction'],
  '04-chunking': ['02-data_extraction', '03-summary'],
  '05-graph_extraction': ['04-chunking'],
  '06-graph_aggregation': ['05-graph_extraction'],
} as const;

/**
 * Get dependent phases (phases that depend on given phase)
 */
export function getDependentPhases(phase: ProcessingPhase): ProcessingPhase[] {
  const dependents: Record<ProcessingPhase, ProcessingPhase[]> = {
    '01-input_data': ['02-data_extraction'],
    '02-data_extraction': ['03-summary', '04-chunking'],
    '03-summary': ['04-chunking'],
    '04-chunking': ['05-graph_extraction'],
    '05-graph_extraction': ['06-graph_aggregation'],
    '06-graph_aggregation': [],
  };
  
  return dependents[phase] || [];
}