// path: tests/unit/utils/storage.test.unit.ts
// version: 1

import { storage } from '@/lib/utils/storage'

describe('storage', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
  })

  describe('set', () => {
    it('sets string value', () => {
      storage.set('test-key', 'test-value')
      
      expect(localStorage.getItem('test-key')).toBe('"test-value"')
    })

    it('sets object value', () => {
      const obj = { name: 'John', age: 30 }
      storage.set('test-key', obj)
      
      expect(JSON.parse(localStorage.getItem('test-key')!)).toEqual(obj)
    })

    it('sets number value', () => {
      storage.set('test-key', 42)
      
      expect(JSON.parse(localStorage.getItem('test-key')!)).toBe(42)
    })

    it('sets boolean value', () => {
      storage.set('test-key', true)
      
      expect(JSON.parse(localStorage.getItem('test-key')!)).toBe(true)
    })

    it('sets array value', () => {
      const arr = [1, 2, 3]
      storage.set('test-key', arr)
      
      expect(JSON.parse(localStorage.getItem('test-key')!)).toEqual(arr)
    })
  })

  describe('get', () => {
    it('gets string value', () => {
      localStorage.setItem('test-key', JSON.stringify('test-value'))
      
      expect(storage.get('test-key')).toBe('test-value')
    })

    it('gets object value', () => {
      const obj = { name: 'John', age: 30 }
      localStorage.setItem('test-key', JSON.stringify(obj))
      
      expect(storage.get('test-key')).toEqual(obj)
    })

    it('gets typed value', () => {
      interface TestData {
        name: string
        age: number
      }
      
      const obj: TestData = { name: 'John', age: 30 }
      localStorage.setItem('test-key', JSON.stringify(obj))
      
      const result = storage.get<TestData>('test-key')
      expect(result).toEqual(obj)
    })

    it('returns null for non-existent key', () => {
      expect(storage.get('non-existent')).toBeNull()
    })

    it('handles JSON parse errors', () => {
      localStorage.setItem('bad-key', 'not valid json')
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      
      expect(storage.get('bad-key')).toBeNull()
      expect(consoleSpy).toHaveBeenCalled()
      
      consoleSpy.mockRestore()
    })
  })

  describe('remove', () => {
    it('removes value', () => {
      storage.set('test-key', 'test-value')
      
      expect(storage.get('test-key')).not.toBeNull()
      
      storage.remove('test-key')
      
      expect(storage.get('test-key')).toBeNull()
    })

    it('handles removing non-existent key', () => {
      expect(() => storage.remove('non-existent')).not.toThrow()
    })
  })

  describe('clear', () => {
    it('clears all values', () => {
      storage.set('key1', 'value1')
      storage.set('key2', 'value2')
      storage.set('key3', 'value3')
      
      expect(storage.get('key1')).not.toBeNull()
      expect(storage.get('key2')).not.toBeNull()
      expect(storage.get('key3')).not.toBeNull()
      
      storage.clear()
      
      expect(storage.get('key1')).toBeNull()
      expect(storage.get('key2')).toBeNull()
      expect(storage.get('key3')).toBeNull()
    })
  })

  describe('Error handling', () => {
    it('handles setItem errors gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      const setItemSpy = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('Quota exceeded')
      })
      
      expect(() => storage.set('test-key', 'value')).not.toThrow()
      expect(consoleSpy).toHaveBeenCalled()
      
      consoleSpy.mockRestore()
      setItemSpy.mockRestore()
    })

    it('handles getItem errors gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      const getItemSpy = jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('Access denied')
      })
      
      expect(storage.get('test-key')).toBeNull()
      expect(consoleSpy).toHaveBeenCalled()
      
      consoleSpy.mockRestore()
      getItemSpy.mockRestore()
    })

    it('handles removeItem errors gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      const removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
        throw new Error('Access denied')
      })
      
      expect(() => storage.remove('test-key')).not.toThrow()
      expect(consoleSpy).toHaveBeenCalled()
      
      consoleSpy.mockRestore()
      removeItemSpy.mockRestore()
    })

    it('handles clear errors gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      const clearSpy = jest.spyOn(Storage.prototype, 'clear').mockImplementation(() => {
        throw new Error('Access denied')
      })
      
      expect(() => storage.clear()).not.toThrow()
      expect(consoleSpy).toHaveBeenCalled()
      
      consoleSpy.mockRestore()
      clearSpy.mockRestore()
    })
  })
})
