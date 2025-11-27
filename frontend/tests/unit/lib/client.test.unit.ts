// path: tests/unit/lib/client.test.unit.ts
// version: 1

import { apiClient, ApiError } from '@/lib/api/client';

// Mock constants
jest.mock('@/lib/utils/constants', () => ({
  MOCK_USER: {
    token: 'test-token-123',
  },
}));

describe('ApiError', () => {
  it('should create ApiError with status and message', () => {
    const error = new ApiError(404, 'Not found');

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(404);
    expect(error.message).toBe('Not found');
    expect(error.name).toBe('ApiError');
  });

  it('should create ApiError with data', () => {
    const errorData = { field: 'email', reason: 'invalid' };
    const error = new ApiError(400, 'Bad request', errorData);

    expect(error.status).toBe(400);
    expect(error.data).toEqual(errorData);
  });
});

describe('apiClient', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('GET requests', () => {
    it('should make successful GET request', async () => {
      const mockData = { id: 1, name: 'Test' };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token-123',
          }),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should include custom headers in GET request', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.get('/test', {
        headers: { 'X-Custom': 'value' },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token-123',
            'X-Custom': 'value',
          }),
        })
      );
    });
  });

  describe('POST requests', () => {
    it('should make successful POST request with data', async () => {
      const postData = { name: 'Test' };
      const mockResponse = { id: 1, ...postData };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.post('/test', postData);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token-123',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should make POST request without body', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.post('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: undefined,
        })
      );
    });
  });

  describe('PUT requests', () => {
    it('should make successful PUT request', async () => {
      const putData = { name: 'Updated' };
      const mockResponse = { id: 1, ...putData };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.put('/test/1', putData);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should make PUT request without body', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.put('/test/1');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'PUT',
          body: undefined,
        })
      );
    });
  });

  describe('DELETE requests', () => {
    it('should make successful DELETE request', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      const result = await apiClient.delete('/test/1');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result).toEqual({ success: true });
    });
  });

  describe('Error handling', () => {
    it('should throw ApiError on HTTP 404', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ message: 'Resource not found' }),
      });

      await expect(apiClient.get('/test')).rejects.toThrow(ApiError);
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        status: 404,
        message: 'Resource not found',
      });
    });

    it('should throw ApiError on HTTP 500', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ message: 'Server error' }),
      });

      await expect(apiClient.get('/test')).rejects.toThrow(ApiError);
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        status: 500,
        message: 'Server error',
      });
    });

    it('should handle error without JSON body', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => {
          throw new Error('No JSON');
        },
      });

      await expect(apiClient.get('/test')).rejects.toMatchObject({
        status: 400,
        message: 'HTTP 400: Bad Request',
      });
    });

    it('should throw ApiError on network error', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network failed'));

      await expect(apiClient.get('/test')).rejects.toThrow(ApiError);
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        status: 0,
        message: 'Network error or server unreachable',
      });
    });

    it('should preserve ApiError when thrown', async () => {
      const apiError = new ApiError(403, 'Forbidden');
      (global.fetch as jest.Mock).mockRejectedValue(apiError);

      await expect(apiClient.get('/test')).rejects.toBe(apiError);
    });
  });

  describe('uploadFile', () => {
    let mockXHR: any;

    beforeEach(() => {
      mockXHR = {
        open: jest.fn(),
        send: jest.fn(),
        setRequestHeader: jest.fn(),
        addEventListener: jest.fn(),
        upload: {
          addEventListener: jest.fn(),
        },
        status: 200,
        responseText: '{"id": 123}',
      };

      global.XMLHttpRequest = jest.fn(() => mockXHR) as any;
    });

    it('should upload file successfully', async () => {
      const file = new File(['content'], 'test.txt', { type: 'text/plain' });

      const uploadPromise = apiClient.uploadFile('/upload', file);

      // Trigger success
      const loadHandler = mockXHR.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'load'
      )[1];
      loadHandler();

      const result = await uploadPromise;

      expect(result).toEqual({ id: 123 });
      expect(mockXHR.open).toHaveBeenCalledWith('POST', 'http://localhost:8000/upload');
      expect(mockXHR.setRequestHeader).toHaveBeenCalledWith(
        'Authorization',
        'Bearer test-token-123'
      );
    });

    it('should track upload progress', async () => {
      const file = new File(['content'], 'test.txt');
      const onProgress = jest.fn();

      apiClient.uploadFile('/upload', file, onProgress);

      // Trigger progress event
      const progressHandler = mockXHR.upload.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'progress'
      )[1];

      progressHandler({ lengthComputable: true, loaded: 50, total: 100 });

      expect(onProgress).toHaveBeenCalledWith(50);
    });

    it('should handle progress without lengthComputable', async () => {
      const file = new File(['content'], 'test.txt');
      const onProgress = jest.fn();

      apiClient.uploadFile('/upload', file, onProgress);

      const progressHandler = mockXHR.upload.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'progress'
      )[1];

      progressHandler({ lengthComputable: false, loaded: 50, total: 100 });

      expect(onProgress).not.toHaveBeenCalled();
    });

    it('should handle upload without progress callback', async () => {
      const file = new File(['content'], 'test.txt');

      const uploadPromise = apiClient.uploadFile('/upload', file);

      const loadHandler = mockXHR.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'load'
      )[1];
      mockXHR.status = 200;
      loadHandler();

      await expect(uploadPromise).resolves.toBeDefined();
    });

    it('should handle upload error with HTTP status', async () => {
      const file = new File(['content'], 'test.txt');

      const uploadPromise = apiClient.uploadFile('/upload', file);

      // Trigger error with HTTP status
      const loadHandler = mockXHR.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'load'
      )[1];
      mockXHR.status = 500;
      mockXHR.statusText = 'Server Error';
      loadHandler();

      await expect(uploadPromise).rejects.toThrow(ApiError);
      await expect(uploadPromise).rejects.toMatchObject({
        status: 500,
        message: 'Upload failed: Server Error',
      });
    });

    it('should handle invalid JSON response', async () => {
      const file = new File(['content'], 'test.txt');

      const uploadPromise = apiClient.uploadFile('/upload', file);

      const loadHandler = mockXHR.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'load'
      )[1];
      mockXHR.status = 200;
      mockXHR.responseText = 'invalid json';
      loadHandler();

      await expect(uploadPromise).rejects.toThrow('Invalid JSON response');
    });

    it('should handle network error during upload', async () => {
      const file = new File(['content'], 'test.txt');

      const uploadPromise = apiClient.uploadFile('/upload', file);

      // Trigger network error
      const errorHandler = mockXHR.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'error'
      )[1];
      errorHandler();

      await expect(uploadPromise).rejects.toThrow(ApiError);
      await expect(uploadPromise).rejects.toMatchObject({
        status: 0,
        message: 'Network error during upload',
      });
    });
  });
});