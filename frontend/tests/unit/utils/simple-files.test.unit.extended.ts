/* path: tests/unit/utils/simple-files.test.unit.extended.ts
   version: 1 - Extended tests for constants.ts, storage.ts, LoginForm.tsx uncovered lines */

   import { API_ENDPOINTS } from '@/lib/utils/constants';
   import { storage } from '@/lib/utils/storage';
   
   describe('Simple Files - Extended Coverage', () => {
     describe('constants.ts - Function endpoints', () => {
       it('should generate conversation endpoint by ID', () => {
         const endpoint = API_ENDPOINTS.CONVERSATION_BY_ID('conv-123');
         expect(endpoint).toBe('/api/conversations/conv-123');
       });
   
       it('should generate group endpoint by ID', () => {
         const endpoint = API_ENDPOINTS.GROUP_BY_ID('group-456');
         expect(endpoint).toBe('/api/groups/group-456');
       });
   
       it('should handle special characters in conversation ID', () => {
         const endpoint = API_ENDPOINTS.CONVERSATION_BY_ID('conv-test-123');
         expect(endpoint).toBe('/api/conversations/conv-test-123');
       });
   
       it('should handle special characters in group ID', () => {
         const endpoint = API_ENDPOINTS.GROUP_BY_ID('group-test-456');
         expect(endpoint).toBe('/api/groups/group-test-456');
       });
     });
   
     describe('storage.ts - Error handling', () => {
       beforeEach(() => {
         localStorage.clear();
         jest.clearAllMocks();
       });
   
       it('should handle error when getting auth token', () => {
         const consoleError = jest.spyOn(console, 'error').mockImplementation();
         
         // Mock localStorage.getItem to throw error
         const originalGetItem = Storage.prototype.getItem;
         Storage.prototype.getItem = jest.fn(() => {
           throw new Error('localStorage error');
         });
   
         const token = storage.getAuthToken();
   
         expect(consoleError).toHaveBeenCalledWith(
           'Error reading auth token:',
           expect.any(Error)
         );
         expect(token).toBeNull();
   
         // Restore
         Storage.prototype.getItem = originalGetItem;
         consoleError.mockRestore();
       });
   
       it('should handle error when setting auth token', () => {
         const consoleError = jest.spyOn(console, 'error').mockImplementation();
         
         // Mock localStorage.setItem to throw error
         const originalSetItem = Storage.prototype.setItem;
         Storage.prototype.setItem = jest.fn(() => {
           throw new Error('localStorage error');
         });
   
         storage.setAuthToken('test-token');
   
         expect(consoleError).toHaveBeenCalledWith(
           'Error setting auth token:',
           expect.any(Error)
         );
   
         // Restore
         Storage.prototype.setItem = originalSetItem;
         consoleError.mockRestore();
       });
   
       it('should handle error when clearing auth token', () => {
         const consoleError = jest.spyOn(console, 'error').mockImplementation();
         
         // Mock localStorage.removeItem to throw error
         const originalRemoveItem = Storage.prototype.removeItem;
         Storage.prototype.removeItem = jest.fn(() => {
           throw new Error('localStorage error');
         });
   
         storage.clearAuthToken();
   
         expect(consoleError).toHaveBeenCalledWith(
           'Error clearing auth token:',
           expect.any(Error)
         );
   
         // Restore
         Storage.prototype.removeItem = originalRemoveItem;
         consoleError.mockRestore();
       });
   
       it('should successfully get auth token when no error', () => {
         localStorage.setItem('auth_token', 'test-token');
         
         const token = storage.getAuthToken();
         
         expect(token).toBe('test-token');
       });
   
       it('should successfully set auth token when no error', () => {
         storage.setAuthToken('new-token');
         
         const token = localStorage.getItem('auth_token');
         
         expect(token).toBe('new-token');
       });
   
       it('should successfully clear auth token when no error', () => {
         localStorage.setItem('auth_token', 'test-token');
         
         storage.clearAuthToken();
         
         const token = localStorage.getItem('auth_token');
         
         expect(token).toBeNull();
       });
     });
   });