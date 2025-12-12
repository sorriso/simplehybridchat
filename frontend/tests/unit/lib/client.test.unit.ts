// path: frontend/tests/unit/lib/client.test.unit.ts
// version: 4

import { apiClient, ApiError } from '@/lib/api/client';

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
  let mockLocalStorage: { [key: string]: string };

  beforeEach(() => {
    // Mock localStorage
    mockLocalStorage = {
      'auth_token': 'test-token-123'
    };

    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn((key: string) => mockLocalStorage[key] || null),
        setItem: jest.fn((key: string, value: string) => {
          mockLocalStorage[key] = value;
        }),
        removeItem: jest.fn((key: string) => {
          delete mockLocalStorage[key];
        }),
        clear: jest.fn(() => {
          mockLocalStorage = {};
        }),
      },
      writable: true,
    });

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
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
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
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
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

    it('should handle 404 error', async () => {
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
  });

  describe('POST requests', () => {
    it('should make successful POST request with data', async () => {
      const mockData = { id: 1, name: 'Created' };
      const requestData = { name: 'Test' };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockData,
      });

      const result = await apiClient.post('/test', requestData);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token-123',
          }),
          body: JSON.stringify(requestData),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should make POST request without body', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      });

      await apiClient.post('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('PUT requests', () => {
    it('should make successful PUT request', async () => {
      const mockData = { id: 1, name: 'Updated' };
      const requestData = { name: 'Updated' };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockData,
      });

      const result = await apiClient.put('/test', requestData);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(requestData),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should make PUT request without body', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      });

      await apiClient.put('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });
  });

  describe('DELETE requests', () => {
    it('should make successful DELETE request', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 204,
        headers: new Headers(),
      });

      const result = await apiClient.delete('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result).toBeUndefined();
    });

    it('should handle DELETE with response body', async () => {
      const mockData = { success: true };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockData,
      });

      const result = await apiClient.delete('/test');

      expect(result).toEqual(mockData);
    });
  });

  describe('Error handling', () => {
    it('should handle network error', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network failed'));

      await expect(apiClient.get('/test')).rejects.toThrow(ApiError);
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        status: 0,
        message: 'Network error or server unreachable',
      });
    });

    it('should handle server error without json response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      await expect(apiClient.get('/test')).rejects.toThrow(ApiError);
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        status: 500,
      });
    });
  });

  describe('uploadFile', () => {
    it('should upload file successfully', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      const mockResponse = { id: 123 };

      // Mock XMLHttpRequest
      const mockXHR = {
        open: jest.fn(),
        send: jest.fn(),
        setRequestHeader: jest.fn(),
        upload: {
          addEventListener: jest.fn(),
        },
        addEventListener: jest.fn((event: string, handler: Function) => {
          if (event === 'load') {
            // Simulate successful upload
            setTimeout(() => {
              (mockXHR as any).status = 200;
              (mockXHR as any).responseText = JSON.stringify(mockResponse);
              handler();
            }, 0);
          }
        }),
      };

      global.XMLHttpRequest = jest.fn(() => mockXHR) as any;

      const result = await apiClient.uploadFile('/upload', mockFile);

      expect(result).toEqual({ id: 123 });
      expect(mockXHR.open).toHaveBeenCalledWith('POST', 'http://localhost:8000/upload');
      expect(mockXHR.setRequestHeader).toHaveBeenCalledWith(
        'Authorization',
        'Bearer test-token-123'
      );
    });

    it('should handle upload error', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      const mockXHR = {
        open: jest.fn(),
        send: jest.fn(),
        setRequestHeader: jest.fn(),
        upload: {
          addEventListener: jest.fn(),
        },
        addEventListener: jest.fn((event: string, handler: Function) => {
          if (event === 'error') {
            setTimeout(() => handler(), 0);
          }
        }),
      };

      global.XMLHttpRequest = jest.fn(() => mockXHR) as any;

      await expect(apiClient.uploadFile('/upload', mockFile)).rejects.toThrow('Network error during upload');
    });

    it('should track upload progress', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      const onProgress = jest.fn();
      const mockResponse = { id: 123 };

      const mockXHR = {
        open: jest.fn(),
        send: jest.fn(),
        setRequestHeader: jest.fn(),
        upload: {
          addEventListener: jest.fn(),
        },
        addEventListener: jest.fn(),
        status: 200,
        responseText: JSON.stringify(mockResponse),
      };

      global.XMLHttpRequest = jest.fn(() => mockXHR) as any;

      const uploadPromise = apiClient.uploadFile('/upload', mockFile, onProgress);

      // Extract and call progress handler
      const progressCall = mockXHR.upload.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'progress'
      );
      const progressHandler = progressCall[1];
      progressHandler({ lengthComputable: true, loaded: 50, total: 100 });

      expect(onProgress).toHaveBeenCalledWith(50);

      // Trigger load to complete the promise
      const loadCall = mockXHR.addEventListener.mock.calls.find(
        (call: any) => call[0] === 'load'
      );
      const loadHandler = loadCall[1];
      loadHandler();

      await uploadPromise;
    });
  });

  describe('Authentication', () => {
    it('should not include Authorization header when no token', async () => {
      // Clear token from localStorage
      mockLocalStorage = {};

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      });

      await apiClient.get('/test');

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const headers = fetchCall[1].headers;
      
      expect(headers['Authorization']).toBeUndefined();
    });
  });
});