// path: tests/unit/hooks/useFileUpload.test.unit.ts
// version: 3

import { renderHook, act, waitFor } from '@testing-library/react'
import { useFileUpload } from '@/lib/hooks/useFileUpload'
import { filesApi } from '@/lib/api/files'
import { UI_CONSTANTS } from '@/lib/utils/constants'

jest.mock('@/lib/api/files')

const mockFilesApi = filesApi as jest.Mocked<typeof filesApi>

describe('useFileUpload', () => {
  /**
   * Create a mock file with actual size property set correctly
   */
  const createMockFile = (name: string, size: number, type: string): File => {
    // Create content of the specified size
    const content = 'x'.repeat(Math.min(size, 100)) // Limit actual content for performance
    const file = new File([content], name, { type })
    
    // Override the size property to return our specified size
    Object.defineProperty(file, 'size', {
      value: size,
      writable: false,
    })
    
    return file
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Initial state', () => {
    it('starts with empty state', () => {
      const { result } = renderHook(() => useFileUpload())
      
      expect(result.current.pendingFiles).toEqual([])
      expect(result.current.uploadedFiles).toEqual([])
      expect(result.current.isUploading).toBe(false)
    })
  })

  describe('Add files', () => {
    it('adds valid file to pending', () => {
      const { result } = renderHook(() => useFileUpload())
      
      const file = createMockFile('test.pdf', 1024, 'application/pdf')
      
      act(() => {
        result.current.addFiles([file])
      })
      
      expect(result.current.pendingFiles).toHaveLength(1)
      expect(result.current.pendingFiles[0].file.name).toBe('test.pdf')
      expect(result.current.pendingFiles[0].status).toBe('pending')
    })

    it('adds multiple valid files', () => {
      const { result } = renderHook(() => useFileUpload())
      
      const files = [
        createMockFile('file1.pdf', 1024, 'application/pdf'),
        createMockFile('file2.png', 2048, 'image/png'),
      ]
      
      act(() => {
        result.current.addFiles(files)
      })
      
      expect(result.current.pendingFiles).toHaveLength(2)
    })

    it('rejects file exceeding size limit', () => {
      const { result } = renderHook(() => useFileUpload())
      
      const file = createMockFile('large.pdf', UI_CONSTANTS.MAX_FILE_SIZE + 1, 'application/pdf')
      
      let returnValue: { validFiles: any[], errors: string[] } | undefined
      act(() => {
        returnValue = result.current.addFiles([file])
      })
      
      expect(result.current.pendingFiles).toHaveLength(0)
      expect(returnValue?.errors).toHaveLength(1)
    })

    it('rejects file with invalid type', () => {
      const { result } = renderHook(() => useFileUpload())
      
      const file = createMockFile('bad.exe', 1024, 'application/x-msdownload')
      
      let returnValue: { validFiles: any[], errors: string[] } | undefined
      act(() => {
        returnValue = result.current.addFiles([file])
      })
      
      expect(result.current.pendingFiles).toHaveLength(0)
      expect(returnValue?.errors).toHaveLength(1)
    })

    it('separates valid and invalid files', () => {
      const { result } = renderHook(() => useFileUpload())
      
      const files = [
        createMockFile('valid.pdf', 1024, 'application/pdf'),
        createMockFile('too-large.pdf', UI_CONSTANTS.MAX_FILE_SIZE + 1, 'application/pdf'),
        createMockFile('invalid.exe', 1024, 'application/x-msdownload'),
      ]
      
      let returnValue: { validFiles: any[], errors: string[] } | undefined
      act(() => {
        returnValue = result.current.addFiles(files)
      })
      
      expect(result.current.pendingFiles).toHaveLength(1)
      expect(returnValue?.errors).toHaveLength(2)
    })
  })

  describe('Remove pending file', () => {
    it('removes file from pending', () => {
      const { result } = renderHook(() => useFileUpload())
      
      const file = createMockFile('test.pdf', 1024, 'application/pdf')
      
      act(() => {
        result.current.addFiles([file])
      })
      
      const fileId = result.current.pendingFiles[0].id
      
      act(() => {
        result.current.removePendingFile(fileId)
      })
      
      expect(result.current.pendingFiles).toHaveLength(0)
    })
  })

  describe('Clear pending files', () => {
    it('clears all pending files', () => {
      const { result } = renderHook(() => useFileUpload())
      
      const files = [
        createMockFile('file1.pdf', 1024, 'application/pdf'),
        createMockFile('file2.png', 2048, 'image/png'),
      ]
      
      act(() => {
        result.current.addFiles(files)
      })
      
      expect(result.current.pendingFiles).toHaveLength(2)
      
      act(() => {
        result.current.clearPendingFiles()
      })
      
      expect(result.current.pendingFiles).toHaveLength(0)
    })
  })

  describe('Upload files', () => {
    it('uploads file with progress', async () => {
      const uploadedFile = {
        id: 'file-1',
        name: 'test.pdf',
        size: 1024,
        mimeType: 'application/pdf',
        url: '/uploads/test.pdf',
        uploadedAt: new Date(),
        status: 'completed' as const,
        userId: 'user-1',
      }
      
      mockFilesApi.upload.mockImplementation(async (file, onProgress) => {
        if (onProgress) {
          onProgress(50)
          onProgress(100)
        }
        return uploadedFile
      })
      
      const { result } = renderHook(() => useFileUpload())
      
      const file = createMockFile('test.pdf', 1024, 'application/pdf')
      
      act(() => {
        result.current.addFiles([file])
      })
      
      await act(async () => {
        await result.current.uploadFiles()
      })
      
      await waitFor(() => {
        expect(result.current.uploadedFiles).toHaveLength(1)
      })
      
      expect(mockFilesApi.upload).toHaveBeenCalledTimes(1)
      expect(result.current.uploadedFiles[0]).toEqual(uploadedFile)
    })

    it('handles upload error', async () => {
      mockFilesApi.upload.mockRejectedValue(new Error('Upload failed'))
      
      const { result } = renderHook(() => useFileUpload())
      
      const file = createMockFile('test.pdf', 1024, 'application/pdf')
      
      act(() => {
        result.current.addFiles([file])
      })
      
      await act(async () => {
        await result.current.uploadFiles()
      })
      
      await waitFor(() => {
        expect(result.current.isUploading).toBe(false)
      })
      
      expect(result.current.pendingFiles[0].status).toBe('error')
      expect(result.current.pendingFiles[0].error).toBe('Upload failed')
    })

    it('uploads multiple files sequentially', async () => {
      const uploadedFiles = [
        {
          id: 'file-1',
          name: 'file1.pdf',
          size: 1024,
          mimeType: 'application/pdf',
          url: '/uploads/file1.pdf',
          uploadedAt: new Date(),
          status: 'completed' as const,
          userId: 'user-1',
        },
        {
          id: 'file-2',
          name: 'file2.png',
          size: 2048,
          mimeType: 'image/png',
          url: '/uploads/file2.png',
          uploadedAt: new Date(),
          status: 'completed' as const,
          userId: 'user-1',
        },
      ]
      
      mockFilesApi.upload
        .mockResolvedValueOnce(uploadedFiles[0])
        .mockResolvedValueOnce(uploadedFiles[1])
      
      const { result } = renderHook(() => useFileUpload())
      
      const files = [
        createMockFile('file1.pdf', 1024, 'application/pdf'),
        createMockFile('file2.png', 2048, 'image/png'),
      ]
      
      act(() => {
        result.current.addFiles(files)
      })
      
      await act(async () => {
        await result.current.uploadFiles()
      })
      
      await waitFor(() => {
        expect(result.current.uploadedFiles).toHaveLength(2)
      })
      
      expect(mockFilesApi.upload).toHaveBeenCalledTimes(2)
    })

    it('sets isUploading during upload process', async () => {
      const uploadedFile = {
        id: 'file-1',
        name: 'test.pdf',
        size: 1024,
        mimeType: 'application/pdf',
        url: '/uploads/test.pdf',
        uploadedAt: new Date(),
        status: 'completed' as const,
        userId: 'user-1',
      }
      
      // Create a slow upload
      mockFilesApi.upload.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(uploadedFile), 100))
      )
      
      const { result } = renderHook(() => useFileUpload())
      
      const file = createMockFile('test.pdf', 1024, 'application/pdf')
      
      act(() => {
        result.current.addFiles([file])
      })
      
      // Start upload without awaiting
      let uploadPromise: Promise<void>
      act(() => {
        uploadPromise = result.current.uploadFiles()
      })
      
      // isUploading should be true during upload
      expect(result.current.isUploading).toBe(true)
      
      // Wait for completion
      await act(async () => {
        await uploadPromise
      })
      
      expect(result.current.isUploading).toBe(false)
    })

    it('does not start upload with no pending files', async () => {
      const { result } = renderHook(() => useFileUpload())
      
      await act(async () => {
        await result.current.uploadFiles()
      })
      
      expect(mockFilesApi.upload).not.toHaveBeenCalled()
    })
  })

  describe('Delete uploaded file', () => {
    it('deletes uploaded file', async () => {
      mockFilesApi.delete.mockResolvedValue(undefined)
      
      // First upload a file
      const uploadedFile = {
        id: 'file-1',
        name: 'test.pdf',
        size: 1024,
        mimeType: 'application/pdf',
        url: '/uploads/test.pdf',
        uploadedAt: new Date(),
        status: 'completed' as const,
        userId: 'user-1',
      }
      
      mockFilesApi.upload.mockResolvedValue(uploadedFile)
      
      const { result } = renderHook(() => useFileUpload())
      
      const file = createMockFile('test.pdf', 1024, 'application/pdf')
      
      act(() => {
        result.current.addFiles([file])
      })
      
      await act(async () => {
        await result.current.uploadFiles()
      })
      
      await waitFor(() => {
        expect(result.current.uploadedFiles).toHaveLength(1)
      })
      
      await act(async () => {
        await result.current.deleteUploadedFile('file-1')
      })
      
      expect(mockFilesApi.delete).toHaveBeenCalledWith('file-1')
      expect(result.current.uploadedFiles).toHaveLength(0)
    })

    it('handles delete error', async () => {
      mockFilesApi.delete.mockRejectedValue(new Error('Delete failed'))
      
      const { result } = renderHook(() => useFileUpload())
      
      await expect(async () => {
        await act(async () => {
          await result.current.deleteUploadedFile('file-1')
        })
      }).rejects.toThrow('Delete failed')
    })
  })
})
