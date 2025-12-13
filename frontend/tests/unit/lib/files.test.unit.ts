// path: frontend/tests/unit/lib/files.test.unit.ts
// version: 4 - FIXED: Added FILES constant to mock

import { filesApi } from '@/lib/api/files';
import { apiClient } from '@/lib/api/client';

// Mock apiClient
jest.mock('@/lib/api/client', () => ({
  apiClient: {
    uploadFile: jest.fn(),
    get: jest.fn(),
    delete: jest.fn(),
  },
}));

// Mock constants - MUST include all exports from real module
jest.mock('@/lib/utils/constants', () => ({
  API_ENDPOINTS: {
    FILES: '/api/files',
    FILES_UPLOAD: '/api/files/upload',
    FILES_LIST: '/api/files',
    FILE_BY_ID: (id: string) => `/api/files/${id}`,
  },
  STORAGE_KEYS: {
    AUTH_TOKEN: 'auth_token',
    CURRENT_USER: 'current_user',
    CURRENT_CONVERSATION: 'current_conversation_id',
    SETTINGS: 'user_settings',
  },
  UI_CONSTANTS: {
    SIDEBAR_WIDTH: 280,
    SIDEBAR_WIDTH_COLLAPSED: 0,
    MAX_FILE_SIZE: 10485760,
    ALLOWED_FILE_TYPES: [],
    MAX_FILES_PER_UPLOAD: 5,
  },
}));

describe('filesApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('upload', () => {
    it('should upload a file successfully', async () => {
      const mockFile = new File(['content'], 'test.txt', { type: 'text/plain' });
      const mockResponse = {
        file: {
          id: 'file-123',
          filename: 'test.txt',
          size: 7,
          mimeType: 'text/plain',
          uploadedAt: new Date().toISOString(),
        },
      };

      (apiClient.uploadFile as jest.Mock).mockResolvedValue(mockResponse);

      const result = await filesApi.upload(mockFile);

      expect(apiClient.uploadFile).toHaveBeenCalledWith(
        '/api/files/upload',
        mockFile,
        undefined
      );
      expect(result).toEqual(mockResponse.file);
    });

    it('should upload file with progress callback', async () => {
      const mockFile = new File(['content'], 'test.txt');
      const mockResponse = {
        file: {
          id: 'file-123',
          filename: 'test.txt',
          size: 7,
          mimeType: 'text/plain',
          uploadedAt: new Date().toISOString(),
        },
      };
      const onProgress = jest.fn();

      (apiClient.uploadFile as jest.Mock).mockResolvedValue(mockResponse);

      const result = await filesApi.upload(mockFile, onProgress);

      expect(apiClient.uploadFile).toHaveBeenCalledWith(
        '/api/files/upload',
        mockFile,
        onProgress
      );
      expect(result).toEqual(mockResponse.file);
    });

    it('should propagate upload errors', async () => {
      const mockFile = new File(['content'], 'test.txt');
      const error = new Error('Upload failed');

      (apiClient.uploadFile as jest.Mock).mockRejectedValue(error);

      await expect(filesApi.upload(mockFile)).rejects.toThrow('Upload failed');
    });
  });

  describe('uploadMultiple', () => {
    it('should upload multiple files successfully', async () => {
      const mockFiles = [
        new File(['content1'], 'test1.txt', { type: 'text/plain' }),
        new File(['content2'], 'test2.txt', { type: 'text/plain' }),
      ];

      const mockResponses = [
        {
          file: {
            id: 'file-1',
            filename: 'test1.txt',
            size: 8,
            mimeType: 'text/plain',
            uploadedAt: new Date().toISOString(),
          },
        },
        {
          file: {
            id: 'file-2',
            filename: 'test2.txt',
            size: 8,
            mimeType: 'text/plain',
            uploadedAt: new Date().toISOString(),
          },
        },
      ];

      (apiClient.uploadFile as jest.Mock)
        .mockResolvedValueOnce(mockResponses[0])
        .mockResolvedValueOnce(mockResponses[1]);

      const result = await filesApi.uploadMultiple(mockFiles);

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual(mockResponses[0].file);
      expect(result[1]).toEqual(mockResponses[1].file);
    });

    it('should track progress for each file', async () => {
      const mockFiles = [
        new File(['content'], 'test1.txt'),
        new File(['content'], 'test2.txt'),
      ];
      const onProgress = jest.fn();

      (apiClient.uploadFile as jest.Mock).mockResolvedValue({
        file: {
          id: 'file-1',
          filename: 'test1.txt',
          size: 7,
          mimeType: 'text/plain',
          uploadedAt: new Date().toISOString(),
        },
      });

      await filesApi.uploadMultiple(mockFiles, onProgress);

      expect(apiClient.uploadFile).toHaveBeenCalledTimes(2);
    });

    it('should fail if any file upload fails', async () => {
      const mockFiles = [
        new File(['content'], 'test1.txt'),
        new File(['content'], 'test2.txt'),
      ];

      (apiClient.uploadFile as jest.Mock)
        .mockResolvedValueOnce({
          file: {
            id: 'file-1',
            filename: 'test1.txt',
            size: 8,
            mimeType: 'text/plain',
            uploadedAt: new Date().toISOString(),
          },
        })
        .mockRejectedValueOnce(new Error('Upload failed'));

      await expect(filesApi.uploadMultiple(mockFiles)).rejects.toThrow('Upload failed');
    });
  });

  describe('getAll', () => {
    it('should fetch all files successfully', async () => {
      const mockFiles = [
        {
          id: 'file-1',
          filename: 'test1.txt',
          size: 100,
          mimeType: 'text/plain',
          uploadedAt: new Date().toISOString(),
        },
        {
          id: 'file-2',
          filename: 'test2.pdf',
          size: 2000,
          mimeType: 'application/pdf',
          uploadedAt: new Date().toISOString(),
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ files: mockFiles });

      const result = await filesApi.getAll();

      expect(apiClient.get).toHaveBeenCalledWith('/api/files');
      expect(result).toEqual(mockFiles);
    });

    it('should return empty array when no files', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ files: [] });

      const result = await filesApi.getAll();

      expect(result).toEqual([]);
    });

    it('should propagate fetch errors', async () => {
      const error = new Error('Fetch failed');
      (apiClient.get as jest.Mock).mockRejectedValue(error);

      await expect(filesApi.getAll()).rejects.toThrow('Fetch failed');
    });
  });

  describe('delete', () => {
    it('should delete file successfully', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue(undefined);

      await filesApi.delete('file-123');

      expect(apiClient.delete).toHaveBeenCalledWith('/api/files/file-123');
    });

    it('should propagate delete errors', async () => {
      const error = new Error('Delete failed');
      (apiClient.delete as jest.Mock).mockRejectedValue(error);

      await expect(filesApi.delete('file-123')).rejects.toThrow('Delete failed');
    });
  });
});